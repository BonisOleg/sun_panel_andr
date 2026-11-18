"""Оформлення: швидкість (фонові сповіщення), ідемпотентність, GTM purchase."""

from __future__ import annotations

import json
import re
import time
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from src.catalog.models import Category, Product
from src.commerce import analytics
from src.commerce.models import Cart, Order
from src.notifications.models import EmailLog

SLOW = 2.0


def _slow_ok(*args, **kwargs):
    time.sleep(SLOW)
    return True


class CheckoutBase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Панелі", slug="paneli")
        self.panel = Product.objects.create(
            name="Сонячна панель Longi 650W Hi-MO10",
            slug="longi-650",
            sku="928801932",
            price_uah="5999.00",
            is_published=True,
            category=self.category,
        )
        self.bolt = Product.objects.create(
            name="Гвинт-шуруп M10×200",
            slug="bolt",
            sku="B-1",
            price_uah="40.50",
            is_published=True,
            category=self.category,
        )

    def fill_checkout(self, email="buyer@example.com"):
        self.client.post(reverse("commerce:cart_add", args=[self.panel.pk]), {"qty": 1})
        self.client.post(reverse("commerce:cart_add", args=[self.bolt.pk]), {"qty": 3})
        r = self.client.post(
            reverse("commerce:checkout"),
            {
                "action": "next",
                "customer_name": "Іван Петренко",
                "customer_phone": "0988200000",
                "customer_email": email,
            },
        )
        self.assertEqual(r.status_code, 302)
        r = self.client.post(
            reverse("commerce:checkout"), {"action": "next", "shipping_method": "pickup"}
        )
        self.assertEqual(r.status_code, 302)

    def confirm(self):
        return self.client.post(
            reverse("commerce:checkout"), {"action": "confirm", "payment_method": "invoice"}
        )

    @staticmethod
    def purchase_json(html: str):
        m = re.search(
            r'<script id="gtm-purchase-data" type="application/json">(.*?)</script>', html, re.S
        )
        return json.loads(m.group(1)) if m else None


@override_settings(NOTIFICATIONS_ASYNC=True)
class CheckoutSpeedTests(CheckoutBase):
    def test_confirm_does_not_wait_for_telegram_and_smtp(self):
        self.fill_checkout()
        with mock.patch(
            "src.notifications.services._send_telegram", side_effect=_slow_ok
        ) as tg, mock.patch(
            "src.notifications.services._send_email", side_effect=_slow_ok
        ) as em, self.captureOnCommitCallbacks(execute=False) as callbacks:
            started = time.perf_counter()
            r = self.confirm()
            elapsed = time.perf_counter() - started
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], reverse("commerce:thanks"))
        self.assertLess(elapsed, 1.0, f"confirm took {elapsed:.2f}s")
        tg.assert_not_called()
        em.assert_not_called()
        self.assertEqual(len(callbacks), 1)  # задача поставлена після commit


class CheckoutIdempotencyTests(CheckoutBase):
    def test_double_submit_returns_same_order_not_empty_cart(self):
        self.fill_checkout()
        with self.captureOnCommitCallbacks(execute=False):
            first = self.confirm()
            second = self.confirm()  # другий клік після того, як перший уже оформив
        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(second["Location"], reverse("commerce:thanks"))
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(self.client.session["order_thanks"], Order.objects.get().number)

    def test_converted_cart_returns_existing_order(self):
        """Паралельний запит, що вже тримав той самий кошик, не створює дубль."""
        from django.test import RequestFactory

        from src.commerce import services

        self.fill_checkout()
        with self.captureOnCommitCallbacks(execute=False):
            self.confirm()
        order = Order.objects.get()
        self.assertEqual(order.cart.status, Cart.Status.CONVERTED)
        request = RequestFactory().post("/")
        request.session = self.client.session
        with mock.patch.object(services, "get_or_create_cart", return_value=order.cart):
            again, created = services.place_order_idempotent(request)
        self.assertFalse(created)
        self.assertEqual(again.pk, order.pk)
        self.assertEqual(Order.objects.count(), 1)

    def test_notifications_sent_once_and_marked(self):
        self.fill_checkout()
        with mock.patch(
            "src.notifications.services._send_telegram", return_value=True
        ) as tg, mock.patch(
            "src.notifications.services._send_email", return_value=True
        ) as em, self.captureOnCommitCallbacks(execute=True):
            self.confirm()
            self.confirm()
        self.assertEqual(tg.call_count, 1)
        self.assertEqual(em.call_count, 1)
        order = Order.objects.get()
        self.assertIsNotNone(order.telegram_sent_at)
        self.assertIsNotNone(order.email_sent_at)


class PurchaseEventTests(CheckoutBase):
    def test_purchase_payload_format_and_once(self):
        self.fill_checkout()
        with self.captureOnCommitCallbacks(execute=False):
            self.confirm()
        order = Order.objects.get()
        r = self.client.get(reverse("commerce:thanks"))
        self.assertEqual(r.status_code, 200)
        html = r.content.decode()
        data = self.purchase_json(html)
        self.assertIsNotNone(data)
        self.assertEqual(data["event"], "purchase")
        self.assertEqual(
            data["user_data"], {"email": "buyer@example.com", "phone_number": "+380988200000"}
        )
        self.assertNotIn("user_data", data["ecommerce"])  # на одному рівні з ecommerce
        eco = data["ecommerce"]
        self.assertEqual(eco["transaction_id"], order.number)
        self.assertRegex(order.number, r"^SL-\d{8}-\d{4}$")
        self.assertEqual(eco["currency"], "UAH")
        self.assertIsInstance(eco["value"], float)
        self.assertEqual(eco["value"], 6120.5)  # 5999 + 3×40.50
        self.assertEqual(
            eco["items"],
            [
                {"item_id": "928801932", "item_name": self.panel.name, "price": 5999.0, "quantity": 1},
                {"item_id": "B-1", "item_name": self.bolt.name, "price": 40.5, "quantity": 3},
            ],
        )
        # Числа в JSON — без лапок, крапка, без пробілів/«грн»
        raw = re.search(r'"value": ([^,}]+)', html).group(1)
        self.assertEqual(raw, "6120.5")
        self.assertIn("js/gtm-events.js", html)
        # F5 — без повторної події
        r2 = self.client.get(reverse("commerce:thanks"))
        self.assertEqual(r2.status_code, 200)
        self.assertIsNone(self.purchase_json(r2.content.decode()))
        self.assertContains(r2, order.number)

    def test_empty_email_is_empty_string(self):
        self.fill_checkout(email="")
        with self.captureOnCommitCallbacks(execute=False):
            self.confirm()
        data = self.purchase_json(self.client.get(reverse("commerce:thanks")).content.decode())
        self.assertEqual(data["user_data"]["email"], "")

    def test_no_purchase_before_order(self):
        r = self.client.get(reverse("commerce:thanks"))
        self.assertEqual(r.status_code, 302)

    def test_phone_e164(self):
        self.assertEqual(analytics.phone_e164("+380 98 820 00 00"), "+380988200000")
        self.assertEqual(analytics.phone_e164("0988200000"), "+380988200000")
        self.assertEqual(analytics.phone_e164("123"), "")


class PendingNotificationsCommandTests(CheckoutBase):
    def test_command_sends_never_tried_channels(self):
        from datetime import timedelta

        from django.core.management import call_command
        from django.utils import timezone

        self.fill_checkout()
        with self.captureOnCommitCallbacks(execute=False):  # фон «загубився»
            self.confirm()
        order = Order.objects.get()
        Order.objects.filter(pk=order.pk).update(created_at=timezone.now() - timedelta(minutes=10))
        with mock.patch(
            "src.notifications.services._send_telegram", return_value=True
        ) as tg, mock.patch("src.notifications.services._send_email", return_value=False) as em:
            call_command("send_pending_notifications", stdout=mock.Mock())
        tg.assert_called_once()
        em.assert_called_once()
        order.refresh_from_db()
        self.assertIsNotNone(order.telegram_sent_at)
        self.assertIsNone(order.email_sent_at)
        # Спроба email уже була (лог FAILED) → другий прогін не дублює
        EmailLog.objects.create(
            kind=EmailLog.Kind.ORDER, channel="email", subject="x", status="failed", object_id=order.number
        )
        with mock.patch("src.notifications.services._send_telegram") as tg2, mock.patch(
            "src.notifications.services._send_email"
        ) as em2:
            call_command("send_pending_notifications", stdout=mock.Mock())
        tg2.assert_not_called()
        em2.assert_not_called()

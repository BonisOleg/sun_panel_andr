"""Реальний фоновий потік: сповіщення доходять після відповіді користувачу."""

from __future__ import annotations

import time
from unittest import mock

from django.test import TransactionTestCase, override_settings
from django.urls import reverse

from src.content.models import ContactLead


def _slow_ok(*args, **kwargs):
    time.sleep(0.5)
    return True


@override_settings(NOTIFICATIONS_ASYNC=True)
class BackgroundThreadTests(TransactionTestCase):
    def test_lead_notified_in_background_thread(self):
        with mock.patch(
            "src.notifications.services._send_telegram", side_effect=_slow_ok
        ) as tg, mock.patch("src.notifications.services._send_email", side_effect=_slow_ok):
            started = time.perf_counter()
            r = self.client.post(
                reverse("content:contacts"),
                {"name": "Олена", "phone": "+380501234567", "email": "", "message": "Тест"},
                HTTP_HX_REQUEST="true",
            )
            elapsed = time.perf_counter() - started
            self.assertEqual(r.status_code, 200)
            self.assertLess(elapsed, 0.4)
            lead = ContactLead.objects.get()
            deadline = time.time() + 5
            while time.time() < deadline:
                lead.refresh_from_db()
                if lead.telegram_sent_at and lead.email_sent_at:
                    break
                time.sleep(0.05)
        self.assertEqual(tg.call_count, 1)
        self.assertIsNotNone(lead.telegram_sent_at)
        self.assertIsNotNone(lead.email_sent_at)

"""Форма контактів: миттєва відповідь (фонові сповіщення) + GTM generate_lead."""

from __future__ import annotations

import json
import time
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from src.content.models import ContactLead

VALID = {
    "name": "Олена",
    "phone": "+380501234567",
    "email": "olena@example.com",
    "message": "Потрібна консультація",
}


def _slow_ok(*args, **kwargs):
    time.sleep(2.0)
    return True


class ContactLeadTests(TestCase):
    @override_settings(NOTIFICATIONS_ASYNC=True)
    def test_htmx_success_fast_and_triggers_generate_lead(self):
        with mock.patch(
            "src.notifications.services._send_telegram", side_effect=_slow_ok
        ) as tg, mock.patch(
            "src.notifications.services._send_email", side_effect=_slow_ok
        ), self.captureOnCommitCallbacks(execute=False) as callbacks:
            started = time.perf_counter()
            r = self.client.post(reverse("content:contacts"), VALID, HTTP_HX_REQUEST="true")
            elapsed = time.perf_counter() - started
        self.assertEqual(r.status_code, 200)
        self.assertLess(elapsed, 1.0, f"lead took {elapsed:.2f}s")
        tg.assert_not_called()
        self.assertEqual(len(callbacks), 1)
        self.assertEqual(ContactLead.objects.count(), 1)
        self.assertEqual(
            json.loads(r["HX-Trigger"]), {"solironLead": {"form_id": "contact_form"}}
        )

    def test_invalid_form_has_no_lead_event(self):
        r = self.client.post(
            reverse("content:contacts"), {**VALID, "phone": "+380"}, HTTP_HX_REQUEST="true"
        )
        self.assertEqual(r.status_code, 400)
        self.assertNotIn("HX-Trigger", r)
        self.assertEqual(ContactLead.objects.count(), 0)

    def test_non_htmx_success_has_marker(self):
        r = self.client.post(reverse("content:contacts"), VALID)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'data-gtm-lead="contact_form"')

    def test_get_has_no_marker(self):
        r = self.client.get(reverse("content:contacts"))
        self.assertNotContains(r, "data-gtm-lead=")

    def test_notifications_delivered_after_commit(self):
        with mock.patch(
            "src.notifications.services._send_telegram", return_value=True
        ) as tg, mock.patch(
            "src.notifications.services._send_email", return_value=True
        ) as em, self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("content:contacts"), VALID, HTTP_HX_REQUEST="true")
        tg.assert_called_once()
        em.assert_called_once()
        lead = ContactLead.objects.get()
        self.assertIsNotNone(lead.telegram_sent_at)
        self.assertIsNotNone(lead.email_sent_at)

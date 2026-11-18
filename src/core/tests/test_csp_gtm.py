from django.test import TestCase
from django.urls import reverse

from .test_csp import _parse_csp

GOOGLE = (
    "https://*.googletagmanager.com",
    "https://*.google-analytics.com",
    "https://*.analytics.google.com",
    "https://*.google.com",
    "https://www.google.com.ua",
    "https://www.googleadservices.com",
    "https://*.doubleclick.net",
)


class GtmCspTests(TestCase):
    def test_google_ads_hosts_allowed_without_unsafe_inline(self):
        r = self.client.get(reverse("core:home"))
        d = _parse_csp(r["Content-Security-Policy"])
        for host in GOOGLE:
            self.assertIn(host, d["connect-src"], host)
        for host in ("https://*.googletagmanager.com", "https://www.google.com.ua", "https://*.doubleclick.net", "https://www.googleadservices.com"):
            self.assertIn(host, d["script-src"], host)
        self.assertIn("https://*.doubleclick.net", d["frame-src"])
        self.assertIn("https:", d["img-src"])
        self.assertNotIn("'unsafe-inline'", d["script-src"])
        self.assertContains(r, "js/gtm-events.js")

"""CSP / COOP headers on the home page; legacy /contacts/ redirect."""

from django.test import TestCase
from django.urls import reverse


def _parse_csp(header: str) -> dict[str, list[str]]:
    directives: dict[str, list[str]] = {}
    for part in header.split(";"):
        part = part.strip()
        if not part:
            continue
        tokens = part.split()
        name = tokens[0]
        directives[name] = tokens[1:]
    return directives


class HomePageCSPTests(TestCase):
    def test_home_csp_allows_gtm_ga4_ads(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)

        header = response.get("Content-Security-Policy")
        self.assertTrue(header, "Content-Security-Policy header missing")
        directives = _parse_csp(header)

        connect = directives.get("connect-src", [])
        for host in (
            "https://ad.doubleclick.net",
            "https://www.google.com",
            "https://www.googletagmanager.com",
            "https://*.google-analytics.com",
            "https://*.analytics.google.com",
            "https://*.g.doubleclick.net",
            "https://www.googleadservices.com",
            "https://pagead2.googlesyndication.com",
            "https://*.clarity.ms",
            "https://c.bing.com",
        ):
            self.assertIn(host, connect)

        script = directives.get("script-src", [])
        self.assertTrue(
            any(t.startswith("'nonce-") and t.endswith("'") for t in script),
            f"script-src missing nonce: {script}",
        )
        self.assertIn("https://www.googletagmanager.com", script)
        self.assertIn("https://*.clarity.ms", script)
        for host in (
            "https://*.googletagmanager.com",
            "https://*.google-analytics.com",
            "https://*.googleadservices.com",
            "https://*.doubleclick.net",
            "https://*.google.com",
        ):
            self.assertIn(host, script)
            self.assertIn(host, connect)
        self.assertNotIn("'unsafe-inline'", script)
        self.assertNotIn("'unsafe-eval'", script)

        frame = directives.get("frame-src", [])
        self.assertIn("https://www.googletagmanager.com", frame)
        self.assertIn("https://td.doubleclick.net", frame)
        self.assertIn("https://*.doubleclick.net", frame)

        for name, tokens in directives.items():
            if name != "style-src-attr":
                self.assertNotIn(
                    "'unsafe-inline'",
                    tokens,
                    f"{name} must not contain 'unsafe-inline'",
                )
            for token in tokens:
                self.assertNotEqual(token, "*", f"{name} must not contain bare *")

    def test_home_has_no_coop_header(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Cross-Origin-Opener-Policy", response.headers)


class ContactsLegacyRedirectTests(TestCase):
    def test_contacts_redirects_to_kontakty(self):
        response = self.client.get("/contacts/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.url, reverse("content:contacts"))
        self.assertEqual(response.url, "/kontakty/")

import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from src.content.models import (
    COOKIE_ACCEPT_LABEL_DEFAULT,
    COOKIE_BANNER_TEXT_DEFAULT,
    COOKIE_NECESSARY_LABEL_DEFAULT,
    COOKIE_POLICY_LINK_LABEL_DEFAULT,
    COOKIE_SETTINGS_LINK_LABEL_DEFAULT,
    SiteSettings,
)

_SCRIPT_OPEN = re.compile(r"<script\b([^>]*)>", re.IGNORECASE)


class CookieBannerTests(TestCase):
    def test_banner_renders_admin_labels(self):
        settings_obj = SiteSettings.load()
        settings_obj.cookie_banner_title = "Заголовок з адмінки"
        settings_obj.cookie_banner_text = "<p>Текст банера з адмінки</p>"
        settings_obj.cookie_accept_label = "Згоден на всі"
        settings_obj.cookie_necessary_label = "Тільки потрібні"
        settings_obj.cookie_policy_link_label = "Читати політику"
        settings_obj.cookie_settings_link_label = "Змінити cookie"
        settings_obj.save()

        html = self.client.get(reverse("core:home")).content.decode()
        for label in (
            "Заголовок з адмінки",
            "Текст банера з адмінки",
            "Згоден на всі",
            "Тільки потрібні",
            "Читати політику",
            "Змінити cookie",
        ):
            self.assertIn(label, html)
        self.assertNotIn(COOKIE_ACCEPT_LABEL_DEFAULT, html)
        self.assertNotIn(COOKIE_NECESSARY_LABEL_DEFAULT, html)
        self.assertNotIn(COOKIE_SETTINGS_LINK_LABEL_DEFAULT, html)
        self.assertIn("cookie-banner__title", html)
        self.assertRegex(html, r'id="cookie-banner"[^>]*\bhidden\b')

    def test_empty_labels_fall_back_to_current_texts(self):
        SiteSettings.load()
        SiteSettings.objects.filter(pk=1).update(
            cookie_banner_title="",
            cookie_banner_text="",
            cookie_accept_label="",
            cookie_necessary_label="",
            cookie_policy_link_label="",
            cookie_settings_link_label="",
        )
        html = self.client.get(reverse("core:home")).content.decode()
        self.assertIn(COOKIE_BANNER_TEXT_DEFAULT, html)
        self.assertIn(COOKIE_ACCEPT_LABEL_DEFAULT, html)
        self.assertIn(COOKIE_NECESSARY_LABEL_DEFAULT, html)
        self.assertIn(COOKIE_POLICY_LINK_LABEL_DEFAULT, html)
        self.assertIn(COOKIE_SETTINGS_LINK_LABEL_DEFAULT, html)
        self.assertNotIn("cookie-banner__title", html)

    def test_banner_html_is_sanitized_and_labels_are_escaped(self):
        SiteSettings.load()
        SiteSettings.objects.filter(pk=1).update(
            cookie_banner_title="<script>bad()</script>",
            cookie_banner_text=(
                "<p>Безпечний <strong>текст</strong></p><script>bad()</script>"
            ),
            cookie_accept_label="<b>Не кнопка</b>",
        )
        html = self.client.get(reverse("core:home")).content.decode()
        self.assertEqual(html.count("bad()"), 1)
        self.assertIn("&lt;script&gt;bad()&lt;/script&gt;", html)
        self.assertNotIn("<script>bad()", html)
        self.assertIn("<strong>текст</strong>", html)
        self.assertIn("&lt;b&gt;Не кнопка&lt;/b&gt;", html)

    def test_save_strips_unsafe_banner_markup(self):
        settings_obj = SiteSettings.load()
        settings_obj.cookie_banner_title = "<script>alert(1)</script>Заголовок"
        settings_obj.cookie_banner_text = "<p>Ок</p><script>alert(1)</script>"
        settings_obj.cookie_accept_label = '<img src="x" onerror="alert(1)">Усі'
        settings_obj.cookie_necessary_label = "   "
        settings_obj.save()
        settings_obj.refresh_from_db()
        self.assertEqual(settings_obj.cookie_banner_title, "Заголовок")
        self.assertNotIn("alert(1)", settings_obj.cookie_banner_title)
        self.assertNotIn("<script", settings_obj.cookie_banner_text.lower())
        self.assertIn("Ок", settings_obj.cookie_banner_text)
        self.assertEqual(settings_obj.cookie_accept_label, "Усі")
        self.assertEqual(settings_obj.cookie_necessary_label, COOKIE_NECESSARY_LABEL_DEFAULT)

    def test_home_consent_script_is_in_head_before_gtm_and_not_inline(self):
        html = self.client.get(reverse("core:home")).content.decode()
        head, sep, _rest = html.partition("</head>")
        self.assertEqual(sep, "</head>")
        self.assertIn("js/consent.js", head)
        consent_at = html.find("js/consent.js")
        gtm_at = html.find("googletagmanager")
        if gtm_at != -1:
            self.assertLess(consent_at, gtm_at)
        opens = list(_SCRIPT_OPEN.finditer(html))
        self.assertGreater(len(opens), 0)
        for match in opens:
            self.assertRegex(match.group(1), r"\bsrc\s*=", match.group(0))

    def test_sitesettings_admin_shows_cookie_fieldset(self):
        get_user_model().objects.create_superuser("cookie-admin", "cookie@example.com", "pass")
        self.client.force_login(get_user_model().objects.get(username="cookie-admin"))
        obj = SiteSettings.load()
        response = self.client.get(reverse("admin:content_sitesettings_change", args=[obj.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cookie-банер")
        self.assertContains(response, "id_cookie_banner_text")
        self.assertContains(response, "id_cookie_accept_label")
        self.assertContains(response, "id_cookie_settings_link_label")

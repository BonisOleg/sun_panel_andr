from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from src.content.management.commands.publish_legal_pages import LEGAL_DIR, PAGES
from src.content.models import ContentPage


class PublishLegalPagesTests(TestCase):
    def test_command_is_idempotent_and_drops_placeholders(self):
        privacy = ContentPage.objects.get(slug="polityka-konfidentsiynosti")
        privacy.title = "Кастомний заголовок"
        privacy.seo_title = "Кастом SEO"
        privacy.seo_description = "Кастом опис"
        privacy.seo_keywords = "ключ"
        privacy.sort_order = 77
        privacy.body = "<p>УТОЧНИТИ чернетка</p>"
        privacy.is_published = False
        privacy.save()

        offer = ContentPage.objects.get(slug="publichnyy-dohovir")
        offer.seo_title = "SEO оферти"
        offer.save()

        first = StringIO()
        call_command("publish_legal_pages", stdout=first)
        first_out = first.getvalue()
        self.assertIn("polityka-konfidentsiynosti: оновлено body, is_published", first_out)
        self.assertIn("publichnyy-dohovir: оновлено body", first_out)

        privacy.refresh_from_db()
        offer.refresh_from_db()
        self.assertEqual(privacy.title, "Кастомний заголовок")
        self.assertEqual(privacy.seo_title, "Кастом SEO")
        self.assertEqual(privacy.seo_description, "Кастом опис")
        self.assertEqual(privacy.seo_keywords, "ключ")
        self.assertEqual(privacy.sort_order, 77)
        self.assertTrue(privacy.is_published)
        self.assertNotIn("УТОЧНИТИ", privacy.body)
        self.assertIn("ім'я, телефон, e-mail, текст повідомлення", privacy.body)
        self.assertIn("DigitalOcean, LLC (дата-центр у м. Франкфурт-на-Майні, Німеччина)", privacy.body)
        self.assertIn("ПІБ", privacy.body)
        self.assertIn("«Прийняти всі»", privacy.body)
        self.assertIn("«Лише необхідні»", privacy.body)
        self.assertIn("«Налаштування cookies»", privacy.body)
        self.assertIn("12 місяців", privacy.body)
        self.assertNotIn("законний інтерес", privacy.body)
        self.assertNotIn("наразі немає", privacy.body)

        self.assertEqual(offer.seo_title, "SEO оферти")
        self.assertIn('href="/polityka-konfidentsiynosti/"', offer.body)
        self.assertNotIn("УТОЧНИТИ", offer.body)

        privacy_body = privacy.body
        offer_body = offer.body
        privacy_updated = privacy.updated_at
        offer_updated = offer.updated_at

        second = StringIO()
        call_command("publish_legal_pages", stdout=second)
        second_out = second.getvalue()
        self.assertIn("polityka-konfidentsiynosti: без змін", second_out)
        self.assertIn("publichnyy-dohovir: без змін", second_out)

        privacy.refresh_from_db()
        offer.refresh_from_db()
        self.assertEqual(privacy.body, privacy_body)
        self.assertEqual(offer.body, offer_body)
        self.assertEqual(privacy.updated_at, privacy_updated)
        self.assertEqual(offer.updated_at, offer_updated)
        self.assertEqual(privacy.title, "Кастомний заголовок")
        self.assertEqual(offer.seo_title, "SEO оферти")

    def test_source_files_have_no_placeholders(self):
        for spec in PAGES:
            text = (LEGAL_DIR / spec["filename"]).read_text(encoding="utf-8")
            self.assertNotIn("УТОЧНИТИ", text)
            self.assertTrue(text.strip())

    def test_creates_missing_page_without_touching_the_other(self):
        ContentPage.objects.filter(slug="publichnyy-dohovir").delete()
        kept = ContentPage.objects.get(slug="polityka-konfidentsiynosti")
        kept.title = "Лишається"
        kept.save()

        out = StringIO()
        call_command("publish_legal_pages", stdout=out)
        text = out.getvalue()
        self.assertIn("publichnyy-dohovir: створено", text)

        created = ContentPage.objects.get(slug="publichnyy-dohovir")
        self.assertEqual(created.title, "Публічний договір")
        self.assertEqual(created.seo_title, "Публічний договір (оферта)")
        self.assertTrue(created.is_published)
        self.assertNotIn("УТОЧНИТИ", created.body)
        self.assertEqual(
            ContentPage.objects.get(slug="polityka-konfidentsiynosti").title,
            "Лишається",
        )
        self.assertTrue((Path(LEGAL_DIR) / "oferta_uk.html").is_file())

    def test_rendered_legal_pages_have_no_placeholder(self):
        call_command("publish_legal_pages", stdout=StringIO())
        privacy = self.client.get(
            reverse("content:page", kwargs={"slug": "polityka-konfidentsiynosti"})
        )
        offer = self.client.get(
            reverse("content:page", kwargs={"slug": "publichnyy-dohovir"})
        )
        self.assertEqual(privacy.status_code, 200)
        self.assertEqual(offer.status_code, 200)
        self.assertNotIn("УТОЧНИТИ", privacy.content.decode())
        self.assertNotIn("УТОЧНИТИ", offer.content.decode())
        self.assertContains(privacy, "ім'я, телефон, e-mail, текст повідомлення")

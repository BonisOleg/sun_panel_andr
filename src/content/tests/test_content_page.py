from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from tinymce.widgets import TinyMCE

from src.content.admin import ContentPageAdmin
from src.content.models import ContentPage


class ContentPageAdminTests(TestCase):
    def test_body_widget_is_tinymce_and_save_sanitizes(self):
        user = get_user_model().objects.create_superuser(
            "pages-admin", "pages@example.com", "pass"
        )
        request = RequestFactory().get("/")
        request.user = user
        model_admin = ContentPageAdmin(ContentPage, AdminSite())
        self.assertIn("body", model_admin.tinymce_fields)
        formfield = model_admin.formfield_for_dbfield(
            ContentPage._meta.get_field("body"),
            request,
        )
        self.assertIsInstance(formfield.widget, TinyMCE)

        self.client.force_login(user)
        page = ContentPage.objects.get(slug="polityka-konfidentsiynosti")
        response = self.client.get(reverse("admin:content_contentpage_change", args=[page.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "tinymce")
        self.assertContains(response, "id_body")

        page.body = "<p>Живий текст</p><script>alert(1)</script>"
        model_admin.save_model(request, page, form=None, change=True)
        page.refresh_from_db()
        self.assertIn("Живий текст", page.body)
        self.assertNotIn("<script", page.body.lower())
        self.assertNotIn("alert(1)", page.body)

    def test_detail_renders_body_only_from_database(self):
        page = ContentPage.objects.get(slug="polityka-konfidentsiynosti")
        page.body = "<p>Маркер лише з бази 918273</p><script>alert(1)</script>"
        page.is_published = True
        page.save()

        response = self.client.get(reverse("content:page", kwargs={"slug": page.slug}))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("Маркер лише з бази 918273", html)
        self.assertNotIn("alert(1)", html)
        self.assertNotIn("<script>alert", html)
        self.assertNotIn("Опишіть, які персональні дані збираються", html)

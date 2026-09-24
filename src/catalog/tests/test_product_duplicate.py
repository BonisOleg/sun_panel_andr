from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from src.catalog.models import Product, ProductImage
from src.catalog.services import copy_product_images, product_duplicate_initial

_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x00\x03\x00\x01\x00\x05\xfe\xd4\xef\x00\x00\x00\x00IEND\xaeB`\x82"
)


@override_settings(MEDIA_ROOT="/tmp/soliron-duplicate-test-media")
class ProductDuplicateTests(TestCase):
    def setUp(self):
        self.source = Product.objects.create(
            name="Панель тестова сонячна",
            slug="panel-test",
            sku="SOL-1",
            description="<p>Опис</p>",
            price_uah="100.00",
            is_published=True,
            seo_title="SEO",
            weight_kg="25.000",
        )
        ProductImage.objects.create(
            product=self.source,
            image=SimpleUploadedFile("panel.png", _PNG, content_type="image/png"),
            alt="фасад",
            is_main=True,
            sort_order=1,
        )
        user = get_user_model().objects.create_superuser(
            "admin", "admin@example.com", "pass"
        )
        self.client.force_login(user)

    def test_initial_clears_identity_fields(self):
        initial = product_duplicate_initial(self.source)
        self.assertEqual(initial["name"], "")
        self.assertEqual(initial["slug"], "")
        self.assertEqual(initial["sku"], "")
        self.assertFalse(initial["is_published"])
        self.assertEqual(initial["price_uah"], self.source.price_uah)
        self.assertEqual(initial["description"], self.source.description)
        self.assertEqual(initial["seo_title"], "SEO")

    def test_add_form_is_prefilled_and_unsaved(self):
        url = reverse("admin:catalog_product_add")
        response = self.client.get(f"{url}?duplicate_from={self.source.pk}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="duplicate_from"')
        self.assertContains(response, f'value="{self.source.pk}"')
        self.assertEqual(Product.objects.count(), 1)
        self.assertContains(response, "Копія «Панель тестова сонячна»")

    def test_admin_save_rejects_empty_sku(self):
        url = reverse("admin:catalog_product_add")
        response = self.client.post(
            f"{url}?duplicate_from={self.source.pk}",
            {
                "duplicate_from": self.source.pk,
                "name": "Панель тестова друга",
                "slug": "panel-test-2",
                "sku": "",
                "description": "<p>Опис</p>",
                "price_uah": "100.00",
                "availability": Product.Availability.IN_STOCK,
                "availability_label": "",
                "card_badge_text": "",
                "card_badge_style": "stock",
                "weight_kg": "25.000",
                "length_cm": "200",
                "width_cm": "110",
                "height_cm": "5",
                "sort_order": "0",
                "seo_title": "SEO",
                "seo_description": "",
                "seo_keywords": "",
                "images-TOTAL_FORMS": "0",
                "images-INITIAL_FORMS": "0",
                "images-MIN_NUM_FORMS": "0",
                "images-MAX_NUM_FORMS": "1000",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 1)

    def test_admin_save_copies_photos_with_new_sku(self):
        url = reverse("admin:catalog_product_add")
        response = self.client.post(
            f"{url}?duplicate_from={self.source.pk}",
            {
                "duplicate_from": self.source.pk,
                "name": "Панель тестова друга",
                "slug": "panel-test-2",
                "sku": "SOL-2",
                "description": "<p>Опис</p>",
                "price_uah": "100.00",
                "availability": Product.Availability.IN_STOCK,
                "availability_label": "",
                "card_badge_text": "",
                "card_badge_style": "stock",
                "weight_kg": "25.000",
                "length_cm": "200",
                "width_cm": "110",
                "height_cm": "5",
                "sort_order": "0",
                "seo_title": "SEO",
                "seo_description": "",
                "seo_keywords": "",
                "images-TOTAL_FORMS": "0",
                "images-INITIAL_FORMS": "0",
                "images-MIN_NUM_FORMS": "0",
                "images-MAX_NUM_FORMS": "1000",
            },
        )
        self.assertEqual(response.status_code, 302, response.content[:1500])
        clone = Product.objects.get(slug="panel-test-2")
        self.assertEqual(clone.sku, "SOL-2")
        self.assertFalse(clone.is_published)
        self.assertEqual(clone.images.count(), 1)
        self.assertEqual(self.source.images.count(), 1)
        self.assertNotEqual(
            clone.images.get().image.name,
            self.source.images.get().image.name,
        )

    def test_save_copies_image_file(self):
        clone = Product.objects.create(
            name="Панель тестова копія",
            slug="panel-test-copy",
            sku="SOL-COPY",
            is_published=False,
        )
        copied, skipped = copy_product_images(self.source, clone)
        self.assertEqual((copied, skipped), (1, 0))
        image = clone.images.get()
        self.assertTrue(image.is_main)
        self.assertEqual(image.alt, "фасад")
        self.assertNotEqual(image.image.name, self.source.images.get().image.name)
        self.source.images.get().image.open("rb").close()

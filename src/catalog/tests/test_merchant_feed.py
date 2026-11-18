"""Google Merchant фід: усі товари, availability, price, product_type, labels, title."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from src.catalog import merchant
from src.catalog.models import Category, Product, ProductImage

G = "{http://base.google.com/ns/1.0}"
_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x00\x03\x00\x01\x00\x05\xfe\xd4\xef\x00\x00\x00\x00IEND\xaeB`\x82"
)


@override_settings(MEDIA_ROOT="/tmp/soliron-feed-test-media")
class MerchantFeedTests(TestCase):
    def setUp(self):
        self.panels = Category.objects.create(name="Панелі", slug="paneli")
        self.zinc = Category.objects.create(name="Кріплення цинк", slug="kriplennya", merchant_label="Zinc_Mounts")
        self.cable = Category.objects.create(name="Кабель", slug="kabel")
        self.alu = Category.objects.create(
            name="Безпрофільна алюмінієва система", slug="bezprofilna-alyuminiyeva-sistema"
        )

    def _product(self, n, **kw):
        defaults = dict(
            name=f"Товар {n}", slug=f"p-{n}", sku=f"S{n}", price_uah="100.00", is_published=True
        )
        defaults.update(kw)
        p = Product.objects.create(**defaults)
        ProductImage.objects.create(
            product=p, image=SimpleUploadedFile(f"{n}.png", _PNG, content_type="image/png"), is_main=True
        )
        return p

    def _items(self):
        r = self.client.get(reverse("catalog:google_feed"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("application/xml", r["Content-Type"])
        root = ET.fromstring(r.content)  # валідний XML
        self.assertIn(b'xmlns:g="http://base.google.com/ns/1.0"', r.content)
        return {i.findtext(f"{G}id"): i for i in root.iter("item")}

    def test_all_published_products_no_limit(self):
        for n in range(60):
            self._product(n, category=self.zinc)
        self._product("hidden", is_published=False)
        items = self._items()
        self.assertEqual(len(items), 60)
        self.assertNotIn("Shidden", items)

    def test_fields_mapping(self):
        self._product(
            "longi",
            name="Панель Longi 650w hi-mo10 Сонячна панель лонги 650вт химо 10 лонгі 650 хімо 10",
            price_uah="5999",
            category=self.panels,
        )
        self._product(
            "kr",
            name="Т-кронштейн для бітумної черепиці кріплення для панелей кронштейн",
            price_uah="85.5",
            category=self.zinc,
            availability=Product.Availability.ON_ORDER,
        )
        self._product("kbe", name="Кабель для сонячних панелей 6мм2 чорний KBE Німеччина", category=self.cable,
                      availability=Product.Availability.OUT_OF_STOCK)
        self._product("alu", name="Блок алюмінієвий 20см", category=self.alu, price_uah="1000.00",
                      availability=Product.Availability.CALL, feed_title="Блок алюмінієвий Soliron 20 см")
        items = self._items()

        longi = items["Slongi"]
        self.assertEqual(longi.findtext(f"{G}title"), "Сонячна панель Longi 650W Hi-MO10")
        self.assertEqual(longi.findtext(f"{G}price"), "5999.00 UAH")
        self.assertEqual(longi.findtext(f"{G}availability"), "in_stock")
        self.assertEqual(longi.findtext(f"{G}product_type"), "Панелі")
        self.assertEqual(longi.findtext(f"{G}custom_label_0"), "Panels")
        self.assertEqual(longi.findtext(f"{G}custom_label_1"), "High_Ticket")
        self.assertEqual(longi.findtext(f"{G}custom_label_2"), "Longi")
        self.assertEqual(longi.findtext(f"{G}brand"), "Longi")

        kr = items["Skr"]
        self.assertEqual(kr.findtext(f"{G}title"), "Т-кронштейн Soliron для бітумної черепиці")
        self.assertEqual(kr.findtext(f"{G}price"), "85.50 UAH")
        self.assertEqual(kr.findtext(f"{G}availability"), "preorder")
        self.assertTrue(kr.findtext(f"{G}availability_date"))
        self.assertEqual(kr.findtext(f"{G}custom_label_0"), "Zinc_Mounts")
        self.assertEqual(kr.findtext(f"{G}custom_label_1"), "Low_Ticket")
        self.assertEqual(kr.findtext(f"{G}custom_label_2"), "Soliron")

        kbe = items["Skbe"]
        self.assertEqual(kbe.findtext(f"{G}availability"), "out_of_stock")
        self.assertEqual(kbe.findtext(f"{G}custom_label_0"), "Cables")
        self.assertEqual(kbe.findtext(f"{G}custom_label_2"), "KBE")

        alu = items["Salu"]
        self.assertEqual(alu.findtext(f"{G}title"), "Блок алюмінієвий Soliron 20 см")  # feed_title з адмінки
        self.assertEqual(alu.findtext(f"{G}availability"), "in_stock")
        self.assertEqual(alu.findtext(f"{G}custom_label_0"), "Aluminum_System")
        self.assertEqual(alu.findtext(f"{G}custom_label_1"), "High_Ticket")  # >=1000

    def test_explicit_brand_wins(self):
        self._product("x", name="Конектор МС4 для сонячних панелей", category=self.cable, brand="Staubli")
        item = self._items()["Sx"]
        self.assertEqual(item.findtext(f"{G}custom_label_2"), "Staubli")
        self.assertEqual(item.findtext(f"{G}title"), "Конектор Staubli МС4 для сонячних панелей")

    def test_title_limit_and_helpers(self):
        self.assertLessEqual(len(merchant.auto_title("Слово " * 80, "Soliron")), 150)
        self.assertEqual(merchant.price_label(999.99), "Low_Ticket")
        self.assertEqual(merchant.format_price("5999"), "5999.00 UAH")
        self.assertEqual(
            merchant.auto_title("Сонячна панель 620вт Jinko solar 620w сонячна 620вт", "Jinko", "Panels"),
            "Сонячна панель Jinko 620W",
        )

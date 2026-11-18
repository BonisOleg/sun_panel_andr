"""Дефолти Google Merchant: custom_label_0 за slug категорії, бренд з назви товару.

Заповнює лише порожні поля — ручні правки в адмінці не перезаписуються.
"""

import re

from django.db import migrations

LABELS = {
    "paneli": "Panels",
    "kriplennya": "Zinc_Mounts",
    "bezprofilna-alyuminiyeva-sistema": "Aluminum_System",
    "kabel": "Cables",
}

# Копія src.catalog.merchant.KNOWN_BRANDS (міграції не імпортують живий код)
BRANDS = (
    (r"\blongi\b|лонг[іи]", "Longi"),
    (r"\bjinko\b|джинко", "Jinko"),
    (r"\bleapton\b", "Leapton"),
    (r"\bkbe\b", "KBE"),
    (r"\btrina\b", "Trina"),
    (r"\bja\s*solar\b", "JA Solar"),
    (r"\bcanadian\s*solar\b", "Canadian Solar"),
    (r"\brisen\b", "Risen"),
    (r"\bst[aä]ubli\b", "Staubli"),
)


def forwards(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    Product = apps.get_model("catalog", "Product")
    for slug, label in LABELS.items():
        Category.objects.filter(slug=slug, merchant_label="").update(merchant_label=label)
    for product in Product.objects.filter(brand="").only("pk", "name"):
        for pattern, brand in BRANDS:
            if re.search(pattern, product.name or "", re.I):
                Product.objects.filter(pk=product.pk).update(brand=brand)
                break


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0005_merchant_feed_fields"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]

"""Mutations + business rules."""

from __future__ import annotations

from pathlib import Path

from django.core.files.base import ContentFile

from src.catalog.models import Product, ProductImage


def product_duplicate_initial(source: Product) -> dict:
    """Поля нової картки. Назва, slug і SKU менеджер заповнює сам."""
    return {
        "duplicate_from": source.pk,
        "category": source.category_id,
        "description": source.description,
        "price_uah": source.price_uah,
        "availability": source.availability,
        "availability_label": source.availability_label,
        "card_badge_text": source.card_badge_text,
        "card_badge_style": source.card_badge_style,
        "weight_kg": source.weight_kg,
        "length_cm": source.length_cm,
        "width_cm": source.width_cm,
        "height_cm": source.height_cm,
        "seo_title": source.seo_title,
        "seo_description": source.seo_description,
        "seo_keywords": source.seo_keywords,
        "sort_order": source.sort_order,
        "is_published": False,
        "name": "",
        "slug": "",
        "sku": "",
    }


def copy_product_images(source: Product, target: Product) -> tuple[int, int]:
    """Копіює фото в нові файли. Відсутній файл пропускає, оригінал не чіпає."""
    copied = 0
    skipped = 0
    has_main = target.images.filter(is_main=True).exists()
    for image in source.images.order_by("sort_order", "id"):
        if not image.image:
            skipped += 1
            continue
        try:
            with image.image.open("rb") as handle:
                payload = handle.read()
        except (FileNotFoundError, OSError, ValueError):
            skipped += 1
            continue
        if not payload:
            skipped += 1
            continue
        is_main = bool(image.is_main) and not has_main
        clone = ProductImage(
            product=target,
            alt=image.alt,
            is_main=is_main,
            sort_order=image.sort_order,
        )
        filename = Path(image.image.name).name or "product.webp"
        clone.image.save(filename, ContentFile(payload), save=True)
        copied += 1
        if is_main:
            has_main = True
    return copied, skipped

"""Імпорт data/olx_7wlnq → catalog.Category / Product / ProductImage."""

from __future__ import annotations

import json
import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable

from django.core.files import File
from django.db import transaction
from django.utils.text import slugify

from src.catalog.models import Category, Product, ProductImage

from .constants import SOURCE, categories_path, data_root, products_dir
from .discover import _slug_hint

logger = logging.getLogger(__name__)

ProgressCb = Callable[[str], None]
SKIP_ROOT_NAMES = {"Усі оголошення", "Все объявления"}


def _noop(msg: str) -> None:
    return None


def _unique_slug(base: str, *, model, exclude_pk: int | None = None) -> str:
    base = (base or "item")[:140].strip("-") or "item"
    slug = base
    n = 2
    while True:
        qs = model.objects.filter(slug=slug)
        if exclude_pk is not None:
            qs = qs.exclude(pk=exclude_pk)
        if not qs.exists():
            return slug
        suffix = f"-{n}"
        slug = f"{base[: 160 - len(suffix)]}{suffix}"
        n += 1


def _ua_slug(text: str) -> str:
    """Slug з кирилиці (django slugify з allow_unicode + наш hint)."""
    hint = _slug_hint(text)
    if hint:
        return hint[:160]
    return slugify(text, allow_unicode=True)[:160] or "item"


def _parse_price(raw: Any) -> Decimal | None:
    if raw is None or raw == "":
        return None
    try:
        return Decimal(str(raw).replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _load_tree(base_dir: Path) -> dict[str, Any]:
    path = categories_path(base_dir)
    if not path.exists():
        raise FileNotFoundError(f"Немає {path} — спочатку parse_olx_7wlnq")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_products(base_dir: Path) -> list[dict[str, Any]]:
    folder = products_dir(base_dir)
    if not folder.exists():
        raise FileNotFoundError(f"Немає {folder} — спочатку parse_olx_7wlnq")
    items: list[dict[str, Any]] = []
    for path in sorted(folder.glob("*.json")):
        items.append(json.loads(path.read_text(encoding="utf-8")))
    return items


def _ensure_category(
    name: str,
    parent: Category | None,
    *,
    apply: bool,
    cache: dict[str, Category],
) -> Category | None:
    if name in SKIP_ROOT_NAMES:
        return parent

    parent_key = (
        f"pk:{parent.pk}"
        if parent is not None and getattr(parent, "pk", None)
        else f"name:{getattr(parent, 'name', None) or 'root'}"
    )
    cache_key = f"{parent_key}::{name}"
    if cache_key in cache:
        return cache[cache_key]

    slug_base = _ua_slug(name)

    if not apply:
        fake = Category(name=name, slug=slug_base, parent=parent)
        cache[cache_key] = fake
        return fake

    existing = None
    if parent is None or getattr(parent, "pk", None):
        existing = Category.objects.filter(name=name, parent=parent).first()
        if existing is None and parent is None:
            existing = Category.objects.filter(slug=slug_base, parent__isnull=True).first()

    if existing:
        cat = existing
    else:
        slug = _unique_slug(slug_base, model=Category)
        cat = Category.objects.create(
            name=name,
            slug=slug,
            parent=parent if parent is not None and parent.pk else None,
            is_active=True,
            sort_order=0,
        )

    cache[cache_key] = cat
    return cat


def import_category_tree(
    tree: dict[str, Any],
    *,
    apply: bool,
    progress: ProgressCb = _noop,
) -> dict[str, Category]:
    """
    Імпорт дерева. Повертає map name→Category (листові + проміжні).
    Корінь «Усі оголошення» пропускається.
    """
    by_name: dict[str, Category] = {}
    cache: dict[str, Category] = {}

    def walk(node: dict[str, Any], parent: Category | None) -> None:
        name = (node.get("name") or "").strip()
        if not name:
            return

        if name in SKIP_ROOT_NAMES:
            current = parent
        else:
            current = _ensure_category(name, parent, apply=apply, cache=cache)
            if current is not None:
                by_name[name] = current

        for child in node.get("children") or []:
            walk(child, current)

    walk(tree, None)
    progress(f"Категорії в map: {len(by_name)} (apply={apply})")
    return by_name


def _category_for_product(
    product: dict[str, Any],
    by_name: dict[str, Category],
    *,
    apply: bool,
    cache: dict[str, Category],
) -> Category | None:
    path = [p for p in (product.get("category_path") or []) if p not in SKIP_ROOT_NAMES]
    parent: Category | None = None
    leaf: Category | None = None
    for name in path:
        leaf = _ensure_category(name, parent, apply=apply, cache=cache)
        if leaf is not None and getattr(leaf, "name", None):
            by_name[name] = leaf
        parent = leaf
    if leaf is None and product.get("category_leaf"):
        leaf = by_name.get(product["category_leaf"])
    return leaf


def _build_description(product: dict[str, Any]) -> str:
    desc = (product.get("description") or "").strip()
    params = product.get("params") or {}
    extra_lines = []
    for k, v in params.items():
        extra_lines.append(f"{k}: {v}")
    url = product.get("source_url") or ""
    if url and url not in desc:
        extra_lines.append(f"Джерело OLX: {url}")
    if extra_lines:
        block = "\n".join(extra_lines)
        if desc:
            return f"{desc}\n\n{block}"
        return block
    return desc


def _sync_images(product_obj: Product, product: dict[str, Any], *, apply: bool) -> int:
    if not apply:
        return sum(1 for x in (product.get("images_local") or []) if x.get("ok") and x.get("path"))

    ProductImage.objects.filter(product=product_obj).delete()
    count = 0
    for idx, item in enumerate(product.get("images_local") or []):
        if not item.get("ok") or not item.get("path"):
            continue
        path = Path(item["path"])
        if not path.is_file():
            logger.warning("Немає файлу фото: %s", path)
            continue
        filename = item.get("filename") or path.name
        img = ProductImage(
            product=product_obj,
            alt=(product_obj.name or "")[:255],
            is_main=(count == 0),
            sort_order=idx,
        )
        with path.open("rb") as fh:
            img.image.save(filename, File(fh), save=True)
        count += 1
    return count


def import_products(
    products: list[dict[str, Any]],
    by_name: dict[str, Category],
    *,
    apply: bool,
    publish: bool,
    progress: ProgressCb = _noop,
) -> dict[str, int]:
    stats = {"created": 0, "updated": 0, "images": 0, "skipped": 0}
    cache: dict[str, Category] = {}

    for product in products:
        sku = str(product.get("supplier_sku") or "").strip()
        name = (product.get("name") or "").strip()
        if not sku or not name:
            stats["skipped"] += 1
            progress(f"SKIP без sku/name: {product.get('source_url')}")
            continue

        category = _category_for_product(product, by_name, apply=apply, cache=cache)
        price = _parse_price(product.get("price_uah"))
        description = _build_description(product)
        slug_base = _ua_slug(product.get("slug_hint") or name)
        slug_base = f"{slug_base[:140]}-{sku}"[:160]

        progress(f"{'APPLY' if apply else 'DRY'} {sku}: {name[:60]}")

        if not apply:
            stats["images"] += _sync_images(Product(), product, apply=False)
            # вважаємо updated/created умовно
            exists = Product.objects.filter(sku=sku).exists()
            stats["updated" if exists else "created"] += 1
            continue

        with transaction.atomic():
            obj = Product.objects.filter(sku=sku).first()
            if obj is None:
                slug = _unique_slug(slug_base, model=Product)
                obj = Product(
                    sku=sku,
                    slug=slug,
                    name=name[:255],
                    description=description,
                    price_uah=price,
                    category=category if getattr(category, "pk", None) else None,
                    availability=Product.Availability.IN_STOCK,
                    is_published=publish,
                )
                obj.save()
                stats["created"] += 1
            else:
                obj.name = name[:255]
                obj.description = description
                obj.price_uah = price
                if category is not None and getattr(category, "pk", None):
                    obj.category = category
                obj.availability = Product.Availability.IN_STOCK
                if publish:
                    obj.is_published = True
                # slug не чіпаємо — адмін міг змінити ЧПУ
                obj.save()
                stats["updated"] += 1

            stats["images"] += _sync_images(obj, product, apply=True)

    return stats


def run_import(
    base_dir: Path,
    *,
    apply: bool = False,
    publish: bool = False,
    progress: ProgressCb = _noop,
) -> dict[str, Any]:
    root = data_root(base_dir)
    if not root.exists():
        raise FileNotFoundError(f"Немає {root} — спочатку parse_olx_7wlnq")

    tree = _load_tree(base_dir)
    products = _load_products(base_dir)
    if not products:
        raise FileNotFoundError("Порожня папка products/ — спочатку parse_olx_7wlnq")

    progress(f"Джерело: {root} (products={len(products)}, apply={apply}, publish={publish})")
    by_name = import_category_tree(tree, apply=apply, progress=progress)
    stats = import_products(
        products,
        by_name,
        apply=apply,
        publish=publish,
        progress=progress,
    )
    result = {
        "source": SOURCE,
        "apply": apply,
        "publish": publish,
        "products_in_json": len(products),
        "categories_mapped": list(by_name.keys()),
        **stats,
    }
    progress(
        f"Результат: created={stats['created']} updated={stats['updated']} "
        f"images={stats['images']} skipped={stats['skipped']}"
    )
    return result

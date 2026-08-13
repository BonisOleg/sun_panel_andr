"""Пайплайн: discover → parse → download images → JSON (без БД)."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .client import OlxClient, OlxHttpError
from .constants import (
    SELLER_ID,
    SELLER_LIST_URL,
    SOURCE,
    categories_path,
    data_root,
    images_dir,
    manifest_path,
    products_dir,
)
from .discover import (
    discover_all_listing_urls,
    merge_breadcrumb_into_tree,
    parse_category_filter_tree,
)
from .media import download_product_images
from .parse_card import parse_product_html

logger = logging.getLogger(__name__)

ProgressCb = Callable[[str], None]


def _noop(msg: str) -> None:
    return None


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def run_parse(
    base_dir: Path,
    *,
    download_images: bool = True,
    limit: int | None = None,
    progress: ProgressCb = _noop,
) -> dict[str, Any]:
    """
    Повний прогін парсера OLX 7wLNQ.

    Артефакти:
      data/olx_7wlnq/categories/tree.json
      data/olx_7wlnq/products/{supplier_sku}.json
      data/olx_7wlnq/images/{supplier_sku}/*
      data/olx_7wlnq/run_meta.json
    """
    root = data_root(base_dir)
    root.mkdir(parents=True, exist_ok=True)
    products_dir(base_dir).mkdir(parents=True, exist_ok=True)
    images_dir(base_dir).mkdir(parents=True, exist_ok=True)

    client = OlxClient()
    started = datetime.now(timezone.utc)
    errors: list[dict[str, str]] = []
    products_ok = 0

    try:
        progress(f"Discover listings: {SELLER_LIST_URL}")
        urls, first_html = discover_all_listing_urls(client)
        if limit is not None:
            urls = urls[: max(0, limit)]

        if not urls:
            raise OlxHttpError(
                "urls_found==0 — abort (ERR-CAT-06). Перевірте URL/селектори."
            )

        tree = parse_category_filter_tree(first_html)
        progress(f"Знайдено оголошень: {len(urls)}")

        for i, url in enumerate(urls, start=1):
            progress(f"[{i}/{len(urls)}] {url}")
            try:
                html = client.get_text(url)
                product = parse_product_html(html, url)
                sku = product["supplier_sku"]
                if not product.get("name"):
                    raise ValueError("Порожня назва товару")

                merge_breadcrumb_into_tree(tree, product.get("category_path") or [])

                if download_images and product.get("image_urls"):
                    dest = images_dir(base_dir) / str(sku)
                    local = download_product_images(
                        client,
                        image_urls=product["image_urls"],
                        dest_dir=dest,
                    )
                    product["images_local"] = local
                else:
                    product["images_local"] = []

                product["parsed_at"] = datetime.now(timezone.utc).isoformat()
                out = products_dir(base_dir) / f"{sku}.json"
                _write_json(out, product)
                products_ok += 1
            except Exception as exc:  # noqa: BLE001 — збираємо помилки по PDP
                logger.exception("Parse failed: %s", url)
                errors.append({"url": url, "error": str(exc)})

        _write_json(categories_path(base_dir), tree)

        finished = datetime.now(timezone.utc)
        meta = {
            "source": SOURCE,
            "seller_id": SELLER_ID,
            "seller_url": SELLER_LIST_URL,
            "started_at": started.isoformat(),
            "finished_at": finished.isoformat(),
            "urls_found": len(urls),
            "products_ok": products_ok,
            "errors_count": len(errors),
            "errors": errors,
            "download_images": download_images,
            "data_dir": str(root),
            "note": (
                "Етап A: лише JSON + фото на диску. "
                "Імпорт у catalog.Product / Category — окрема команда."
            ),
        }
        _write_json(manifest_path(base_dir), meta)
        progress(
            f"Готово: ok={products_ok}, errors={len(errors)}, urls={len(urls)}"
        )
        return meta
    finally:
        client.close()

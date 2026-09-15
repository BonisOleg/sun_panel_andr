"""Google Merchant Center product feed (RSS 2.0 + g: namespace)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from django.db.models import Prefetch
from django.http import HttpResponse
from django.urls import reverse
from django.views import View

from src.catalog.models import Product, ProductImage
from src.content.models import SiteSettings
from src.seo.utils import absolute_url, meta_text

_G_NS = "http://base.google.com/ns/1.0"
_G = f"{{{_G_NS}}}"

_AVAIL = {
    Product.Availability.IN_STOCK: "in_stock",
    Product.Availability.ON_ORDER: "backorder",
    Product.Availability.OUT_OF_STOCK: "out_of_stock",
    Product.Availability.CALL: "in_stock",
}


def merchant_products_qs():
    images = Prefetch(
        "images",
        queryset=ProductImage.objects.order_by("-is_main", "sort_order", "id"),
        to_attr="ordered_images",
    )
    return (
        Product.objects.filter(is_published=True, price_uah__isnull=False)
        .select_related("category")
        .prefetch_related(images)
        .order_by("sort_order", "id")
    )


def _product_image_url(product: Product, request) -> str:
    images = getattr(product, "ordered_images", None) or []
    if not images or not images[0].image:
        return ""
    return absolute_url(images[0].image.url, request)


def _g_el(parent: ET.Element, tag: str, text: str) -> ET.Element:
    el = ET.SubElement(parent, f"{_G}{tag}")
    el.text = text
    return el


class GoogleMerchantFeedView(View):
    """GET /feeds/google.xml і /feeds/google-merchant.xml — published + price_uah."""

    def get(self, request):
        ET.register_namespace("g", _G_NS)
        site = SiteSettings.load()
        brand = (site.site_name or "Soliron").strip() or "Soliron"
        channel_link = absolute_url("/", request)

        rss = ET.Element("rss", {"version": "2.0"})
        channel = ET.SubElement(rss, "channel")
        ET.SubElement(channel, "title").text = f"{brand} — Google Merchant"
        ET.SubElement(channel, "link").text = channel_link
        ET.SubElement(channel, "description").text = meta_text(
            site.footer_tagline or f"Каталог {brand}"
        )

        for product in merchant_products_qs():
            image_url = _product_image_url(product, request)
            if not image_url:
                continue

            item = ET.SubElement(channel, "item")
            sku = (product.sku or "").strip()
            _g_el(item, "id", sku or str(product.pk))
            _g_el(item, "title", meta_text(product.name, limit=150))
            desc = meta_text(product.description or product.name, limit=5000)
            _g_el(item, "description", desc or product.name)
            _g_el(
                item,
                "link",
                absolute_url(
                    reverse("catalog:product", kwargs={"slug": product.slug}),
                    request,
                ),
            )
            _g_el(item, "image_link", image_url)
            _g_el(
                item,
                "availability",
                _AVAIL.get(product.availability, "in_stock"),
            )
            _g_el(item, "price", f"{product.price_uah:.2f} UAH")
            _g_el(item, "condition", "new")
            _g_el(item, "brand", brand)
            if product.category_id and product.category:
                _g_el(item, "product_type", product.category.name)

        xml_bytes = ET.tostring(rss, encoding="utf-8", xml_declaration=True)
        return HttpResponse(xml_bytes, content_type="application/xml; charset=utf-8")

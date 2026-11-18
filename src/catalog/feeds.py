"""Google Merchant Center product feed (RSS 2.0 + g: namespace)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from django.db.models import Prefetch
from django.http import HttpResponse
from django.urls import reverse
from django.views import View

from src.catalog import merchant
from src.catalog.models import Product, ProductImage
from src.content.models import SiteSettings
from src.seo.utils import absolute_url, meta_text

_G_NS = "http://base.google.com/ns/1.0"
_G = f"{{{_G_NS}}}"

def merchant_products_qs():
    """Усі опубліковані товари з ціною — без ліміту/пагінації."""
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
            category = product.category if product.category_id else None
            label0 = merchant.category_label(category)
            item_brand, _src = merchant.product_brand(product, default=brand)
            title, _tsrc = merchant.feed_title(product, item_brand, label0)
            _g_el(item, "id", sku or str(product.pk))
            _g_el(item, "title", title)
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
                merchant.AVAILABILITY.get(product.availability, "in_stock"),
            )
            if product.availability == Product.Availability.ON_ORDER:
                # Google вимагає availability_date для preorder
                _g_el(item, "availability_date", merchant.preorder_date())
            _g_el(item, "price", merchant.format_price(product.price_uah))
            _g_el(item, "condition", "new")
            if item_brand:
                _g_el(item, "brand", item_brand)
            if category is not None:
                _g_el(item, "product_type", category.name)
            if label0:
                _g_el(item, "custom_label_0", label0)
            _g_el(item, "custom_label_1", merchant.price_label(product.price_uah))
            if item_brand:
                _g_el(item, "custom_label_2", item_brand)

        xml_bytes = ET.tostring(rss, encoding="utf-8", xml_declaration=True)
        return HttpResponse(xml_bytes, content_type="application/xml; charset=utf-8")

"""GTM dataLayer payload для події purchase (Google Ads / GA4 Enhanced Conversions).

Формат (ТЗ клієнта): user_data на одному рівні з ecommerce; value/price — числа
JS (float, 2 знаки), без пробілів/ком/«грн»; currency = "UAH".
item_id = той самий id, що й у Merchant-фіді (SKU або pk) — для динамічного ремаркетингу.
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Q
from django.utils import timezone

from .models import Order

LEAD_EVENT = {"event": "generate_lead", "form_id": "contact_form"}


def _num(value) -> float:
    if value is None:
        return 0.0
    return float(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def phone_e164(phone: str) -> str:
    """+380XXXXXXXXX або "" (якщо номер некоректний)."""
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("380") and len(digits) == 12:
        return f"+{digits}"
    if digits.startswith("0") and len(digits) == 10:
        return f"+38{digits}"
    return ""


def feed_item_id(*, sku: str, product_id: int | None) -> str:
    sku = (sku or "").strip()
    if sku:
        return sku
    return str(product_id) if product_id else ""


def purchase_payload(order: Order) -> dict:
    items = []
    for item in order.items.all():
        items.append(
            {
                "item_id": feed_item_id(sku=item.product_sku, product_id=item.product_id),
                "item_name": item.product_name,
                "price": _num(item.unit_price_uah),
                "quantity": int(item.qty),
            }
        )
    return {
        "event": "purchase",
        "user_data": {
            "email": (order.customer_email or "").strip().lower(),
            "phone_number": phone_e164(order.customer_phone),
        },
        "ecommerce": {
            "transaction_id": order.number,
            "value": _num(order.total_uah),
            "currency": "UAH",
            "items": items,
        },
    }


def claim_purchase_event(order: Order) -> bool:
    """Атомарно позначити, що purchase віддано. True — лише перший раз."""
    updated = Order.objects.filter(
        Q(pk=order.pk) & Q(analytics_sent_at__isnull=True)
    ).update(analytics_sent_at=timezone.now())
    return updated == 1

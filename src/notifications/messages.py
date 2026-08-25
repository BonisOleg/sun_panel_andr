"""Plain-text bodies for admin Email + Telegram (same content)."""

from __future__ import annotations

from decimal import Decimal


def _money(value) -> str:
    if value is None:
        return "за запитом"
    if isinstance(value, Decimal):
        return f"{value} UAH"
    return f"{value} UAH"


def format_order_message(order) -> tuple[str, str]:
    """Return (subject, body) with full checkout snapshot."""
    subject = f"[Soliron] Замовлення {order.number}"
    lines = [
        f"Замовлення {order.number}",
        f"Статус: {order.get_status_display()}",
        "",
        "Клієнт:",
        f"ПІБ: {order.customer_name}",
        f"Телефон: {order.customer_phone}",
        f"Email: {order.customer_email or '—'}",
        f"Компанія: {order.customer_company or '—'}",
        "",
        f"Доставка: {order.get_shipping_method_display()}",
    ]
    if order.shipping_method == order.ShippingMethod.NOVA_POSHTA:
        lines.append(f"Місто НП: {order.np_city_name or '—'}")
        lines.append(f"Відділення НП: {order.np_warehouse_name or '—'}")
    elif order.shipping_method == order.ShippingMethod.DELIVERY:
        mode = order.get_delivery_mode_display() or order.delivery_mode or "—"
        lines.append(f"Режим Delivery: {mode}")
        lines.append(f"Місто: {order.delivery_city_name or '—'}")
        if order.delivery_mode == order.DeliveryMode.WAREHOUSE:
            lines.append(f"Склад: {order.delivery_warehouse_name or '—'}")
        elif order.delivery_address:
            lines.append(f"Адреса: {order.delivery_address}")
        if order.delivery_cost_uah is not None:
            lines.append(f"Вартість доставки: {_money(order.delivery_cost_uah)}")
        if order.tracking_number:
            lines.append(f"ТТН: {order.tracking_number}")
    elif order.shipping_method == order.ShippingMethod.PICKUP:
        lines.append("Самовивіз (уточнити з менеджером)")

    lines.append(f"Оплата: {order.get_payment_method_display()}")
    if order.customer_comment:
        lines.append(f"Коментар: {order.customer_comment}")

    lines.append("")
    lines.append("Товари:")
    items = list(order.items.all())
    if not items:
        lines.append("— (порожньо)")
    for item in items:
        sku = item.product_sku or "—"
        unit = _money(item.unit_price_uah)
        line_total = _money(item.line_total_uah)
        lines.append(
            f"- [{sku}] {item.product_name} × {item.qty} "
            f"(ціна {unit}, сума {line_total})"
        )
    lines.append("")
    lines.append(f"Підсумок: {_money(order.subtotal_uah)}")
    lines.append(f"Разом: {_money(order.total_uah)}")
    return subject, "\n".join(lines)


def format_lead_message(lead) -> tuple[str, str]:
    subject = f"[Soliron] Зворотний звʼязок: {lead.name}"
    body = "\n".join(
        [
            "Зворотний звʼязок з сайту",
            "",
            f"Імʼя: {lead.name}",
            f"Телефон: {lead.phone}",
            f"Email: {lead.email or '—'}",
            f"Повідомлення:",
            lead.message or "—",
            "",
            f"Джерело: {lead.source_url or '—'}",
        ]
    )
    return subject, body

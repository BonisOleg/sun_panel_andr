"""notifications — Email адміну (order + contact lead)."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

from src.content.models import SiteSettings

from .models import EmailLog

logger = logging.getLogger(__name__)


def _notify_email() -> str:
    site = SiteSettings.load()
    return (site.notify_email or getattr(settings, "DEFAULT_FROM_EMAIL", "") or "").strip()


def _log(*, kind: str, to_email: str, subject: str, payload, status: str, error: str = "", object_id: str = ""):
    EmailLog.objects.create(
        kind=kind,
        to_email=to_email,
        subject=subject,
        payload=payload,
        status=status,
        error=error,
        object_id=object_id,
    )


def send_order_email(order) -> bool:
    to_email = _notify_email()
    if not to_email:
        logger.warning("notify_email empty — order email skipped")
        _log(
            kind=EmailLog.Kind.ORDER,
            to_email="",
            subject=f"Замовлення {order.number}",
            payload={"order": order.number},
            status=EmailLog.Status.FAILED,
            error="notify_email не налаштовано",
            object_id=order.number,
        )
        return False

    lines = [
        f"Замовлення {order.number}",
        f"ПІБ: {order.customer_name}",
        f"Телефон: {order.customer_phone}",
        f"Email: {order.customer_email or '—'}",
        f"Компанія: {order.customer_company or '—'}",
        f"Доставка: {order.get_shipping_method_display()}",
    ]
    if order.shipping_method == order.ShippingMethod.NOVA_POSHTA:
        lines.append(f"НП: {order.np_city_name} / {order.np_warehouse_name}")
    elif order.shipping_method == order.ShippingMethod.DELIVERY:
        mode = order.get_delivery_mode_display() or order.delivery_mode
        lines.append(f"Delivery режим: {mode}")
        lines.append(f"Місто: {order.delivery_city_name}")
        if order.delivery_mode == order.DeliveryMode.WAREHOUSE:
            lines.append(f"Склад: {order.delivery_warehouse_name}")
        elif order.delivery_address:
            lines.append(f"Адреса: {order.delivery_address}")
        if order.delivery_cost_uah is not None:
            lines.append(f"Вартість доставки: {order.delivery_cost_uah} UAH")
        if order.tracking_number:
            lines.append(f"ТТН: {order.tracking_number}")
    lines.append(f"Оплата: {order.get_payment_method_display()}")
    if order.customer_comment:
        lines.append(f"Коментар: {order.customer_comment}")
    lines.append("")
    lines.append("Товари:")
    for item in order.items.all():
        price = item.unit_price_uah if item.unit_price_uah is not None else "за запитом"
        lines.append(f"- {item.product_name} x{item.qty} = {price}")
    lines.append(f"Сума: {order.total_uah} UAH")
    body = "\n".join(lines)
    subject = f"[Soliron] Замовлення {order.number}"
    try:
        send_mail(
            subject,
            body,
            getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"),
            [to_email],
            fail_silently=False,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("order email failed")
        _log(
            kind=EmailLog.Kind.ORDER,
            to_email=to_email,
            subject=subject,
            payload={"order": order.number},
            status=EmailLog.Status.FAILED,
            error=str(exc),
            object_id=order.number,
        )
        return False
    _log(
        kind=EmailLog.Kind.ORDER,
        to_email=to_email,
        subject=subject,
        payload={"order": order.number, "total": str(order.total_uah)},
        status=EmailLog.Status.SENT,
        object_id=order.number,
    )
    return True


def send_lead_email(lead) -> bool:
    to_email = _notify_email()
    subject = f"[Soliron] Зворотний звʼязок: {lead.name}"
    body = (
        f"Імʼя: {lead.name}\n"
        f"Телефон: {lead.phone}\n"
        f"Email: {lead.email or '—'}\n"
        f"Повідомлення:\n{lead.message}\n"
        f"Джерело: {lead.source_url or '—'}\n"
    )
    if not to_email:
        _log(
            kind=EmailLog.Kind.CONTACT_LEAD,
            to_email="",
            subject=subject,
            payload={"lead_id": lead.pk},
            status=EmailLog.Status.FAILED,
            error="notify_email не налаштовано",
            object_id=str(lead.pk),
        )
        return False
    try:
        send_mail(
            subject,
            body,
            getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost"),
            [to_email],
            fail_silently=False,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("lead email failed")
        _log(
            kind=EmailLog.Kind.CONTACT_LEAD,
            to_email=to_email,
            subject=subject,
            payload={"lead_id": lead.pk},
            status=EmailLog.Status.FAILED,
            error=str(exc),
            object_id=str(lead.pk),
        )
        return False
    _log(
        kind=EmailLog.Kind.CONTACT_LEAD,
        to_email=to_email,
        subject=subject,
        payload={"lead_id": lead.pk},
        status=EmailLog.Status.SENT,
        object_id=str(lead.pk),
    )
    return True

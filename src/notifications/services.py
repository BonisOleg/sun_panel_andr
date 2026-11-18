"""notifications — Email (Resend SMTP) + Telegram адміну."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from src.content.models import SiteSettings

from .messages import format_lead_message, format_order_message
from .models import EmailLog
from .telegram import (
    TelegramAPIError,
    TelegramConfigError,
    is_configured as telegram_configured,
    send_telegram_message,
)

logger = logging.getLogger(__name__)


def _notify_email() -> str:
    site = SiteSettings.load()
    return (
        (site.notify_email or "").strip()
        or (getattr(settings, "NOTIFY_EMAIL", "") or "").strip()
    )


def _smtp_ready() -> bool:
    """Avoid hanging checkout when EMAIL_HOST is set without Resend API key."""
    backend = (getattr(settings, "EMAIL_BACKEND", "") or "").lower()
    if any(x in backend for x in ("console", "locmem", "dummy", "filebased")):
        return True
    host = (getattr(settings, "EMAIL_HOST", "") or "").strip()
    if not host:
        return False
    return bool((getattr(settings, "EMAIL_HOST_PASSWORD", "") or "").strip())


def _log(
    *,
    kind: str,
    channel: str,
    recipient: str,
    subject: str,
    payload: Any,
    status: str,
    error: str = "",
    object_id: str = "",
) -> None:
    EmailLog.objects.create(
        kind=kind,
        channel=channel,
        to_email=recipient[:254],
        subject=subject,
        payload=payload,
        status=status,
        error=error,
        object_id=object_id,
    )


def _send_email(*, kind: str, subject: str, body: str, object_id: str, payload: Any) -> bool:
    to_email = _notify_email()
    if not to_email:
        logger.warning("notify_email empty — email skipped (%s)", kind)
        _log(
            kind=kind,
            channel=EmailLog.Channel.EMAIL,
            recipient="",
            subject=subject,
            payload=payload,
            status=EmailLog.Status.FAILED,
            error="notify_email не налаштовано",
            object_id=object_id,
        )
        return False
    if not _smtp_ready():
        logger.warning("SMTP not ready (no EMAIL_HOST_PASSWORD) — email skipped (%s)", kind)
        _log(
            kind=kind,
            channel=EmailLog.Channel.EMAIL,
            recipient=to_email,
            subject=subject,
            payload=payload,
            status=EmailLog.Status.FAILED,
            error="EMAIL_HOST_PASSWORD не налаштовано (Resend API key)",
            object_id=object_id,
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
        logger.exception("email failed (%s)", kind)
        _log(
            kind=kind,
            channel=EmailLog.Channel.EMAIL,
            recipient=to_email,
            subject=subject,
            payload=payload,
            status=EmailLog.Status.FAILED,
            error=str(exc),
            object_id=object_id,
        )
        return False
    _log(
        kind=kind,
        channel=EmailLog.Channel.EMAIL,
        recipient=to_email,
        subject=subject,
        payload=payload,
        status=EmailLog.Status.SENT,
        object_id=object_id,
    )
    return True


def _send_telegram(*, kind: str, subject: str, body: str, object_id: str, payload: Any) -> bool:
    chat_id = (getattr(settings, "TELEGRAM_CHAT_ID", "") or "").strip()
    text = f"{subject}\n\n{body}"
    if not telegram_configured():
        logger.warning("Telegram not configured — skipped (%s)", kind)
        _log(
            kind=kind,
            channel=EmailLog.Channel.TELEGRAM,
            recipient=chat_id,
            subject=subject,
            payload=payload,
            status=EmailLog.Status.FAILED,
            error="TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID не налаштовано",
            object_id=object_id,
        )
        return False
    try:
        send_telegram_message(text)
    except (TelegramConfigError, TelegramAPIError) as exc:
        logger.exception("telegram failed (%s)", kind)
        _log(
            kind=kind,
            channel=EmailLog.Channel.TELEGRAM,
            recipient=chat_id,
            subject=subject,
            payload=payload,
            status=EmailLog.Status.FAILED,
            error=str(exc),
            object_id=object_id,
        )
        return False
    except Exception as exc:  # noqa: BLE001
        logger.exception("telegram unexpected error (%s)", kind)
        _log(
            kind=kind,
            channel=EmailLog.Channel.TELEGRAM,
            recipient=chat_id,
            subject=subject,
            payload=payload,
            status=EmailLog.Status.FAILED,
            error=str(exc),
            object_id=object_id,
        )
        return False
    _log(
        kind=kind,
        channel=EmailLog.Channel.TELEGRAM,
        recipient=chat_id,
        subject=subject,
        payload=payload,
        status=EmailLog.Status.SENT,
        object_id=object_id,
    )
    return True


_ALL_CHANNELS = ("telegram", "email")


def _notify(*, kind, subject, body, object_id, payload, channels) -> dict[str, bool]:
    result: dict[str, bool] = {}
    if "telegram" in channels:
        result["telegram"] = _send_telegram(
            kind=kind, subject=subject, body=body, object_id=object_id, payload=payload
        )
    if "email" in channels:
        result["email"] = _send_email(
            kind=kind, subject=subject, body=body, object_id=object_id, payload=payload
        )
    return result


def notify_order(order, channels=_ALL_CHANNELS) -> dict[str, bool]:
    """Telegram first, then Email. Channels independent; never raises."""
    subject, body = format_order_message(order)
    payload = {"order": order.number, "total": str(order.total_uah)}
    return _notify(
        kind=EmailLog.Kind.ORDER,
        subject=subject,
        body=body,
        object_id=order.number,
        payload=payload,
        channels=channels,
    )


def notify_lead(lead, channels=_ALL_CHANNELS) -> dict[str, bool]:
    """Telegram first, then Email. Channels independent; never raises."""
    subject, body = format_lead_message(lead)
    return _notify(
        kind=EmailLog.Kind.CONTACT_LEAD,
        subject=subject,
        body=body,
        object_id=str(lead.pk),
        payload={"lead_id": lead.pk},
        channels=channels,
    )


def _pending_channels(obj) -> tuple[str, ...]:
    pending = []
    if not obj.telegram_sent_at:
        pending.append("telegram")
    if not obj.email_sent_at:
        pending.append("email")
    return tuple(pending)


def _mark_sent(obj, sent: dict[str, bool]) -> None:
    now = timezone.now()
    fields: list[str] = []
    if sent.get("email"):
        obj.email_sent_at = now
        fields.append("email_sent_at")
    if sent.get("telegram"):
        obj.telegram_sent_at = now
        fields.append("telegram_sent_at")
    if fields:
        type(obj).objects.filter(pk=obj.pk).update(**{f: now for f in fields})


def deliver_order_notifications(order_id: int, channels=None) -> dict[str, bool]:
    """Фонова задача: надіслати сповіщення про замовлення (лише невідправлені канали)."""
    from src.commerce.models import Order

    order = Order.objects.filter(pk=order_id).prefetch_related("items").first()
    if order is None:
        return {}
    todo = tuple(c for c in (channels or _pending_channels(order)) if c in _pending_channels(order))
    if not todo:
        return {}
    sent = notify_order(order, channels=todo)
    _mark_sent(order, sent)
    return sent


def deliver_lead_notifications(lead_id: int, channels=None) -> dict[str, bool]:
    """Фонова задача: надіслати сповіщення про лід (лише невідправлені канали)."""
    from src.content.models import ContactLead

    lead = ContactLead.objects.filter(pk=lead_id).first()
    if lead is None:
        return {}
    todo = tuple(c for c in (channels or _pending_channels(lead)) if c in _pending_channels(lead))
    if not todo:
        return {}
    sent = notify_lead(lead, channels=todo)
    _mark_sent(lead, sent)
    return sent


def schedule_order_notifications(order) -> None:
    from .background import schedule

    schedule(deliver_order_notifications, order.pk)


def schedule_lead_notifications(lead) -> None:
    from .background import schedule

    schedule(deliver_lead_notifications, lead.pk)


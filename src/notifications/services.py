"""notifications — Email (Resend SMTP) + Telegram адміну."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.core.mail import send_mail

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


def notify_order(order) -> dict[str, bool]:
    """Telegram first, then Email. Channels independent; never raises."""
    subject, body = format_order_message(order)
    payload = {"order": order.number, "total": str(order.total_uah)}
    object_id = order.number
    kind = EmailLog.Kind.ORDER
    return {
        "telegram": _send_telegram(
            kind=kind, subject=subject, body=body, object_id=object_id, payload=payload
        ),
        "email": _send_email(
            kind=kind, subject=subject, body=body, object_id=object_id, payload=payload
        ),
    }


def notify_lead(lead) -> dict[str, bool]:
    """Telegram first, then Email. Channels independent; never raises."""
    subject, body = format_lead_message(lead)
    payload = {"lead_id": lead.pk}
    object_id = str(lead.pk)
    kind = EmailLog.Kind.CONTACT_LEAD
    return {
        "telegram": _send_telegram(
            kind=kind, subject=subject, body=body, object_id=object_id, payload=payload
        ),
        "email": _send_email(
            kind=kind, subject=subject, body=body, object_id=object_id, payload=payload
        ),
    }


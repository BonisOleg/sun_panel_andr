"""content selectors + contact lead service."""

from __future__ import annotations

import re
from dataclasses import dataclass

from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone

from src.notifications.services import notify_lead

from .models import BlogPost, ContactLead, HomeAdvantage, HomePage


class LeadError(Exception):
    pass


@dataclass(frozen=True)
class AdvantageStub:
    title: str
    text: str
    icon: None = None


DEFAULT_ADVANTAGES: tuple[AdvantageStub, ...] = (
    AdvantageStub("Висока якість", "Обладнання перевірених виробників для стабільної роботи станції."),
    AdvantageStub("Швидка доставка", "Комплектація та відправка під ваш обʼєкт у зручні терміни."),
    AdvantageStub("Гарантія", "Офіційна гарантія та підтримка після покупки."),
    AdvantageStub("Експертна консультація", "Допоможемо підібрати панелі та кріплення під задачу."),
)


def get_home_page() -> HomePage:
    return HomePage.load()


def home_advantages() -> list[HomeAdvantage] | list[AdvantageStub]:
    qs = list(HomeAdvantage.objects.filter(is_active=True).order_by("sort_order", "id"))
    return qs or list(DEFAULT_ADVANTAGES)


def published_posts() -> QuerySet[BlogPost]:
    now = timezone.now()
    return BlogPost.objects.filter(
        is_published=True,
        published_at__isnull=False,
        published_at__lte=now,
    ).order_by("-published_at", "-id")


def get_published_post(slug: str) -> BlogPost:
    return get_object_or_404(published_posts(), slug=slug)


_NAME_RE = re.compile(
    r"^[A-Za-zА-Яа-яЁёІіЇїЄєҐґʼ'`’\-\s]+$",
    re.UNICODE,
)
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_UA_PHONE_RE = re.compile(r"^\+380\d{9}$")
MESSAGE_MAX_LEN = 800


def _normalize_phone(phone: str) -> str:
    """Нормалізує до формату +380XXXXXXXXX (рівно 9 цифр після +380)."""
    digits = re.sub(r"\D", "", (phone or "").strip())
    if digits.startswith("380"):
        digits = digits[3:]
    elif digits.startswith("0") and len(digits) >= 10:
        digits = digits[1:]
    digits = digits[:9]
    if not digits:
        return "+380"
    return f"+380{digits}"


def validate_contact_lead(
    *,
    name: str,
    phone: str,
    message: str,
    email: str = "",
) -> dict[str, str]:
    name = (name or "").strip()
    phone = _normalize_phone(phone)
    message = (message or "").strip()
    email = (email or "").strip()
    errors: dict[str, str] = {}

    if not name:
        errors["name"] = "Вкажіть імʼя"
    elif re.search(r"\d", name):
        errors["name"] = "Імʼя не може містити цифри — лише літери"
    elif not _NAME_RE.fullmatch(name):
        errors["name"] = "Імʼя: лише літери, пробіли, дефіс або апостроф"

    if not phone or phone == "+380":
        errors["phone"] = "Вкажіть номер телефону після +380"
    elif not _UA_PHONE_RE.fullmatch(phone):
        errors["phone"] = (
            "Український номер: +380 і рівно 9 цифр (наприклад +380501234567)"
        )

    if email and not _EMAIL_RE.fullmatch(email):
        errors["email"] = "Некоректний email — приклад: name@example.com"

    if not message:
        errors["message"] = "Вкажіть повідомлення"
    elif len(message) > MESSAGE_MAX_LEN:
        errors["message"] = (
            f"Максимум {MESSAGE_MAX_LEN} символів (зараз {len(message)})"
        )

    if errors:
        raise LeadError(errors)

    return {
        "name": name,
        "phone": phone,
        "email": email,
        "message": message,
    }


@transaction.atomic
def create_contact_lead(*, name: str, phone: str, message: str, email: str = "", source_url: str = "") -> ContactLead:
    cleaned = validate_contact_lead(
        name=name,
        phone=phone,
        message=message,
        email=email,
    )

    lead = ContactLead.objects.create(
        name=cleaned["name"],
        phone=cleaned["phone"],
        email=cleaned["email"],
        message=cleaned["message"],
        source_url=(source_url or "")[:512],
    )
    return lead


def create_contact_lead_and_notify(
    *, name: str, phone: str, message: str, email: str = "", source_url: str = ""
) -> ContactLead:
    lead = create_contact_lead(
        name=name,
        phone=phone,
        message=message,
        email=email,
        source_url=source_url,
    )
    channels = notify_lead(lead)
    update_fields: list[str] = []
    now = timezone.now()
    if channels.get("email"):
        lead.email_sent_at = now
        update_fields.append("email_sent_at")
    if channels.get("telegram"):
        lead.telegram_sent_at = now
        update_fields.append("telegram_sent_at")
    if update_fields:
        lead.save(update_fields=update_fields)
    return lead

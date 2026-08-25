"""notifications_email_log — tables.md §3.15 (+ channel for Telegram)."""

from django.db import models

from src.core.models import CreatedAtModel


class EmailLog(CreatedAtModel):
    class Kind(models.TextChoices):
        ORDER = "order", "Замовлення"
        CONTACT_LEAD = "contact_lead", "Зворотний звʼязок"

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        TELEGRAM = "telegram", "Telegram"

    class Status(models.TextChoices):
        SENT = "sent", "Надіслано"
        FAILED = "failed", "Помилка"

    kind = models.CharField(max_length=32, choices=Kind.choices)
    channel = models.CharField(
        max_length=16,
        choices=Channel.choices,
        default=Channel.EMAIL,
    )
    to_email = models.CharField(
        "Отримувач",
        max_length=255,
        blank=True,
        default="",
        help_text="Email або Telegram chat_id",
    )
    subject = models.CharField(max_length=255)
    payload = models.JSONField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    error = models.TextField(blank=True, default="")
    object_id = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        db_table = "notifications_email_log"
        ordering = ["-created_at"]
        verbose_name = "Лог сповіщення"
        verbose_name_plural = "Логи сповіщень"

    def __str__(self) -> str:
        return f"{self.channel}:{self.kind}:{self.to_email}:{self.status}"

"""notifications_email_log — tables.md §3.15."""

from django.db import models

from src.core.models import CreatedAtModel


class EmailLog(CreatedAtModel):
    class Kind(models.TextChoices):
        ORDER = "order", "Замовлення"
        CONTACT_LEAD = "contact_lead", "Зворотний звʼязок"

    class Status(models.TextChoices):
        SENT = "sent", "Надіслано"
        FAILED = "failed", "Помилка"

    kind = models.CharField(max_length=32, choices=Kind.choices)
    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    payload = models.JSONField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    error = models.TextField(blank=True, default="")
    object_id = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        db_table = "notifications_email_log"
        ordering = ["-created_at"]
        verbose_name = "Email лог"
        verbose_name_plural = "Email логи"

    def __str__(self) -> str:
        return f"{self.kind}:{self.to_email}:{self.status}"

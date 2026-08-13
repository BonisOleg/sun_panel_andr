"""seo_redirect_301 — tables.md §3.16."""

from django.db import models

from src.core.models import CreatedAtModel


class Redirect301(CreatedAtModel):
    old_path = models.CharField(max_length=512, unique=True)
    new_path = models.CharField(max_length=512)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "seo_redirect_301"
        verbose_name = "Редирект 301"
        verbose_name_plural = "Редиректи 301"

    def __str__(self) -> str:
        return f"{self.old_path} → {self.new_path}"

"""Shared kernel: abstract mixins only (tables.md). Без бізнес-моделей."""

from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("Створено", auto_now_add=True)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        abstract = True


class CreatedAtModel(models.Model):
    created_at = models.DateTimeField("Створено", auto_now_add=True)

    class Meta:
        abstract = True


class UpdatedAtModel(models.Model):
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        abstract = True


class SeoFieldsMixin(models.Model):
    """SEO override — колонки на сутності (не polymorphic)."""

    seo_title = models.CharField("SEO title", max_length=512, blank=True, default="")
    seo_description = models.TextField("SEO description", blank=True, default="")
    seo_keywords = models.CharField(
        "SEO keywords",
        max_length=512,
        blank=True,
        default="",
    )

    class Meta:
        abstract = True

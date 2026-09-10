"""CMS info pages (legal / Ads requirements)."""

from django.db import models
from tinymce.models import HTMLField

from src.core.models import SeoFieldsMixin, TimeStampedModel
from src.core.richtext import sanitize_richtext


class ContentPage(TimeStampedModel, SeoFieldsMixin):
    title = models.CharField("Заголовок", max_length=255)
    slug = models.SlugField("Slug", max_length=160, unique=True)
    body = HTMLField("Текст")
    is_published = models.BooleanField("Опубліковано", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        db_table = "content_page"
        ordering = ["sort_order", "title"]
        verbose_name = "Інфо-сторінка"
        verbose_name_plural = "Інфо-сторінки"
        indexes = [
            models.Index(fields=["is_published", "sort_order"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if self.body:
            self.body = sanitize_richtext(self.body)
        super().save(*args, **kwargs)

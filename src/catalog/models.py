"""catalog_* — tables.md §3.1–3.3."""

from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from src.content.image_processing import optimize_image_to_webp
from src.core.models import CreatedAtModel, SeoFieldsMixin, TimeStampedModel
from .text_utils import sanitize_product_name


class CardBadgeStyle(models.TextChoices):
    STOCK = "stock", "Наявність (зелений)"
    TOP = "top", "TOP / акцент (жовтий)"
    SALE = "sale", "Знижка (бежевий)"
    SOFT = "soft", "Нейтральний"


class Category(TimeStampedModel, SeoFieldsMixin):
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Батьківська",
    )
    name = models.CharField("Назва", max_length=255)
    slug = models.SlugField("Slug", max_length=160, unique=True)
    description = models.TextField("Опис", blank=True, default="")
    image = models.ImageField("Зображення", upload_to="catalog/categories/", blank=True)
    card_badge_text = models.CharField(
        "Бейдж на картці",
        max_length=40,
        blank=True,
        default="",
        help_text="Напр. TOP, Новинка. Порожньо = без бейджа.",
    )
    card_badge_style = models.CharField(
        "Стиль бейджа",
        max_length=16,
        choices=CardBadgeStyle.choices,
        default=CardBadgeStyle.STOCK,
    )
    is_active = models.BooleanField("Активна", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        db_table = "catalog_category"
        ordering = ["sort_order", "name"]
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
        indexes = [
            models.Index(fields=["parent", "sort_order"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def display_card_badge(self) -> str:
        return (self.card_badge_text or "").strip()

    def save(self, *args, **kwargs):
        self._process_image()
        super().save(*args, **kwargs)

    def _process_image(self, *, force: bool = False) -> None:
        if not self.image:
            return
        try:
            file_obj = self.image.file
        except (FileNotFoundError, ValueError, OSError):
            return
        filename = Path(self.image.name).name or "category.jpg"
        processed = optimize_image_to_webp(file_obj, filename=filename, force=force)
        if processed is None:
            return
        self.image.save(processed.name, processed, save=False)


class Product(TimeStampedModel, SeoFieldsMixin):
    class Availability(models.TextChoices):
        IN_STOCK = "in_stock", "В наявності"
        ON_ORDER = "on_order", "Під замовлення"
        OUT_OF_STOCK = "out_of_stock", "Немає в наявності"
        CALL = "call", "Уточнюйте"

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="Категорія",
    )
    name = models.CharField("Назва", max_length=255)
    slug = models.SlugField("Slug", max_length=160, unique=True)
    description = models.TextField("Опис", blank=True, default="")
    price_uah = models.DecimalField(
        "Ціна UAH",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    availability = models.CharField(
        "Наявність",
        max_length=32,
        choices=Availability.choices,
        default=Availability.IN_STOCK,
    )
    availability_label = models.CharField(
        "Текст статусу",
        max_length=120,
        blank=True,
        default="",
        help_text="Кастомний текст наявності (PDP і бейдж, якщо бейдж картки порожній).",
    )
    card_badge_text = models.CharField(
        "Бейдж на картці",
        max_length=40,
        blank=True,
        default="",
        help_text="Напр. TOP, -10%. Порожньо = текст наявності.",
    )
    card_badge_style = models.CharField(
        "Стиль бейджа",
        max_length=16,
        choices=CardBadgeStyle.choices,
        default=CardBadgeStyle.STOCK,
        blank=True,
    )
    sku = models.CharField("SKU", max_length=64, blank=True, default="")
    weight_kg = models.DecimalField(
        "Вага, кг",
        max_digits=8,
        decimal_places=3,
        default=25,
    )
    length_cm = models.PositiveIntegerField("Довжина, см", default=200)
    width_cm = models.PositiveIntegerField("Ширина, см", default=110)
    height_cm = models.PositiveIntegerField("Висота, см", default=5)
    is_published = models.BooleanField("Опубліковано", default=False)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        db_table = "catalog_product"
        ordering = ["sort_order", "-updated_at"]
        verbose_name = "Товар"
        verbose_name_plural = "Товари"
        indexes = [
            models.Index(fields=["is_published", "sort_order"]),
            models.Index(fields=["category"]),
            models.Index(fields=["availability"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(price_uah__isnull=True) | Q(price_uah__gte=0),
                name="catalog_product_price_uah_nonneg",
            ),
            models.UniqueConstraint(
                fields=["sku"],
                condition=~Q(sku=""),
                name="catalog_product_sku_unique_if_set",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        if self.price_uah is not None and self.price_uah < 0:
            raise ValidationError({"price_uah": "Ціна не може бути відʼємною"})
        if self.name:
            self.name = sanitize_product_name(self.name)

    def save(self, *args, **kwargs):
        if self.name:
            self.name = sanitize_product_name(self.name)
        super().save(*args, **kwargs)

    @property
    def volume_m3(self) -> float:
        """Обʼєм однієї одиниці в м³ (L×W×H см → м³)."""
        return (self.length_cm * self.width_cm * self.height_cm) / 1_000_000

    @property
    def can_add_to_cart(self) -> bool:
        return self.is_published and self.availability != self.Availability.OUT_OF_STOCK

    @property
    def display_card_badge(self) -> str:
        custom = (self.card_badge_text or "").strip()
        if custom:
            return custom
        label = (self.availability_label or "").strip()
        if label:
            return label
        return self.get_availability_display()

    @property
    def display_card_badge_style(self) -> str:
        if (self.card_badge_text or "").strip() and self.card_badge_style:
            return self.card_badge_style
        if self.availability == self.Availability.IN_STOCK:
            return CardBadgeStyle.STOCK
        if self.availability == self.Availability.OUT_OF_STOCK:
            return CardBadgeStyle.SALE
        return CardBadgeStyle.SOFT


class ProductImage(CreatedAtModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Товар",
    )
    image = models.ImageField("Зображення", upload_to="catalog/products/")
    alt = models.CharField("Alt", max_length=255, blank=True, default="")
    is_main = models.BooleanField("Головне", default=False)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        db_table = "catalog_product_image"
        ordering = ["sort_order", "id"]
        verbose_name = "Фото товару"
        verbose_name_plural = "Фото товарів"
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=Q(is_main=True),
                name="catalog_product_image_one_main",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product_id}:{self.pk}"

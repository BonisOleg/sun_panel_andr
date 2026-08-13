"""shipping_np_* + shipping_delivery_* — tables.md · novaposhta_skill · Delivery Auto."""

from django.db import models

from src.core.models import UpdatedAtModel


class NPCity(UpdatedAtModel):
    ref = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255, db_index=True)
    area = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "shipping_np_city"
        verbose_name = "НП місто"
        verbose_name_plural = "НП міста"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class NPWarehouse(UpdatedAtModel):
    ref = models.CharField(max_length=64, unique=True)
    city = models.ForeignKey(
        NPCity,
        on_delete=models.CASCADE,
        related_name="warehouses",
    )
    number = models.CharField(max_length=16, blank=True, default="")
    description = models.CharField(max_length=512)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "shipping_np_warehouse"
        verbose_name = "НП відділення"
        verbose_name_plural = "НП відділення"
        indexes = [
            models.Index(fields=["city", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.description


class DeliveryCity(UpdatedAtModel):
    """Кеш міст Delivery Auto (GetAreasList)."""

    city_id = models.CharField(max_length=64, unique=True)
    name_uk = models.CharField(max_length=255, db_index=True)
    region_name = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "shipping_delivery_city"
        verbose_name = "Delivery місто"
        verbose_name_plural = "Delivery міста"
        ordering = ["name_uk"]

    def __str__(self) -> str:
        return self.name_uk


class DeliveryWarehouse(UpdatedAtModel):
    """Кеш вантажних складів Delivery Auto (GetWarehousesList / Info)."""

    warehouse_id = models.CharField(max_length=64, unique=True)
    city = models.ForeignKey(
        DeliveryCity,
        on_delete=models.CASCADE,
        related_name="warehouses",
    )
    name_uk = models.CharField(max_length=255)
    address_uk = models.CharField(max_length=512, blank=True, default="")
    phone = models.CharField(max_length=128, blank=True, default="")
    max_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    warehouse_type = models.IntegerField(null=True, blank=True)
    is_freight = models.BooleanField(
        default=True,
        help_text="Вантажне відділення (не мікро/pickup-only).",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "shipping_delivery_warehouse"
        verbose_name = "Delivery склад"
        verbose_name_plural = "Delivery склади"
        indexes = [
            models.Index(fields=["city", "is_active", "is_freight"]),
        ]

    def __str__(self) -> str:
        return self.name_uk

"""commerce_* — tables.md §3.4–3.7."""

from django.db import models
from django.db.models import Q

from src.core.models import TimeStampedModel


class Cart(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Активний"
        CONVERTED = "converted", "Оформлений"
        ABANDONED = "abandoned", "Покинутий"

    session_key = models.CharField("Session", max_length=40, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        db_table = "commerce_cart"
        verbose_name = "Кошик"
        verbose_name_plural = "Кошики"
        indexes = [
            models.Index(
                fields=["session_key"],
                name="commerce_cart_active_sess",
                condition=Q(status="active"),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.session_key}:{self.status}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.RESTRICT,
        related_name="cart_items",
    )
    qty = models.PositiveIntegerField(default=1)
    unit_price_uah = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "commerce_cart_item"
        verbose_name = "Позиція кошика"
        verbose_name_plural = "Позиції кошика"
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="commerce_cart_item_unique_product",
            ),
            models.CheckConstraint(
                condition=Q(qty__gte=1),
                name="commerce_cart_item_qty_gte_1",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.cart_id}:{self.product_id} x{self.qty}"


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = "new", "Нове"
        PROCESSING = "processing", "В обробці"
        COMPLETED = "completed", "Виконано"
        CANCELLED = "cancelled", "Скасовано"

    class ShippingMethod(models.TextChoices):
        PICKUP = "pickup", "Самовивіз"
        DELIVERY = "delivery", "Delivery"
        NOVA_POSHTA = "nova_poshta", "Нова Пошта"

    class DeliveryMode(models.TextChoices):
        WAREHOUSE = "warehouse", "На вантажне відділення"
        DOORS = "doors", "Адресна доставка (двері)"

    class PaymentMethod(models.TextChoices):
        INVOICE = "invoice", "Рахунок-фактура"
        CASH = "cash", "Готівка"

    number = models.CharField(max_length=32, unique=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )
    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=32)
    customer_email = models.EmailField(blank=True, default="")
    customer_company = models.CharField(max_length=255, blank=True, default="")
    customer_comment = models.TextField(blank=True, default="")
    shipping_method = models.CharField(max_length=20, choices=ShippingMethod.choices)
    delivery_mode = models.CharField(
        max_length=20,
        choices=DeliveryMode.choices,
        blank=True,
        default="",
    )
    delivery_city_id = models.CharField(max_length=64, blank=True, default="")
    delivery_city_name = models.CharField(max_length=255, blank=True, default="")
    delivery_warehouse_id = models.CharField(max_length=64, blank=True, default="")
    delivery_warehouse_name = models.CharField(max_length=255, blank=True, default="")
    delivery_address = models.TextField(blank=True, default="")
    delivery_cost_uah = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    tracking_number = models.CharField(max_length=64, blank=True, default="")
    np_city_ref = models.CharField(max_length=64, blank=True, default="")
    np_city_name = models.CharField(max_length=255, blank=True, default="")
    np_warehouse_ref = models.CharField(max_length=64, blank=True, default="")
    np_warehouse_name = models.CharField(max_length=255, blank=True, default="")
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    subtotal_uah = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_uah = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cart = models.ForeignKey(
        Cart,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    email_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "commerce_order"
        ordering = ["-created_at"]
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["customer_phone"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return self.number


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    product_sku = models.CharField(max_length=64, blank=True, default="")
    product_name = models.CharField(max_length=255)
    qty = models.PositiveIntegerField()
    unit_price_uah = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    line_total_uah = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "commerce_order_item"
        verbose_name = "Позиція замовлення"
        verbose_name_plural = "Позиції замовлення"
        constraints = [
            models.CheckConstraint(
                condition=Q(qty__gte=1),
                name="commerce_order_item_qty_gte_1",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.order_id}:{self.product_name}"

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Cart, CartItem, Order, OrderItem


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product",
        "product_sku",
        "product_name",
        "qty",
        "unit_price_uah",
        "line_total_uah",
    )


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "number",
        "status",
        "customer_name",
        "customer_phone",
        "shipping_method",
        "tracking_number",
        "total_uah",
        "created_at",
    )
    list_filter = ("status", "shipping_method", "delivery_mode", "payment_method")
    search_fields = (
        "number",
        "customer_name",
        "customer_phone",
        "customer_email",
        "tracking_number",
    )
    inlines = [OrderItemInline]
    readonly_fields = ("number", "created_at", "updated_at", "email_sent_at")


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ("id", "session_key", "status", "updated_at")
    list_filter = ("status",)
    inlines = [CartItemInline]

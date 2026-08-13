from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline

from src.core.admin_mixins import TinyMCEAdminMixin
from src.core.admin_widgets import ClearableImageInput
from src.core.richtext import sanitize_richtext

from .models import Category, Product, ProductImage


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "image" and formfield is not None:
            formfield.widget = ClearableImageInput()
        return formfield


@admin.register(Category)
class CategoryAdmin(TinyMCEAdminMixin, ModelAdmin):
    tinymce_fields = ("description",)
    tinymce_height = 360
    list_display = ("image_preview", "name", "slug", "parent", "card_badge_text", "is_active", "sort_order")
    list_filter = ("is_active", "card_badge_style")
    search_fields = ("name", "slug", "card_badge_text")
    prepopulated_fields = {"slug": ("name",)}
    list_display_links = ("image_preview", "name")
    fieldsets = (
        (
            None,
            {
                "fields": ("parent", "name", "slug", "description"),
            },
        ),
        (
            "Зображення картки",
            {
                "description": (
                    "Фото на головній в блоці «Каталог обладнання». "
                    "Рекомендовано ~960×720 px (4:3). "
                    "Завантажити — іконка ↑ (Upload) справа. "
                    "Прибрати — галочка «Очистити…» і «Зберегти»."
                ),
                "fields": ("image",),
            },
        ),
        ("Картка каталогу", {"fields": ("card_badge_text", "card_badge_style")}),
        ("Статус", {"fields": ("is_active", "sort_order")}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_keywords"), "classes": ("collapse",)}),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "image" and formfield is not None:
            formfield.widget = ClearableImageInput()
        return formfield

    def save_model(self, request, obj, form, change):
        if obj.description:
            obj.description = sanitize_richtext(obj.description)
        super().save_model(request, obj, form, change)

    @admin.display(description="Фото")
    def image_preview(self, obj):
        if not obj.image:
            return format_html(
                '<span style="display:inline-block;width:56px;height:42px;'
                'border-radius:8px;background:#d6e4eb;"></span>'
            )
        return format_html(
            '<img src="{}" alt="" width="56" height="42" '
            'style="object-fit:cover;border-radius:8px;display:block;" loading="lazy">',
            obj.image.url,
        )


@admin.register(Product)
class ProductAdmin(TinyMCEAdminMixin, ModelAdmin):
    tinymce_fields = ("description",)
    list_display = (
        "name",
        "sku",
        "category",
        "price_uah",
        "availability",
        "card_badge_text",
        "is_published",
    )
    list_filter = ("is_published", "availability", "card_badge_style", "category")
    search_fields = ("name", "sku", "slug", "card_badge_text")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline]
    fieldsets = (
        (None, {"fields": ("category", "name", "slug", "description", "sku")}),
        ("Ціна та наявність", {"fields": ("price_uah", "availability", "availability_label")}),
        (
            "Габарити (Delivery)",
            {
                "fields": ("weight_kg", "length_cm", "width_cm", "height_cm"),
                "description": "Для калькулятора Delivery: обʼємна вага = max(факт, м³×250).",
            },
        ),
        (
            "Картка каталогу",
            {
                "fields": ("card_badge_text", "card_badge_style"),
                "description": "Бейдж на сітці. Якщо текст порожній — показується наявність.",
            },
        ),
        ("Статус", {"fields": ("is_published", "sort_order")}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_keywords"), "classes": ("collapse",)}),
    )

    def save_model(self, request, obj, form, change):
        if obj.description:
            obj.description = sanitize_richtext(obj.description)
        super().save_model(request, obj, form, change)

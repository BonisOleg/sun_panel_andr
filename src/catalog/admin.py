from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action
from unfold.enums import ActionVariant

from src.core.admin_mixins import TinyMCEAdminMixin
from src.core.admin_widgets import ClearableImageInput
from src.core.richtext import sanitize_richtext

from .models import Category, Product, ProductImage
from .services import copy_product_images, product_duplicate_initial


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


class ProductAddForm(forms.ModelForm):
    duplicate_from = forms.IntegerField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Product
        fields = "__all__"

    def clean_duplicate_from(self):
        source_id = self.cleaned_data.get("duplicate_from")
        if not source_id:
            return None
        if not Product.objects.filter(pk=source_id).exists():
            raise forms.ValidationError("Товар для дублювання не знайдено.")
        return source_id


@admin.register(Product)
class ProductAdmin(TinyMCEAdminMixin, ModelAdmin):
    tinymce_fields = ("description",)
    actions_detail = ["duplicate_product"]
    actions_row = ["duplicate_product_row"]
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

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            kwargs["form"] = ProductAddForm
        return super().get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj is not None:
            return fieldsets
        first_name, first_opts = fieldsets[0]
        first_opts = {**first_opts, "fields": ("duplicate_from", *first_opts["fields"])}
        return ((first_name, first_opts), *fieldsets[1:])

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        source = self._duplicate_source(request.GET.get("duplicate_from"))
        if source is None:
            return initial
        initial.update(product_duplicate_initial(source))
        return initial

    def add_view(self, request, form_url="", extra_context=None):
        if request.method == "GET" and request.GET.get("duplicate_from"):
            source = self._duplicate_source(request.GET.get("duplicate_from"))
            if source is None:
                self.message_user(
                    request,
                    "Товар для дублювання не знайдено.",
                    level=messages.ERROR,
                )
            else:
                self.message_user(
                    request,
                    f"Копія «{source.name}». Заповніть назву, slug і артикул. "
                    "Фото скопіюються після збереження.",
                    level=messages.INFO,
                )
        return super().add_view(request, form_url, extra_context)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if change:
            return
        source_id = form.cleaned_data.get("duplicate_from")
        source = self._duplicate_source(source_id)
        if source is None:
            return
        copied, skipped = copy_product_images(source, form.instance)
        if copied:
            self.message_user(
                request,
                f"Скопійовано фото: {copied}.",
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f"Не вдалося скопіювати фото: {skipped}. Файли відсутні на диску.",
                level=messages.WARNING,
            )

    @action(
        description="Дублювати",
        url_path="duplicate",
        icon="content_copy",
        variant=ActionVariant.PRIMARY,
    )
    def duplicate_product(self, request, object_id):
        return self._duplicate_redirect(request, object_id)

    @action(
        description="Дублювати",
        url_path="duplicate-row",
        icon="content_copy",
    )
    def duplicate_product_row(self, request, object_id):
        return self._duplicate_redirect(request, object_id)

    def _duplicate_redirect(self, request, object_id):
        if not self.has_add_permission(request):
            raise PermissionDenied
        source = self.get_object(request, object_id)
        if source is None:
            raise Http404("Товар не знайдено")
        url = reverse("admin:catalog_product_add")
        return redirect(f"{url}?duplicate_from={source.pk}")

    @staticmethod
    def _duplicate_source(raw_id):
        if raw_id in (None, ""):
            return None
        try:
            source_id = int(raw_id)
        except (TypeError, ValueError):
            return None
        return Product.objects.filter(pk=source_id).first()

    def save_model(self, request, obj, form, change):
        if obj.description:
            obj.description = sanitize_richtext(obj.description)
        super().save_model(request, obj, form, change)

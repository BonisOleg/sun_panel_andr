from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from unfold.admin import ModelAdmin
from unfold.widgets import UnfoldAdminTextareaWidget

from src.content.image_processing import BLOG_BODY_IMAGE_HELP
from src.core.admin_mixins import TinyMCEAdminMixin, TinyMCEShortAdminMixin
from src.core.admin_widgets import ClearableImageInput, LogoClearableImageInput
from src.core.richtext import sanitize_richtext

from .models import (
    DEFAULT_LOGO_STATIC,
    BlogPost,
    ContactLead,
    HomeAdvantage,
    HomeBanner,
    HomePage,
    SiteSettings,
)


class SingletonAdmin(ModelAdmin):
    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj, _ = self.model.objects.get_or_create(pk=1)
        return HttpResponseRedirect(
            reverse(f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change", args=[obj.pk])
        )


def _site_logo_fieldset_description() -> str:
    from src.content.models import DEFAULT_LOGO_FOOTER_STATIC

    logo_url = staticfiles_storage.url(DEFAULT_LOGO_STATIC)
    footer_url = staticfiles_storage.url(DEFAULT_LOGO_FOOTER_STATIC)
    return mark_safe(
        "<p><strong>Рекомендований розмір:</strong> WebP/PNG "
        "<strong>~320×75 px</strong> (прозорий фон; висота в шапці ~40–50&nbsp;px; "
        "ширина до ~220&nbsp;px). "
        "У футері дефолтний світлий варіант (~36–44&nbsp;px).</p>"
        "<p>Оригінали: <code>static/images/logo-soliron.webp</code> (шапка) та "
        "<code>static/images/logo-soliron-footer.webp</code> (футер). "
        "Після заміни поставте галочку «Повернути оригінальний логотип Soliron» "
        "і збережіть — знову покажуться ці варіанти.</p>"
        f'<p style="margin:0.75rem 0 0;display:flex;flex-wrap:wrap;gap:12px;align-items:center">'
        f'<span>Шапка: <img src="{logo_url}" alt="Оригінал для шапки" '
        f'style="display:inline-block;vertical-align:middle;height:40px;width:auto;'
        f'max-width:220px;background:#f6f2f7;padding:6px 10px;border-radius:8px"></span>'
        f'<span>Футер: <img src="{footer_url}" alt="Оригінал для футера" '
        f'style="display:inline-block;vertical-align:middle;height:40px;width:auto;'
        f'max-width:220px;background:#6c5685;padding:6px 10px;border-radius:8px"></span></p>'
    )


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonAdmin):
    def get_fieldsets(self, request, obj=None):
        return (
            (
                "Сайт",
                {
                    "fields": ("site_name", "logo"),
                    "description": _site_logo_fieldset_description(),
                },
            ),
            (
                "Сторінка «Контакти» — тексти",
                {
                    "fields": (
                        "contacts_eyebrow",
                        "contacts_title",
                        "contacts_lead",
                        "contacts_info_title",
                        "contacts_form_title",
                        "contacts_map_title",
                    ),
                },
            ),
            (
                "Контакти (публічні)",
                {
                    "fields": (
                        "phone_primary",
                        "phone_secondary",
                        "email",
                        "address",
                        "work_schedule",
                    ),
                },
            ),
            (
                "Офіційні реквізити",
                {
                    "fields": ("legal_company_name", "legal_edrpou", "legal_iban"),
                },
            ),
            (
                "Карта Google Maps",
                {
                    "description": (
                        "1) Відкрийте точку на Google Maps → «Поділитися» → «Вставити карту». "
                        "2) Натисніть «Копіювати HTML». "
                        "3) Вставте скопійоване у поле «Вставте сюди код карти» нижче "
                        "(велике темне поле для тексту). "
                        "4) Збережіть — карта зʼявиться на /kontakty/."
                    ),
                    "fields": ("map_embed_url",),
                },
            ),
            (
                "Месенджери (сторінка контактів)",
                {
                    "description": "Окремо від соцмереж у футері. Галочка + посилання.",
                    "fields": (
                        "messenger_telegram_enabled",
                        "messenger_telegram_url",
                        "messenger_viber_enabled",
                        "messenger_viber_url",
                        "messenger_whatsapp_enabled",
                        "messenger_whatsapp_url",
                    ),
                },
            ),
            (
                "Футер",
                {
                    "fields": ("footer_tagline",),
                },
            ),
            (
                "Соцмережі (футер)",
                {
                    "description": (
                        "Увімкніть галочку і вкажіть URL — інакше пункт не показується у футері."
                    ),
                    "fields": (
                        "social_facebook_enabled",
                        "social_facebook_url",
                        "social_instagram_enabled",
                        "social_instagram_url",
                        "social_telegram_enabled",
                        "social_telegram_url",
                        "social_youtube_enabled",
                        "social_youtube_url",
                    ),
                },
            ),
            (
                "Email адміністратора",
                {
                    "description": (
                        "Сюди надходять листи про нові замовлення та форми "
                        "зворотного звʼязку. Обовʼязково заповніть для роботи checkout."
                    ),
                    "fields": ("notify_email",),
                },
            ),
            (
                "Аналітика та SEO",
                {
                    "fields": ("gtm_container_id", "ga4_measurement_id", "robots_txt"),
                },
            ),
        )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "logo" and formfield is not None:
            formfield.widget = LogoClearableImageInput()
        if db_field.name == "map_embed_url" and formfield is not None:
            formfield.widget = UnfoldAdminTextareaWidget(
                attrs={
                    "rows": 6,
                    "placeholder": (
                        "Сюди вставити, наприклад:\n"
                        "<iframe src=\"https://www.google.com/maps/embed?pb=...\" "
                        "width=\"600\" height=\"450\" ...></iframe>"
                    ),
                }
            )
        if db_field.name in {"address", "work_schedule"} and formfield is not None:
            formfield.widget.attrs.setdefault("rows", 3)
        return formfield


@admin.register(HomePage)
class HomePageAdmin(TinyMCEShortAdminMixin, SingletonAdmin):
    tinymce_fields = ("offer_subtitle",)

    fieldsets = (
        (
            "Hero — тексти",
            {
                "fields": (
                    "status_text",
                    "title_before",
                    "title_highlight",
                    "title_after",
                    "lead",
                ),
            },
        ),
        (
            "Hero — кнопки",
            {
                "fields": (
                    "cta_primary_label",
                    "cta_primary_url",
                    "cta_secondary_label",
                    "cta_secondary_url",
                ),
            },
        ),
        (
            "Hero — зображення",
            {
                "description": "Desktop 1400×1050 (4:3). Mobile 800×1000 (4:5).",
                "fields": ("image", "image_mobile", "image_alt"),
            },
        ),
        (
            "Hero — бейдж на фото",
            {
                "fields": ("float_badge_title", "float_badge_subtitle"),
            },
        ),
        (
            "Пропозиція під кнопками",
            {
                "fields": (
                    "offer_enabled",
                    "offer_title",
                    "offer_subtitle",
                    "offer_link_label",
                    "offer_link_url",
                ),
            },
        ),
        (
            "Секція каталогу",
            {
                "fields": (
                    "categories_eyebrow",
                    "categories_title",
                    "categories_description",
                ),
            },
        ),
        (
            "Секція «Про нас»",
            {
                "description": "Картки переваг редагуються окремо: Переваги.",
                "fields": (
                    "advantages_eyebrow",
                    "advantages_title",
                    "advantages_description",
                ),
            },
        ),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in {"image", "image_mobile"} and formfield is not None:
            formfield.widget = ClearableImageInput()
        return formfield


@admin.register(HomeBanner)
class HomeBannerAdmin(TinyMCEShortAdminMixin, ModelAdmin):
    tinymce_fields = ("subtitle",)
    list_display = ("title", "is_active", "sort_order", "has_desktop_image", "has_mobile_image")
    list_filter = ("is_active",)
    ordering = ("sort_order", "id")
    fieldsets = (
        (
            "Legacy",
            {
                "description": "Не показується на сайті. Редагуйте «Головна сторінка».",
                "fields": ("title", "subtitle", "link_url", "is_active", "sort_order"),
            },
        ),
        (
            "Зображення",
            {"fields": ("image", "image_mobile")},
        ),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in {"image", "image_mobile"} and formfield is not None:
            formfield.widget = ClearableImageInput()
        return formfield

    def save_model(self, request, obj, form, change):
        if obj.subtitle:
            obj.subtitle = sanitize_richtext(obj.subtitle)
        super().save_model(request, obj, form, change)

    @admin.display(boolean=True, description="Desktop")
    def has_desktop_image(self, obj):
        return bool(obj.image)

    @admin.display(boolean=True, description="Mobile")
    def has_mobile_image(self, obj):
        return bool(obj.image_mobile)


@admin.register(HomeAdvantage)
class HomeAdvantageAdmin(TinyMCEShortAdminMixin, ModelAdmin):
    tinymce_fields = ("text",)
    list_display = ("title", "is_active", "sort_order")
    list_filter = ("is_active",)
    ordering = ("sort_order", "id")
    fieldsets = (
        (None, {"fields": ("title", "text", "icon", "sort_order", "is_active")}),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "icon" and formfield is not None:
            formfield.widget = ClearableImageInput()
        return formfield

    def save_model(self, request, obj, form, change):
        if obj.text:
            obj.text = sanitize_richtext(obj.text)
        super().save_model(request, obj, form, change)


@admin.action(description="Опублікувати вибрані статті")
def publish_posts(modeladmin, request, queryset):
    now = timezone.now()
    for post in queryset:
        post.is_published = True
        if post.published_at is None:
            post.published_at = now
        post.save()


@admin.action(description="Зняти з публікації")
def unpublish_posts(modeladmin, request, queryset):
    queryset.update(is_published=False)


@admin.register(BlogPost)
class BlogPostAdmin(TinyMCEAdminMixin, ModelAdmin):
    tinymce_fields = ("body",)
    list_display = ("title", "slug", "is_published", "published_at", "has_cover", "updated_at")
    list_filter = ("is_published", "published_at")
    search_fields = ("title", "slug", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    ordering = ("-published_at", "-id")
    actions = (publish_posts, unpublish_posts)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Стаття",
            {
                "description": (
                    "Slug лише латиницею (a-z, 0-9, дефіс), напр. yak-obraty-paneli. "
                    "Текст статті — візуальний редактор TinyMCE (як WordPress)."
                ),
                "fields": ("title", "slug", "excerpt", "body"),
            },
        ),
        (
            "Зображення",
            {
                "description": (
                    "Обкладинка картки та шапки статті. "
                    "Натисніть іконку ↑ (Upload) справа, щоб обрати своє фото. "
                    f"{BLOG_BODY_IMAGE_HELP} "
                    "Додаткові фото в тексті — кнопка Image у редакторі."
                ),
                "fields": ("cover_image",),
            },
        ),
        (
            "Публікація",
            {
                "description": (
                    "Якщо «Опубліковано» увімкнено, а дата порожня — "
                    "дата публікації проставиться автоматично при збереженні."
                ),
                "fields": ("is_published", "published_at"),
            },
        ),
        (
            "SEO",
            {
                "classes": ("collapse",),
                "fields": ("seo_title", "seo_description", "seo_keywords"),
            },
        ),
        (
            "Службове",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "cover_image" and formfield is not None:
            formfield.widget = ClearableImageInput()
        return formfield

    def save_model(self, request, obj, form, change):
        if obj.is_published and obj.published_at is None:
            obj.published_at = timezone.now()
        if obj.body:
            obj.body = sanitize_richtext(obj.body)
        super().save_model(request, obj, form, change)

    @admin.display(boolean=True, description="Обкладинка")
    def has_cover(self, obj):
        return bool(obj.cover_image)


@admin.register(ContactLead)
class ContactLeadAdmin(ModelAdmin):
    list_display = ("name", "phone", "email", "is_processed", "created_at")
    list_filter = ("is_processed",)
    search_fields = ("name", "phone", "email")
    readonly_fields = ("created_at", "email_sent_at")

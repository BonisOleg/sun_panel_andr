"""content_* — tables.md §3.10–3.14."""

from pathlib import Path

from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.html import strip_tags
from tinymce.models import HTMLField

from src.content.image_processing import (
    BLOG_COVER_HELP,
    BLOG_IMAGE_EXTENSIONS,
    center_crop_if_oversized,
)
from src.content.map_embed import normalize_map_embed
from src.core.models import CreatedAtModel, SeoFieldsMixin, TimeStampedModel
from src.core.richtext import sanitize_richtext

from src.content.models_2 import HomePage  # noqa: F401

# Оригінали у static; у шапці/футері — якщо logo порожній.
DEFAULT_LOGO_STATIC = "images/logo-soliron.png"
DEFAULT_LOGO_FOOTER_STATIC = "images/logo-soliron-footer.png"
DEFAULT_LOGO_HELP = (
    "Логотип у шапці (PNG з прозорим фоном). "
    "Рекомендований розмір файлу: 424×100 px (@2x для висоти ~48 px у десктоп-шапці; "
    "на мобільному CSS показує ~40 px). Ширина в шапці до ~220 px. "
    "Оригінал для шапки: static/images/logo-soliron.png; "
    "світлий для футера: static/images/logo-soliron-footer.png. "
    "Щоб повернути оригінал після заміни — очистіть поле (галочка «Повернути оригінальний логотип») і збережіть."
)


class SiteSettings(TimeStampedModel):
    site_name = models.CharField(max_length=120, default="Soliron")
    logo = models.ImageField(
        upload_to="content/logo/",
        blank=True,
        help_text=DEFAULT_LOGO_HELP,
    )
    phone_primary = models.CharField("Телефон", max_length=32, blank=True, default="")
    phone_secondary = models.CharField("Додатковий телефон", max_length=32, blank=True, default="")
    email = models.EmailField("Email", blank=True, default="")
    address = models.TextField(
        "Адреса",
        blank=True,
        default="",
        help_text="Звичайний текст, можна кілька рядків. Без HTML-редактора.",
    )
    work_schedule = models.TextField(
        "Графік роботи",
        blank=True,
        default="Пн–Пт: 09:00–18:00\nСб–Нд: вихідний",
        help_text="Кожен рядок — окремий пункт графіка.",
    )
    map_embed_url = models.TextField(
        "Вставте сюди код карти",
        blank=True,
        default="",
        help_text=(
            "Клікніть у велике поле нижче і вставте (Cmd+V) код з Google Maps. "
            "Підходить весь блок <iframe …></iframe> або лише посилання з src=…. "
            "Після збереження карта зʼявиться на сторінці «Контакти»."
        ),
    )
    map_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    map_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    legal_company_name = models.CharField(
        "Назва / ФОП",
        max_length=255,
        blank=True,
        default="",
    )
    legal_edrpou = models.CharField(
        "ЄДРПОУ / ІПН",
        max_length=32,
        blank=True,
        default="",
    )
    legal_iban = models.CharField(
        "IBAN",
        max_length=64,
        blank=True,
        default="",
    )
    contacts_eyebrow = models.CharField(
        "Контакти — надзаголовок",
        max_length=80,
        blank=True,
        default="Звʼязок",
    )
    contacts_title = models.CharField(
        "Контакти — заголовок",
        max_length=160,
        blank=True,
        default="Контакти",
    )
    contacts_lead = models.TextField(
        "Контакти — підзаголовок",
        blank=True,
        default="Напишіть нам або зателефонуйте — відповімо з робочими деталями.",
    )
    contacts_info_title = models.CharField(
        "Заголовок блоку реквізитів",
        max_length=120,
        blank=True,
        default="Реквізити",
    )
    contacts_form_title = models.CharField(
        "Заголовок форми",
        max_length=120,
        blank=True,
        default="Зворотний звʼязок",
    )
    contacts_map_title = models.CharField(
        "Заголовок карти",
        max_length=120,
        blank=True,
        default="Як нас знайти",
    )
    messenger_telegram_url = models.CharField(
        "Telegram (посилання)",
        max_length=255,
        blank=True,
        default="",
        help_text="Напр. https://t.me/username",
    )
    messenger_telegram_enabled = models.BooleanField("Показати Telegram", default=False)
    messenger_viber_url = models.CharField(
        "Viber (посилання)",
        max_length=255,
        blank=True,
        default="",
        help_text="Напр. viber://chat?number=%2B380XXXXXXXXX",
    )
    messenger_viber_enabled = models.BooleanField("Показати Viber", default=False)
    messenger_whatsapp_url = models.CharField(
        "WhatsApp (посилання)",
        max_length=255,
        blank=True,
        default="",
        help_text="Напр. https://wa.me/380XXXXXXXXX",
    )
    messenger_whatsapp_enabled = models.BooleanField("Показати WhatsApp", default=False)
    footer_tagline = models.TextField(
        "Слоган у футері",
        blank=True,
        default="Сонячні панелі та системи кріплень. Корпоративний каталог з оформленням замовлення.",
    )
    social_facebook_url = models.URLField("Facebook URL", blank=True, default="")
    social_facebook_enabled = models.BooleanField("Показати Facebook", default=False)
    social_instagram_url = models.URLField("Instagram URL", blank=True, default="")
    social_instagram_enabled = models.BooleanField("Показати Instagram", default=False)
    social_telegram_url = models.URLField("Telegram URL", blank=True, default="")
    social_telegram_enabled = models.BooleanField("Показати Telegram", default=False)
    social_youtube_url = models.URLField("YouTube URL", blank=True, default="")
    social_youtube_enabled = models.BooleanField("Показати YouTube", default=False)
    notify_email = models.EmailField(
        "Email адміністратора",
        blank=True,
        default="",
        help_text="Листи про замовлення та зворотний звʼязок",
    )
    gtm_container_id = models.CharField(max_length=32, blank=True, default="")
    ga4_measurement_id = models.CharField(max_length=32, blank=True, default="")
    robots_txt = models.TextField(blank=True, default="")

    class Meta:
        db_table = "content_site_settings"
        verbose_name = "Налаштування сайту"
        verbose_name_plural = "Налаштування сайту"

    def __str__(self) -> str:
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1
        if self.address:
            self.address = strip_tags(self.address).strip()
        self.map_embed_url = normalize_map_embed(self.map_embed_url)
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "SiteSettings":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def map_iframe_src(self) -> str:
        return normalize_map_embed(self.map_embed_url)

    @property
    def logo_url(self) -> str:
        """URL кастомного лого або оригіналу зі static (шапка)."""
        if self.logo:
            return self.logo.url
        from django.templatetags.static import static

        return static(DEFAULT_LOGO_STATIC)

    @property
    def logo_footer_url(self) -> str:
        """URL кастомного лого або світлого оригіналу для футера."""
        if self.logo:
            return self.logo.url
        from django.templatetags.static import static

        return static(DEFAULT_LOGO_FOOTER_STATIC)

    @property
    def uses_default_logo(self) -> bool:
        return not bool(self.logo)

    def has_legal_requisites(self) -> bool:
        return bool(
            (self.legal_company_name or "").strip()
            or (self.legal_edrpou or "").strip()
            or (self.legal_iban or "").strip()
        )

    def visible_social_links(self) -> list[dict[str, str]]:
        candidates = (
            ("facebook", "Facebook", self.social_facebook_enabled, self.social_facebook_url),
            ("instagram", "Instagram", self.social_instagram_enabled, self.social_instagram_url),
            ("telegram", "Telegram", self.social_telegram_enabled, self.social_telegram_url),
            ("youtube", "YouTube", self.social_youtube_enabled, self.social_youtube_url),
        )
        links: list[dict[str, str]] = []
        for key, label, enabled, url in candidates:
            url = (url or "").strip()
            if enabled and url:
                links.append({"key": key, "label": label, "url": url})
        return links

    def visible_messenger_links(self) -> list[dict[str, str]]:
        candidates = (
            ("telegram", "Telegram", self.messenger_telegram_enabled, self.messenger_telegram_url),
            ("viber", "Viber", self.messenger_viber_enabled, self.messenger_viber_url),
            ("whatsapp", "WhatsApp", self.messenger_whatsapp_enabled, self.messenger_whatsapp_url),
        )
        links: list[dict[str, str]] = []
        for key, label, enabled, url in candidates:
            url = (url or "").strip()
            if enabled and url:
                links.append({"key": key, "label": label, "url": url})
        return links


class HomeBanner(TimeStampedModel):
    """Legacy: не використовується на фронті. Залишено для сумісності схеми."""

    title = models.CharField(max_length=255, blank=True, default="")
    subtitle = models.TextField(blank=True, default="")
    image = models.ImageField(
        upload_to="content/banners/",
        blank=True,
        help_text=(
            "Desktop hero: рекомендуємо 1400×1050 px (співвідношення 4:3, JPG/WebP). "
            "Щоб видалити поточне зображення — позначте «Очистити» і збережіть."
        ),
    )
    image_mobile = models.ImageField(
        upload_to="content/banners/mobile/",
        blank=True,
        help_text=(
            "Mobile hero: рекомендуємо 800×1000 px (співвідношення 4:5, JPG/WebP). "
            "Щоб видалити — позначте «Очистити» і збережіть."
        ),
    )
    link_url = models.CharField(max_length=512, blank=True, default="")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "content_home_banner"
        ordering = ["sort_order", "id"]
        verbose_name = "Банер головної (legacy)"
        verbose_name_plural = "Банери головної (legacy)"

    def __str__(self) -> str:
        return self.title or f"Banner #{self.pk}"


class HomeAdvantage(TimeStampedModel):
    title = models.CharField(max_length=255)
    text = models.TextField(blank=True, default="")
    icon = models.ImageField(upload_to="content/advantages/", blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "content_home_advantage"
        ordering = ["sort_order", "id"]
        verbose_name = "Перевага"
        verbose_name_plural = "Переваги"

    def __str__(self) -> str:
        return self.title


class BlogPost(TimeStampedModel, SeoFieldsMixin):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=160, unique=True)
    excerpt = models.TextField(blank=True, default="")
    body = HTMLField()
    cover_image = models.ImageField(
        upload_to="content/blog/",
        blank=True,
        help_text=BLOG_COVER_HELP,
        validators=[FileExtensionValidator(allowed_extensions=list(BLOG_IMAGE_EXTENSIONS))],
    )
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "content_blog_post"
        ordering = ["-published_at", "-id"]
        verbose_name = "Стаття блогу"
        verbose_name_plural = "Статті блогу"
        indexes = [
            models.Index(fields=["is_published", "-published_at"]),
        ]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if self.is_published and self.published_at is None:
            self.published_at = timezone.now()
        if self.body:
            self.body = sanitize_richtext(self.body)
        self._process_cover_image()
        super().save(*args, **kwargs)

    def _process_cover_image(self) -> None:
        if not self.cover_image:
            return
        try:
            file_obj = self.cover_image.file
        except (FileNotFoundError, ValueError, OSError):
            return
        filename = Path(self.cover_image.name).name or "cover.jpg"
        processed = center_crop_if_oversized(file_obj, filename=filename)
        if processed is None:
            return
        self.cover_image.save(processed.name, processed, save=False)


class ContactLead(CreatedAtModel):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32)
    email = models.EmailField(blank=True, default="")
    message = models.TextField()
    source_url = models.CharField(max_length=512, blank=True, default="")
    is_processed = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "content_contact_lead"
        ordering = ["-created_at"]
        verbose_name = "Заявка ЗЗ"
        verbose_name_plural = "Заявки ЗЗ"
        indexes = [
            models.Index(fields=["is_processed", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} {self.phone}"

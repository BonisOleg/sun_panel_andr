"""HomePage singleton — split from models.py (≤500 lines)."""

from django.db import models

from src.core.models import TimeStampedModel
from src.core.richtext import sanitize_richtext


class HomePage(TimeStampedModel):
    """Singleton: весь редакторський контент головної (крім списку переваг)."""

    status_text = models.CharField(
        "Статус-рядок",
        max_length=255,
        blank=True,
        default="Працюємо з 2012 року • 500+ встановлених обʼєктів",
    )
    title_before = models.CharField(
        "Заголовок (перед акцентом)",
        max_length=120,
        blank=True,
        default="Енергія",
    )
    title_highlight = models.CharField(
        "Заголовок (акцент)",
        max_length=80,
        blank=True,
        default="сонця",
    )
    title_after = models.CharField(
        "Заголовок (після акценту)",
        max_length=160,
        blank=True,
        default="для вашого дому та бізнесу",
    )
    lead = models.TextField(
        "Підзаголовок",
        blank=True,
        default=(
            "Проєктування, постачання та монтаж сонячних електростанцій під ключ. "
            "Автономність, прозорі терміни та гарантія до 30 років."
        ),
    )
    cta_primary_label = models.CharField(
        "CTA основна — текст",
        max_length=80,
        blank=True,
        default="Каталог обладнання",
    )
    cta_primary_url = models.CharField(
        "CTA основна — URL",
        max_length=512,
        blank=True,
        default="/katalog/",
    )
    cta_secondary_label = models.CharField(
        "CTA друга — текст",
        max_length=80,
        blank=True,
        default="Безкоштовна консультація",
    )
    cta_secondary_url = models.CharField(
        "CTA друга — URL",
        max_length=512,
        blank=True,
        default="/kontakty/",
    )
    image = models.ImageField(
        "Hero desktop",
        upload_to="content/home/",
        blank=True,
        help_text=(
            "Desktop hero: 1400×1050 px (4:3, JPG/WebP). "
            "Очистити — галочка «Очистити» і зберегти."
        ),
    )
    image_mobile = models.ImageField(
        "Hero mobile",
        upload_to="content/home/mobile/",
        blank=True,
        help_text=(
            "Mobile hero: 800×1000 px (4:5, JPG/WebP). "
            "Очистити — галочка «Очистити» і зберегти."
        ),
    )
    image_alt = models.CharField(
        "Alt зображення",
        max_length=255,
        blank=True,
        default="Soliron — сонячні електростанції",
    )
    float_badge_title = models.CharField(
        "Бейдж — заголовок",
        max_length=80,
        blank=True,
        default="Гарантія 30 років",
    )
    float_badge_subtitle = models.CharField(
        "Бейдж — підпис",
        max_length=120,
        blank=True,
        default="Якість без компромісів",
    )
    offer_enabled = models.BooleanField("Показувати пропозицію", default=True)
    offer_title = models.CharField(
        "Пропозиція — заголовок",
        max_length=255,
        blank=True,
        default="Каталог сонячних панелей і кріплень",
    )
    offer_subtitle = models.TextField("Пропозиція — текст", blank=True, default="")
    offer_link_label = models.CharField(
        "Пропозиція — кнопка",
        max_length=80,
        blank=True,
        default="Детальніше",
    )
    offer_link_url = models.CharField(
        "Пропозиція — URL",
        max_length=512,
        blank=True,
        default="/katalog/",
    )
    categories_eyebrow = models.CharField(
        "Каталог — надзаголовок",
        max_length=80,
        blank=True,
        default="АСОРТИМЕНТ",
    )
    categories_title = models.CharField(
        "Каталог — заголовок",
        max_length=160,
        blank=True,
        default="Каталог обладнання",
    )
    categories_description = models.CharField(
        "Каталог — опис",
        max_length=255,
        blank=True,
        default="Оберіть категорію, щоб перейти до товарів.",
    )
    advantages_eyebrow = models.CharField(
        "Про нас — надзаголовок",
        max_length=80,
        blank=True,
        default="Чому Soliron",
    )
    advantages_title = models.CharField(
        "Про нас — заголовок",
        max_length=160,
        blank=True,
        default="Про нас",
    )
    advantages_description = models.CharField(
        "Про нас — опис",
        max_length=255,
        blank=True,
        default="Якість, терміни та підтримка на кожному етапі.",
    )

    class Meta:
        db_table = "content_home_page"
        verbose_name = "Головна сторінка"
        verbose_name_plural = "Головна сторінка"

    def __str__(self) -> str:
        return "Головна сторінка"

    def save(self, *args, **kwargs):
        self.pk = 1
        if self.offer_subtitle:
            self.offer_subtitle = sanitize_richtext(self.offer_subtitle)
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "HomePage":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj



"""Опублікувати публічний договір і політику конфіденційності з HTML-файлів."""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from src.content.models import ContentPage
from src.core.richtext import sanitize_richtext

LEGAL_DIR = Path(__file__).resolve().parents[2] / "legal_texts"

PAGES = (
    {
        "slug": "publichnyy-dohovir",
        "filename": "oferta_uk.html",
        "title": "Публічний договір",
        "sort_order": 30,
        "seo_title": "Публічний договір (оферта)",
        "seo_description": "Публічний договір купівлі-продажу Soliron.",
    },
    {
        "slug": "polityka-konfidentsiynosti",
        "filename": "privacy_uk.html",
        "title": "Політика конфіденційності",
        "sort_order": 40,
        "seo_title": "Політика конфіденційності",
        "seo_description": "Політика обробки персональних даних Soliron.",
    },
)


class Command(BaseCommand):
    help = (
        "Оновлює body інфо-сторінок публічного договору та політики "
        "конфіденційності з HTML-файлів. Заголовок і SEO наявних рядків не чіпає."
    )

    def handle(self, *args, **options):
        for spec in PAGES:
            body = self._read_body(spec["filename"])
            self._publish(spec, body)

    def _read_body(self, filename: str) -> str:
        path = LEGAL_DIR / filename
        if not path.is_file():
            raise CommandError(f"Немає файлу {path}")
        raw = path.read_text(encoding="utf-8")
        if "УТОЧНИТИ" in raw:
            raise CommandError(f"У {filename} лишився маркер УТОЧНИТИ")
        body = sanitize_richtext(raw)
        if not body or "УТОЧНИТИ" in body:
            raise CommandError(f"Порожній або непідготовлений текст: {filename}")
        return body

    def _publish(self, spec: dict, body: str) -> None:
        slug = spec["slug"]
        page = ContentPage.objects.filter(slug=slug).first()
        if page is None:
            ContentPage(
                slug=slug,
                title=spec["title"],
                body=body,
                is_published=True,
                sort_order=spec["sort_order"],
                seo_title=spec["seo_title"],
                seo_description=spec["seo_description"],
                seo_keywords="",
            ).save()
            self.stdout.write(self.style.SUCCESS(f"{slug}: створено"))
            return

        changed: list[str] = []
        if page.body != body:
            page.body = body
            changed.append("body")
        if not page.is_published:
            page.is_published = True
            changed.append("is_published")
        if not changed:
            self.stdout.write(f"{slug}: без змін")
            return
        page.save(update_fields=["body", "is_published", "updated_at"])
        self.stdout.write(
            self.style.SUCCESS(f"{slug}: оновлено {', '.join(changed)}")
        )

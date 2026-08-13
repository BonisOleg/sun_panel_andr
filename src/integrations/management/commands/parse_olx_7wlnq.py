"""CLI: python3 manage.py parse_olx_7wlnq"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from src.integrations.parsers.olx_7wlnq import run_parse
from src.integrations.parsers.olx_7wlnq.client import OlxHttpError


class Command(BaseCommand):
    help = (
        "Парсер OLX продавця 7wLNQ → data/olx_7wlnq/ "
        "(категорії, товари, фото). Без запису в БД."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Обмежити кількість оголошень (smoke-тест).",
        )
        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Не завантажувати фото (лише JSON + URL).",
        )

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        limit = options["limit"]
        download_images = not options["skip_images"]

        def progress(msg: str) -> None:
            self.stdout.write(msg)

        try:
            meta = run_parse(
                base_dir,
                download_images=download_images,
                limit=limit,
                progress=progress,
            )
        except OlxHttpError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"OK products={meta['products_ok']} "
                f"errors={meta['errors_count']} "
                f"dir={meta['data_dir']}"
            )
        )
        if meta["errors"]:
            for err in meta["errors"]:
                self.stderr.write(f"  ERR {err['url']}: {err['error']}")

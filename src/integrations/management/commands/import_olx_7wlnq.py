"""CLI: python3 manage.py import_olx_7wlnq [--apply] [--publish]"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from src.integrations.parsers.olx_7wlnq.import_db import run_import


class Command(BaseCommand):
    help = (
        "Імпорт data/olx_7wlnq → Category/Product/ProductImage. "
        "За замовчуванням dry-run; запис лише з --apply."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Записати в БД (без прапорця — лише dry-run).",
        )
        parser.add_argument(
            "--publish",
            action="store_true",
            help="Поставити is_published=True (інакше False для нових).",
        )

    def handle(self, *args, **options):
        apply = bool(options["apply"])
        publish = bool(options["publish"])
        base_dir = Path(settings.BASE_DIR)

        def progress(msg: str) -> None:
            self.stdout.write(msg)

        try:
            result = run_import(
                base_dir,
                apply=apply,
                publish=publish,
                progress=progress,
            )
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc

        mode = "APPLY" if apply else "DRY-RUN"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: created={result['created']} updated={result['updated']} "
                f"images={result['images']} skipped={result['skipped']} "
                f"categories={result['categories_mapped']}"
            )
        )
        if not apply:
            self.stdout.write("Для запису в БД: python3 manage.py import_olx_7wlnq --apply")

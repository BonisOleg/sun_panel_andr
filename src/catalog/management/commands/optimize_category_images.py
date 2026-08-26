"""Re-encode category images to WebP (max 912×608)."""

from django.core.management.base import BaseCommand

from src.catalog.models import Category


class Command(BaseCommand):
    help = "Optimize existing Category.image files to WebP with resize."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-encode even if already WebP and within size limits.",
        )

    def handle(self, *args, **options):
        force = bool(options["force"])
        qs = Category.objects.exclude(image="").exclude(image__isnull=True)
        total = qs.count()
        changed = 0
        skipped = 0
        errors = 0

        self.stdout.write(f"Categories with images: {total}")
        for cat in qs.iterator():
            before = cat.image.name
            try:
                cat._process_image(force=force)
                after = cat.image.name
                if after != before:
                    Category.objects.filter(pk=cat.pk).update(image=after)
                    changed += 1
                    self.stdout.write(f"OK {cat.pk} {before} → {after}")
                else:
                    skipped += 1
            except Exception as exc:  # noqa: BLE001 — report and continue batch
                errors += 1
                self.stderr.write(f"ERR {cat.pk} {before}: {exc}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. changed={changed} skipped={skipped} errors={errors}"
            )
        )

from django.core.management.base import BaseCommand, CommandError

from src.shipping.models import NPCity
from src.shipping.services import (
    NovaPoshtaError,
    sync_all_warehouses,
    sync_cities,
    sync_warehouses_for_city,
)


class Command(BaseCommand):
    help = "Синк міст/відділень Нової Пошти в локальну БД (novaposhta_skill)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--warehouses",
            action="store_true",
            help="Також синкнути відділення для всіх міст (довго).",
        )
        parser.add_argument(
            "--city-ref",
            default="",
            help="Синк відділень лише для одного CityRef.",
        )

    def handle(self, *args, **options):
        try:
            n = sync_cities()
            self.stdout.write(self.style.SUCCESS(f"Міста: {n}"))
            if options["city_ref"]:
                city = NPCity.objects.filter(ref=options["city_ref"]).first()
                if city is None:
                    raise CommandError("Місто не знайдено після sync")
                w = sync_warehouses_for_city(city)
                self.stdout.write(self.style.SUCCESS(f"Відділення: {w}"))
            elif options["warehouses"]:
                total = sync_all_warehouses()
                self.stdout.write(self.style.SUCCESS(f"Відділення разом: {total}"))
        except NovaPoshtaError as exc:
            raise CommandError(str(exc)) from exc

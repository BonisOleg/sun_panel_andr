"""Синк міст/складів Delivery Auto у локальну БД (cron раз на добу)."""

from django.core.management.base import BaseCommand, CommandError

from src.shipping.delivery import DeliveryAPIError
from src.shipping.delivery.sync import sync_all_warehouses, sync_cities, sync_warehouses_for_city
from src.shipping.models import DeliveryCity


class Command(BaseCommand):
    help = (
        "Синхронізує міста та вантажні склади Delivery Auto. "
        "Рекомендовано: cron щодоби, напр. 0 3 * * *."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--warehouses",
            action="store_true",
            help="Також синкнути склади для всіх активних міст (довго, ~N запитів).",
        )
        parser.add_argument(
            "--city-id",
            default="",
            help="Синк складів лише для одного Delivery city_id (GUID).",
        )
        parser.add_argument(
            "--fl-all",
            action="store_true",
            help="Тягнути всі населені пункти (fl_all=true), не лише міста зі складами.",
        )
        parser.add_argument(
            "--with-info",
            action="store_true",
            help="Для кожного складу викликати GetWarehousesInfo (телефон; дуже довго).",
        )

    def handle(self, *args, **options):
        try:
            n_cities = sync_cities(fl_all=bool(options["fl_all"]))
            self.stdout.write(self.style.SUCCESS(f"Міста: {n_cities}"))

            city_id = (options["city_id"] or "").strip()
            if city_id:
                city = DeliveryCity.objects.filter(city_id=city_id).first()
                if city is None:
                    raise CommandError("Місто не знайдено після sync міст")
                n_wh = sync_warehouses_for_city(
                    city,
                    with_info=bool(options["with_info"]),
                )
                self.stdout.write(self.style.SUCCESS(f"Склади ({city.name_uk}): {n_wh}"))
            elif options["warehouses"]:
                def _progress(city: DeliveryCity, n: int) -> None:
                    self.stdout.write(f"  {city.name_uk}: {n}")

                total = sync_all_warehouses(
                    with_info=bool(options["with_info"]),
                    progress=_progress,
                )
                self.stdout.write(self.style.SUCCESS(f"Склади разом: {total}"))
            else:
                self.stdout.write(
                    "Лише міста. Для складів: --warehouses або --city-id=<GUID>"
                )
        except DeliveryAPIError as exc:
            raise CommandError(str(exc)) from exc

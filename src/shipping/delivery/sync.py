"""Синхронізація міст/складів Delivery Auto у локальну БД."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from django.db import transaction

from src.shipping.models import DeliveryCity, DeliveryWarehouse

from .client import DeliveryAPIClient
from .exceptions import DeliveryAPIError

logger = logging.getLogger(__name__)


def _is_freight_warehouse(row: dict[str, Any]) -> bool:
    """Вантажне відділення: типи 0/3 (склад / склад з переказом)."""
    wtype = row.get("warehouseType", row.get("WarehouseType"))
    if wtype is not None and wtype not in (0, 3):
        return False
    return True


@transaction.atomic
def sync_cities(
    client: DeliveryAPIClient | None = None,
    *,
    fl_all: bool = False,
) -> int:
    """Upsert міст з GetAreasList; відсутні в відповіді → is_active=False."""
    client = client or DeliveryAPIClient()
    rows = client.get_areas_list(fl_all=fl_all)
    seen: set[str] = set()
    count = 0
    for row in rows:
        city_id = str(row.get("id") or "").strip()
        name = (row.get("name") or "").strip()
        if not city_id or not name:
            continue
        seen.add(city_id)
        DeliveryCity.objects.update_or_create(
            city_id=city_id,
            defaults={
                "name_uk": name,
                "region_name": (row.get("regionName") or "").strip(),
                "is_active": True,
            },
        )
        count += 1

    if seen:
        DeliveryCity.objects.exclude(city_id__in=seen).update(is_active=False)
    logger.info("Delivery cities synced: %s (fl_all=%s)", count, fl_all)
    return count


def sync_warehouses_for_city(
    city: DeliveryCity,
    client: DeliveryAPIClient | None = None,
    *,
    with_info: bool = False,
) -> int:
    """Upsert складів одного міста; зайві для міста → is_active=False."""
    client = client or DeliveryAPIClient()
    rows = client.get_warehouses_list(city_id=city.city_id)
    seen: set[str] = set()
    count = 0
    for row in rows:
        warehouse_id = str(row.get("id") or "").strip()
        name = (row.get("name") or "").strip()
        if not warehouse_id or not name:
            continue
        seen.add(warehouse_id)
        phone = ""
        if with_info:
            try:
                info = client.get_warehouse_info(warehouse_id)
                phone = (info.get("Phone") or "").strip()
            except DeliveryAPIError:
                logger.warning("GetWarehousesInfo failed for %s", warehouse_id)

        DeliveryWarehouse.objects.update_or_create(
            warehouse_id=warehouse_id,
            defaults={
                "city": city,
                "name_uk": name,
                "address_uk": (row.get("address") or "").strip(),
                "phone": phone,
                "max_weight": None,
                "warehouse_type": row.get("warehouseType"),
                "is_freight": _is_freight_warehouse(row),
                "is_active": True,
            },
        )
        count += 1

    qs = DeliveryWarehouse.objects.filter(city=city)
    if seen:
        qs.exclude(warehouse_id__in=seen).update(is_active=False)
    elif count == 0:
        qs.update(is_active=False)
    return count


def sync_all_warehouses(
    client: DeliveryAPIClient | None = None,
    *,
    with_info: bool = False,
    progress: Callable[[DeliveryCity, int], None] | None = None,
) -> int:
    """Синк складів для всіх активних міст Delivery."""
    client = client or DeliveryAPIClient()
    total = 0
    cities = DeliveryCity.objects.filter(is_active=True).iterator()
    for city in cities:
        n = sync_warehouses_for_city(city, client, with_info=with_info)
        total += n
        if progress:
            progress(city, n)
    logger.info("Delivery warehouses synced: %s", total)
    return total

"""NP local search + sync (novaposhta_skill) — checkout reads DB only."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests
from django.conf import settings
from django.db import transaction
from django.db.models import Case, IntegerField, Value, When
from django.db.models.functions import Length

from .models import NPCity, NPWarehouse

logger = logging.getLogger(__name__)
NP_API_URL = "https://api.novaposhta.ua/v2.0/json/"


class NovaPoshtaError(Exception):
    pass


def search_cities(query: str, limit: int = 20) -> list[dict]:
    """Пошук міст НП з локальної БД.

    Пріоритет: точна назва → починається з запиту → містить;
    далі коротші назви (Київ вище за «…(Київська обл.)»).
    """
    query = (query or "").strip()
    if len(query) < 2:
        return []
    qs = (
        NPCity.objects.filter(is_active=True, name__icontains=query)
        .annotate(
            match_rank=Case(
                When(name__iexact=query, then=Value(0)),
                When(name__istartswith=query, then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
            name_len=Length("name"),
        )
        .order_by("match_rank", "name_len", "name")[:limit]
    )
    return [
        {"ref": c.ref, "name": c.name, "area": c.area}
        for c in qs
    ]


def list_warehouses(city_ref: str, query: str = "", limit: int = 50) -> list[dict]:
    city_ref = (city_ref or "").strip()
    if not city_ref:
        return []
    qs = NPWarehouse.objects.filter(city__ref=city_ref, is_active=True)
    q = (query or "").strip()
    if q:
        qs = qs.filter(description__icontains=q)
    qs = qs.order_by("description")[:limit]
    return [
        {
            "ref": w.ref,
            "description": w.description,
            "number": w.number,
            "city_ref": city_ref,
        }
        for w in qs
    ]


def _api_key() -> str:
    return getattr(settings, "NP_API_KEY", "") or ""


def _api_delay() -> float:
    return float(getattr(settings, "NP_API_DELAY", 0.35) or 0)


def _api_max_retries() -> int:
    return int(getattr(settings, "NP_API_MAX_RETRIES", 6) or 6)


def _is_rate_limit_error(errors: list[Any]) -> bool:
    text = " ".join(str(item) for item in errors).lower()
    return "many requests" in text or "to many requests" in text


def _call(model_name: str, method: str, props: dict[str, Any]) -> list[dict]:
    key = _api_key()
    if not key:
        raise NovaPoshtaError("NP_API_KEY не налаштовано")
    body = {
        "apiKey": key,
        "modelName": model_name,
        "calledMethod": method,
        "methodProperties": props,
    }
    retries = _api_max_retries()
    for attempt in range(retries):
        try:
            resp = requests.post(NP_API_URL, json=body, timeout=60)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as exc:
            logger.exception("NP API network error")
            raise NovaPoshtaError("Помилка звʼязку з Новою Поштою") from exc
        if data.get("success"):
            delay = _api_delay()
            if delay > 0:
                time.sleep(delay)
            return data.get("data") or []
        errors = data.get("errors") or data.get("errorCodes") or ["unknown"]
        if _is_rate_limit_error(errors) and attempt < retries - 1:
            wait = min(60, 2 ** attempt * 3)
            logger.warning("NP rate limit (%s), retry %s/%s in %ss", errors, attempt + 1, retries, wait)
            time.sleep(wait)
            continue
        logger.error("NP API error: %s", errors)
        raise NovaPoshtaError("; ".join(str(e) for e in errors))
    return []


@transaction.atomic
def sync_cities() -> int:
    """Page must be a string (novaposhta_skill)."""
    page = 1
    count = 0
    while True:
        rows = _call(
            "Address",
            "getCities",
            {"Page": str(page), "Limit": "500"},
        )
        if not rows:
            break
        for row in rows:
            NPCity.objects.update_or_create(
                ref=row["Ref"],
                defaults={
                    "name": row.get("Description") or "",
                    "area": row.get("AreaDescription") or "",
                    "is_active": True,
                },
            )
            count += 1
        page += 1
    return count


def _city_for_warehouse_row(
    row: dict[str, Any],
    cache: dict[str, NPCity],
) -> NPCity | None:
    city_ref = (row.get("CityRef") or "").strip()
    if not city_ref:
        return None
    if city_ref in cache:
        return cache[city_ref]
    city = NPCity.objects.filter(ref=city_ref).first()
    if city is None:
        city, _ = NPCity.objects.get_or_create(
            ref=city_ref,
            defaults={
                "name": row.get("CityDescription") or "",
                "area": row.get("SettlementAreaDescription") or "",
                "is_active": True,
            },
        )
    cache[city_ref] = city
    return city


def _upsert_warehouse_row(row: dict[str, Any], city: NPCity) -> None:
    NPWarehouse.objects.update_or_create(
        ref=row["Ref"],
        defaults={
            "city": city,
            "number": str(row.get("Number") or ""),
            "description": row.get("Description") or "",
            "is_active": True,
        },
    )


@transaction.atomic
def sync_warehouses_for_city(city: NPCity) -> int:
    page = 1
    count = 0
    while True:
        rows = _call(
            "Address",
            "getWarehouses",
            {"CityRef": city.ref, "Page": str(page), "Limit": "500"},
        )
        if not rows:
            break
        for row in rows:
            _upsert_warehouse_row(row, city)
            count += 1
        page += 1
    return count


def sync_all_warehouses() -> int:
    """Bulk getWarehouses без CityRef — один прохід з пагінацією (novaposhta_skill)."""
    page = 1
    count = 0
    city_cache: dict[str, NPCity] = {}
    while True:
        rows = _call(
            "Address",
            "getWarehouses",
            {"Page": str(page), "Limit": "500"},
        )
        if not rows:
            break
        with transaction.atomic():
            for row in rows:
                city = _city_for_warehouse_row(row, city_cache)
                if city is None:
                    continue
                _upsert_warehouse_row(row, city)
                count += 1
        logger.info("NP warehouses synced page %s (%s rows, total %s)", page, len(rows), count)
        page += 1
    return count

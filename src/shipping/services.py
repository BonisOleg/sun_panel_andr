"""NP local search + sync (novaposhta_skill) — checkout reads DB only."""

from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings
from django.db import transaction

from .models import NPCity, NPWarehouse

logger = logging.getLogger(__name__)
NP_API_URL = "https://api.novaposhta.ua/v2.0/json/"


class NovaPoshtaError(Exception):
    pass


def search_cities(query: str, limit: int = 20) -> list[dict]:
    query = (query or "").strip()
    if len(query) < 2:
        return []
    qs = NPCity.objects.filter(is_active=True, name__icontains=query).order_by("name")[
        :limit
    ]
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
    try:
        resp = requests.post(NP_API_URL, json=body, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.exception("NP API network error")
        raise NovaPoshtaError("Помилка звʼязку з Новою Поштою") from exc
    if not data.get("success"):
        errors = data.get("errors") or data.get("errorCodes") or ["unknown"]
        logger.error("NP API error: %s", errors)
        raise NovaPoshtaError("; ".join(str(e) for e in errors))
    return data.get("data") or []


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
            NPWarehouse.objects.update_or_create(
                ref=row["Ref"],
                defaults={
                    "city": city,
                    "number": str(row.get("Number") or ""),
                    "description": row.get("Description") or "",
                    "is_active": True,
                },
            )
            count += 1
        page += 1
    return count

"""Пошук міст/складів Delivery лише з локальної БД (checkout)."""

from __future__ import annotations

from src.shipping.models import DeliveryCity, DeliveryWarehouse

from .aliases import expand_city_query


def _matches_any(haystack: str, terms: list[str]) -> bool:
    text = (haystack or "").casefold()
    return any(term in text for term in terms)


def _match_rank(name: str, terms: list[str]) -> int:
    """0 = точний збіг, 1 = починається з терміну, 2 = містить."""
    text = (name or "").casefold()
    if any(text == term for term in terms):
        return 0
    if any(text.startswith(term) for term in terms):
        return 1
    return 2


def search_cities(query: str, limit: int = 20) -> list[dict]:
    """Case-insensitive + латиниця (Kyiv) / маленькі літери (київ).

    SQLite `icontains` некоректний для кирилиці — фільтруємо через casefold.
    """
    terms = expand_city_query(query)
    if not terms:
        return []

    cities = (
        DeliveryCity.objects.filter(is_active=True)
        .only("city_id", "name_uk", "region_name")
    )
    scored: list[tuple[int, str, dict]] = []
    for c in cities.iterator():
        if not _matches_any(c.name_uk, terms):
            continue
        scored.append(
            (
                _match_rank(c.name_uk, terms),
                c.name_uk.casefold(),
                {
                    "id": c.city_id,
                    "name": c.name_uk,
                    "region": c.region_name,
                },
            )
        )
    scored.sort(key=lambda row: (row[0], row[1]))
    return [row[2] for row in scored[:limit]]


def list_warehouses(
    city_id: str,
    query: str = "",
    limit: int = 50,
) -> list[dict]:
    city_id = (city_id or "").strip()
    if not city_id:
        return []
    qs = DeliveryWarehouse.objects.filter(
        city__city_id=city_id,
        is_active=True,
        is_freight=True,
    ).only("warehouse_id", "name_uk", "address_uk")

    q = (query or "").strip()
    terms = [q.casefold()] if len(q) >= 1 else []

    results: list[dict] = []
    for w in qs.order_by("name_uk").iterator():
        if terms and not (
            _matches_any(w.name_uk, terms) or _matches_any(w.address_uk, terms)
        ):
            continue
        results.append(
            {
                "id": w.warehouse_id,
                "name": w.name_uk,
                "address": w.address_uk,
                "city_id": city_id,
            }
        )
        if len(results) >= limit:
            break
    return results

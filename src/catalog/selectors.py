"""catalog selectors — read-only (tables.md / business_logic.md)."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from django.db.models import Prefetch, Q, QuerySet
from django.shortcuts import get_object_or_404

from .models import Category, Product, ProductImage

SORT_CHOICES = {
    "": ("sort_order", "-updated_at"),
    "newest": ("-updated_at", "sort_order"),
    "price_asc": ("price_uah", "sort_order"),
    "price_desc": ("-price_uah", "sort_order"),
    "name": ("name",),
}


def active_root_categories() -> QuerySet[Category]:
    return Category.objects.filter(is_active=True, parent__isnull=True).order_by(
        "sort_order",
        "name",
    )


def get_category_by_slug(slug: str) -> Category:
    return get_object_or_404(Category, slug=slug, is_active=True)


def category_descendant_ids(category: Category) -> list[int]:
    """BFS subtree including self (MVP without CTE)."""
    ids = [category.id]
    frontier = [category.id]
    while frontier:
        children = list(
            Category.objects.filter(parent_id__in=frontier, is_active=True).values_list(
                "id",
                flat=True,
            )
        )
        frontier = [cid for cid in children if cid not in ids]
        ids.extend(frontier)
    return ids


def category_ancestors(category: Category) -> list[Category]:
    chain: list[Category] = []
    current: Category | None = category
    seen: set[int] = set()
    while current is not None and current.id not in seen:
        chain.append(current)
        seen.add(current.id)
        current = current.parent
    chain.reverse()
    return chain


def published_products() -> QuerySet[Product]:
    return (
        Product.objects.filter(is_published=True)
        .select_related("category")
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.order_by("sort_order", "id"),
            )
        )
        .order_by("sort_order", "-updated_at")
    )


def _parse_price(raw: str | None) -> Decimal | None:
    value = (raw or "").strip().replace(" ", "").replace(",", ".")
    if not value:
        return None
    try:
        amount = Decimal(value)
    except InvalidOperation:
        return None
    if amount < 0:
        return None
    return amount


def parse_catalog_filters(request) -> dict:
    sort = (request.GET.get("sort") or "").strip()
    if sort not in SORT_CHOICES:
        sort = ""
    return {
        "q": (request.GET.get("q") or "").strip(),
        "sort": sort,
        "price_min": _parse_price(request.GET.get("price_min")),
        "price_max": _parse_price(request.GET.get("price_max")),
        "price_min_raw": (request.GET.get("price_min") or "").strip(),
        "price_max_raw": (request.GET.get("price_max") or "").strip(),
    }


def _query_stem(query: str) -> str | None:
    folded = query.casefold()
    for suf in ("іх", "их", "ій", "ий", "ої", "ою", "ею", "і", "и", "а", "у", "ю"):
        if len(folded) > len(suf) + 3 and folded.endswith(suf):
            return query[: -len(suf)]
    return None


def _query_variants(query: str) -> list[str]:
    """Substring variants for uk/ru endings (сонячні → сонячн / сонячна…)."""
    variants = [query]
    seen = {query.casefold()}
    stem = _query_stem(query)
    if stem and stem.casefold() not in seen:
        variants.append(stem)
        seen.add(stem.casefold())
        for ending in ("а", "е", "і", "ий", "ій", "их", "іх", "ої", "ою"):
            form = stem + ending
            key = form.casefold()
            if key not in seen:
                variants.append(form)
                seen.add(key)
    return variants


def filter_products(
    *,
    category: Category | None = None,
    q: str = "",
    price_min: Decimal | None = None,
    price_max: Decimal | None = None,
    sort: str = "",
) -> QuerySet[Product]:
    qs = published_products()
    if category is not None:
        qs = qs.filter(category_id__in=category_descendant_ids(category))
    query = (q or "").strip()
    if query:
        name_sku = Q()
        for term in _query_variants(query):
            name_sku |= Q(name__icontains=term) | Q(sku__icontains=term)
        qs = qs.filter(name_sku)
    if price_min is not None:
        qs = qs.filter(price_uah__gte=price_min)
    if price_max is not None:
        qs = qs.filter(price_uah__lte=price_max)
    order = SORT_CHOICES.get(sort) or SORT_CHOICES[""]
    return qs.order_by(*order)


SUGGEST_MIN_CHARS = 2
SUGGEST_LIMIT = 6
SUGGEST_CANDIDATE_POOL = 40


def _suggest_relevance(name: str, sku: str, query: str, variants: list[str]) -> tuple:
    """Sort key: lower tuple = more relevant to q."""
    name_f = (name or "").casefold()
    sku_f = (sku or "").casefold()
    q_f = query.casefold()
    stem = _query_stem(query)
    stem_f = stem.casefold() if stem else ""

    score = 0
    best_pos = 10_000

    if q_f and q_f in name_f:
        score += 120
        best_pos = min(best_pos, name_f.find(q_f))

    for v in sorted(variants, key=len, reverse=True):
        vf = v.casefold()
        if len(vf) < 2:
            continue
        pos = name_f.find(vf)
        in_sku = vf in sku_f
        if pos < 0 and not in_sku:
            continue
        if pos >= 0:
            best_pos = min(best_pos, pos)
            # слово / межа токена
            at_boundary = pos == 0 or not name_f[pos - 1].isalnum()
            score += (70 if at_boundary else 35) + len(vf) * 2
            score += name_f.count(vf) * 8
        elif in_sku:
            score += 20 + len(vf)

    # «сонячна панель» > «для сонячних панелей» (комплектуючі)
    if stem_f:
        if f"для {stem_f}" in name_f:
            score -= 45
        if re.search(rf"(?:^|[\s\"«]){re.escape(stem_f)}\w*\s+\w+", name_f):
            score += 40
        if best_pos <= 28:
            score += 20

    # коротша назва з тим самим збігом — зазвичай точніший товар
    score -= min(len(name_f), 80) // 20

    return (-score, best_pos, len(name_f))


def suggest_products(q: str, *, limit: int = SUGGEST_LIMIT) -> list[Product]:
    """Header live-search suggestions ranked by relevance to q."""
    query = (q or "").strip()
    cap = max(1, min(limit, SUGGEST_LIMIT))
    if len(query) < SUGGEST_MIN_CHARS:
        return []

    variants = _query_variants(query)
    candidates = list(filter_products(q=query)[:SUGGEST_CANDIDATE_POOL])
    ranked = sorted(
        candidates,
        key=lambda p: _suggest_relevance(p.name, p.sku or "", query, variants),
    )

    out: list[Product] = []
    seen_names: set[str] = set()
    for product in ranked:
        key = " ".join((product.name or "").casefold().split())
        if key in seen_names:
            continue
        seen_names.add(key)
        out.append(product)
        if len(out) >= cap:
            break
    return out


def get_published_product(slug: str) -> Product:
    return get_object_or_404(
        published_products(),
        slug=slug,
    )

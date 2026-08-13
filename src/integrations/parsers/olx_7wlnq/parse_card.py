"""Парсинг PDP OLX — DOM primary, JSON-LD лише fallback (ERR-CAT-01)."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from .constants import BASE_ORIGIN, PLACEHOLDER_IMAGE_MARKERS, REGION_BREADCRUMB_MARKERS
from .discover import ID_IN_URL_RE, _slug_hint

PRICE_RE = re.compile(
    r"([\d\s\u00a0]+(?:[.,]\d+)?)\s*(грн\.?|uah|₴)?",
    re.I,
)
NUMERIC_ID_RE = re.compile(r"ID:\s*(\d+)", re.I)
PUBLISHED_RE = re.compile(r"Опубліковано[^\n\d]*([\d]{1,2}\s+\S+\s+\d{4}[^\n]*)", re.I)


def _text(el: Tag | None) -> str:
    if el is None:
        return ""
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()


def _is_placeholder(url: str) -> bool:
    low = (url or "").lower()
    return any(m in low for m in PLACEHOLDER_IMAGE_MARKERS)


def parse_price_uah(raw: str) -> Decimal | None:
    if not raw:
        return None
    m = PRICE_RE.search(raw.replace("\u00a0", " "))
    if not m:
        return None
    num = m.group(1).replace(" ", "").replace("\u00a0", "").replace(",", ".")
    try:
        return Decimal(num)
    except InvalidOperation:
        return None


def _category_path_from_breadcrumbs(crumbs: list[str]) -> list[str]:
    out: list[str] = []
    for c in crumbs:
        if c in ("Головна", "OLX"):
            continue
        if any(x in c for x in REGION_BREADCRUMB_MARKERS):
            continue
        # «Електрика - Полтава» вже відсіяно маркерами
        if c not in out:
            out.append(c)
    return out


def _extract_images(soup: BeautifulSoup, html: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    def add(u: str) -> None:
        if not u or _is_placeholder(u):
            return
        # розкодувати \u002F якщо прийшло з prerender
        u = (
            u.replace("\\\\u002F", "/")
            .replace("\\u002F", "/")
            .replace("\\/", "/")
        )
        if not u.startswith("http"):
            u = urljoin(BASE_ORIGIN, u)
        base = u.split(";")[0].split("?")[0]
        if "apollo.olxcdn.com" not in base and "/files/" not in base:
            return
        if base in seen:
            return
        seen.add(base)
        urls.append(base)

    for img in soup.select("img[src], img[data-src], source[srcset]"):
        for attr in ("src", "data-src"):
            add(img.get(attr, ""))
        srcset = img.get("srcset") or ""
        for part in srcset.split(","):
            add(part.strip().split(" ")[0])

    for m in re.finditer(
        r"https://ireland\.apollo\.olxcdn\.com/v1/files/[A-Za-z0-9_-]+-UA/image",
        html,
    ):
        add(m.group(0))

    # prerender escape
    for m in re.finditer(
        r"ireland\.apollo\.olxcdn\.com\\\\u002Fv1\\\\u002Ffiles\\\\u002F([A-Za-z0-9_-]+-UA)\\\\u002Fimage",
        html,
    ):
        add(f"https://ireland.apollo.olxcdn.com/v1/files/{m.group(1)}/image")
    for m in re.finditer(
        r"ireland\.apollo\.olxcdn\.com\\u002Fv1\\u002Ffiles\\u002F([A-Za-z0-9_-]+-UA)\\u002Fimage",
        html,
    ):
        add(f"https://ireland.apollo.olxcdn.com/v1/files/{m.group(1)}/image")

    return urls


def _extract_description(soup: BeautifulSoup) -> str:
    # Primary: видимий блок опису
    node = soup.select_one('[data-cy="ad_description"]')
    if node:
        # прибрати заголовок «Опис» всередині
        text = node.get_text("\n", strip=True)
        text = re.sub(r"^Опис\s*", "", text, flags=re.I).strip()
        if len(text) >= 40:
            return text

    for h in soup.find_all(["h2", "h3", "h4"]):
        if _text(h).lower() == "опис":
            parts: list[str] = []
            for sib in h.next_siblings:
                if isinstance(sib, Tag) and sib.name in ("h2", "h3", "h4"):
                    break
                if isinstance(sib, Tag):
                    t = sib.get_text("\n", strip=True)
                    if t:
                        parts.append(t)
            merged = "\n".join(parts).strip()
            if len(merged) >= 40:
                return merged

    return ""


def _extract_params(soup: BeautifulSoup) -> dict[str, str]:
    params: dict[str, str] = {}
    container = soup.select_one('[data-testid="ad-parameters-container"]')
    if container:
        # пари p/p або li
        texts = [_text(p) for p in container.find_all(["p", "li", "span"])]
        texts = [t for t in texts if t]
        # часто "Стан: Нове" одним рядком
        for t in texts:
            if ":" in t:
                k, v = t.split(":", 1)
                params[k.strip()] = v.strip()
            elif t in ("Бізнес", "Приватна особа"):
                params["Тип продавця"] = t

    body = soup.get_text("\n", strip=True)
    m = re.search(r"Стан:\s*([^\n]+)", body)
    if m and "Стан" not in params:
        params["Стан"] = m.group(1).strip()
    if re.search(r"\bБізнес\b", body) and "Тип продавця" not in params:
        params["Тип продавця"] = "Бізнес"
    return params


def parse_product_html(html: str, source_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")

    title = ""
    h = soup.select_one('[data-cy="ad_title"], h1')
    if h:
        title = _text(h)
    if not title:
        # OLX часто ставить назву в h4 біля ціни
        for hx in soup.find_all(["h1", "h2", "h3", "h4"]):
            t = _text(hx)
            if t and t not in ("Опис", "Повідомлення") and "грн" not in t.lower():
                if len(t) > 15:
                    title = t
                    break
    if not title:
        ttag = soup.find("title")
        if ttag:
            title = _text(ttag).split(":")[0].strip()

    price_raw = ""
    price_el = soup.select_one('[data-testid="ad-price-container"], [data-testid="ad-price"]')
    if price_el:
        price_raw = _text(price_el)
    if not price_raw:
        for hx in soup.find_all(["h2", "h3"]):
            t = _text(hx)
            if "грн" in t.lower():
                price_raw = t
                break
    price_uah = parse_price_uah(price_raw)

    crumbs = []
    for a in soup.select('[data-testid="breadcrumb-item"], ol li a, nav[data-testid] a'):
        t = _text(a)
        if t:
            crumbs.append(t)
    if not crumbs:
        for a in soup.select("ol li a"):
            t = _text(a)
            if t:
                crumbs.append(t)

    category_path = _category_path_from_breadcrumbs(crumbs)
    leaf = category_path[-1] if category_path else None

    description = _extract_description(soup)
    params = _extract_params(soup)
    images = _extract_images(soup, html)

    m_id = NUMERIC_ID_RE.search(soup.get_text(" ", strip=True))
    numeric_id = m_id.group(1) if m_id else None
    m_slug = ID_IN_URL_RE.search(source_url)
    slug_id = m_slug.group(1) if m_slug else None
    supplier_sku = numeric_id or slug_id or _slug_hint(title)[:64]

    location = ""
    loc = soup.select_one('[data-testid="map-aside-section"], [data-testid="location-date"]')
    if loc:
        location = _text(loc)
    if not location:
        mloc = re.search(
            r"Місцезнаходження\s*([^\n]+)",
            soup.get_text("\n", strip=True),
        )
        if mloc:
            location = mloc.group(1).strip(" ,")

    published = ""
    mpub = PUBLISHED_RE.search(soup.get_text("\n", strip=True))
    if mpub:
        published = mpub.group(0).strip()

    return {
        "source": "olx_7wlnq",
        "supplier_sku": supplier_sku,
        "olx_numeric_id": numeric_id,
        "olx_slug_id": slug_id,
        "source_url": source_url,
        "name": title,
        "slug_hint": _slug_hint(title)[:160],
        "price_uah": str(price_uah) if price_uah is not None else None,
        "price_raw": price_raw,
        "currency": "UAH",
        "description": description,
        "params": params,
        "category_path": category_path,
        "category_leaf": leaf,
        "breadcrumbs_raw": crumbs,
        "location": location,
        "published": published,
        "image_urls": images,
        "images_local": [],
        "is_business": params.get("Тип продавця") == "Бізнес",
        "condition": params.get("Стан", ""),
    }

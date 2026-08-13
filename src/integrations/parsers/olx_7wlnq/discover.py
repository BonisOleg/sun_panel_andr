"""Discover: listing URLs + дерево категорій з фільтра продавця."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

from .client import OlxClient
from .constants import BASE_ORIGIN, SELLER_LIST_URL

logger = logging.getLogger(__name__)

AD_HREF_RE = re.compile(r"/d/(?:uk/)?obyavlenie/[^\"'#?]+", re.I)
ID_IN_URL_RE = re.compile(r"ID([A-Za-z0-9]+)\.html", re.I)
# OLX seller listing ховає URL у __PRERENDERED_STATE__ (подвійне екранування \u002F)
PRERENDER_AD_RE = re.compile(
    r"obyavlenie\\\\u002F([a-z0-9\-]+-ID[A-Za-z0-9]+)\.html",
    re.I,
)
PRERENDER_AD_RE_ALT = re.compile(
    r"obyavlenie\\u002F([a-z0-9\-]+-ID[A-Za-z0-9]+)\.html",
    re.I,
)


def normalize_ad_url(href: str) -> str | None:
    if not href:
        return None
    full = urljoin(BASE_ORIGIN, href)
    parsed = urlparse(full)
    if "/obyavlenie/" not in parsed.path:
        return None
    clean = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    if not ID_IN_URL_RE.search(clean):
        return None
    return clean


def extract_listing_urls(html: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()

    def add(url: str | None) -> None:
        if url and url not in seen:
            seen.add(url)
            found.append(url)

    # 1) DOM-лінки (якщо SSR віддав <a href>)
    soup = BeautifulSoup(html, "lxml")
    for a in soup.select("a[href]"):
        add(normalize_ad_url(a.get("href", "")))

    # 2) Прямі path у HTML
    for m in AD_HREF_RE.finditer(html):
        add(normalize_ad_url(m.group(0)))

    # 3) __PRERENDERED_STATE__ (основний шлях для seller listing)
    for rex in (PRERENDER_AD_RE, PRERENDER_AD_RE_ALT):
        for slug in rex.findall(html):
            add(normalize_ad_url(f"/d/uk/obyavlenie/{slug}.html"))

    return found


def _clean_cat_label(text: str) -> tuple[str, int | None]:
    raw = re.sub(r"\s+", " ", text or "").strip()
    count = None
    m = re.search(r"^(.*?)(?:\s+)(\d+)\s*$", raw)
    if m:
        raw = m.group(1).strip()
        count = int(m.group(2))
    # інколи в одному li зліплені кілька рівнів
    return raw, count


def parse_category_filter_tree(html: str) -> dict[str, Any]:
    """Дерево з сайдбар-фільтра «Категорії» на сторінці продавця."""
    soup = BeautifulSoup(html, "lxml")
    root: dict[str, Any] = {
        "name": "Усі оголошення",
        "count": None,
        "children": [],
        "source": "olx_filter",
    }

    heading = None
    for tag in soup.find_all(["h3", "h4", "h5"]):
        if "Категорії" in tag.get_text(" ", strip=True):
            heading = tag
            break
    if heading is None:
        return root

    container = heading.find_parent(["aside", "nav", "section", "div"]) or heading.parent
    if container is None:
        return root

    # Збираємо всі li з лічильниками біля фільтра
    items: list[tuple[str, int | None, int]] = []
    for li in container.find_all("li"):
        text = li.get_text(" ", strip=True)
        if not text or "оголошен" in text.lower() and "Усі" not in text:
            # пропускаємо сміття, але «Усі оголошення» лишаємо
            pass
        name, count = _clean_cat_label(text)
        if not name:
            continue
        # глибина за вкладеністю ul
        depth = 0
        parent = li.parent
        while parent and parent is not container:
            if getattr(parent, "name", None) == "ul":
                depth += 1
            parent = parent.parent
        # відсікаємо футерні пункти
        low = name.lower()
        if any(
            x in low
            for x in (
                "мобільн",
                "допомога",
                "політика",
                "карта ",
                "olx.",
                "робота",
                "доставка",
                "блог",
                "реклама",
                "умови",
            )
        ):
            continue
        if count is None and name not in ("Усі оголошення", "Дім і сад"):
            # без лічильника — часто не категорія
            if " / " not in name and name not in (
                "Електрика",
                "Елементи кріплення",
                "Оздоблювальні та облицювальні матеріали",
                "Будівництво / ремонт",
            ):
                continue
        items.append((name, count, depth))

    # дедуп зі збереженням порядку, беремо max depth як ієрархію
    # OLX часто рендерить flat list після expand — будуємо за відомим порядком
    flat_names = []
    seen_names: set[str] = set()
    for name, count, depth in items:
        key = name
        if key in seen_names:
            continue
        # ігноруємо зліплені рядки типу "Дім і сад 18 Будівництво..."
        if name.count(" 18") > 0 or len(name) > 80:
            # спробувати розбити відомі сегменти
            continue
        seen_names.add(key)
        flat_names.append({"name": name, "count": count, "depth": depth})

    if not flat_names:
        # fallback: regex по тексту контейнера
        block = container.get_text("\n", strip=True)
        for line in block.splitlines():
            line = line.strip()
            m = re.match(
                r"^(Усі оголошення|Дім і сад|Будівництво / ремонт|"
                r"Електрика|Оздоблювальні та облицювальні матеріали|"
                r"Елементи кріплення)\s+(\d+)\s*$",
                line,
            )
            if m:
                flat_names.append(
                    {"name": m.group(1), "count": int(m.group(2)), "depth": 0}
                )

    # Фіксована ієрархія OLX для цього продавця (підтверджена розвідкою)
    order_map = {
        "Усі оголошення": 0,
        "Дім і сад": 1,
        "Будівництво / ремонт": 2,
        "Електрика": 3,
        "Оздоблювальні та облицювальні матеріали": 3,
        "Елементи кріплення": 3,
    }
    nodes_by_name: dict[str, dict[str, Any]] = {}
    for item in flat_names:
        name = item["name"]
        node = {
            "name": name,
            "slug_hint": _slug_hint(name),
            "count": item.get("count"),
            "children": [],
            "source": "olx_filter",
        }
        nodes_by_name[name] = node

    # якщо немає вузлів — мінімальне дерево з розвідки
    if "Дім і сад" not in nodes_by_name:
        for name, depth in (
            ("Усі оголошення", 0),
            ("Дім і сад", 1),
            ("Будівництво / ремонт", 2),
            ("Електрика", 3),
            ("Оздоблювальні та облицювальні матеріали", 3),
            ("Елементи кріплення", 3),
        ):
            nodes_by_name[name] = {
                "name": name,
                "slug_hint": _slug_hint(name),
                "count": None,
                "children": [],
                "source": "olx_filter_fallback",
            }

    parent_of = {
        "Дім і сад": "Усі оголошення",
        "Будівництво / ремонт": "Дім і сад",
        "Електрика": "Будівництво / ремонт",
        "Оздоблювальні та облицювальні матеріали": "Будівництво / ремонт",
        "Елементи кріплення": "Будівництво / ремонт",
    }

    root_node = nodes_by_name.get("Усі оголошення") or root
    for name, node in nodes_by_name.items():
        if name == "Усі оголошення":
            continue
        parent_name = parent_of.get(name)
        if parent_name and parent_name in nodes_by_name:
            nodes_by_name[parent_name]["children"].append(node)
        elif name in order_map and order_map[name] == 1:
            root_node["children"].append(node)

    return root_node if root_node.get("name") else root


def _slug_hint(name: str) -> str:
    table = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "h",
        "ґ": "g",
        "д": "d",
        "е": "e",
        "є": "ie",
        "ж": "zh",
        "з": "z",
        "и": "y",
        "і": "i",
        "ї": "i",
        "й": "i",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "kh",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "shch",
        "ь": "",
        "ю": "iu",
        "я": "ia",
        "ы": "y",
        "э": "e",
        "ъ": "",
    }
    out = []
    for ch in name.lower().replace("/", " ").replace("'", ""):
        if ch in table:
            out.append(table[ch])
        elif ch.isalnum():
            out.append(ch)
        elif ch in (" ", "-", "_"):
            out.append("-")
    slug = re.sub(r"-+", "-", "".join(out)).strip("-")
    return slug[:160] or "category"


def merge_breadcrumb_into_tree(tree: dict[str, Any], path: list[str]) -> None:
    """Доповнює дерево шляхами з PDP (BFS через картки)."""
    # path: ["Дім і сад", "Будівництво / ремонт", "Електрика"]
    node = tree
    # якщо корінь «Усі оголошення» — діти починаються з L1
    for name in path:
        if not name or name == "Головна":
            continue
        children = node.setdefault("children", [])
        found = None
        for ch in children:
            if ch.get("name") == name:
                found = ch
                break
        if found is None:
            found = {
                "name": name,
                "slug_hint": _slug_hint(name),
                "count": None,
                "children": [],
                "source": "olx_breadcrumb",
            }
            children.append(found)
        node = found


def discover_all_listing_urls(client: OlxClient, *, max_pages: int = 20) -> tuple[list[str], str]:
    """Повертає унікальні URL оголошень + HTML першої сторінки (для дерева)."""
    all_urls: list[str] = []
    seen: set[str] = set()
    first_html = ""
    total_pages = None

    for page in range(1, max_pages + 1):
        url = SELLER_LIST_URL if page == 1 else f"{SELLER_LIST_URL}?page={page}"
        logger.info("Listing page %d: %s", page, url)
        html = client.get_text(url)
        if page == 1:
            first_html = html
            m = re.search(r'totalPages\\":(\d+)', html)
            if m:
                total_pages = int(m.group(1))
            m2 = re.search(r'totalElements\\":(\d+)', html)
            if m2:
                logger.info("totalElements=%s totalPages=%s", m2.group(1), total_pages)

        urls = extract_listing_urls(html)
        new = [u for u in urls if u not in seen]
        if not new:
            break
        for u in new:
            seen.add(u)
            all_urls.append(u)

        if total_pages is not None and page >= total_pages:
            break
        if len(new) == 0:
            break

    return all_urls, first_html

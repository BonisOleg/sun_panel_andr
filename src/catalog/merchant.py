"""Google Merchant Center: бренд, заголовок, custom labels, availability.

Заголовок (ТЗ): [Тип товару] + [Бренд] + [Модель/характеристика], ≤150 символів,
без SEO-переспаму. Пріоритет: Product.feed_title (адмінка) → автогенерація з назви.
Бренд: Product.brand → відомий бренд у назві → назва сайту (власні кріплення Soliron).
"""

from __future__ import annotations

import re
from decimal import Decimal

TITLE_MAX = 150
LOW_TICKET_LIMIT = Decimal("1000")

# custom_label_0 за slug категорії — фолбек, якщо Category.merchant_label порожній
LABEL_BY_CATEGORY_SLUG = {
    "paneli": "Panels",
    "kriplennya": "Zinc_Mounts",
    "bezprofilna-alyuminiyeva-sistema": "Aluminum_System",
    "kabel": "Cables",
}

KNOWN_BRANDS: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"\blongi\b|лонг[іи]", re.I), "Longi"),
    (re.compile(r"\bjinko\b|джинко", re.I), "Jinko"),
    (re.compile(r"\bleapton\b", re.I), "Leapton"),
    (re.compile(r"\bkbe\b", re.I), "KBE"),
    (re.compile(r"\btrina\b", re.I), "Trina"),
    (re.compile(r"\bja\s*solar\b", re.I), "JA Solar"),
    (re.compile(r"\bcanadian\s*solar\b", re.I), "Canadian Solar"),
    (re.compile(r"\brisen\b", re.I), "Risen"),
    (re.compile(r"\bst[aä]ubli\b", re.I), "Staubli"),
)

AVAILABILITY = {
    "in_stock": "in_stock",
    "on_order": "preorder",
    "out_of_stock": "out_of_stock",
    "call": "in_stock",
}


def detect_brand(text: str) -> str:
    for rx, brand in KNOWN_BRANDS:
        if rx.search(text or ""):
            return brand
    return ""


def product_brand(product, default: str = "") -> tuple[str, str]:
    """(brand, source): source ∈ field | name | site."""
    explicit = (getattr(product, "brand", "") or "").strip()
    if explicit:
        return explicit, "field"
    detected = detect_brand(product.name)
    if detected:
        return detected, "name"
    return (default or "").strip(), "site"


def category_label(category) -> str:
    if category is None:
        return ""
    explicit = (getattr(category, "merchant_label", "") or "").strip()
    if explicit:
        return explicit
    return LABEL_BY_CATEGORY_SLUG.get(category.slug, "")


def price_label(price) -> str:
    if price is None:
        return ""
    return "Low_Ticket" if Decimal(price) < LOW_TICKET_LIMIT else "High_Ticket"


def preorder_date() -> str:
    """ISO 8601 дата для g:availability_date (сьогодні + MERCHANT_PREORDER_DAYS, дефолт 14)."""
    from datetime import timedelta

    from django.conf import settings
    from django.utils import timezone

    days = int(getattr(settings, "MERCHANT_PREORDER_DAYS", 14) or 14)
    moment = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    return (moment + timedelta(days=days)).isoformat(timespec="minutes")


def format_price(price) -> str:
    return f"{Decimal(price).quantize(Decimal('0.01'))} UAH"


_WS = re.compile(r"\s+")
_STOP_TAIL = {
    "для", "на", "з", "і", "та", "в", "у", "кріплення", "панелей", "панелі",
    "кронштейн", "сонячна", "сонячних", "панель",
}
_SPAM_CUT = re.compile(r"\s(?:кріплення|кріплень|крепление|крепления)\s+(?:для|на)\b", re.I)
_POWER = re.compile(r"(\d{3,4})\s*(?:w|вт)\b", re.I)
_MODEL = re.compile(
    r"\b(hi-?mo\s*\d+[a-z]?|tiger\s*neo|black\s*frame|full\s*black|bifacial)\b", re.I
)


def _model_fmt(raw: str) -> str:
    text = _WS.sub(" ", raw.strip())
    low = text.lower().replace(" ", "")
    if low.startswith(("hi-mo", "himo")):
        return "Hi-MO" + re.sub(r"^hi-?mo", "", low)
    return " ".join(w.capitalize() for w in text.split())


def _stem(word: str) -> str:
    return re.sub(r"[^\wʼ'’-]", "", word.lower())[:5]


def _dedupe(name: str) -> str:
    """Обрізати назву там, де починається повтор ключових слів (SEO-хвіст)."""
    words = name.split()
    out: list[str] = []
    seen: set[str] = set()
    cut = False
    for idx, word in enumerate(words):
        stem = _stem(word)
        if len(stem) >= 5 and stem in seen and idx >= 2:
            cut = True
            break
        if len(stem) >= 5:
            seen.add(stem)
        out.append(word)
    if cut:
        while len(out) > 1 and out[-1].lower().strip(",.;") in _STOP_TAIL:
            out.pop()
    return " ".join(out)


def _insert_brand(text: str, brand: str) -> str:
    if not brand or re.search(re.escape(brand), text, re.I):
        return text
    words = text.split()
    k = 1
    while k < len(words) and k < 3 and not re.search(r"\d|^(для|на|в|з)$", words[k], re.I):
        k += 1
    return " ".join(words[:k] + [brand] + words[k:])


def auto_title(name: str, brand: str, label: str = "") -> str:
    raw = _WS.sub(" ", (name or "").strip())
    if label == "Panels":
        power = _POWER.search(raw)
        model = _MODEL.search(raw)
        parts = ["Сонячна панель"]
        if brand:
            parts.append(brand)
        if power:
            parts.append(f"{power.group(1)}W")
        if model:
            parts.append(_model_fmt(model.group(1)))
        if len(parts) >= 3:
            return " ".join(parts)[:TITLE_MAX]
    spam = _SPAM_CUT.search(raw)
    if spam and len(raw[: spam.start()].split()) >= 2:
        raw = raw[: spam.start()]
    title = _dedupe(raw)
    if brand:
        without = re.sub(r"\s*\b" + re.escape(brand) + r"\b", "", title, flags=re.I).strip()
        title = _insert_brand(without or title, brand)
    return title[:TITLE_MAX].rstrip()


def feed_title(product, brand: str, label: str) -> tuple[str, str]:
    """(title, source): source ∈ field | auto."""
    explicit = (getattr(product, "feed_title", "") or "").strip()
    if explicit:
        return explicit[:TITLE_MAX], "field"
    return auto_title(product.name, brand, label), "auto"

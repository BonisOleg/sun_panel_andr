"""Cleanup OLX/SEO product text for storefront display."""

from __future__ import annotations

import re

_WS = re.compile(r"\s+")
_RU_LETTER = re.compile(r"[ыэъёЫЭЪЁ]")
_RU_WORD = re.compile(
    r"(?iu)^(?:"
    r"монтажный|монтажного|монтажные|"
    r"профиль|профиля|профилю|"
    r"креплени[еяй]|крепления|"
    r"прижим|прижима|"
    r"солнечн(?:ый|ая|ое|ые|ых|ого|ой)|"
    r"солнеяная|битумной|битумный|битумную|"
    r"алюминиевый|алюминиевая|алюминиевые|"
    r"провод(?:а|у)?|"
    r"пенелей|батарей|батареи|батарея|панели|"
    r"черепицы|черепицу"
    r")$"
)
_RU_PHRASE_START = re.compile(
    r"(?iu)(?<=\s)(?:"
    r"монтажный|профиль|креплени|прижим|"
    r"солнечн|солнеяная|битумн|алюмини|"
    r"провод\b|пенелей|батарей|черепицы"
    r")"
)
_FILLER_LEAD = frozenset({"для", "панелей", "панелі", "та", "і", "й", "на"})
_FILLER_TAIL = frozenset({"для", "та", "і", "й", "на", "або"})
_OLX_FOOTER = re.compile(r"(?is)(?:\n|^)\s*Тип продавця\s*:.*\Z")
_OLX_LINE = re.compile(r"(?im)^\s*(?:Джерело\s+OLX|Тип продавця|Стан)\s*:.*$")
_SPEC_LINE = re.compile(r"^(.{2,48}?)\s*[:\-–—]\s*(.+)$")
_PRICE_ONLY = re.compile(r"(?iu)^(роздріб|опт|дилер|до\s+\d|від\s+\d)\b")


def sanitize_product_name(name: str) -> str:
    """Remove Russian duplicate SEO tails; never hard-truncate length."""
    original = _WS.sub(" ", (name or "").strip())
    if not original:
        return ""

    text = original
    match = _RU_PHRASE_START.search(text)
    if match and match.start() >= 18:
        head = text[: match.start()].rstrip(" ,.-–—")
        first = head.split(" ", 1)[0].strip(".,;:()[]«»\"'") if head else ""
        head_is_ru = bool(
            first and (_RU_LETTER.search(first) or _RU_WORD.fullmatch(first))
        )
        if len(head) >= 18 and not head_is_ru and (
            _RU_LETTER.search(text[match.start() :]) or _RU_WORD.search(text[match.start() :])
        ):
            text = head

    kept: list[str] = []
    for token in text.split(" "):
        bare = token.strip(".,;:()[]«»\"'")
        if not bare:
            continue
        if _RU_LETTER.search(bare) or _RU_WORD.fullmatch(bare):
            continue
        kept.append(token)

    result = _WS.sub(" ", " ".join(kept)).strip(" ,.-–—")
    result = _drop_leading_filler(result)
    result = _dedupe_repeated_tail(result)
    result = _strip_trailing_filler(result)
    result = _ensure_solar_panel_prefix(original, result)
    result = _capitalize(result)

    if not result or len(result) < 12:
        return original
    return result


def _drop_leading_filler(text: str) -> str:
    words = text.split()
    if len(words) < 3:
        return text
    i = 0
    while i < len(words) - 1 and words[i].casefold().strip(".,") in _FILLER_LEAD:
        rest = words[i + 1]
        # Keep dropping while next token looks like a real product word
        if len(rest) >= 3:
            i += 1
            continue
        break
    trimmed = " ".join(words[i:])
    return trimmed if len(trimmed) >= 12 else text


def _strip_trailing_filler(text: str) -> str:
    words = text.split()
    while words and words[-1].casefold().strip(".,") in _FILLER_TAIL:
        words.pop()
    return " ".join(words)


def _ensure_solar_panel_prefix(original: str, result: str) -> str:
    low = result.casefold()
    if low.startswith("панель") and "соняч" not in low:
        if re.search(r"(?iu)сонячн|солнечн", original):
            return "Сонячна " + result
    return result


def _capitalize(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def _dedupe_repeated_tail(text: str) -> str:
    words = text.split()
    n = len(words)
    if n < 4:
        return text
    lowered = [w.casefold() for w in words]
    for size in range(min(n // 2, 6), 1, -1):
        if lowered[-size:] == lowered[-2 * size : -size]:
            return " ".join(words[:-size])
    cleaned: list[str] = []
    prev_pair = None
    i = 0
    while i < n:
        if i + 1 < n:
            pair = (lowered[i], lowered[i + 1])
            if pair == ("сонячна", "панель") and prev_pair == pair:
                i += 2
                continue
            if pair == ("сонячна", "панель"):
                prev_pair = pair
        cleaned.append(words[i])
        i += 1
    return " ".join(cleaned)


def clean_description(text: str) -> str:
    raw = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return ""
    raw = _OLX_FOOTER.sub("", raw)
    raw = _OLX_LINE.sub("", raw)
    lines = [ln.rstrip() for ln in raw.split("\n")]
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines).strip()


def short_description(text: str, *, max_chars: int = 240) -> str:
    cleaned = clean_description(text)
    for para in cleaned.split("\n"):
        para = _WS.sub(" ", para).strip()
        if len(para) < 24:
            continue
        if _PRICE_ONLY.match(para):
            continue
        if len(para) <= max_chars:
            return para
        chunk = para[: max_chars + 1]
        if " " in chunk:
            chunk = chunk.rsplit(" ", 1)[0]
        return chunk.rstrip(".,;:") + "…"
    return ""


def parse_specs(text: str, *, limit: int = 12) -> list[tuple[str, str]]:
    cleaned = clean_description(text)
    specs: list[tuple[str, str]] = []
    seen: set[str] = set()

    for line in cleaned.split("\n"):
        line = _WS.sub(" ", line).strip()
        if not line or len(line) > 140:
            continue
        match = _SPEC_LINE.match(line)
        if not match:
            continue
        label = match.group(1).strip(" .")
        value = match.group(2).strip()
        key = label.casefold()
        if key in seen or key.startswith("джерело") or "olx" in key:
            continue
        if not value:
            continue
        seen.add(key)
        specs.append((label, value))
        if len(specs) >= limit:
            return specs

    if len(specs) < 3:
        for line in cleaned.split("\n"):
            line = _WS.sub(" ", line).strip()
            dim = re.search(
                r"(\d+[.,]?\d*\s*[xх×]\s*\d+[.,]?\d*(?:\s*[xх×]\s*\d+[.,]?\d*)?)",
                line,
                re.I,
            )
            if dim and "розмір" not in seen:
                specs.append(
                    ("Розмір", dim.group(1).replace("х", "×").replace("x", "×"))
                )
                seen.add("розмір")
            mat = re.search(
                r"(?iu)\b(оцинкован\w*|алюміні\w*|анодован\w*|мідн\w*|мідь)\b",
                line,
            )
            if mat and "матеріал" not in seen:
                specs.append(("Матеріал", mat.group(1)))
                seen.add("матеріал")
            if len(specs) >= limit:
                break

    return specs[:limit]

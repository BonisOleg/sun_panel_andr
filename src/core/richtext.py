"""Sanitize HTML з TinyMCE — безпечно для мобільної верстки."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, NavigableString, Tag
from django.utils.html import linebreaks
from django.utils.safestring import mark_safe

ALLOWED_TAGS = frozenset(
    {
        "p",
        "br",
        "strong",
        "b",
        "em",
        "i",
        "u",
        "h2",
        "h3",
        "h4",
        "ul",
        "ol",
        "li",
        "a",
        "blockquote",
        "figure",
        "img",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
    }
)
ALLOWED_ATTRS = {
    "a": frozenset({"href", "title", "rel", "target"}),
    "img": frozenset({"src", "alt", "width", "height"}),
    "td": frozenset({"colspan", "rowspan"}),
    "th": frozenset({"colspan", "rowspan"}),
}
_DROP_TAGS = frozenset({"script", "style", "iframe", "object", "embed", "form", "figcaption"})
_HAS_HTML = re.compile(r"<[a-zA-Z][^>]*>")
_LAZY_ATTR = re.compile(r"\s*loading\s*=\s*[\"']?lazy[\"']?", re.I)


def strip_lazy_and_figcaption(html: str) -> str:
    text = _LAZY_ATTR.sub("", html or "")
    text = re.sub(r"<figcaption\b[^>]*>.*?</figcaption>", "", text, flags=re.I | re.S)
    return text


def sanitize_richtext(html: str) -> str:
    raw = strip_lazy_and_figcaption(html or "").strip()
    if not raw:
        return ""

    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup.find_all(_DROP_TAGS):
        tag.decompose()

    for tag in soup.find_all(True):
        if not isinstance(tag, Tag):
            continue
        name = tag.name.lower()
        if name not in ALLOWED_TAGS:
            tag.unwrap()
            continue
        allowed = ALLOWED_ATTRS.get(name, frozenset())
        for attr in list(tag.attrs):
            if attr not in allowed:
                del tag.attrs[attr]
        if name == "a":
            href = (tag.get("href") or "").strip()
            if href.startswith("javascript:"):
                del tag["href"]
            tag["rel"] = "noopener noreferrer"
        if name == "img":
            src = (tag.get("src") or "").strip()
            if not src or src.startswith("javascript:"):
                tag.decompose()

    parts: list[str] = []
    for child in soup.contents:
        if isinstance(child, NavigableString):
            text = str(child).strip()
            if text:
                parts.append(text)
        else:
            parts.append(str(child))
    return "".join(parts).strip()


def render_richtext(text: str):
    """HTML з TinyMCE → |safe; звичайний текст → linebreaks."""
    raw = (text or "").strip()
    if not raw:
        return ""
    if _HAS_HTML.search(raw):
        return mark_safe(sanitize_richtext(raw))
    return mark_safe(linebreaks(raw))

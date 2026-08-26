"""Inline critical CSS and emit non-blocking stylesheet links."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

_STATIC_ROOT = Path(settings.BASE_DIR) / "static"


@lru_cache(maxsize=64)
def _read_static_css(path: str, mtime_ns: int) -> str:
    del mtime_ns  # cache bust key only
    found = finders.find(path)
    if not found:
        fallback = _STATIC_ROOT / path
        if not fallback.is_file():
            return ""
        found = str(fallback)
    return Path(found).read_text(encoding="utf-8")


def _css_mtime_ns(path: str) -> int:
    found = finders.find(path)
    candidate = Path(found) if found else _STATIC_ROOT / path
    try:
        return candidate.stat().st_mtime_ns
    except OSError:
        return 0


@register.simple_tag
def inline_static_css(*paths: str) -> str:
    """Concatenate and inline static CSS files (for critical CSS)."""
    chunks: list[str] = []
    for path in paths:
        css = _read_static_css(path, _css_mtime_ns(path))
        if css:
            chunks.append(f"/* {path} */\n{css}")
    return mark_safe("\n".join(chunks))


@register.simple_tag(takes_context=True)
def async_css(context, *paths: str) -> str:
    """
    Non-blocking stylesheets: media=print until css-async.js sets media=all.
    Avoids inline onload handlers (blocked by script-src CSP).
    """
    version = context.get("static_version", "")
    parts: list[str] = []
    for path in paths:
        href = static(path)
        if version:
            sep = "&" if "?" in href else "?"
            href = f"{href}{sep}v={version}"
        parts.append(
            format_html(
                '<link rel="stylesheet" href="{}" media="print" data-async-css>'
                '<noscript><link rel="stylesheet" href="{}"></noscript>',
                href,
                href,
            )
        )
    return mark_safe("\n".join(parts))

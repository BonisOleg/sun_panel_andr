"""SEO helpers: canonical base URL + plain-text meta snippets."""

from __future__ import annotations

import re

from django.conf import settings
from django.utils.html import strip_tags


_WS_RE = re.compile(r"\s+")


def public_base_url(request=None) -> str:
    configured = (getattr(settings, "PUBLIC_BASE_URL", "") or "").rstrip("/")
    if configured:
        return configured
    if request is not None:
        return request.build_absolute_uri("/").rstrip("/")
    return ""


def absolute_url(path: str, request=None) -> str:
    path = path or "/"
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = "/" + path
    base = public_base_url(request)
    if base:
        return base + path
    if request is not None:
        return request.build_absolute_uri(path)
    return path


def meta_text(value: str, limit: int = 160) -> str:
    text = _WS_RE.sub(" ", strip_tags(value or "")).strip()
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0]
    return (cut or text[: limit - 1]).rstrip(".,;:") + "…"

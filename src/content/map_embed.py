"""Normalize Google Maps embed paste (iframe HTML or bare src URL)."""

from __future__ import annotations

import re

_IFRAME_SRC_RE = re.compile(
    r"""<iframe[^>]+src=["']([^"']+)["']""",
    re.IGNORECASE | re.DOTALL,
)
_SRC_ONLY_RE = re.compile(
    r"""^https?://(?:www\.)?(?:google\.[a-z.]+/maps|maps\.google\.[a-z.]+)""",
    re.IGNORECASE,
)


def normalize_map_embed(value: str) -> str:
    """Return iframe `src` URL. Accepts full Google «Вставити карту» HTML or URL."""
    raw = (value or "").strip()
    if not raw:
        return ""
    if "<iframe" in raw.lower():
        match = _IFRAME_SRC_RE.search(raw)
        if match:
            return match.group(1).strip()
        return ""
    if raw.startswith(("http://", "https://")):
        return raw
    return raw


def is_plausible_map_src(url: str) -> bool:
    if not url:
        return False
    return bool(_SRC_ONLY_RE.match(url) or "google.com/maps" in url or "maps.google." in url)

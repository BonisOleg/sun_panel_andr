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


def _compact_url(url: str) -> str:
    return re.sub(r"\s+", "", url or "")


def normalize_map_embed(value: str) -> str:
    """Return iframe src. Accepts Google embed HTML or a maps URL, even with line breaks."""
    raw = (value or "").strip()
    if not raw:
        return ""
    if "<iframe" in raw.lower():
        match = _IFRAME_SRC_RE.search(raw)
        url = _compact_url(match.group(1)) if match else ""
    elif raw.lower().startswith(("http://", "https://")):
        url = _compact_url(raw)
    else:
        return ""
    return url if is_plausible_map_src(url) else ""


def is_plausible_map_src(url: str) -> bool:
    if not url:
        return False
    return bool(_SRC_ONLY_RE.match(url) or "google.com/maps" in url or "maps.google." in url)

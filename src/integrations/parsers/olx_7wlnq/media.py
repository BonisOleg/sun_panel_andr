"""Завантаження зображень на диск."""

from __future__ import annotations

import logging
import mimetypes
import re
import time
from pathlib import Path

from .client import OlxClient, OlxHttpError
from .constants import DELAY_IMAGE_SEC, PLACEHOLDER_IMAGE_MARKERS

logger = logging.getLogger(__name__)


def _ext_from_url_or_content(url: str, content_type: str | None, body: bytes) -> str:
    if body[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if body[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if body[:4] == b"RIFF" and body[8:12] == b"WEBP":
        return ".webp"
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if ext:
            return ".jpg" if ext == ".jpe" else ext
    if ".png" in url.lower():
        return ".png"
    if ".webp" in url.lower():
        return ".webp"
    return ".jpg"


def _file_id(url: str) -> str:
    m = re.search(r"/files/([^/]+)/", url)
    if m:
        return re.sub(r"[^\w.-]", "_", m.group(1))[:80]
    return re.sub(r"[^\w.-]", "_", url[-40:])


def download_product_images(
    client: OlxClient,
    *,
    image_urls: list[str],
    dest_dir: Path,
    delay: float = DELAY_IMAGE_SEC,
) -> list[dict]:
    """
    Завантажує фото в dest_dir.
    Повертає [{url, path, filename, ok, error}].
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []
    for idx, url in enumerate(image_urls, start=1):
        if any(m in url.lower() for m in PLACEHOLDER_IMAGE_MARKERS):
            results.append(
                {
                    "url": url,
                    "path": None,
                    "filename": None,
                    "ok": False,
                    "error": "placeholder",
                }
            )
            continue
        # більший превʼю якщо CDN підтримує
        fetch_url = url
        if "apollo.olxcdn.com" in url and ";s=" not in url:
            fetch_url = f"{url};s=1000x700"

        try:
            body = client.get_bytes(fetch_url)
            # get_bytes вже робить delay; додатковий для картинок коротший
            ext = _ext_from_url_or_content(fetch_url, None, body)
            filename = f"{idx:02d}_{_file_id(url)}{ext}"
            path = dest_dir / filename
            path.write_bytes(body)
            results.append(
                {
                    "url": url,
                    "path": str(path),
                    "filename": filename,
                    "ok": True,
                    "error": None,
                    "bytes": len(body),
                }
            )
            time.sleep(delay)
        except (OlxHttpError, OSError) as exc:
            logger.warning("Image download failed %s: %s", url, exc)
            results.append(
                {
                    "url": url,
                    "path": None,
                    "filename": None,
                    "ok": False,
                    "error": str(exc),
                }
            )
    return results

"""Telegram Bot API — outbound admin alerts (one chat_id)."""

from __future__ import annotations

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

TELEGRAM_MAX_LEN = 4096


class TelegramConfigError(Exception):
    pass


class TelegramAPIError(Exception):
    pass


def is_configured() -> bool:
    return bool(
        (getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()
        and (getattr(settings, "TELEGRAM_CHAT_ID", "") or "").strip()
    )


def _chunks(text: str, limit: int = TELEGRAM_MAX_LEN) -> list[str]:
    text = text or ""
    if len(text) <= limit:
        return [text] if text else []
    parts: list[str] = []
    rest = text
    while rest:
        if len(rest) <= limit:
            parts.append(rest)
            break
        cut = rest.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = limit
        parts.append(rest[:cut])
        rest = rest[cut:].lstrip("\n")
    return parts


def send_telegram_message(text: str) -> None:
    """Send plain text to TELEGRAM_CHAT_ID. Raises on config/API failure."""
    token = (getattr(settings, "TELEGRAM_BOT_TOKEN", "") or "").strip()
    chat_id = (getattr(settings, "TELEGRAM_CHAT_ID", "") or "").strip()
    if not token or not chat_id:
        raise TelegramConfigError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID не налаштовано")

    timeout = int(getattr(settings, "TELEGRAM_API_TIMEOUT", 5) or 5)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for part in _chunks(text):
        try:
            resp = requests.post(
                url,
                json={"chat_id": chat_id, "text": part, "disable_web_page_preview": True},
                timeout=timeout,
            )
        except requests.RequestException as exc:
            logger.exception("Telegram network error")
            raise TelegramAPIError("Помилка звʼязку з Telegram") from exc
        try:
            data = resp.json()
        except ValueError as exc:
            raise TelegramAPIError(f"Telegram non-JSON HTTP {resp.status_code}") from exc
        if resp.status_code >= 400 or not data.get("ok"):
            desc = data.get("description") or f"HTTP {resp.status_code}"
            raise TelegramAPIError(str(desc))

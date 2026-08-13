"""HMACAuthorization для Delivery Auto API v4.

Формат заголовка (офіційний приклад):
  HMACAuthorization: amx {public_key}:{timestamp_ms}:{hmac_sha256_hex}

Повідомлення для підпису: ``public_key + timestamp_ms`` (ASCII).
Ключ HMAC: secret_key (ASCII).
Timestamp: мілісекунди від 1970-01-09 UTC (як у sample C#, TotalMilliseconds).
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timezone
from typing import Final

# База з офіційного C#-прикладу Delivery (не Unix epoch 1970-01-01).
_DELIVERY_EPOCH: Final = datetime(1970, 1, 9, tzinfo=timezone.utc)


def delivery_timestamp_ms(now: datetime | None = None) -> str:
    """Мілісекунди від 1970-01-09 UTC як рядок для заголовка."""
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    delta = moment - _DELIVERY_EPOCH
    return str(int(delta.total_seconds() * 1000))


def sign_hmac(public_key: str, secret_key: str, timestamp_ms: str) -> str:
    """HmacSHA256(public_key + timestamp, secret) → lowercase hex."""
    message = f"{public_key}{timestamp_ms}".encode("ascii")
    digest = hmac.new(
        secret_key.encode("ascii"),
        message,
        hashlib.sha256,
    ).hexdigest()
    return digest


def build_hmac_authorization(
    public_key: str,
    secret_key: str,
    *,
    now: datetime | None = None,
) -> str:
    """Повне значення заголовка HMACAuthorization (з префіксом amx)."""
    ts = delivery_timestamp_ms(now)
    signature = sign_hmac(public_key, secret_key, ts)
    return f"amx {public_key}:{ts}:{signature}"


def build_hmac_headers(
    public_key: str,
    secret_key: str,
    *,
    now: datetime | None = None,
) -> dict[str, str]:
    """Заголовки для авторизованих методів (ТТН тощо)."""
    return {
        "HMACAuthorization": build_hmac_authorization(
            public_key,
            secret_key,
            now=now,
        ),
    }

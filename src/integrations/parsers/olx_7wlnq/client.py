"""HTTP-клієнт з retry / backoff (parsing_data_remote_server)."""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from .constants import DELAY_SEC, MAX_RETRIES, REQUEST_TIMEOUT, USER_AGENT

logger = logging.getLogger(__name__)


class OlxHttpError(RuntimeError):
    pass


class OlxClient:
    def __init__(
        self,
        *,
        timeout: int = REQUEST_TIMEOUT,
        max_retries: int = MAX_RETRIES,
        delay: float = DELAY_SEC,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay = delay
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.5",
            }
        )

    def get_text(self, url: str) -> str:
        return self._request(url, binary=False)  # type: ignore[return-value]

    def get_bytes(self, url: str) -> bytes:
        return self._request(url, binary=True)  # type: ignore[return-value]

    def _request(self, url: str, *, binary: bool) -> str | bytes:
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code in (429, 503):
                    wait = self.delay * attempt
                    logger.warning(
                        "HTTP %s on %s (attempt %d/%d), sleep %.1fs",
                        resp.status_code,
                        url,
                        attempt,
                        self.max_retries,
                        wait,
                    )
                    time.sleep(wait)
                    continue
                if 400 <= resp.status_code < 500:
                    raise OlxHttpError(f"HTTP {resp.status_code} for {url}")
                resp.raise_for_status()
                if binary:
                    return resp.content
                text = resp.content.decode(resp.encoding or "utf-8", errors="replace")
                if "\ufffd" in text:
                    logger.warning("Encoding replacements in %s", url)
                time.sleep(self.delay)
                return text
            except OlxHttpError:
                raise
            except (requests.RequestException, OSError) as exc:
                last_exc = exc
                wait = self.delay * attempt
                logger.warning(
                    "Network error on %s (attempt %d/%d): %s",
                    url,
                    attempt,
                    self.max_retries,
                    exc,
                )
                time.sleep(wait)
        raise OlxHttpError(f"Failed to fetch {url} after {self.max_retries} attempts: {last_exc}")

    def close(self) -> None:
        self.session.close()

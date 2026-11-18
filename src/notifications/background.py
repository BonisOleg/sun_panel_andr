"""Фонова відправка сповіщень (Telegram/SMTP) — поза HTTP-запитом.

Причина: Telegram (requests, timeout 5 с) і Resend SMTP (EMAIL_TIMEOUT 8 с на
кожну мережеву операцію) виконувались синхронно у view — користувач чекав
5–12 с. Тепер запит лише ставить задачу після commit, відповідь — одразу.

Надійність: якщо воркер gunicorn перезапуститься до відправки, задачу
підбере `manage.py send_pending_notifications` (cron, кожні 10 хв).
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from django.conf import settings
from django.db import close_old_connections, connection, transaction

logger = logging.getLogger(__name__)

_executor: ThreadPoolExecutor | None = None


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        workers = int(getattr(settings, "NOTIFICATIONS_THREADS", 2) or 2)
        _executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="notify")
    return _executor


def _run(fn: Callable, *args) -> None:
    close_old_connections()
    try:
        fn(*args)
    except Exception:  # noqa: BLE001 — фон ніколи не валить процес
        logger.exception("background notification failed: %s%r", getattr(fn, "__name__", fn), args)
    finally:
        connection.close()


def schedule(fn: Callable, *args) -> None:
    """Запустити fn(*args) після commit поточної транзакції.

    NOTIFICATIONS_ASYNC=False (тести) — виконати синхронно, без потоку.
    """
    if not getattr(settings, "NOTIFICATIONS_ASYNC", True):
        transaction.on_commit(lambda: fn(*args))
        return
    transaction.on_commit(lambda: _get_executor().submit(_run, fn, *args))

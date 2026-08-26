#!/usr/bin/env bash
# Точка входу cron-сервісу (Docker): supercronic щодня о 03:00.
# Повний sync лише за розкладом — без boot-sync (уникаємо NP rate limit при рестартах).
set -euo pipefail

if [[ "${CRON_BOOT_SYNC:-0}" == "1" ]]; then
  echo "==> Initial shipping sync on boot (CRON_BOOT_SYNC=1)"
  /app/deploy/sync_shipping.sh || echo "WARN: initial sync failed (буде повтор о 03:00)"
fi

echo "==> Starting supercronic"
exec /usr/local/bin/supercronic -passthrough-logs /app/deploy/crontab

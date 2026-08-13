#!/usr/bin/env bash
# Точка входу cron-сервісу (Docker): разовий sync при старті + supercronic.
set -euo pipefail

echo "==> Initial shipping sync on boot"
/app/deploy/sync_shipping.sh || echo "WARN: initial sync failed (буде повтор о 03:00)"

echo "==> Starting supercronic"
exec supercronic -passthrough-logs /app/deploy/crontab

#!/usr/bin/env bash
# Щоденний синк довідників доставки (Delivery Auto + Нова Пошта).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
  PY="${VIRTUAL_ENV}/bin/python"
elif [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PY="${ROOT}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
else
  PY="python"
fi

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.production}"
LOG_DIR="${ROOT}/data/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/shipping_sync.log"
STAMP="$(date '+%Y-%m-%dT%H:%M:%S%z')"

{
  echo "===== ${STAMP} shipping sync start ====="
  echo "python: $PY settings: $DJANGO_SETTINGS_MODULE"
  "$PY" manage.py sync_delivery_data --warehouses

  # НП опційний: без NP_API_KEY не валимо весь cron
  set +e
  "$PY" manage.py sync_novaposhta --warehouses
  np_rc=$?
  set -e
  if [[ "$np_rc" -ne 0 ]]; then
    echo "WARN: sync_novaposhta failed (exit ${np_rc}); перевірте NP_API_KEY"
  fi

  echo "===== $(date '+%Y-%m-%dT%H:%M:%S%z') shipping sync done ====="
} >>"$LOG_FILE" 2>&1

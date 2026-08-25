#!/usr/bin/env bash
# Перенос Postgres + media з старого дроплета на новий.
#
# Локально (з доступом до обох SSH host):
#   ./deploy/docker/migrate-from-droplet.sh export   # з soliron (старий)
#   ./deploy/docker/migrate-from-droplet.sh import   # на soliron-prod (новий)
#
# Або на серверах окремо:
#   OLD:  ./deploy/docker/migrate-from-droplet.sh export-local
#   NEW:  ./deploy/docker/migrate-from-droplet.sh import-local
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

OLD_HOST="${OLD_HOST:-soliron}"
NEW_HOST="${NEW_HOST:-soliron-prod}"
REMOTE_ROOT="${REMOTE_ROOT:-/var/www/soliron}"
DATA_DIR="$ROOT/deploy/data"
STAMP="$(date +%Y%m%d-%H%M%S)"
DUMP_SQL="$DATA_DIR/soliron_pg_${STAMP}.sql.gz"
MEDIA_TAR="$DATA_DIR/soliron_media_${STAMP}.tar.gz"
LATEST_SQL="$DATA_DIR/soliron_pg_latest.sql.gz"
LATEST_MEDIA="$DATA_DIR/soliron_media_latest.tar.gz"

compose_cmd() {
  local -a cmd=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)
  if ls /etc/letsencrypt/live/*/fullchain.pem >/dev/null 2>&1; then
    cmd+=(-f docker-compose.ssl.yml)
  fi
  "${cmd[@]}" "$@"
}

ensure_data_dir() {
  mkdir -p "$DATA_DIR"
}

cmd_export_local() {
  ensure_data_dir
  echo "==> pg_dump (db service)"
  compose_cmd exec -T db sh -c \
    'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl' \
    | gzip -c > "$DUMP_SQL"
  ln -sfn "$(basename "$DUMP_SQL")" "$LATEST_SQL"

  echo "==> media volume"
  compose_cmd exec -T web tar -C /app/media -czf - . > "$MEDIA_TAR"
  ln -sfn "$(basename "$MEDIA_TAR")" "$LATEST_MEDIA"

  echo "==> export-local OK"
  ls -lh "$DUMP_SQL" "$MEDIA_TAR"
}

cmd_import_local() {
  local sql="${1:-$LATEST_SQL}"
  local media="${2:-$LATEST_MEDIA}"
  if [ ! -f "$sql" ]; then
    echo "FATAL: missing $sql"
    exit 1
  fi
  if [ ! -f "$media" ]; then
    echo "FATAL: missing $media"
    exit 1
  fi

  echo "==> wait db"
  local i=0
  while [ "$i" -lt 40 ]; do
    if compose_cmd exec -T db pg_isready -U "${POSTGRES_USER:-soliron}" >/dev/null 2>&1; then
      break
    fi
    i=$((i + 1))
    sleep 2
  done

  echo "==> restore Postgres (DROP SCHEMA public cascade)"
  compose_cmd exec -T db sh -c \
    'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO \"$POSTGRES_USER\"; GRANT ALL ON SCHEMA public TO public;"'
  gunzip -c "$sql" | compose_cmd exec -T db sh -c \
    'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1'

  echo "==> media → volume"
  compose_cmd exec -T web mkdir -p /app/media
  compose_cmd cp "$media" web:/tmp/media_migrate.tar.gz
  compose_cmd exec -T web sh -c 'rm -rf /app/media/*; tar -xzf /tmp/media_migrate.tar.gz -C /app/media; rm -f /tmp/media_migrate.tar.gz'

  echo "==> migrate + collectstatic"
  compose_cmd exec -T web python manage.py migrate --noinput
  compose_cmd exec -T web python manage.py collectstatic --noinput

  echo "==> import-local OK"
}

cmd_export() {
  ensure_data_dir
  echo "==> remote export on $OLD_HOST"
  ssh "$OLD_HOST" "cd '$REMOTE_ROOT' && bash ./deploy/docker/migrate-from-droplet.sh export-local"
  echo "==> scp dumps"
  scp "$OLD_HOST:$REMOTE_ROOT/deploy/data/soliron_pg_latest.sql.gz" "$LATEST_SQL"
  scp "$OLD_HOST:$REMOTE_ROOT/deploy/data/soliron_media_latest.tar.gz" "$LATEST_MEDIA"
  ls -lh "$LATEST_SQL" "$LATEST_MEDIA"
}

cmd_import() {
  if [ ! -f "$LATEST_SQL" ] || [ ! -f "$LATEST_MEDIA" ]; then
    echo "FATAL: run export first (missing latest dumps in $DATA_DIR)"
    exit 1
  fi
  echo "==> push dumps to $NEW_HOST"
  ssh "$NEW_HOST" "mkdir -p '$REMOTE_ROOT/deploy/data'"
  scp "$LATEST_SQL" "$NEW_HOST:$REMOTE_ROOT/deploy/data/soliron_pg_latest.sql.gz"
  scp "$LATEST_MEDIA" "$NEW_HOST:$REMOTE_ROOT/deploy/data/soliron_media_latest.tar.gz"
  echo "==> remote import"
  ssh "$NEW_HOST" "cd '$REMOTE_ROOT' && bash ./deploy/docker/migrate-from-droplet.sh import-local"
}

usage() {
  cat <<EOF
Usage:
  $0 export-local | import-local [sql.gz] [media.tar.gz]
  $0 export | import

Env:
  OLD_HOST=soliron NEW_HOST=soliron-prod REMOTE_ROOT=/var/www/soliron
EOF
  exit 1
}

case "${1:-}" in
  export-local) cmd_export_local ;;
  import-local) cmd_import_local "${2:-}" "${3:-}" ;;
  export) cmd_export ;;
  import) cmd_import ;;
  *) usage ;;
esac

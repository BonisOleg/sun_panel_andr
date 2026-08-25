# Production: soliron.com.ua → 68.183.212.53

Перенос з тестового дроплета `134.209.237.106` (SSH host `soliron`) на прод `68.183.212.53` (SSH host `soliron-prod`).

## 0. Локальний SSH

У `~/.ssh/config` має бути:

```
Host soliron
  HostName 134.209.237.106
  User root
  IdentityFile ~/.ssh/id_soliron_do
  IdentitiesOnly yes

Host soliron-prod
  HostName 68.183.212.53
  User root
  IdentityFile ~/.ssh/id_soliron_do
  IdentitiesOnly yes
```

Публічний ключ на новий сервер:

```bash
ssh-copy-id -i ~/.ssh/id_soliron_do.pub root@68.183.212.53
# або вручну: cat ~/.ssh/id_soliron_do.pub → /root/.ssh/authorized_keys
```

Перевірка: `ssh soliron-prod 'uname -a'`.

## 1. Перший деплой на новий сервер (HTTP по IP)

```bash
ssh soliron-prod
apt-get update && apt-get install -y git curl
bash -c "$(curl -fsSL https://get.docker.com)"   # або: bash deploy/docker/install-docker.sh після clone
mkdir -p /var/www && cd /var/www
git clone <REPO_URL> soliron
cd /var/www/soliron

cp .env.docker.example .env
nano .env   # SECRET_KEY, POSTGRES_PASSWORD, DATABASE_URL, NP_API_KEY, …

# DATABASE_URL приклад:
# DATABASE_URL=postgres://soliron:PASSWORD@db:5432/soliron

bash deploy/docker/deploy.sh
curl -sf http://127.0.0.1/healthz/
curl -sf http://68.183.212.53/healthz/
```

## 2. Перенос БД + media зі старого дроплета

З машини, де є обидва SSH-хости:

```bash
# потрібен актуальний код зі скриптом на ОБОХ серверах
./deploy/docker/migrate-from-droplet.sh export   # OLD: soliron
./deploy/docker/migrate-from-droplet.sh import   # NEW: soliron-prod
```

Або вручну на серверах:

```bash
# OLD
ssh soliron
cd /var/www/soliron
bash ./deploy/docker/migrate-from-droplet.sh export-local

# локально
scp soliron:/var/www/soliron/deploy/data/soliron_pg_latest.sql.gz ./
scp soliron:/var/www/soliron/deploy/data/soliron_media_latest.tar.gz ./
scp soliron_pg_latest.sql.gz soliron_media_latest.tar.gz soliron-prod:/var/www/soliron/deploy/data/

# NEW
ssh soliron-prod
cd /var/www/soliron
bash ./deploy/docker/migrate-from-droplet.sh import-local
```

Після імпорту: `curl -sI http://68.183.212.53/ | head` і перевірка адмінки/каталогу/картинок.

## 3. DNS (коли готові)

A-записи:

| Host | Value |
|------|--------|
| `@` / `soliron.com.ua` | `68.183.212.53` |
| `www` | `68.183.212.53` (або CNAME → `@`) |

Після пропагації в `.env` на проді:

```
PUBLIC_BASE_URL=http://soliron.com.ua
CSRF_TRUSTED_ORIGINS=http://68.183.212.53,http://soliron.com.ua,http://www.soliron.com.ua
```

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d web cron
```

## 4. SSL (пізніше)

1. DNS уже на новий IP.
2. Certbot (на хості, не в контейнері) для `soliron.com.ua` + `www`.
3. У `.env`: `PUBLIC_BASE_URL=https://soliron.com.ua`, cookie/SSL flags `True`, CSRF з `https://…`.
4. `docker compose … -f docker-compose.ssl.yml up -d` (підхопить `deploy/nginx/docker.prod.conf`).

## 5. SEO checklist після деплою

- [ ] `/robots.txt` — абсолютний `Sitemap: http(s)://…/sitemap.xml`
- [ ] `/sitemap.xml` — URL з правильним Host
- [ ] Головна / товар / блог — `meta description`, `og:*`, `canonical`
- [ ] Кошик / checkout — `noindex`
- [ ] Після HTTPS оновити `PUBLIC_BASE_URL`

## 6. Оновлення коду надалі

```bash
ssh soliron-prod
cd /var/www/soliron
git pull
bash deploy/docker/deploy.sh
```

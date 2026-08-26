FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

ARG TARGETARCH=amd64
ARG SUPERCRONIC_VERSION=v0.2.36

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl ca-certificates \
    && ARCH="${TARGETARCH}" \
    && case "${ARCH}" in \
         amd64|x86_64) SC_ARCH=amd64 ;; \
         arm64|aarch64) SC_ARCH=arm64 ;; \
         *) SC_ARCH=amd64 ;; \
       esac \
    && curl -fsSL \
      "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-${SC_ARCH}" \
      -o /usr/local/bin/supercronic \
    && chmod +x /usr/local/bin/supercronic \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN chmod +x deploy/entrypoint.sh deploy/sync_shipping.sh deploy/run_cron.sh

EXPOSE 8000

ENTRYPOINT ["deploy/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]

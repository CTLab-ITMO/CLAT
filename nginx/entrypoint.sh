#!/bin/sh
# Генерирует самоподписанный сертификат при первом запуске (чтобы nginx мог
# стартовать и работать по https до того, как будут положены настоящие серты),
# затем запускает nginx.
set -e

DOMAIN="${DOMAIN:-<domen_name>}"
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"

if [ ! -f "${CERT_DIR}/fullchain.pem" ]; then
    echo "[entrypoint] Certificate for ${DOMAIN} not found, installing openssl..."
    apk add --no-cache openssl >/dev/null 2>&1
    echo "[entrypoint] Generating temporary self-signed certificate..."
    mkdir -p "${CERT_DIR}"
    openssl req -x509 -nodes -newkey rsa:2048 -days 3650 \
        -keyout "${CERT_DIR}/privkey.pem" \
        -out "${CERT_DIR}/fullchain.pem" \
        -subj "/CN=${DOMAIN}"
fi

# Фоновый reload раз в сутки — чтобы nginx подхватывал обновлённые сертификаты
( while true; do sleep 86400; nginx -s reload; done ) &

exec nginx -g "daemon off;"
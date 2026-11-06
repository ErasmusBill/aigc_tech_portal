#!/bin/sh
set -eu

echo "==> Running database migrations..."
python manage.py migrate --noinput

echo "==> Bootstrapping platform system of record and initial admin..."
python manage.py bootstrap_platform

echo "==> Collecting static assets for WhiteNoise..."
python manage.py collectstatic --noinput || true

echo "==> Starting production ASGI application server (Uvicorn)..."
exec uvicorn t4f_backend.asgi:application \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers "${WEB_WORKERS:-4}" \
    --proxy-headers \
    --forwarded-allow-ips='*' \
    --timeout-keep-alive 65 \
    --access-log

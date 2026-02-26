#!/bin/sh
set -e

echo "==> migrate..."
python manage.py migrate --noinput

echo "==> rasmlarni kichraytirish..."
python manage.py compress_images

echo "==> gunicorn ishga tushmoqda..."
exec gunicorn --bind 0.0.0.0:8000 --workers 3 config.wsgi:application

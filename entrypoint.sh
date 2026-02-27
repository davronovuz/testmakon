#!/bin/sh

echo "==> postgres tayyor bo'lguncha kutilmoqda..."
until python manage.py showmigrations --list > /dev/null 2>&1; do
  echo "  DB tayyor emas, 2 soniya kutamiz..."
  sleep 2
done

echo "==> migrate..."
python manage.py migrate --noinput

echo "==> rasmlarni kichraytirish..."
python manage.py compress_images || echo "  compress_images xato berdi, davom etilmoqda..."

echo "==> staticfiles..."
python manage.py collectstatic --noinput || echo "  collectstatic xato, davom etilmoqda..."

echo "==> daphne (ASGI + WebSocket) ishga tushmoqda..."
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application

#!/bin/sh
set -e

echo "⏳ Waiting for PostgreSQL..."
python manage.py wait_for_db

echo "📦 Applying migrations..."
python manage.py migrate --noinput

echo "🧹 Collecting static files..."
python manage.py collectstatic --noinput

echo "🚀 Starting application..."
exec "$@"

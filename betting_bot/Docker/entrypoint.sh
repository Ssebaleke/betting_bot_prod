#!/bin/bash

echo "🚀 Starting Django betting bot..."

cd /app/betting_bot

# Wait for database
if [ -f "wait_for_db.py" ]; then
    python manage.py wait_for_db
fi

# Django setup
python manage.py migrate
python manage.py collectstatic --noinput

# CORRECT nested WSGI path
exec gunicorn betting_bot.betting_bot.wsgi:application --bind 0.0.0.0:8000
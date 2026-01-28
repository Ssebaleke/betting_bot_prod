FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# This is the "magic" line that fixes the ModuleNotFoundError
ENV PYTHONPATH=/app/betting_bot

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

# Gunicorn now looks for wsgi.py inside the betting_bot folder
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "betting_bot.wsgi:application"]
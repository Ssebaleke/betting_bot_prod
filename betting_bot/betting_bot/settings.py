"""
Django settings for betting_bot project.
Docker-friendly settings.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# This file is: betting_bot/betting_bot/settings.py
# So BASE_DIR becomes: /app/betting_bot
BASE_DIR = Path(__file__).resolve().parent.parent


# =========================
# SECURITY
# =========================

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-change-this-in-production")

DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")


# =========================
# APPLICATIONS
# =========================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Local apps (docker-safe)
    "betting_bot.accounts",
    "betting_bot.packages",
    "betting_bot.subscription",
    "betting_bot.payments",
    "betting_bot.odds",
    "betting_bot.bots",
    "betting_bot.configs",
    "betting_bot.predictions",
    "betting_bot.api",

]


# =========================
# MIDDLEWARE
# =========================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =========================
# URLS & WSGI  ✅ FIXED
# =========================

ROOT_URLCONF = "betting_bot.betting_bot.urls"
WSGI_APPLICATION = "betting_bot.betting_bot.wsgi.application"


# =========================
# TEMPLATES
# =========================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# =========================
# DATABASE
# - If DATABASE_URL exists -> use Postgres (docker db service)
# - Otherwise -> fallback to SQLite
# =========================

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL:
    # expected: postgres://user:pass@host:port/dbname
    # Example for your docker-compose:
    # postgres://betbot:betbot@db:5432/betbot
    from urllib.parse import urlparse

    u = urlparse(DATABASE_URL)

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": u.path.lstrip("/"),
            "USER": u.username,
            "PASSWORD": u.password,
            "HOST": u.hostname,
            "PORT": u.port or 5432,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# =========================
# PASSWORD VALIDATION
# =========================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# =========================
# INTERNATIONALIZATION
# =========================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Kampala"
USE_I18N = True
USE_TZ = True


# =========================
# STATIC FILES
# =========================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"


# =========================
# DEFAULT PRIMARY KEY
# =========================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

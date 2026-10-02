import os
import sys
from datetime import timedelta
from pathlib import Path

import environ

if sys.platform == "darwin" and not os.environ.get("DYLD_FALLBACK_LIBRARY_PATH"):
    # `uv run`'s own hardened-runtime signature makes macOS strip DYLD_* env vars from its
    # children (astral-sh/uv#7764, closed as not planned), so WeasyPrint can't dlopen() its
    # Homebrew-installed native libs. dyld re-reads this var on every dlopen() call, not just
    # at process launch, so setting it here (before WeasyPrint is imported anywhere) is enough.
    os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = "/opt/homebrew/lib:/usr/local/lib"

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(str(BASE_DIR / ".env"))

SECRET_KEY = env("DJANGO_SECRET_KEY", default="change-me-in-production")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Bascules d'instance (désactivées par défaut) : la collation dans l'agenda hebdomadaire et les
# alertes de carence nutritionnelle, toutes deux jugées pas assez mûres/voulues pour être actives
# sans que l'administrateur de l'instance ne les active explicitement.
PLANNING_SNACK_ENABLED = env.bool("PLANNING_SNACK_ENABLED", default=False)
NUTRITION_ALERTS_ENABLED = env.bool("NUTRITION_ALERTS_ENABLED", default=False)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "corsheaders",
    "apps.accounts",
    "apps.ingredients",
    "apps.recipes",
    "apps.nutrition",
    "apps.planning",
    "apps.shopping",
    "apps.importer",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://postgres:postgres@localhost:5432/cocotte"),
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticatedOrReadOnly",),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_RATES": {
        "comment_create": "10/hour",
        "rating_create": "30/hour",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # Sert de repère d'activité à la purge des comptes inactifs (RGPD, durée de conservation).
    "UPDATE_LAST_LOGIN": True,
}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"])

# En dev par défaut, les emails (dont les liens de réinitialisation de mot de passe)
# s'affichent dans la console au lieu d'être vraiment envoyés.
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Cocotte <noreply@cocotte.app>")

# Sert à construire le lien de réinitialisation de mot de passe envoyé par email
# (le frontend et l'API vivent sur des origines différentes en dev).
FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:5173")

# RGPD : informations affichées sur les pages « Mentions légales » et « Confidentialité »
# (GET /api/auth/legal/). À renseigner par l'administrateur de l'instance.
PRIVACY_POLICY_VERSION = env("PRIVACY_POLICY_VERSION", default="1")
LEGAL_PUBLISHER_NAME = env("LEGAL_PUBLISHER_NAME", default="")
LEGAL_PUBLISHER_ADDRESS = env("LEGAL_PUBLISHER_ADDRESS", default="")
LEGAL_CONTACT_EMAIL = env("LEGAL_CONTACT_EMAIL", default="")
LEGAL_HOST_NAME = env("LEGAL_HOST_NAME", default="")
LEGAL_HOST_ADDRESS = env("LEGAL_HOST_ADDRESS", default="")
# Contact pour exercer ses droits (ou DPO) ; repli sur LEGAL_CONTACT_EMAIL.
PRIVACY_CONTACT_EMAIL = env("PRIVACY_CONTACT_EMAIL", default="") or LEGAL_CONTACT_EMAIL

# Suppression des comptes sans connexion depuis N jours (0 = désactivée), précédée d'un e-mail
# de préavis N_WARNING jours avant. Appliquée par `manage.py purge_inactive_users`.
INACTIVE_ACCOUNT_RETENTION_DAYS = env.int("INACTIVE_ACCOUNT_RETENTION_DAYS", default=730)
INACTIVE_ACCOUNT_WARNING_DAYS = env.int("INACTIVE_ACCOUNT_WARNING_DAYS", default=30)

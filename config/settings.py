"""Django settings for the News 4 U project."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Secure defaults can be overridden explicitly for production deployments.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "development-only-change-this-key-before-deployment",
)
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"
SECURE_SSL_REDIRECT = (
    (os.environ.get("SECURE_SSL_REDIRECT") or str(not DEBUG)).lower()
    == "true"
)
SESSION_COOKIE_SECURE = (
    (os.environ.get("SESSION_COOKIE_SECURE") or str(not DEBUG)).lower()
    == "true"
)
CSRF_COOKIE_SECURE = (
    (os.environ.get("CSRF_COOKIE_SECURE") or str(not DEBUG)).lower()
    == "true"
)
SECURE_HSTS_SECONDS = int(
    os.environ.get("SECURE_HSTS_SECONDS")
    or ("31536000" if not DEBUG else "0")
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    (
        os.environ.get("SECURE_HSTS_INCLUDE_SUBDOMAINS")
        or str(not DEBUG)
    ).lower()
    == "true"
)
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost",
    ).split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "accounts.apps.AccountsConfig",
    "publications.apps.PublicationsConfig",
    "articles.apps.ArticlesConfig",
]

MIDDLEWARE = [
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database selection: SQLite keeps a fresh checkout runnable; set
# DB_ENGINE=mysql for MariaDB.
if os.environ.get("DB_ENGINE", "sqlite").lower() == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "news_application"),
            "USER": os.environ.get("DB_USER", "news_app"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.environ.get(
                "SQLITE_NAME",
                BASE_DIR / "db.sqlite3",
            ),
        }
    }

AUTH_USER_MODEL = "accounts.User"
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"

# Email defaults to the console backend locally so approval
# notifications are still visible during development.
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "news@example.com",
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = (
    os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"
)
EMAIL_USE_SSL = (
    os.environ.get("EMAIL_USE_SSL", "false").lower() == "true"
)
if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ValueError(
        "Configure either EMAIL_USE_TLS or EMAIL_USE_SSL, not both."
    )

# The approval logger may use a dedicated shared key; development
# falls back to the project secret when one is not supplied.
INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY", SECRET_KEY)
APPROVED_ARTICLES_API_URL = os.environ.get(
    "APPROVED_ARTICLES_API_URL",
    "http://127.0.0.1:8000/api/approved/",
)
APPROVED_API_TIMEOUT = float(
    os.environ.get("APPROVED_API_TIMEOUT", "5")
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),
    "PAGE_SIZE": 20,
}

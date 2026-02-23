# config/settings.py
from __future__ import annotations

import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

# ==========================
# BASE / ENV
# ==========================
BASE_DIR = Path(__file__).resolve().parent.parent

RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
IS_RENDER = bool(RENDER_HOST)

SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise Exception("SECRET_KEY (or DJANGO_SECRET_KEY) environment variable not set")


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


DEBUG = env_bool("DEBUG", default=False)

# ==========================
# HOSTS / CSRF / SITE URL
# ==========================
DEFAULT_ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
    "172.31.254.31",
    "career.oxu.uz",
    "www.career.oxu.uz",
]

extra_hosts = os.getenv("ALLOWED_HOSTS", "").strip()
if extra_hosts:
    DEFAULT_ALLOWED_HOSTS += [h.strip() for h in extra_hosts.split(",") if h.strip()]

ALLOWED_HOSTS = list(dict.fromkeys(DEFAULT_ALLOWED_HOSTS))

DEFAULT_CSRF_TRUSTED = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000",
    "https://career.oxu.uz",
    "https://www.career.oxu.uz",
]

CSRF_TRUSTED_ORIGINS = ["https://career.oxu.uz"]


if DEBUG:
    SITE_URL = "http://localhost:8000"
elif IS_RENDER:
    SITE_URL = f"https://{RENDER_HOST}"
else:
    SITE_URL = "https://career.oxu.uz"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# ==========================
# APPLICATIONS
# ==========================
INSTALLED_APPS = [
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # OAuth provider
    "oauth2_provider",

    # Third-party apps
    "corsheaders",
    "jazzmin",
    "widget_tweaks",
    "modeltranslation",
    "phonenumber_field",
    "django_countries",
    "django_ckeditor_5",
    "rest_framework",
    "rest_framework_simplejwt",
    "explorer",

    # Local apps
    "accounts",
    "core",
    "alumni",
    "resources",
    "events",
    "employers",
    "cvbuilder",
    "jobs",
]

AUTH_USER_MODEL = "accounts.CustomUser"

# ==========================
# MIDDLEWARE
# ==========================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",

    "accounts.middleware.NotificationMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "accounts.middleware.BruteForceProtectionMiddleware",

    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# ==========================
# TEMPLATES
# ==========================
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
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.i18n",

                # Custom context processors
                "core.context_processors.site_info",
                "accounts.context_processors.auth_context",
                "jobs.context_processors.jobs_context",
                "events.context_processors.events_context",
                "resources.context_processors.resources_context",
                "employers.context_processors.employers_context",
            ],
            "debug": DEBUG,
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ==========================
# DATABASE
# ==========================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "mydb"),
        "USER": os.getenv("DB_USER", "myuser"),
        "PASSWORD": os.getenv("DB_PASSWORD", "password"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

# ==========================
# PASSWORD VALIDATION
# ==========================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==========================
# INTERNATIONALIZATION
# ==========================
LANGUAGES = [
    ("en", "English"),
    ("ru", "Русский"),
    ("uz", "Oʻzbekcha"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]
LANGUAGE_CODE = "en"

TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_L10N = True
USE_TZ = True

MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_LANGUAGES = ("uz", "ru", "en")
PHONENUMBER_DEFAULT_REGION = "UZ"

# ==========================
# CKEDITOR 5
# ==========================
CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading",
            "bold",
            "italic",
            "underline",
            "strikethrough",
            "bulletedList",
            "numberedList",
            "blockQuote",
            "imageUpload",
            "link",
            "undo",
            "redo",
        ],
        "language": "ru",
        "height": "300px",
        "width": "100%",
    },
    "extends": {
        "blockToolbar": [
            "paragraph",
            "heading1",
            "heading2",
            "heading3",
            "bulletedList",
            "numberedList",
            "blockQuote",
        ],
        "toolbar": [
            "heading",
            "outdent",
            "indent",
            "bold",
            "italic",
            "link",
            "underline",
            "strikethrough",
            "code",
            "subscript",
            "superscript",
            "highlight",
            "codeBlock",
            "sourceEditing",
            "insertImage",
            "bulletedList",
            "numberedList",
            "todoList",
            "blockQuote",
            "imageUpload",
            "fontSize",
            "fontFamily",
            "fontColor",
            "fontBackgroundColor",
            "alignment",
            "horizontalLine",
            "removeFormat",
            "undo",
            "redo",
        ],
        "image": {
            "toolbar": [
                "imageTextAlternative",
                "imageStyle:alignLeft",
                "imageStyle:alignRight",
                "imageStyle:alignCenter",
                "imageStyle:side",
                "toggleImageCaption",
                "imageResize",
            ],
            "styles": ["full", "side", "alignLeft", "alignRight", "alignCenter"],
        },
        "table": {
            "contentToolbar": [
                "tableColumn",
                "tableRow",
                "mergeTableCells",
                "tableProperties",
                "tableCellProperties",
            ],
        },
        "heading": {
            "options": [
                {"model": "paragraph", "title": "Paragraph", "class": "ck-heading_paragraph"},
                {"model": "heading1", "view": "h1", "title": "Heading 1", "class": "ck-heading_heading1"},
                {"model": "heading2", "view": "h2", "title": "Heading 2", "class": "ck-heading_heading2"},
                {"model": "heading3", "view": "h3", "title": "Heading 3", "class": "ck-heading_heading3"},
            ],
        },
        "language": "ru",
    },
}

CKEDITOR_5_UPLOAD_PATH = "uploads/"
CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"
CKEDITOR_5_ALLOW_ALL_FILE_TYPES = False
CKEDITOR_5_UPLOAD_FILE_TYPES = ["jpeg", "jpg", "png", "gif", "bmp", "webp", "svg"]

# ==========================
# STATIC / MEDIA
# ==========================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==========================
# AUTH BACKENDS
# ==========================
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "accounts.backends.EmailBackend",
    "accounts.backends.OAuthBackend",
]

# ==========================
# DRF / JWT
# ==========================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=60),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
    "TOKEN_OBTAIN_SERIALIZER": "accounts.serializers.CustomTokenObtainPairSerializer",
}

# ==========================
# CORS
# ==========================
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "https://career.oxu.uz",
    "https://www.career.oxu.uz",
]

# ==========================
# CACHE
# ==========================
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake-prod" if not DEBUG else "unique-snowflake-dev",
    }
}

BRUTEFORCE_CONFIG = {
    "MAX_ATTEMPTS": 10,
    "BLOCK_TIME": 900,
    "ATTEMPTS_TTL": 300,
    "WARNING_THRESHOLD": 5,
}

# ==========================
# EXPLORER
# ==========================
EXPLORER_CONNECTIONS = {"Default": "default"}
EXPLORER_DEFAULT_CONNECTION = "default"
EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES = ("auth_", "django_")

# ==========================
# OAUTH (custom integration)
# ==========================
OAUTH_PROVIDER_NAME = "oxu"
OAUTH_AUTHORIZE_URL = "https://digital.oxu.uz/oauth2/authorize.asp"
OAUTH_TOKEN_URL = "https://digital.oxu.uz/oauth2/token.asp"
OAUTH_USERINFO_URL = "https://digital.oxu.uz/oauth2/userinfo.asp"
OAUTH_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID")
OAUTH_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET")
OAUTH_REDIRECT_URI = "https://career.oxu.uz/oauth/callback/"
OAUTH_SCOPE = "openid profile email phone"
OAUTH_SUCCESS_REDIRECT = "/"

OAUTH2_PROVIDER_NAME = OAUTH_PROVIDER_NAME
OAUTH2_CLIENT_ID = OAUTH_CLIENT_ID
OAUTH2_CLIENT_SECRET = OAUTH_CLIENT_SECRET
OAUTH2_BASE_URL = "https://digital.oxu.uz/oauth2"
OAUTH2_AUTHORIZE_URL = OAUTH_AUTHORIZE_URL
OAUTH2_TOKEN_URL = OAUTH_TOKEN_URL
OAUTH2_USERINFO_URL = OAUTH_USERINFO_URL
OAUTH2_SCOPE = OAUTH_SCOPE
OAUTH2_REDIRECT_URI = OAUTH_REDIRECT_URI

OAUTH_MICROSERVICE_URL = os.environ.get("OAUTH_MICROSERVICE_URL", "https://oauth-microservice.local")
OAUTH_SERVICE_TOKEN = os.environ.get("OAUTH_SERVICE_TOKEN", "")
OAUTH_ALLOWED_UNIVERSITIES = [
    u.strip() for u in os.environ.get("OAUTH_ALLOWED_UNIVERSITIES", "MyUniversity").split(",")
    if u.strip()
]

# ==========================
# SECURITY
# ==========================
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", default=False)

SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0") or "0")
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", default=False)

SESSION_COOKIE_AGE = 86400
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

OAUTH_STATE_TTL = int(os.getenv("OAUTH_STATE_TTL", "600"))
OAUTH_STUDENT_SESSION_AGE = int(
    os.getenv("OAUTH_STUDENT_SESSION_AGE", str(SESSION_COOKIE_AGE))
)
OAUTH_SET_TOKEN_COOKIES = env_bool("OAUTH_SET_TOKEN_COOKIES", default=True)
OAUTH_ACCESS_COOKIE_NAME = os.getenv("OAUTH_ACCESS_COOKIE_NAME", "student_access")
OAUTH_REFRESH_COOKIE_NAME = os.getenv("OAUTH_REFRESH_COOKIE_NAME", "student_refresh")

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

# ==========================
# EMAIL
# ==========================
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@oxu.uz"

# ==========================
# JAZZMIN
# ==========================
JAZZMIN_SETTINGS = {
    "site_title": "OXU University Admin",
    "site_header": "OXU University",
    "site_brand": "OXU University",
    "welcome_sign": "Welcome to OXU University Admin Panel",
    "copyright": "OXU University",
    "search_model": ["auth.User", "alumni.Alumni"],
    "user_avatar": None,
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Site", "url": "/", "new_window": True},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    "order_with_respect_to": ["accounts", "alumni", "jobs", "events", "resources", "auth"],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "accounts.CustomUser": "fas fa-user",
        "accounts.UserProfile": "fas fa-id-card",
        "alumni.Alumni": "fas fa-graduation-cap",
        "alumni.Company": "fas fa-building",
        "jobs.Job": "fas fa-briefcase",
        "events.Event": "fas fa-calendar-alt",
        "resources.Resource": "fas fa-book",
        "cvbuilder.CV": "fas fa-file-alt",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

# ==========================
# LOGGING
# ==========================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {"format": "{levelname} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
        "file": {
            "class": "logging.FileHandler",
            "filename": str(BASE_DIR / "logs/django.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": True,
        },
        "accounts": {
            "handlers": ["console", "file"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
    },
}

try:
    (BASE_DIR / "logs").mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Could not create logs directory: {e}")

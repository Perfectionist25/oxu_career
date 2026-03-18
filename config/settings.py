
from __future__ import annotations

import os
import importlib.util
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()




BASE_DIR = Path(__file__).resolve().parent.parent

RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
IS_RENDER = bool(RENDER_HOST)

def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_list(name: str) -> list[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def host_to_csrf_origins(host: str, port: str) -> list[str]:
    clean_host = host.strip().lstrip(".")
    if not clean_host or clean_host == "*":
        return []
    return unique(
        [
            f"http://{clean_host}",
            f"http://{clean_host}:{port}",
            f"https://{clean_host}",
            f"https://{clean_host}:{port}",
        ]
    )


DEBUG = env_bool("DEBUG", default=not IS_RENDER)

SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-local-dev-key-change-me"
    else:
        raise Exception("SECRET_KEY (or DJANGO_SECRET_KEY) environment variable not set")


# HOSTS / CSRF / SITE URL

DEFAULT_ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "0.0.0.0",
    "172.31.254.31",
    "career.oxu.uz",
    "www.career.oxu.uz",
]

RUNSERVER_PORT = os.getenv("RUNSERVER_PORT", "8000").strip() or "8000"
extra_allowed_hosts = env_list("ALLOWED_HOSTS")
if "*" in extra_allowed_hosts:
    ALLOWED_HOSTS = ["*"]
else:
    ALLOWED_HOSTS = unique(DEFAULT_ALLOWED_HOSTS + extra_allowed_hosts)

DEFAULT_CSRF_TRUSTED = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000",
    "https://career.oxu.uz",
    "https://www.career.oxu.uz",
]

derived_csrf_origins: list[str] = []
for allowed_host in ALLOWED_HOSTS:
    derived_csrf_origins.extend(host_to_csrf_origins(allowed_host, RUNSERVER_PORT))

CSRF_TRUSTED_ORIGINS = unique(
    DEFAULT_CSRF_TRUSTED + derived_csrf_origins + env_list("CSRF_TRUSTED_ORIGINS")
)


SITE_URL = (os.getenv("SITE_URL") or os.getenv("PUBLIC_SITE_URL") or "").strip().rstrip("/")
if SITE_URL:
    pass
elif DEBUG:
    dev_host = os.getenv("RUNSERVER_PUBLIC_HOST", "").strip() or "localhost"
    SITE_URL = f"http://{dev_host}:{RUNSERVER_PORT}"
elif IS_RENDER:
    SITE_URL = f"https://{RENDER_HOST}"
else:
    SITE_URL = "https://career.oxu.uz"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True




BRUTEFORCE_MAX_ATTEMPTS = int(os.getenv("BRUTEFORCE_MAX_ATTEMPTS", "10"))
BRUTEFORCE_ATTEMPT_WINDOW_SECONDS = int(os.getenv("BRUTEFORCE_ATTEMPT_WINDOW_SECONDS", "300"))
BRUTEFORCE_BLOCK_SECONDS = int(os.getenv("BRUTEFORCE_BLOCK_SECONDS", "900"))
BRUTEFORCE_WARNING_THRESHOLD = int(
    os.getenv("BRUTEFORCE_WARNING_THRESHOLD", str(max(3, BRUTEFORCE_MAX_ATTEMPTS // 2)))
)




INSTALLED_APPS = [
    "jazzmin",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",


    "corsheaders",
    "widget_tweaks",
    "modeltranslation",
    "phonenumber_field",
    "django_countries",
    "django_ckeditor_5",
    "rest_framework",
    "rest_framework_simplejwt",
    "explorer",


    "accounts",
    "core",
    "alumni",
    "resources",
    "events",
    "employers",
    "cvbuilder",
    "jobs",
]

OAUTH2_PROVIDER_ENABLED = importlib.util.find_spec("oauth2_provider") is not None
if OAUTH2_PROVIDER_ENABLED:
    INSTALLED_APPS.append("oauth2_provider")

AUTH_USER_MODEL = "accounts.CustomUser"




MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",

    "accounts.middleware.NotificationMiddleware",
    "django.middleware.locale.LocaleMiddleware",

    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "accounts.middleware.BruteForceProtectionMiddleware",
    "accounts.middleware.StudentSessionTimeoutMiddleware",
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
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.i18n",


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




AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]




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




STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
    BASE_DIR / "node_modules"
    ]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

SERVE_MEDIA_FILES = env_bool("SERVE_MEDIA_FILES", default=True)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"




AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "accounts.backends.EmailBackend",
    "accounts.backends.OAuthBackend",
]




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
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "20"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("JWT_REFRESH_DAYS", "7"))),
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




CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "https://career.oxu.uz",
    "https://www.career.oxu.uz",
]




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




EXPLORER_CONNECTIONS = {"Default": "default"}
EXPLORER_DEFAULT_CONNECTION = "default"
EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES = ("auth_", "django_")




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


# SECURITY

SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=not DEBUG)
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
    os.getenv(
        "OAUTH_STUDENT_SESSION_AGE",
        str(int(SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())),
    )
)
OAUTH_SET_TOKEN_COOKIES = env_bool("OAUTH_SET_TOKEN_COOKIES", default=True)
OAUTH_ACCESS_COOKIE_NAME = os.getenv("OAUTH_ACCESS_COOKIE_NAME", "student_access")
OAUTH_REFRESH_COOKIE_NAME = os.getenv("OAUTH_REFRESH_COOKIE_NAME", "student_refresh")

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"




EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@oxu.uz"




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

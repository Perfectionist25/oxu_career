# config/settings.py
from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

from pathlib import Path
import os
from datetime import timedelta

# ==========================
# BASE / ENV
# ==========================
BASE_DIR = Path(__file__).resolve().parent.parent


def _resolve_path_from_env(var_name: str, default_dir_name: str) -> Path:
    raw = (os.getenv(var_name) or "").strip()
    if not raw:
        return BASE_DIR / default_dir_name
    path = Path(raw).expanduser()
    if not path.is_absolute():
        return BASE_DIR / path
    # Guard against accidental root-level paths like "/media_dir".
    if path.parent == Path("/"):
        return BASE_DIR / path.name
    return path

# Render detection (самый надёжный маркер)
=======
# Render detection

RENDER_HOST = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
IS_RENDER = bool(os.getenv("RENDER_EXTERNAL_HOSTNAME"))

SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
<<<<<<< HEAD
    raise Exception("SECRET_KEY (or DJANGO_SECRET_KEY) environment variable not set")

DEBUG = os.getenv("DEBUG")
=======
    # Xavfsizlik uchun vaqtincha default kalit (agar env da bo'lmasa)
    if not IS_RENDER:
        SECRET_KEY = 'django-insecure-default-key-change-me'
    else:
        raise Exception("SECRET_KEY (or DJANGO_SECRET_KEY) environment variable not set")

DEBUG = os.getenv("DEBUG", "False") == "True"
>>>>>>> 1ab1a4c (VPS version)

# ==========================
# HOSTS / CSRF / HTTPS
# ==========================
<<<<<<< HEAD
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "172.31.254.31", "career.oxu.uz", "www.career.oxu.uz"]

CSRF_TRUSTED_ORIGINS = ["https://career.oxu.uz"]

# Прод URL (для ссылок/редиректов)
if DEBUG:
    SITE_URL = "http://localhost:8000"
elif IS_RENDER:
    SITE_URL = f"https://{RENDER_HOST}"
=======
ALLOWED_HOSTS = [
    "127.0.0.1",
"172.31.254.31", 
    "localhost", 
    "0.0.0.0", 
    "*",             # Hamma IP larni ruxsat etish (Test uchun)
    "career.oxu.uz", 
    "www.career.oxu.uz"
]

# Env orqali qo'shimcha hostlar
extra_hosts = os.getenv("ALLOWED_HOSTS", "").strip()
if extra_hosts:
    ALLOWED_HOSTS += [h.strip() for h in extra_hosts.split(",") if h.strip()]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000",
    "https://career.oxu.uz",
    "https://www.career.oxu.uz",
]

# Sizning IP manzilingiz (Buni albatta o'zingiznikiga o'zgartiring agar aniq bo'lsa)
# Masalan: "http://54.123.45.67:8000"

# Qo'shimcha CSRF manbalari env dan
extra_csrf = os.getenv("CSRF_TRUSTED_ORIGINS", "").strip()
if extra_csrf:
    CSRF_TRUSTED_ORIGINS += [x.strip() for x in extra_csrf.split(",") if x.strip()]

# Site URL
if DEBUG:
    SITE_URL = "http://localhost:8000"
>>>>>>> 1ab1a4c (VPS version)
else:
    SITE_URL = "https://career.oxu.uz"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

<<<<<<< HEAD
# Render за прокси отдаёт https — это правильно
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

=======
>>>>>>> 1ab1a4c (VPS version)
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

<<<<<<< HEAD
    # Django OAuth Toolkit (если используешь как provider)
    "oauth2_provider",

    # Third-party apps
=======
    # Django OAuth Toolkit
    "oauth2_provider",

    # Third-party apps
    "corsheaders",          # <--- [YANGI] CORS ishlashi uchun SHART
>>>>>>> 1ab1a4c (VPS version)
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
    "django.contrib.sessions.middleware.SessionMiddleware",
<<<<<<< HEAD

=======
    
    "corsheaders.middleware.CorsMiddleware",  # <--- [YANGI] CORS Middleware (Eng tepada bo'lishi kerak)
    
>>>>>>> 1ab1a4c (VPS version)
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
<<<<<<< HEAD

=======
>>>>>>> 1ab1a4c (VPS version)
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
<<<<<<< HEAD
#DATABASES = {
#    "default": {
#        "ENGINE": "django.db.backends.sqlite3",
#        "NAME": BASE_DIR / "db.sqlite3",
#    }
#}


# if IS_RENDER:
#     DB_DIR = Path("/var/data")
#     DB_DIR.mkdir(parents=True, exist_ok=True)

#     DATABASES = {
#         "default": {
#             "ENGINE": "django.db.backends.sqlite3",
#             "NAME": str(DB_DIR / "db.sqlite3"),
#             "OPTIONS": {
#                 "timeout": 20,
#             },
#         }
#     }


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT")
    }
}

# DATABASES = {
#   "default": {
#     "ENGINE": "django.db.backends.sqlite3",
#     "NAME": BASE_DIR / "db.sqlite3",
#   }
# }


=======
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

>>>>>>> 1ab1a4c (VPS version)
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
<<<<<<< HEAD
    ("ru", "Русский"),
    ("uz", "Oʻzbekcha"),
=======
    ("ru", "Ruscha"),
    ("uz", "Ozbekcha"),
>>>>>>> 1ab1a4c (VPS version)
]

LOCALE_PATHS = [BASE_DIR / "locale"]
LANGUAGE_CODE = "en"

TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_L10N = True
USE_TZ = True

MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
MODELTRANSLATION_LANGUAGES = ("uz", "ru", "en")
<<<<<<< HEAD

=======
>>>>>>> 1ab1a4c (VPS version)
PHONENUMBER_DEFAULT_REGION = "UZ"

# ==========================
# CKEDITOR 5
# ==========================
CKEDITOR_5_CONFIGS = {
    "default": {
<<<<<<< HEAD
        "toolbar": [
            "heading",
            "|",
            "bold",
            "italic",
            "underline",
            "strikethrough",
            "|",
            "bulletedList",
            "numberedList",
            "|",
            "blockQuote",
            "imageUpload",
            "link",
            "|",
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
            "|",
            "bulletedList",
            "numberedList",
            "|",
            "blockQuote",
        ],
        "toolbar": [
            "heading",
            "|",
            "outdent",
            "indent",
            "|",
            "bold",
            "italic",
            "link",
            "underline",
            "strikethrough",
            "code",
            "subscript",
            "superscript",
            "highlight",
            "|",
            "codeBlock",
            "sourceEditing",
            "insertImage",
            "bulletedList",
            "numberedList",
            "todoList",
            "|",
            "blockQuote",
            "imageUpload",
            "|",
            "fontSize",
            "fontFamily",
            "fontColor",
            "fontBackgroundColor",
            "|",
            "alignment",
            "|",
            "horizontalLine",
            "|",
            "removeFormat",
            "|",
            "undo",
            "redo",
        ],
        "image": {
            "toolbar": [
                "imageTextAlternative",
                "|",
                "imageStyle:alignLeft",
                "imageStyle:alignRight",
                "imageStyle:alignCenter",
                "imageStyle:side",
                "|",
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
            ]
        },
        "heading": {
            "options": [
                {"model": "paragraph", "title": "Paragraph", "class": "ck-heading_paragraph"},
                {"model": "heading1", "view": "h1", "title": "Heading 1", "class": "ck-heading_heading1"},
                {"model": "heading2", "view": "h2", "title": "Heading 2", "class": "ck-heading_heading2"},
                {"model": "heading3", "view": "h3", "title": "Heading 3", "class": "ck-heading_heading3"},
            ]
        },
        "language": "ru",
    },
}

CKEDITOR_5_UPLOAD_PATH = "uploads/"
CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"
CKEDITOR_5_ALLOW_ALL_FILE_TYPES = False
CKEDITOR_5_UPLOAD_FILE_TYPES = ["jpeg", "jpg", "png", "gif", "bmp", "webp", "svg"]
=======
        "toolbar": ["heading", "|", "bold", "italic", "link", "bulletedList", "numberedList", "blockQuote", "imageUpload", "undo", "redo"],
        "language": "ru",
    },
    "extends": {
        "blockToolbar": ["paragraph", "heading1", "heading2"],
        "toolbar": ["heading", "|", "bold", "italic", "link", "uploadImage", "blockQuote"],
        "language": "ru",
    },
}
CKEDITOR_5_UPLOAD_PATH = "uploads/"
CKEDITOR_5_FILE_UPLOAD_PERMISSION = "staff"
CKEDITOR_5_ALLOW_ALL_FILE_TYPES = True
>>>>>>> 1ab1a4c (VPS version)

# ==========================
# STATIC / MEDIA
# ==========================
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
<<<<<<< HEAD
STATIC_ROOT = "/var/www/alijob/static" #_resolve_path_from_env("STATIC_ROOT", "staticfiles")

MEDIA_URL = "/media/"
MEDIA_ROOT = "/var/www/alijob/media" #_resolve_path_from_env("MEDIA_ROOT", "media_dir")
=======
STATIC_ROOT = "/var/www/career/static"

MEDIA_URL = "/media/"
MEDIA_ROOT = "/var/www/career/media"
>>>>>>> 1ab1a4c (VPS version)

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
<<<<<<< HEAD
        "rest_framework.authentication.TokenAuthentication",
=======
>>>>>>> 1ab1a4c (VPS version)
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
<<<<<<< HEAD

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
# CORS (если используешь django-cors-headers — у тебя не подключён в INSTALLED_APPS)
# ==========================
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "https://career.oxu.uz",
]
if IS_RENDER:
    CORS_ALLOWED_ORIGINS.append(f"https://{RENDER_HOST}")

=======
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ==========================
# CORS HEADERS (FIXED)
# ==========================
CORS_ALLOW_ALL_ORIGINS = True  # Hozircha hammaga ruxsat (Development)
>>>>>>> 1ab1a4c (VPS version)
CORS_ALLOW_CREDENTIALS = True

# ==========================
# CACHE
# ==========================
<<<<<<< HEAD
# На Render redis://127.0.0.1 не существует — поэтому в проде оставим LocMemCache,
# а локально можешь включить redis если хочешь.
if DEBUG:
    # dev: locmem
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }
else:
    # prod: locmem (стабильно)
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "prod-snowflake",
        }
    }
=======
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}
>>>>>>> 1ab1a4c (VPS version)

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
<<<<<<< HEAD
EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES = ("auth_", "django_")

# ==========================
# OAUTH (external provider)
=======

# ==========================
# OAUTH
>>>>>>> 1ab1a4c (VPS version)
# ==========================
OAUTH2_PROVIDER_NAME = "oxu"
OAUTH2_CLIENT_ID = os.getenv("OAUTH2_CLIENT_ID")
OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET")
<<<<<<< HEAD

OAUTH2_BASE_URL = "https://digital.oxu.uz/oauth2"
OAUTH2_AUTHORIZE_URL = f"{OAUTH2_BASE_URL}/authorize"
OAUTH2_TOKEN_URL = f"{OAUTH2_BASE_URL}/token.asp"
OAUTH2_USERINFO_URL = f"{OAUTH2_BASE_URL}/userinfo.asp"
OAUTH2_SCOPE = "openid profile email phone"

# Redirect URI
if DEBUG:
    OAUTH2_REDIRECT_URI = "http://localhost:8000/accounts/oauth/callback/"
elif IS_RENDER:
    OAUTH2_REDIRECT_URI = f"https://{RENDER_HOST}/accounts/oauth/callback/"
else:
    OAUTH2_REDIRECT_URI = "https://career.oxu.uz/accounts/oauth/callback/"

# Старые настройки (оставил как было)
OAUTH_MICROSERVICE_URL = os.environ.get("OAUTH_MICROSERVICE_URL", "https://oauth-microservice.local")
OAUTH_SERVICE_TOKEN = os.environ.get("OAUTH_SERVICE_TOKEN", "")
OAUTH_ALLOWED_UNIVERSITIES = [
    u.strip() for u in os.environ.get("OAUTH_ALLOWED_UNIVERSITIES", "MyUniversity").split(",")
]

# ==========================
# SECURITY
# ==========================
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = True

SESSION_COOKIE_AGE = 86400
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = "DENY"
=======
OAUTH2_BASE_URL = "https://digital.oxu.uz/oauth2"
OAUTH2_REDIRECT_URI = "https://career.oxu.uz/accounts/oauth/callback/"

# ==========================
# SECURITY / HTTPS (FIXED FOR IP ACCESS)
# ==========================
# DIQQAT: SSL (HTTPS) sertifikatingiz bo'lmaguncha bularni FALSE qilib turing
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Agar DEBUG=False bo'lsa ham HTTP da ishlashiga ruxsat berish
if not DEBUG:
    X_FRAME_OPTIONS = "DENY"
    # SECURE_SSL_REDIRECT = True  <-- Buni yoqmang, toki domen va SSL ulamaguncha!
>>>>>>> 1ab1a4c (VPS version)

# ==========================
# EMAIL
# ==========================
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@oxu.uz"

# ==========================
<<<<<<< HEAD
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
=======
# LOGGING (FIXED)
>>>>>>> 1ab1a4c (VPS version)
# ==========================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
<<<<<<< HEAD
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
=======
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
        "simple": {"format": "{levelname} {message}", "style": "{"},
>>>>>>> 1ab1a4c (VPS version)
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs/django.log",
            "formatter": "verbose",
<<<<<<< HEAD
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

# Создать папку logs
logs_dir = BASE_DIR / "logs"
logs_dir.mkdir(exist_ok=True)
=======
            "level": "INFO",
        },
    },
    "loggers": {
        "django": {"handlers": ["console", "file"], "level": "INFO", "propagate": True},
    },
}

# Log papkasini xavfsiz yaratish
try:
    logs_dir = BASE_DIR / "logs"
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)
except Exception as e:
    print(f"Log papkasini yaratib bo'lmadi (Ruxsat yo'q): {e}")
>>>>>>> 1ab1a4c (VPS version)

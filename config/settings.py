from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-smszkt-pg7m@dqqk%&c=ui-mfxrw9##*4v##0&75j9_((bl^0o"

DEBUG = True

ALLOWED_HOSTS = ["*"]

SITE_URL = "http://localhost:8000" if DEBUG else "https://career.oxu.uz"

LOGIN_URL = "/accounts/login/"

PHONENUMBER_DEFAULT_REGION = "UZ"

INSTALLED_APPS = [
    # "modeltranslation",
    "jazzmin",

    #  Application
    "accounts.apps.AccountsConfig",  # User authentication
    "core.apps.CoreConfig",  # Main app
    "alumni.apps.AlumniConfig",  # Alumni network
    "resources.apps.ResourcesConfig",  # Resource library
    "events.apps.EventsConfig",  # Event management
    "employers.apps.EmployersConfig",  # Employer profiles
    "cvbuilder.apps.CvbuilderConfig",  # CV builder
    "jobs.apps.JobsConfig",  # Job listings

    # Сторонние приложения
    "phonenumber_field",
    "django_countries",

    # Django приложения
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "explorer",
]

EXPLORER_CONNECTIONS = {
    "Default": "default",
}

EXPLORER_DEFAULT_CONNECTION = "default"
EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES = ("auth_", "django_")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # ПЕРЕМЕСТИТЬ СЮДА для правильной работы i18n
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
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.i18n",
                # Кастомные контекст-процессоры
                'core.context_processors.site_info',
                'accounts.context_processors.auth_context',
                'jobs.context_processors.jobs_context',
                'events.context_processors.events_context',
                'resources.context_processors.resources_context',
                'employers.context_processors.employers_context',
            ],
            'debug': DEBUG,
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'oxu_career',
#         'USER': 'django_user',
#         'PASSWORD': 'secure_password',
#         'HOST': '127.0.0.1',
#         'PORT': '3306',
#         'OPTIONS': {
#             'charset': 'utf8mb4',
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
#         }
#     }
# }


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Мультиязычность
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

# Modeltranslation configuration
MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
MODELTRANSLATION_LANGUAGES = ('uz', 'ru', 'en')

# Статические файлы
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Медиа файлы
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Кастомная модель пользователя
AUTH_USER_MODEL = "accounts.CustomUser"  # ДОБАВИТЬ

# Настройки аутентификации
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "accounts.backends.EmailBackend",  # ДОБАВИТЬ если есть в accounts
]

# Настройки login/logout
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Email настройки (для разработки)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@oxu.uz"

# Jazzmin настройки
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
    "order_with_respect_to": [
        "accounts",
        "alumni",
        "jobs",
        "events",
        "resources",
        "auth",
    ],
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

# Безопасность (для разработки)
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# Удалить проблемный код с ADMIN_ORDERING (он не работает с Jazzmin)
# Вместо этого используйте настройки Jazzmin выше

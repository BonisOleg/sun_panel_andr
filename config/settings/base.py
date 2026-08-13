"""Soliron shared settings."""

from pathlib import Path

from decouple import Csv, config
from django.templatetags.static import static

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "tinymce",
    "django_htmx",
    "src.core",
    "src.catalog",
    "src.commerce",
    "src.shipping",
    "src.content",
    "src.notifications",
    "src.seo",
    "src.integrations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "src.core.context_processors.site_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uk"
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ("'self'",),
        "script-src": ("'self'",),
        "style-src": ("'self'", "https://fonts.googleapis.com"),
        "style-src-attr": ("'unsafe-inline'",),
        "img-src": ("'self'", "data:", "blob:", "https:"),
        "font-src": ("'self'", "https://fonts.gstatic.com"),
        "connect-src": ("'self'",),
        "frame-src": (
            "'self'",
            "https://www.google.com",
            "https://maps.google.com",
            "https://www.google.com.ua",
            "https://maps.google.com.ua",
        ),
        "frame-ancestors": ("'none'",),
        "base-uri": ("'self'",),
        "form-action": ("'self'",),
    },
    "EXCLUDE_URL_PREFIXES": ("/admin/",),
}

# Повний тулбар «як у WordPress/Joomla» — admin_skill (Prometey vault)
TINYMCE_DEFAULT_CONFIG = {
    "height": 520,
    "menubar": "file edit view insert format tools table help",
    "plugins": (
        "advlist autolink lists link image charmap preview anchor "
        "searchreplace visualblocks code fullscreen media table "
        "wordcount quickbars autosave"
    ),
    "toolbar": (
        "undo redo | blocks fontfamily fontsize | bold italic underline | "
        "forecolor removeformat | alignleft aligncenter alignright | "
        "bullist numlist | link image media table | code fullscreen"
    ),
    "block_formats": "Абзац=p; Заголовок 2=h2; Заголовок 3=h3; Цитата=blockquote",
    "paste_data_images": True,
    "browser_spellcheck": True,
    "promotion": False,
    "branding": False,
    "content_css": False,
    "skin": "oxide",
    "relative_urls": False,
    "remove_script_host": False,
    "convert_urls": True,
    "automatic_uploads": True,
    "images_reuse_filename": False,
    "images_file_types": "jpg,jpeg,png,webp",
    "file_picker_types": "image",
    "images_upload_credentials": True,
    "images_upload_handler": "appTinyMceUploadHandler",
    "valid_elements": (
        "p,br,strong/b,em/i,u,h2,h3,h4,ul,ol,li,"
        "a[href|title|target|rel],blockquote,figure,"
        "img[src|alt|width|height],"
        "table,thead,tbody,tr,th[colspan|rowspan],td[colspan|rowspan]"
    ),
    "invalid_elements": "script,iframe,object,embed,form,figcaption",
    "content_style": (
        "body{font-family:Manrope,Segoe UI,sans-serif;font-size:16px;"
        "line-height:1.65;color:#6c5685;max-width:100%;overflow-wrap:anywhere}"
        "img,table{max-width:100%;height:auto}"
        "img{display:block;border-radius:8px}"
        "ul,ol{padding-left:1.35rem}"
        "table{border-collapse:collapse}"
        "td,th{border:1px solid #d6e4eb;padding:0.4rem 0.6rem}"
    ),
}
TINYMCE_EXTRA_MEDIA = {
    "js": ["admin/js/tinymce_body.js"],
    "css": {"all": ["admin/css/tinymce_unfold.css"]},
}

def _admin_navigation(request):
    from src.content.admin_nav import build_navigation

    return build_navigation(request)


UNFOLD = {
    "SITE_TITLE": "Soliron Admin",
    "SITE_HEADER": "Soliron — Адмінпанель",
    "SITE_SYMBOL": "solar_power",
    "SITE_ICON": lambda request: static("images/favicon/admin-icon.png"),
    "COLORS": {
        "base": {
            "50": "#f6f2f7",
        },
    },
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "any",
            "type": "image/x-icon",
            "href": lambda request: static("images/favicon/favicon.ico"),
        },
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/png",
            "href": lambda request: static("images/favicon/favicon-32x32.png"),
        },
        {
            "rel": "icon",
            "sizes": "16x16",
            "type": "image/png",
            "href": lambda request: static("images/favicon/favicon-16x16.png"),
        },
        {
            "rel": "apple-touch-icon",
            "sizes": "180x180",
            "type": "image/png",
            "href": lambda request: static("images/favicon/apple-touch-icon.png"),
        },
        {
            "rel": "manifest",
            "href": "/site.webmanifest",
        },
    ],
    "SHOW_HISTORY": True,
    "SIDEBAR": {
        "show_search": True,
        "command_search": True,
        "show_all_applications": False,
        "navigation": _admin_navigation,
    },
}

NP_API_KEY = config("NP_API_KEY", default="")

# Delivery Auto API v4 — публічні довідники без ключів; calc/ТТН потребують HMAC.
DELIVERY_PUBLIC_KEY = config("DELIVERY_PUBLIC_KEY", default="")
DELIVERY_SECRET_KEY = config("DELIVERY_SECRET_KEY", default="")
DELIVERY_BASE_URL = config(
    "DELIVERY_BASE_URL",
    default="https://www.delivery-auto.com/api/v4/Public/",
)
# TODO: підставити GUID складу/міста відправника після реєстрації бізнес-кабінету Delivery.
DELIVERY_SENDER_WAREHOUSE_ID = config("DELIVERY_SENDER_WAREHOUSE_ID", default="")
DELIVERY_SENDER_CITY_ID = config("DELIVERY_SENDER_CITY_ID", default="")
# TODO: GUID послуги обрешітки з відповіді PostReceiptCalculate / довідника доп.послуг.
DELIVERY_CRATE_SERVICE_ID = config("DELIVERY_CRATE_SERVICE_ID", default="")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "src": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}

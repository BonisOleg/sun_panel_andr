"""Global template context."""

from pathlib import Path

from django.conf import settings


def _static_asset_version() -> int:
    """Newest mtime across all project CSS/JS — shared ?v= cache-bust (ERR-117 / 600d15)."""
    static_root = Path(settings.BASE_DIR) / "static"
    mtimes = [
        int(path.stat().st_mtime)
        for pattern in ("css/**/*.css", "js/**/*.js")
        for path in static_root.glob(pattern)
    ]
    return max(mtimes) if mtimes else 0


def site_context(request):
    from src.content.models import SiteSettings
    from src.commerce.selectors import cart_items_count
    from src.seo.utils import absolute_url, meta_text, public_base_url

    settings_obj = SiteSettings.load()
    site_name = (settings_obj.site_name or "Soliron").strip() or "Soliron"
    default_description = meta_text(
        settings_obj.footer_tagline
        or f"{site_name} — сонячні панелі, кріплення та монтаж під ключ."
    )
    path = request.path if request is not None else "/"
    return {
        "site_settings": settings_obj,
        "cart_count": cart_items_count(request),
        "static_version": _static_asset_version(),
        "public_base_url": public_base_url(request),
        "seo_title": site_name,
        "seo_description": default_description,
        "seo_keywords": "",
        "seo_canonical": absolute_url(path, request),
        "seo_og_title": site_name,
        "seo_og_type": "website",
        "seo_og_image": absolute_url(settings_obj.logo_url, request),
        "seo_robots": "",
    }

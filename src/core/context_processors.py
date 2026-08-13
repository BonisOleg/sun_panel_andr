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

    settings_obj = SiteSettings.load()
    return {
        "site_settings": settings_obj,
        "cart_count": cart_items_count(request),
        "static_version": _static_asset_version(),
    }

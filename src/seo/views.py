import json

from django.http import HttpResponse
from django.templatetags.static import static

from src.content.models import SiteSettings


def robots_txt(_request):
    settings = SiteSettings.load()
    body = settings.robots_txt.strip() or (
        "User-agent: *\n"
        "Disallow: /admin/\n"
        "Sitemap: /sitemap.xml\n"
    )
    return HttpResponse(body, content_type="text/plain")


def webmanifest(_request):
    site = SiteSettings.load()
    name = (site.site_name or "Soliron").strip() or "Soliron"
    payload = {
        "name": name,
        "short_name": name[:12],
        "description": f"{name} — інтернет-магазин",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#6c5685",
        "lang": "uk",
        "icons": [
            {
                "src": static("images/favicon/android-chrome-192x192.png"),
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": static("images/favicon/android-chrome-512x512.png"),
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any",
            },
        ],
    }
    return HttpResponse(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        content_type="application/manifest+json",
    )

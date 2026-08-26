import json

from django.conf import settings as django_settings
from django.http import HttpResponse
from django.templatetags.static import static

from src.content.models import SiteSettings
from src.seo.utils import absolute_url, public_base_url


def robots_txt(request):
    settings = SiteSettings.load()
    body = settings.robots_txt.strip()
    if not body:
        sitemap = absolute_url("/sitemap.xml", request)
        admin_prefix = f"/{django_settings.ADMIN_URL.lstrip('/')}"
        body = (
            "User-agent: *\n"
            f"Disallow: {admin_prefix}\n"
            "Disallow: /admin/\n"
            "Disallow: /koshyk/\n"
            "Disallow: /oformlennya/\n"
            f"Sitemap: {sitemap}\n"
        )
    elif "Sitemap:" not in body and public_base_url(request):
        body = body.rstrip() + f"\nSitemap: {absolute_url('/sitemap.xml', request)}\n"
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

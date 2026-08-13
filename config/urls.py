from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("tinymce/", include("tinymce.urls")),
    path("admin/", admin.site.urls),
    path("healthz/", include("src.core.urls_health")),
    path("", include("src.seo.urls")),
    path("", include("src.shipping.urls")),
    path("", include("src.catalog.urls")),
    path("", include("src.commerce.urls")),
    path("", include("src.content.urls")),
    path("", include("src.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

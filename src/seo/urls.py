from django.contrib.sitemaps.views import sitemap
from django.urls import path

from . import views
from .sitemaps import sitemaps

app_name = "seo"

urlpatterns = [
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("robots.txt", views.robots_txt, name="robots"),
    path("site.webmanifest", views.webmanifest, name="webmanifest"),
]

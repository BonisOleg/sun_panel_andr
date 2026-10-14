from django.urls import path
from django.views.generic import RedirectView

from . import views
from .views_upload import tinymce_blog_image_upload

app_name = "content"

urlpatterns = [
    path("api/hero-offer/", views.HeroOfferPartialView.as_view(), name="hero_offer"),
    path("api/categories/", views.CategoriesPartialView.as_view(), name="categories_api"),
    path(
        "api/content/tinymce-upload/",
        tinymce_blog_image_upload,
        name="tinymce_blog_image_upload",
    ),
    path("blog/", views.BlogListView.as_view(), name="blog_list"),
    path("blog/<slug:slug>/", views.BlogDetailView.as_view(), name="blog_detail"),
    path("kontakty/", views.ContactsView.as_view(), name="contacts"),
    # Legacy/external /contacts/ → canonical /kontakty/ (no DB; seo.Redirect301 unused in MW).
    path(
        "contacts/",
        RedirectView.as_view(
            pattern_name="content:contacts",
            permanent=True,
            query_string=True,
        ),
    ),
    path("<slug:slug>/", views.ContentPageDetailView.as_view(), name="page"),
]

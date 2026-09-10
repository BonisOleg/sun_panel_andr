from django.urls import path

from . import views
from .feeds import GoogleMerchantFeedView

app_name = "catalog"

urlpatterns = [
    path("katalog/", views.CatalogListView.as_view(), name="list"),
    path("katalog/<slug:slug>/", views.CategoryListView.as_view(), name="category"),
    path("tovar/<slug:slug>/", views.ProductDetailView.as_view(), name="product"),
    path("poshuk/", views.SearchView.as_view(), name="search"),
    path(
        "feeds/google-merchant.xml",
        GoogleMerchantFeedView.as_view(),
        name="google_merchant_feed",
    ),
]

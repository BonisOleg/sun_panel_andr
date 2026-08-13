from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("katalog/", views.CatalogListView.as_view(), name="list"),
    path("katalog/<slug:slug>/", views.CategoryListView.as_view(), name="category"),
    path("tovar/<slug:slug>/", views.ProductDetailView.as_view(), name="product"),
    path("poshuk/", views.SearchView.as_view(), name="search"),
]

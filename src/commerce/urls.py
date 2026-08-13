from django.urls import path

from . import views

app_name = "commerce"

urlpatterns = [
    path("koshyk/", views.CartDetailView.as_view(), name="cart"),
    path("koshyk/add/<int:product_id>/", views.CartAddView.as_view(), name="cart_add"),
    path(
        "koshyk/update/<int:item_id>/",
        views.CartUpdateView.as_view(),
        name="cart_update",
    ),
    path(
        "koshyk/remove/<int:item_id>/",
        views.CartRemoveView.as_view(),
        name="cart_remove",
    ),
    path("oformlennya/", views.CheckoutView.as_view(), name="checkout"),
]

from django.urls import path

from . import views

app_name = "shipping"

urlpatterns = [
    path("api/np/cities/", views.NPCitiesView.as_view(), name="np_cities"),
    path("api/np/warehouses/", views.NPWarehousesView.as_view(), name="np_warehouses"),
    path(
        "api/delivery/cities/",
        views.DeliveryCitiesView.as_view(),
        name="delivery_cities",
    ),
    path(
        "api/delivery/warehouses/",
        views.DeliveryWarehousesView.as_view(),
        name="delivery_warehouses",
    ),
]

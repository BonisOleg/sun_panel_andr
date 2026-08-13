from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import DeliveryCity, DeliveryWarehouse, NPCity, NPWarehouse


@admin.register(NPCity)
class NPCityAdmin(ModelAdmin):
    list_display = ("name", "area", "ref", "is_active")
    search_fields = ("name", "ref", "area")
    list_filter = ("is_active",)


@admin.register(NPWarehouse)
class NPWarehouseAdmin(ModelAdmin):
    list_display = ("description", "city", "number", "is_active")
    search_fields = ("description", "ref", "number")
    list_filter = ("is_active", "city")


@admin.register(DeliveryCity)
class DeliveryCityAdmin(ModelAdmin):
    list_display = ("name_uk", "region_name", "city_id", "is_active")
    search_fields = ("name_uk", "city_id", "region_name")
    list_filter = ("is_active",)


@admin.register(DeliveryWarehouse)
class DeliveryWarehouseAdmin(ModelAdmin):
    list_display = (
        "name_uk",
        "city",
        "is_freight",
        "warehouse_type",
        "is_active",
    )
    search_fields = ("name_uk", "warehouse_id", "address_uk")
    list_filter = ("is_active", "is_freight", "city")

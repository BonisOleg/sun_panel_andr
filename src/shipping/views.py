from django.http import JsonResponse
from django.views import View

from . import services
from .delivery import search as delivery_search


class NPCitiesView(View):
    def get(self, request):
        q = request.GET.get("q", "")
        return JsonResponse({"results": services.search_cities(q)})


class NPWarehousesView(View):
    def get(self, request):
        city = request.GET.get("city") or request.GET.get("city_ref") or ""
        q = request.GET.get("q", "")
        return JsonResponse({"results": services.list_warehouses(city, q)})


class DeliveryCitiesView(View):
    def get(self, request):
        q = request.GET.get("q", "")
        return JsonResponse({"results": delivery_search.search_cities(q)})


class DeliveryWarehousesView(View):
    def get(self, request):
        city_id = (
            request.GET.get("city_id")
            or request.GET.get("city")
            or ""
        )
        q = request.GET.get("q", "")
        return JsonResponse(
            {"results": delivery_search.list_warehouses(city_id, q)}
        )

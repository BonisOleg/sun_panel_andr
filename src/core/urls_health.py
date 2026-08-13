from django.http import HttpResponse
from django.urls import path


def healthz(_request):
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("", healthz, name="healthz"),
]

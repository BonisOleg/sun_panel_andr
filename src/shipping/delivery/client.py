"""HTTP-клієнт Delivery Auto API v4 (requests, без сторонніх SDK)."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urljoin

import requests
from django.conf import settings

from .auth import build_hmac_headers
from .exceptions import DeliveryAPIError, DeliveryAuthError, DeliveryConfigError

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
DEFAULT_CULTURE = "uk-UA"


class DeliveryAPIClient:
    """Тонкий REST-клієнт: публічні GET без ключів; POST з HMAC за потреби."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        public_key: str | None = None,
        secret_key: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = (base_url or settings.DELIVERY_BASE_URL).rstrip("/") + "/"
        self.public_key = public_key if public_key is not None else settings.DELIVERY_PUBLIC_KEY
        self.secret_key = secret_key if secret_key is not None else settings.DELIVERY_SECRET_KEY
        self.timeout = timeout
        self._session = session or requests.Session()

    def has_credentials(self) -> bool:
        return bool(self.public_key and self.secret_key)

    def require_credentials(self) -> None:
        if not self.has_credentials():
            raise DeliveryConfigError(
                "DELIVERY_PUBLIC_KEY / DELIVERY_SECRET_KEY не налаштовано"
            )

    def get(
        self,
        method_name: str,
        params: dict[str, Any] | None = None,
        *,
        auth: bool = False,
    ) -> Any:
        return self._request("GET", method_name, params=params, auth=auth)

    def post(
        self,
        method_name: str,
        payload: dict[str, Any] | None = None,
        *,
        auth: bool = False,
    ) -> Any:
        return self._request("POST", method_name, json=payload, auth=auth)

    def get_areas_list(
        self,
        *,
        culture: str = DEFAULT_CULTURE,
        country: int = 1,
        fl_all: bool = False,
    ) -> list[dict[str, Any]]:
        """Публічний довідник міст (без ключів).

        fl_all=False — лише міста зі складами (~250); True — усі населені пункти.
        """
        data = self.get(
            "GetAreasList",
            {
                "culture": culture,
                "country": country,
                "fl_all": str(fl_all).lower(),
            },
        )
        return data if isinstance(data, list) else []

    def get_warehouses_list(
        self,
        *,
        city_id: str | None = None,
        culture: str = DEFAULT_CULTURE,
        country: int = 1,
        include_regional_centers: bool = False,
    ) -> list[dict[str, Any]]:
        """Публічний довідник складів (без ключів)."""
        params: dict[str, Any] = {
            "culture": culture,
            "country": country,
            "includeRegionalCenters": str(include_regional_centers).lower(),
        }
        if city_id:
            params["CityId"] = city_id
        data = self.get("GetWarehousesList", params)
        return data if isinstance(data, list) else []

    def get_warehouse_info(
        self,
        warehouse_id: str,
        *,
        culture: str = DEFAULT_CULTURE,
    ) -> dict[str, Any]:
        """Деталі складу (телефон тощо). Публічний метод."""
        data = self.get(
            "GetWarehousesInfo",
            {"culture": culture, "WarehousesId": warehouse_id},
        )
        if isinstance(data, list):
            return data[0] if data else {}
        return data if isinstance(data, dict) else {}

    def _request(
        self,
        http_method: str,
        method_name: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        auth: bool = False,
    ) -> Any:
        url = urljoin(self.base_url, method_name.lstrip("/"))
        headers: dict[str, str] = {
            "Accept": "application/json",
        }
        if auth:
            self.require_credentials()
            headers.update(
                build_hmac_headers(self.public_key, self.secret_key)
            )

        try:
            response = self._session.request(
                http_method,
                url,
                params=params,
                json=json,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.exception("Delivery API network error: %s %s", http_method, method_name)
            raise DeliveryAPIError("Помилка звʼязку з Delivery Auto") from exc

        if response.status_code in (401, 403):
            raise DeliveryAuthError(
                "Авторизація Delivery відхилена",
                status_code=response.status_code,
            )
        if response.status_code >= 400:
            raise DeliveryAPIError(
                f"Delivery HTTP {response.status_code}",
                status_code=response.status_code,
            )

        try:
            body = response.json()
        except ValueError as exc:
            raise DeliveryAPIError("Delivery повернув не-JSON відповідь") from exc

        if isinstance(body, dict) and body.get("status") is False:
            message = body.get("message") or body.get("Message") or "Delivery status=false"
            raise DeliveryAPIError(str(message), status_code=response.status_code)

        if isinstance(body, dict) and "data" in body:
            return body["data"]
        return body

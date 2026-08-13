"""Помилки інтеграції Delivery Auto."""


class DeliveryAPIError(Exception):
    """Загальна помилка відповіді / мережі Delivery API."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        self.status_code = status_code
        super().__init__(message)


class DeliveryConfigError(DeliveryAPIError):
    """Не налаштовано ключі, склад відправника або інші env-параметри."""


class DeliveryAuthError(DeliveryAPIError):
    """HMAC / авторизація відхилена API."""

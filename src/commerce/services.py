"""commerce cart / checkout services — business_logic.md §2.2–2.3."""

from __future__ import annotations

import re
from decimal import Decimal

from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone

from src.catalog.models import Product, ProductImage
from src.notifications.services import send_order_email

from .models import Cart, CartItem, Order, OrderItem

CHECKOUT_SESSION_KEY = "checkout"
MAX_QTY = 999


class CartError(Exception):
    pass


class CheckoutError(Exception):
    pass


def _ensure_session(request) -> str:
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def get_or_create_cart(request) -> Cart:
    session_key = _ensure_session(request)
    cart = (
        Cart.objects.filter(session_key=session_key, status=Cart.Status.ACTIVE)
        .order_by("-updated_at")
        .first()
    )
    if cart is None:
        cart = Cart.objects.create(
            session_key=session_key,
            status=Cart.Status.ACTIVE,
        )
    return cart


def cart_items_qs(cart: Cart):
    return (
        cart.items.select_related("product")
        .prefetch_related(
            Prefetch(
                "product__images",
                queryset=ProductImage.objects.filter(is_main=True),
                to_attr="main_images",
            )
        )
        .order_by("id")
    )


def cart_subtotal(cart: Cart) -> Decimal:
    total = Decimal("0.00")
    for item in cart_items_qs(cart):
        if item.unit_price_uah is not None:
            total += item.unit_price_uah * item.qty
    return total


def get_checkout_draft(request) -> dict:
    return request.session.get(CHECKOUT_SESSION_KEY) or {"step": 1}


def save_checkout_draft(request, data: dict) -> None:
    request.session[CHECKOUT_SESSION_KEY] = data
    request.session.modified = True


def clear_checkout_draft(request) -> None:
    if CHECKOUT_SESSION_KEY in request.session:
        del request.session[CHECKOUT_SESSION_KEY]
        request.session.modified = True


_NAME_RE = re.compile(
    r"^[A-Za-zА-Яа-яЁёІіЇїЄєҐґʼ'`’\-\s]+$",
    re.UNICODE,
)
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_UA_PHONE_RE = re.compile(r"^\+380\d{9}$")


def _normalize_phone(phone: str) -> str:
    """Нормалізує до формату +380XXXXXXXXX (рівно 9 цифр після +380)."""
    raw = (phone or "").strip()
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("380"):
        digits = digits[3:]
    elif digits.startswith("0") and len(digits) >= 10:
        digits = digits[1:]
    digits = digits[:9]
    if not digits:
        return "+380"
    return f"+380{digits}"


def validate_step1(data: dict) -> dict:
    name = (data.get("customer_name") or "").strip()
    phone = _normalize_phone(data.get("customer_phone") or "")
    email = (data.get("customer_email") or "").strip()
    company = (data.get("customer_company") or "").strip()
    errors: dict[str, str] = {}

    if not name:
        errors["customer_name"] = "Вкажіть ПІБ"
    elif re.search(r"\d", name):
        errors["customer_name"] = "ПІБ не може містити цифри — лише літери"
    elif not _NAME_RE.fullmatch(name):
        errors["customer_name"] = (
            "ПІБ: лише літери, пробіли, дефіс або апостроф"
        )

    if not phone or phone == "+380":
        errors["customer_phone"] = "Вкажіть номер телефону після +380"
    elif not _UA_PHONE_RE.fullmatch(phone):
        errors["customer_phone"] = (
            "Український номер: +380 і рівно 9 цифр (наприклад +380501234567)"
        )

    if email and not _EMAIL_RE.fullmatch(email):
        errors["customer_email"] = (
            "Некоректний email — приклад: name@example.com"
        )

    if errors:
        raise CheckoutError(errors)
    return {
        "customer_name": name,
        "customer_phone": phone,
        "customer_email": email,
        "customer_company": company,
    }


def validate_step2(data: dict) -> dict:
    method = (data.get("shipping_method") or "").strip()
    comment = (data.get("customer_comment") or "").strip()
    errors: dict[str, str] = {}
    if method not in Order.ShippingMethod.values:
        errors["shipping_method"] = "Оберіть спосіб доставки"
        raise CheckoutError(errors)

    result = {
        "shipping_method": method,
        "customer_comment": comment,
        "delivery_mode": "",
        "delivery_city_id": "",
        "delivery_city_name": "",
        "delivery_warehouse_id": "",
        "delivery_warehouse_name": "",
        "delivery_address": "",
        "delivery_cost_uah": None,
        "tracking_number": "",
        "np_city_ref": "",
        "np_city_name": "",
        "np_warehouse_ref": "",
        "np_warehouse_name": "",
    }
    if method == Order.ShippingMethod.DELIVERY:
        mode = (data.get("delivery_mode") or "").strip()
        city_id = (data.get("delivery_city_id") or "").strip()
        city_name = (data.get("delivery_city_name") or "").strip()
        wh_id = (data.get("delivery_warehouse_id") or "").strip()
        wh_name = (data.get("delivery_warehouse_name") or "").strip()
        address = (data.get("delivery_address") or "").strip()
        if mode not in Order.DeliveryMode.values:
            errors["delivery_mode"] = "Оберіть тип доставки Delivery"
        if not city_id or not city_name:
            errors["delivery_city_id"] = "Оберіть місто"
        if mode == Order.DeliveryMode.WAREHOUSE:
            if not wh_id or not wh_name:
                errors["delivery_warehouse_id"] = "Оберіть вантажний склад"
        elif mode == Order.DeliveryMode.DOORS:
            if not address:
                errors["delivery_address"] = "Вкажіть вулицю та будинок"
        if errors:
            raise CheckoutError(errors)
        result.update(
            {
                "delivery_mode": mode,
                "delivery_city_id": city_id,
                "delivery_city_name": city_name,
                "delivery_warehouse_id": wh_id if mode == Order.DeliveryMode.WAREHOUSE else "",
                "delivery_warehouse_name": wh_name if mode == Order.DeliveryMode.WAREHOUSE else "",
                "delivery_address": address if mode == Order.DeliveryMode.DOORS else "",
            }
        )
    elif method == Order.ShippingMethod.NOVA_POSHTA:
        city_ref = (data.get("np_city_ref") or "").strip()
        city_name = (data.get("np_city_name") or "").strip()
        wh_ref = (data.get("np_warehouse_ref") or "").strip()
        wh_name = (data.get("np_warehouse_name") or "").strip()
        if not city_ref or not city_name:
            errors["np_city_ref"] = "Оберіть місто"
        if not wh_ref or not wh_name:
            errors["np_warehouse_ref"] = "Оберіть відділення"
        if errors:
            raise CheckoutError(errors)
        result.update(
            {
                "np_city_ref": city_ref,
                "np_city_name": city_name,
                "np_warehouse_ref": wh_ref,
                "np_warehouse_name": wh_name,
            }
        )
    return result


def validate_step3(data: dict) -> dict:
    method = (data.get("payment_method") or "").strip()
    if method not in Order.PaymentMethod.values:
        raise CheckoutError({"payment_method": "Оберіть спосіб оплати"})
    return {"payment_method": method}


def _next_order_number() -> str:
    stamp = timezone.localdate().strftime("%Y%m%d")
    prefix = f"SL-{stamp}-"
    last = (
        Order.objects.filter(number__startswith=prefix)
        .order_by("-number")
        .values_list("number", flat=True)
        .first()
    )
    seq = 1
    if last:
        try:
            seq = int(last.rsplit("-", 1)[-1]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:04d}"


@transaction.atomic
def add_item(request, *, product_id: int, qty: int = 1) -> Cart:
    if qty < 1 or qty > MAX_QTY:
        raise CartError("Некоректна кількість")
    product = Product.objects.filter(pk=product_id, is_published=True).first()
    if product is None:
        raise CartError("Товар не знайдено")
    if product.availability == Product.Availability.OUT_OF_STOCK:
        raise CartError("Товар недоступний для замовлення")
    cart = get_or_create_cart(request)
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"qty": qty, "unit_price_uah": product.price_uah},
    )
    if not created:
        item.qty = min(item.qty + qty, MAX_QTY)
        item.unit_price_uah = product.price_uah
        item.save(update_fields=["qty", "unit_price_uah"])
    cart.save(update_fields=["updated_at"])
    return cart


@transaction.atomic
def update_item_qty(request, *, item_id: int, qty: int) -> Cart:
    cart = get_or_create_cart(request)
    item = cart.items.select_related("product").filter(pk=item_id).first()
    if item is None:
        raise CartError("Позицію не знайдено")
    if qty < 1:
        item.delete()
    else:
        item.qty = min(qty, MAX_QTY)
        item.save(update_fields=["qty"])
    cart.save(update_fields=["updated_at"])
    return cart


@transaction.atomic
def remove_item(request, *, item_id: int) -> Cart:
    cart = get_or_create_cart(request)
    deleted, _ = cart.items.filter(pk=item_id).delete()
    if not deleted:
        raise CartError("Позицію не знайдено")
    cart.save(update_fields=["updated_at"])
    return cart


@transaction.atomic
def place_order(request) -> Order:
    draft = get_checkout_draft(request)
    step1 = validate_step1(draft)
    step2 = validate_step2(draft)
    step3 = validate_step3(draft)

    cart = get_or_create_cart(request)
    items = list(cart_items_qs(cart).select_for_update())
    if not items:
        raise CheckoutError({"cart": "Кошик порожній"})

    lines: list[dict] = []
    subtotal = Decimal("0.00")
    for item in items:
        product = item.product
        if product is None or not product.is_published:
            raise CheckoutError({"cart": f"Товар недоступний: {item.product_id}"})
        if product.availability == Product.Availability.OUT_OF_STOCK:
            raise CheckoutError({"cart": f"Немає в наявності: {product.name}"})
        live_price = product.price_uah
        line_total = None
        if live_price is not None:
            line_total = live_price * item.qty
            subtotal += line_total
        lines.append(
            {
                "product": product,
                "product_sku": product.sku,
                "product_name": product.name,
                "qty": item.qty,
                "unit_price_uah": live_price,
                "line_total_uah": line_total,
            }
        )

    order = Order.objects.create(
        number=_next_order_number(),
        status=Order.Status.NEW,
        **step1,
        **step2,
        **step3,
        subtotal_uah=subtotal,
        total_uah=subtotal,
        cart=cart,
    )
    OrderItem.objects.bulk_create(
        [OrderItem(order=order, **line) for line in lines]
    )
    cart.status = Cart.Status.CONVERTED
    cart.save(update_fields=["status", "updated_at"])
    clear_checkout_draft(request)

    sent = send_order_email(order)
    if sent:
        order.email_sent_at = timezone.now()
        order.save(update_fields=["email_sent_at"])
    return order

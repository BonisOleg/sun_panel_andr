"""commerce thin views — cart + 3-step checkout."""

from __future__ import annotations

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from . import services
from .models import Order
from .selectors import cart_items_count


def _htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


def _cart_context(request):
    cart = services.get_or_create_cart(request)
    items = list(services.cart_items_qs(cart))
    return {
        "cart": cart,
        "items": items,
        "subtotal": services.cart_subtotal(cart),
        "cart_count": cart_items_count(request),
    }


class CartDetailView(View):
    def get(self, request):
        return render(request, "commerce/cart.html", _cart_context(request))


class CartAddView(View):
    def post(self, request, product_id: int):
        try:
            qty = int(request.POST.get("qty") or 1)
            services.add_item(request, product_id=product_id, qty=qty)
        except (services.CartError, ValueError) as exc:
            if _htmx(request):
                return HttpResponse(str(exc), status=400)
            return render(
                request,
                "commerce/cart.html",
                {**_cart_context(request), "error": str(exc)},
                status=400,
            )
        if _htmx(request):
            return render(
                request,
                "commerce/partials/cart_badge.html",
                {"cart_count": cart_items_count(request)},
            )
        return redirect("commerce:cart")


def _cart_htmx_template(request) -> str:
    """Повертає partial залежно від hx-target (сторінка кошика vs checkout)."""
    target = (request.headers.get("HX-Target") or "").strip()
    if target == "cart-body":
        return "commerce/partials/cart_body.html"
    return "commerce/partials/cart_table.html"


def _cart_htmx_response(request):
    """Основний partial кошика + OOB-оновлення лічильника в хедері."""
    return render(
        request,
        "commerce/partials/cart_htmx_swap.html",
        {
            **_cart_context(request),
            "main_partial": _cart_htmx_template(request),
        },
    )


class CartUpdateView(View):
    def post(self, request, item_id: int):
        try:
            qty = int(request.POST.get("qty") or 1)
            services.update_item_qty(request, item_id=item_id, qty=qty)
        except (services.CartError, ValueError) as exc:
            return HttpResponse(str(exc), status=400)
        if _htmx(request):
            return _cart_htmx_response(request)
        return redirect("commerce:cart")


class CartRemoveView(View):
    def post(self, request, item_id: int):
        try:
            services.remove_item(request, item_id=item_id)
        except services.CartError as exc:
            return HttpResponse(str(exc), status=400)
        if _htmx(request):
            return _cart_htmx_response(request)
        return redirect("commerce:cart")


class CheckoutView(View):
    template_name = "commerce/checkout.html"

    def get(self, request):
        if request.session.get("order_thanks"):
            number = request.session.pop("order_thanks")
            request.session.modified = True
            return render(
                request,
                "commerce/thanks.html",
                {"order_number": number},
            )
        cart = services.get_or_create_cart(request)
        items = list(services.cart_items_qs(cart))
        if not items:
            return redirect("commerce:cart")
        draft = services.get_checkout_draft(request)
        step = int(draft.get("step") or 1)
        ctx = {
            **_cart_context(request),
            "draft": draft,
            "step": step,
            "errors": {},
            "shipping_choices": Order.ShippingMethod.choices,
            "payment_choices": Order.PaymentMethod.choices,
        }
        return render(request, self.template_name, ctx)

    def post(self, request):
        action = (request.POST.get("action") or "next").strip()
        draft = services.get_checkout_draft(request)
        step = int(draft.get("step") or 1)
        errors = {}

        try:
            if action == "back":
                draft["step"] = max(1, step - 1)
                services.save_checkout_draft(request, draft)
                return redirect("commerce:checkout")

            if step == 1:
                cleaned = services.validate_step1(request.POST)
                draft.update(cleaned)
                draft["step"] = 2
                services.save_checkout_draft(request, draft)
                return redirect("commerce:checkout")

            if step == 2:
                cleaned = services.validate_step2(request.POST)
                draft.update(cleaned)
                draft["step"] = 3
                services.save_checkout_draft(request, draft)
                return redirect("commerce:checkout")

            if step == 3 and action == "confirm":
                cleaned = services.validate_step3(request.POST)
                draft.update(cleaned)
                services.save_checkout_draft(request, draft)
                order = services.place_order(request)
                request.session["order_thanks"] = order.number
                request.session.modified = True
                return redirect("commerce:checkout")
        except services.CheckoutError as exc:
            payload = exc.args[0] if exc.args else {"__all__": str(exc)}
            errors = payload if isinstance(payload, dict) else {"__all__": str(payload)}
        except services.CartError as exc:
            errors = {"cart": str(exc)}

        ctx = {
            **_cart_context(request),
            "draft": draft,
            "step": int(draft.get("step") or step),
            "errors": errors,
            "shipping_choices": Order.ShippingMethod.choices,
            "payment_choices": Order.PaymentMethod.choices,
        }
        return render(request, self.template_name, ctx, status=400)

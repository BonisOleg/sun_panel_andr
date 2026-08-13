"""Read-only cart helpers."""

from django.db.models import Sum

from .models import Cart, CartItem


def cart_items_count(request) -> int:
    session_key = getattr(request.session, "session_key", None)
    if not session_key:
        return 0
    cart = (
        Cart.objects.filter(session_key=session_key, status=Cart.Status.ACTIVE)
        .only("id")
        .first()
    )
    if cart is None:
        return 0
    total = CartItem.objects.filter(cart=cart).aggregate(n=Sum("qty"))["n"]
    return int(total or 0)

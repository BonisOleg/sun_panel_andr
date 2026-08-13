"""catalog thin views."""

from django.shortcuts import render
from django.utils.html import strip_tags
from django.views.generic import DetailView, ListView

from src.core.richtext import render_richtext

from . import selectors
from .models import Product
from .text_utils import parse_specs, short_description

PRODUCT_GRID_PARTIAL = "catalog/partials/product_grid.html"


class HtmxProductGridMixin:
    """Return product grid partial for HTMX filter swaps."""

    def render_to_response(self, context, **response_kwargs):
        if getattr(self.request, "htmx", False):
            return render(self.request, PRODUCT_GRID_PARTIAL, context)
        return super().render_to_response(context, **response_kwargs)

    def catalog_filters(self) -> dict:
        return selectors.parse_catalog_filters(self.request)

    def filtered_queryset(self, *, category=None):
        f = self.catalog_filters()
        return selectors.filter_products(
            category=category,
            q=f["q"],
            price_min=f["price_min"],
            price_max=f["price_max"],
            sort=f["sort"],
        )

    def inject_filter_context(self, ctx: dict) -> dict:
        f = self.catalog_filters()
        ctx.update(
            {
                "q": f["q"],
                "sort": f["sort"],
                "price_min": f["price_min_raw"],
                "price_max": f["price_max_raw"],
                "categories": selectors.active_root_categories(),
            }
        )
        return ctx


class CatalogListView(HtmxProductGridMixin, ListView):
    template_name = "catalog/list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        return self.filtered_queryset()

    def get_context_data(self, **kwargs):
        return self.inject_filter_context(super().get_context_data(**kwargs))


class CategoryListView(HtmxProductGridMixin, ListView):
    template_name = "catalog/list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        self.category = selectors.get_category_by_slug(self.kwargs["slug"])
        return self.filtered_queryset(category=self.category)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["category"] = self.category
        ctx["breadcrumbs"] = selectors.category_ancestors(self.category)
        return self.inject_filter_context(ctx)


class ProductDetailView(DetailView):
    template_name = "catalog/product_detail.html"
    context_object_name = "product"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return selectors.published_products()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product: Product = ctx["product"]
        crumbs = []
        if product.category_id:
            crumbs = selectors.category_ancestors(product.category)
        desc = product.description or ""
        plain = strip_tags(desc)
        specs = parse_specs(plain)
        quick = list(specs[:3])
        if product.sku and not any(k.casefold() == "артикул" for k, _ in quick):
            quick.insert(0, ("Артикул", product.sku))
            quick = quick[:3]
        ctx["breadcrumbs"] = crumbs
        ctx["product_images"] = list(product.images.all())
        ctx["product_short_desc"] = short_description(plain)
        ctx["product_description_html"] = render_richtext(desc)
        ctx["product_specs"] = specs
        ctx["product_quick_specs"] = quick
        return ctx


SUGGEST_PARTIAL = "catalog/partials/header_search_results.html"


class SearchView(HtmxProductGridMixin, ListView):
    """Full search page, or HTMX header suggestions partial (§41 / 600d10)."""

    template_name = "catalog/list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        return self.filtered_queryset()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_search"] = True
        return self.inject_filter_context(ctx)

    def render_to_response(self, context, **response_kwargs):
        if getattr(self.request, "htmx", False):
            q = (self.request.GET.get("q") or "").strip()
            products = list(selectors.suggest_products(q))
            return render(
                self.request,
                SUGGEST_PARTIAL,
                {"products": products, "q": q},
            )
        return ListView.render_to_response(self, context, **response_kwargs)

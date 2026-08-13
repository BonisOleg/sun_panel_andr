"""content thin views."""

from django.shortcuts import render
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from src.catalog import selectors as catalog_selectors
from src.catalog.models import Category

from . import services


def _htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


class HomeView(TemplateView):
    template_name = "content/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["home"] = services.get_home_page()
        ctx["advantages"] = services.home_advantages()
        ctx["categories"] = catalog_selectors.active_root_categories()
        return ctx


class HeroOfferPartialView(View):
    """HTMX: блок пропозиції з singleton HomePage."""

    def get(self, request):
        home = services.get_home_page()
        return render(request, "content/partials/hero_offer.html", {"home": home})


class CategoriesPartialView(View):
    """HTMX stub: category cards; ?type=root|slug filters set."""

    def get(self, request):
        type_param = (request.GET.get("type") or "root").strip()
        if type_param == "root" or not type_param:
            categories = catalog_selectors.active_root_categories()
        else:
            parent = Category.objects.filter(slug=type_param, is_active=True).first()
            if parent is None:
                categories = catalog_selectors.active_root_categories()
            else:
                children = Category.objects.filter(parent=parent, is_active=True).order_by(
                    "sort_order",
                    "name",
                )
                categories = children if children.exists() else Category.objects.filter(pk=parent.pk)
        return render(
            request,
            "content/partials/category_grid.html",
            {"categories": categories},
        )


class BlogListView(ListView):
    template_name = "content/blog_list.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        return services.published_posts()


class BlogDetailView(DetailView):
    template_name = "content/blog_detail.html"
    context_object_name = "post"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        return services.published_posts()


class ContactsView(View):
    template_name = "content/contacts.html"

    def get(self, request):
        return render(request, self.template_name, {"errors": {}, "form": {}})

    def post(self, request):
        try:
            services.create_contact_lead(
                name=request.POST.get("name", ""),
                phone=request.POST.get("phone", ""),
                message=request.POST.get("message", ""),
                email=request.POST.get("email", ""),
                source_url=request.build_absolute_uri(),
            )
        except services.LeadError as exc:
            errors = exc.args[0] if exc.args else {"form": str(exc)}
            if not isinstance(errors, dict):
                errors = {"form": str(errors)}
            if "__all__" in errors:
                errors["form"] = errors.pop("__all__")
            ctx = {
                "errors": errors,
                "form": {
                    "name": request.POST.get("name", ""),
                    "phone": request.POST.get("phone", ""),
                    "email": request.POST.get("email", ""),
                    "message": request.POST.get("message", ""),
                },
            }
            if _htmx(request):
                return render(request, "content/partials/contact_form.html", ctx, status=400)
            return render(request, self.template_name, ctx, status=400)

        if _htmx(request):
            return render(request, "content/partials/contact_thanks.html")
        return render(request, self.template_name, {"success": True, "errors": {}, "form": {}})

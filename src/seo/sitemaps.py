from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from src.catalog.models import Category, Product
from src.content.models import BlogPost


class StaticSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return [
            "core:home",
            "catalog:list",
            "content:blog_list",
            "content:contacts",
        ]

    def location(self, item):
        return reverse(item)


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.filter(is_active=True)

    def location(self, obj):
        return reverse("catalog:category", kwargs={"slug": obj.slug})


class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse("catalog:product", kwargs={"slug": obj.slug})


class BlogSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return BlogPost.objects.filter(is_published=True, published_at__isnull=False)

    def lastmod(self, obj):
        return obj.published_at

    def location(self, obj):
        return reverse("content:blog_detail", kwargs={"slug": obj.slug})


sitemaps = {
    "static": StaticSitemap,
    "categories": CategorySitemap,
    "products": ProductSitemap,
    "blog": BlogSitemap,
}

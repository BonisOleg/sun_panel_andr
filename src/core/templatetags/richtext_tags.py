from django import template
from django.utils.html import strip_tags

from src.core.richtext import render_richtext

register = template.Library()


@register.filter(name="richtext")
def richtext_filter(value):
    return render_richtext(value or "")


@register.filter(name="plain")
def plain_filter(value):
    return strip_tags(value or "").strip()

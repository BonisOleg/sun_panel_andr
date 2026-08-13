from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Redirect301


@admin.register(Redirect301)
class Redirect301Admin(ModelAdmin):
    list_display = ("old_path", "new_path", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("old_path", "new_path")

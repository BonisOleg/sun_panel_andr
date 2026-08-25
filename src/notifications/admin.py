from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import EmailLog


@admin.register(EmailLog)
class EmailLogAdmin(ModelAdmin):
    list_display = ("kind", "channel", "to_email", "subject", "status", "created_at")
    list_filter = ("kind", "channel", "status")
    search_fields = ("to_email", "subject", "object_id")
    readonly_fields = ("created_at",)

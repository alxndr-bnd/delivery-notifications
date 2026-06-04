from django.contrib import admin

from .models import Notification, OptOut


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("delivery", "kind", "channel", "status", "sent_at", "created_at")
    list_filter = ("kind", "channel", "status")
    search_fields = ("delivery__recipient_name", "provider_message_id")


@admin.register(OptOut)
class OptOutAdmin(admin.ModelAdmin):
    list_display = ("phone", "scope", "created_at")
    search_fields = ("phone",)

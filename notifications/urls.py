from django.urls import path

from .webhooks import infobip_optout, infobip_reports, telegram_webhook

app_name = "notifications"

urlpatterns = [
    path("infobip/reports/", infobip_reports, name="infobip_reports"),
    path("infobip/optout/", infobip_optout, name="infobip_optout"),
    path("telegram/webhook/", telegram_webhook, name="telegram_webhook"),
]

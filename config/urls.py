"""URL configuration for Javi.

Корень `/` и ассеты лендинга отдаёт WhiteNoise (WHITENOISE_ROOT=landing).
Django обслуживает кабинет и служебные пути ниже.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),  # set_language
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("app/", include("deliveries.urls")),
    path("api/v1/", include("deliveries.api_urls")),  # публичный API по ключу
    # Публичная OpenAPI-документация (без логина) — для интеграторов.
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("t/", include("tracking.urls")),  # публичная страница статуса (без логина)
    path("webhooks/", include("notifications.urls")),  # вебхуки Infobip (по секрету)
    path("tasks/", include("tasks.urls")),  # колбэки Cloud Tasks (по секрету)
]

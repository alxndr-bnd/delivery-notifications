"""DRF-аутентификация и throttling по API-ключу магазина.

Ключ читается из `Authorization: Bearer javi_live_…` или `X-Api-Key`. По sha256-хэшу
ищем не отозванный `ApiKey`, обновляем `last_used_at` и возвращаем магазин как
`request.user` (DRF требует «user-подобный» объект; нам важен только `.shop`).
"""

from __future__ import annotations

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework import authentication, exceptions
from rest_framework.throttling import SimpleRateThrottle

from .models import ApiKey, Shop, hash_api_key


def read_api_key(request) -> str | None:
    """Достаёт сырой ключ из `Authorization: Bearer …` или `X-Api-Key`."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[len("Bearer ") :].strip() or None
    x_key = request.headers.get("X-Api-Key", "").strip()
    return x_key or None


def resolve_shop(raw_key: str) -> Shop | None:
    """Сырой ключ → Shop (не отозванный ключ) или None. Обновляет `last_used_at`."""
    try:
        api_key = ApiKey.objects.select_related("shop").get(
            key_hash=hash_api_key(raw_key), revoked_at__isnull=True
        )
    except ApiKey.DoesNotExist:
        return None
    ApiKey.objects.filter(pk=api_key.pk).update(last_used_at=timezone.now())
    return api_key.shop


class ApiKeyAuthentication(authentication.BaseAuthentication):
    """Аутентифицирует запрос по API-ключу магазина.

    Возвращает `(shop, raw_key)` — DRF кладёт `shop` в `request.user`. Если ключ не
    передан, возвращаем None (DRF продолжит цепочку → IsAuthenticated даст 401 единым
    конвертом). Если ключ передан, но невалиден/отозван — 401.
    """

    keyword = "Bearer"

    def authenticate(self, request):
        raw = read_api_key(request)
        if not raw:
            return None
        shop = resolve_shop(raw)
        if shop is None:
            raise exceptions.AuthenticationFailed(_("Missing or invalid API key."))
        return (shop, raw)

    def authenticate_header(self, request):
        # Чтобы DRF отдавал 401 (а не 403) при отсутствии аутентификации.
        return self.keyword


class ApiKeyAuthScheme(OpenApiAuthenticationExtension):
    """Описывает ключевую аутентификацию для OpenAPI-схемы (drf-spectacular)."""

    target_class = "deliveries.auth.ApiKeyAuthentication"
    name = "ApiKeyAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "description": (
                "Shop API key: `Authorization: Bearer javi_live_…` "
                "(or header `X-Api-Key: javi_live_…`)."
            ),
        }


class ApiKeyRateThrottle(SimpleRateThrottle):
    """Rate limit на API-ключ (а не на IP). Лимит — REST_FRAMEWORK throttle rate `api_key`."""

    scope = "api_key"

    def get_cache_key(self, request, view):
        raw = read_api_key(request)
        if not raw:
            return None  # неаутентифицированные не троттлим здесь (их отсечёт 401)
        return self.cache_format % {"scope": self.scope, "ident": hash_api_key(raw)}

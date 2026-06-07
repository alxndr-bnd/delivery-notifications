"""Фабрики провайдеров — единая точка выбора реализации (свап вендора/фейка в тестах)."""

from __future__ import annotations

from django.conf import settings
from django.utils.module_loading import import_string

from .base import MapsProvider, MessagingProvider, RoutesProvider
from .cache import CachingMapsProvider
from .chained import ChainedMessagingProvider
from .metering import MeteringMapsProvider, MeteringMessagingProvider, MeteringRoutesProvider


def _metering_on() -> bool:
    return getattr(settings, "USAGE_METERING_ENABLED", True)


def get_maps_provider() -> MapsProvider:
    """MapsProvider по `settings.MAPS_PROVIDER`. Порядок Caching(Metering(real)) —
    кэш-хит не доходит до счётчика, считаются только реальные вызовы геокодинга."""
    provider = import_string(settings.MAPS_PROVIDER)()
    if _metering_on():
        provider = MeteringMapsProvider(provider)
    return CachingMapsProvider(provider)


def get_routes_provider() -> RoutesProvider:
    """RoutesProvider (ETA) по `settings.ROUTES_PROVIDER`, со счётчиком квоты Maps Routes."""
    provider = import_string(settings.ROUTES_PROVIDER)()
    if _metering_on():
        provider = MeteringRoutesProvider(provider)
    return provider


def _default_chain_paths() -> list[str]:
    """Дефолтная цепочка из legacy-настроек Infobip — повторяет прежнее поведение.

    `INFOBIP_CHANNEL=sms` → только [Sms]; иначе [Viber] + [Sms] если SMS-fallback включён.
    """
    if getattr(settings, "INFOBIP_CHANNEL", "viber") == "sms":
        chain = ["integrations.infobip.SmsProvider"]
    else:
        chain = ["integrations.infobip.ViberProvider"]
        # P2: WhatsApp между Viber и SMS, только когда WHATSAPP_ENABLED (иначе цепочка
        # байт-в-байт прежняя Viber→SMS).
        if getattr(settings, "WHATSAPP_ENABLED", False):
            chain.append("integrations.whatsapp.WhatsAppProvider")
        if getattr(settings, "INFOBIP_SMS_FALLBACK", True):
            chain.append("integrations.infobip.SmsProvider")
    # P3: Telegram — opt-in-only side channel. Само-скипается для не-opted-in номеров,
    # поэтому безопасно ставить ПЕРВЫМ (для остальных проваливается дальше на Viber).
    if getattr(settings, "TELEGRAM_ENABLED", False):
        chain.insert(0, "integrations.telegram.TelegramProvider")
    return chain


def _chain_paths() -> list[str]:
    """Пути провайдеров настроенной цепочки (MESSAGING_CHAIN или дефолт Viber→SMS)."""
    return getattr(settings, "MESSAGING_CHAIN", None) or _default_chain_paths()


def chain_channel_paths() -> list[tuple[str, str]]:
    """[(channel, dotted_path), …] для цепочки. channel — класс-атрибут провайдера,
    читаем без инстанцирования (P4: вычислить следующий неиспробованный канал)."""
    return [(import_string(p).channel, p) for p in _chain_paths()]


def get_messaging_provider_for(paths: list[str]) -> MessagingProvider:
    """Messaging-цепочка из заданного подмножества путей (P4-эскалация), с метерингом."""
    provider = ChainedMessagingProvider([import_string(p)() for p in paths])
    if _metering_on():
        provider = MeteringMessagingProvider(provider)
    return provider


def _build_messaging_chain() -> MessagingProvider:
    """Собирает MessagingProvider из настроек.

    Приоритет: явный одиночный `MESSAGING_PROVIDER` (обратная совместимость / тесты) →
    используется напрямую. Иначе — `ChainedMessagingProvider` из `MESSAGING_CHAIN`
    (или дефолтной цепочки, повторяющей legacy Viber→SMS).
    """
    single = getattr(settings, "MESSAGING_PROVIDER", "")
    if single:
        return import_string(single)()
    paths = getattr(settings, "MESSAGING_CHAIN", None) or _default_chain_paths()
    return ChainedMessagingProvider([import_string(p)() for p in paths])


def get_messaging_provider() -> MessagingProvider:
    """MessagingProvider по настройкам, со счётчиком по фактическому каналу.

    Прод-путь — цепочка одно-канальных провайдеров (`MESSAGING_CHAIN`, дефолт Viber→SMS),
    обёрнутая `MeteringMessagingProvider`. Одиночный `MESSAGING_PROVIDER` имеет приоритет
    (тесты/legacy-свап вендора)."""
    provider = _build_messaging_chain()
    if _metering_on():
        provider = MeteringMessagingProvider(provider)
    return provider

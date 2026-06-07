"""P2: WhatsApp-провайдер (Infobip template) + его место в цепочке.

Отдельный файл (integrations/tests.py трогает другой агент). Транспорт WhatsApp
переиспользует `_InfobipTransport._post`, поэтому HTTP патчим в `integrations.infobip.requests`.
"""

from unittest.mock import patch

import pytest
import requests
from django.test import override_settings

from integrations.metering import MeteringMessagingProvider
from integrations.models import METRIC_SMS, METRIC_VIBER, METRIC_WHATSAPP, ProviderUsage
from integrations.providers import _default_chain_paths, get_messaging_provider
from integrations.whatsapp import WhatsAppProvider


def _ok_response(message_id="wa-1"):
    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"messages": [{"messageId": message_id}]}

    return _Resp()


def _wa(**kwargs):
    base = {
        "base_url": "https://x",
        "api_key": "k",
        "sender": "447860099299",
        "template_name": "delivery_on_the_way",
        "template_lang": "en",
    }
    base.update(kwargs)
    return WhatsAppProvider(**base)


# --- WhatsAppProvider: payload shape & success ---


def test_whatsapp_sends_template_with_placeholder_and_auth():
    """AC: hits template endpoint, App auth, templateName + single body placeholder, to без '+'."""
    with patch("integrations.infobip.requests.post", return_value=_ok_response()) as post:
        result = _wa().send_text("+381641234567", "Vaša porudžbina je krenula")

    assert result.ok and result.channel == "whatsapp"
    assert result.provider_message_id == "wa-1"

    url = post.call_args.args[0]
    assert url.endswith("/whatsapp/1/message/template")
    assert post.call_args.kwargs["headers"]["Authorization"] == "App k"

    msg = post.call_args.kwargs["json"]["messages"][0]
    assert msg["from"] == "447860099299"
    assert msg["to"] == "381641234567"  # без «+»
    content = msg["content"]
    assert content["templateName"] == "delivery_on_the_way"
    assert content["language"] == "en"
    assert content["templateData"]["body"]["placeholders"] == ["Vaša porudžbina je krenula"]


def test_whatsapp_single_channel_no_attempts():
    """Одно-канальный провайдер: attempts пуст."""
    with patch("integrations.infobip.requests.post", return_value=_ok_response()):
        result = _wa().send_text("+381641234567", "hi")
    assert result.attempts == ()


# --- Soft-fail behavior ---


def test_whatsapp_soft_fails_on_network_error():
    """Сетевая ошибка → ok=False (без исключения), channel пуст — цепочка упадёт в SMS."""
    with patch(
        "integrations.infobip.requests.post",
        side_effect=requests.RequestException("wa down"),
    ):
        result = _wa().send_text("+381641234567", "hi")
    assert result.ok is False and result.channel == ""


def test_whatsapp_soft_fails_on_bad_json():
    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            raise ValueError("no json")

    with patch("integrations.infobip.requests.post", return_value=_Resp()):
        result = _wa().send_text("+381641234567", "hi")
    assert result.ok is False


def test_whatsapp_soft_fails_on_missing_config():
    """Нет ключа / sender / шаблона → ok=False без HTTP-вызова."""
    with patch("integrations.infobip.requests.post") as post:
        assert _wa(api_key="").send_text("+381", "x").ok is False
        assert _wa(sender="").send_text("+381", "x").ok is False
        assert _wa(template_name="").send_text("+381", "x").ok is False
    assert post.call_count == 0


# --- Chain wiring (gated by WHATSAPP_ENABLED) ---


@override_settings(INFOBIP_CHANNEL="viber", INFOBIP_SMS_FALLBACK=True, WHATSAPP_ENABLED=True)
def test_default_chain_includes_whatsapp_between_viber_and_sms_when_enabled():
    assert _default_chain_paths() == [
        "integrations.infobip.ViberProvider",
        "integrations.whatsapp.WhatsAppProvider",
        "integrations.infobip.SmsProvider",
    ]


@override_settings(INFOBIP_CHANNEL="viber", INFOBIP_SMS_FALLBACK=True, WHATSAPP_ENABLED=False)
def test_default_chain_unchanged_when_whatsapp_disabled():
    assert _default_chain_paths() == [
        "integrations.infobip.ViberProvider",
        "integrations.infobip.SmsProvider",
    ]


@override_settings(
    INFOBIP_BASE_URL="https://x",
    INFOBIP_API_KEY="k",
    INFOBIP_SENDER="S",
    INFOBIP_CHANNEL="viber",
    INFOBIP_SMS_FALLBACK=True,
    WHATSAPP_ENABLED=True,
    WHATSAPP_SENDER="447860099299",
    WHATSAPP_TEMPLATE_NAME="delivery_on_the_way",
    MESSAGING_PROVIDER="",
    MESSAGING_CHAIN=[],
    USAGE_METERING_ENABLED=False,
)
def test_real_chain_viber_fail_falls_through_to_whatsapp():
    """Реальная цепочка через фабрику: Viber падает → WhatsApp выигрывает (до SMS не доходит)."""

    def _side_effect(url, **kwargs):
        if url.endswith("/viber/2/messages"):
            raise requests.RequestException("viber down")
        return _ok_response(message_id="wa-1")

    with patch("integrations.infobip.requests.post", side_effect=_side_effect) as post:
        result = get_messaging_provider().send_text("+381641234567", "hi")

    assert result.ok and result.channel == "whatsapp"
    assert tuple((a.channel, a.ok) for a in result.attempts) == (
        ("viber", False),
        ("whatsapp", True),
    )
    # SMS не вызывался (WhatsApp выиграл).
    urls = [c.args[0] for c in post.call_args_list]
    assert not any(u.endswith("/sms/2/text/advanced") for u in urls)


# --- Metering ---


@pytest.mark.django_db
@override_settings(
    INFOBIP_BASE_URL="https://x",
    INFOBIP_API_KEY="k",
    INFOBIP_SENDER="S",
    INFOBIP_CHANNEL="viber",
    INFOBIP_SMS_FALLBACK=True,
    WHATSAPP_ENABLED=True,
    WHATSAPP_SENDER="447860099299",
    WHATSAPP_TEMPLATE_NAME="delivery_on_the_way",
    MESSAGING_PROVIDER="",
    MESSAGING_CHAIN=[],
)
def test_metering_counts_successful_whatsapp_send():
    """Метеринг считает победивший whatsapp-канал, не проигравший viber, и не sms."""

    def _side_effect(url, **kwargs):
        if url.endswith("/viber/2/messages"):
            raise requests.RequestException("viber down")
        return _ok_response(message_id="wa-1")

    with patch("integrations.infobip.requests.post", side_effect=_side_effect):
        result = get_messaging_provider().send_text("+381641234567", "hi")

    assert result.ok and result.channel == "whatsapp"
    assert ProviderUsage.objects.get(metric=METRIC_WHATSAPP).count == 1
    assert not ProviderUsage.objects.filter(metric=METRIC_VIBER).exists()
    assert not ProviderUsage.objects.filter(metric=METRIC_SMS).exists()


@pytest.mark.django_db
def test_metering_counts_whatsapp_via_wrapper_directly():
    """Прямой провайдер под MeteringMessagingProvider считает whatsapp при успехе."""
    with patch("integrations.infobip.requests.post", return_value=_ok_response()):
        MeteringMessagingProvider(_wa()).send_text("+381641234567", "hi")
    assert ProviderUsage.objects.get(metric=METRIC_WHATSAPP).count == 1

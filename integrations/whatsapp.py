"""Одно-канальный WhatsApp-провайдер поверх Infobip (шаблонные сообщения).

WhatsApp business-initiated сообщения требуют ПРЕДОДОБРЕННЫЙ Utility-шаблон (не свободный
текст). Отправляем через Infobip WhatsApp template endpoint, подставляя runtime-`text`
единственным body-placeholder (предполагается шаблон с одной переменной `{{1}}`).

Транспорт (auth/_post) переиспользуем из `_InfobipTransport` (см. infobip.py). Мягкая
деградация: сетевая/JSON-ошибка либо отсутствие ключа/sender/шаблона → ok=False (без
исключения), чтобы `ChainedMessagingProvider` упал в следующий канал (SMS).
"""

from __future__ import annotations

import logging

from django.conf import settings

from .base import MessagingProvider, SendResult
from .infobip import _InfobipTransport

logger = logging.getLogger(__name__)


class WhatsAppProvider(_InfobipTransport, MessagingProvider):
    """Шлёт ТОЛЬКО WhatsApp через Infobip template endpoint, channel=whatsapp."""

    channel = "whatsapp"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        sender: str | None = None,
        template_name: str | None = None,
        template_lang: str | None = None,
        timeout: int | None = None,
    ) -> None:
        kwargs = {} if timeout is None else {"timeout": timeout}
        super().__init__(base_url=base_url, api_key=api_key, **kwargs)
        # sender тут — WhatsApp-номер отправителя (WHATSAPP_SENDER), а не INFOBIP_SENDER;
        # ставим ПОСЛЕ super(), чтобы `or INFOBIP_SENDER` транспорта не подменял пустой WA-sender.
        self.sender = sender if sender is not None else settings.WHATSAPP_SENDER
        self.template_name = (
            template_name if template_name is not None else settings.WHATSAPP_TEMPLATE_NAME
        )
        self.template_lang = (
            template_lang if template_lang is not None else settings.WHATSAPP_TEMPLATE_LANG
        )

    def send_text(self, to_e164: str, text: str) -> SendResult:
        if not self.api_key or not self.sender or not self.template_name:
            logger.error("WhatsApp не сконфигурирован (key/sender/template) — отправка отключена")
            return SendResult(ok=False)
        to = to_e164.lstrip("+")  # Infobip ожидает номер без «+»
        message = {
            "from": self.sender,
            "to": to,
            "content": {
                "templateName": self.template_name,
                "templateData": {"body": {"placeholders": [text]}},
                "language": self.template_lang,
            },
        }
        ok, mid = self._post(
            f"{self.base_url}/whatsapp/1/message/template", {"messages": [message]}
        )
        return SendResult(ok=ok, provider_message_id=mid, channel="whatsapp" if ok else "")

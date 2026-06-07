"""P3 — Telegram bot webhook: захват opt-in (shared contact → TelegramContact)."""

from __future__ import annotations

import json

import pytest
from django.test import Client, override_settings
from django.urls import reverse

from notifications.models import TelegramContact

pytestmark = pytest.mark.django_db

SECRET = "tg-secret"
URL = reverse("notifications:telegram_webhook")


def _post(body: dict, *, secret=SECRET):
    headers = {}
    if secret is not None:
        headers["HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN"] = secret
    return Client().post(
        URL, data=json.dumps(body), content_type="application/json", **headers
    )


def _shared_contact_update(phone="+381641234567", chat_id=555):
    return {
        "update_id": 1,
        "message": {
            "chat": {"id": chat_id},
            "contact": {"phone_number": phone, "user_id": chat_id},
        },
    }


@override_settings(TELEGRAM_WEBHOOK_SECRET=SECRET)
def test_shared_contact_upserts_telegram_contact():
    resp = _post(_shared_contact_update(phone="0641234567", chat_id=555))
    assert resp.status_code == 200
    contact = TelegramContact.objects.get(chat_id="555")
    assert contact.phone == "+381641234567"  # normalized to E.164


@override_settings(TELEGRAM_WEBHOOK_SECRET=SECRET)
def test_upsert_updates_existing_chat_id():
    TelegramContact.objects.create(phone="+381641234567", chat_id="111")
    resp = _post(_shared_contact_update(phone="+381641234567", chat_id=999))
    assert resp.status_code == 200
    assert TelegramContact.objects.count() == 1
    assert TelegramContact.objects.get(phone="+381641234567").chat_id == "999"


@override_settings(TELEGRAM_WEBHOOK_SECRET=SECRET)
def test_wrong_secret_rejected():
    resp = _post(_shared_contact_update(), secret="nope")
    assert resp.status_code == 403
    assert TelegramContact.objects.count() == 0


@override_settings(TELEGRAM_WEBHOOK_SECRET=SECRET)
def test_missing_secret_rejected():
    resp = _post(_shared_contact_update(), secret=None)
    assert resp.status_code == 403
    assert TelegramContact.objects.count() == 0


@override_settings(TELEGRAM_WEBHOOK_SECRET="")
def test_empty_configured_secret_rejects_all():
    resp = _post(_shared_contact_update(), secret="")
    assert resp.status_code == 403


@override_settings(TELEGRAM_WEBHOOK_SECRET=SECRET)
def test_unrelated_update_ignored():
    resp = _post({"update_id": 2, "message": {"chat": {"id": 7}, "text": "/help"}})
    assert resp.status_code == 200
    assert TelegramContact.objects.count() == 0


@override_settings(TELEGRAM_WEBHOOK_SECRET=SECRET)
def test_invalid_phone_ignored():
    resp = _post(_shared_contact_update(phone="not-a-number", chat_id=3))
    assert resp.status_code == 200
    assert TelegramContact.objects.count() == 0

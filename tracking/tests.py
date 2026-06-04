from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.utils import timezone

from deliveries.models import Delivery, Shop, TrackingToken

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


def _token(status=Delivery.Status.ON_THE_WAY, *, eta_minutes=20, city="Beograd"):
    user = get_user_model().objects.create_user(email="t@shop.rs", password="pass12345")
    shop = Shop.objects.create(owner=user, name="Pizza Napoli")
    delivery = Delivery.objects.create(
        shop=shop,
        recipient_name="Ana",
        recipient_phone="+381641234567",
        dest_address="Tajna adresa 5, Beograd",
        dest_city=city,
        status=status,
        eta_at=timezone.now() + timedelta(minutes=eta_minutes) if eta_minutes else None,
    )
    return TrackingToken.objects.create(delivery=delivery)


def test_on_the_way_shows_eta_city_no_private_data(client):
    """AC#1/#3: статус U dostavi → ETA + город; без телефона/полного адреса."""
    token = _token(Delivery.Status.ON_THE_WAY)
    body = client.get(f"/t/{token.token}/").content.decode()
    assert "Pizza Napoli" in body
    assert "Stiže okvirno do" in body
    assert "Beograd" in body
    # степпер всегда рендерится целиком
    assert "Primljeno" in body and "U dostavi" in body and "Isporučeno" in body
    assert "+381641234567" not in body
    assert "Tajna adresa" not in body


def test_created_step_primljeno(client):
    token = _token(Delivery.Status.CREATED, eta_minutes=0)
    body = client.get(f"/t/{token.token}/").content.decode()
    assert "Porudžbina je primljena" in body


def test_delivered_step(client):
    token = _token(Delivery.Status.DELIVERED, eta_minutes=0)
    body = client.get(f"/t/{token.token}/").content.decode()
    assert "isporučena" in body


def test_unknown_token_404(client):
    assert client.get("/t/nonexistent-token/").status_code == 404


def test_expired_link_410(client):
    token = _token()
    token.expires_at = timezone.now() - timedelta(hours=1)
    token.save()
    resp = client.get(f"/t/{token.token}/")
    assert resp.status_code == 410
    assert "istekao" in resp.content.decode()


@override_settings(TRACKING_RATE_LIMIT=2)
def test_rate_limit_429(client):
    """AC#5: сверх лимита запросов с одного IP → 429."""
    token = _token()
    url = f"/t/{token.token}/"
    assert client.get(url, REMOTE_ADDR="9.9.9.9").status_code == 200
    assert client.get(url, REMOTE_ADDR="9.9.9.9").status_code == 200
    assert client.get(url, REMOTE_ADDR="9.9.9.9").status_code == 429

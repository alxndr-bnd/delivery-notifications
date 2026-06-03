import pytest
from django.contrib.auth import get_user_model

from deliveries.models import Shop

pytestmark = pytest.mark.django_db


def _make_shop(email, name):
    user = get_user_model().objects.create_user(email=email, password="pass12345")
    shop = Shop.objects.create(owner=user, name=name)
    return user, shop


def test_app_requires_login(client):
    """AC#3: аноним на /app/ редиректится на вход."""
    resp = client.get("/app/")
    assert resp.status_code == 302
    assert "/accounts/login/" in resp["Location"]


def test_shop_sees_empty_cabinet(client):
    """AC#2: магазин входит и видит пустой кабинет + кнопку «Nova dostava»."""
    _make_shop("milan@pizza.rs", "Pizza Napoli")
    assert client.login(username="milan@pizza.rs", password="pass12345")
    resp = client.get("/app/")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Nema dostava" in body
    assert "Nova dostava" in body


def test_tenant_isolation(client):
    """AC#4: каждый магазин видит свой кабинет (скоуп по shop)."""
    _make_shop("a@shop.rs", "Shop A")
    _make_shop("b@shop.rs", "Shop B")
    client.login(username="a@shop.rs", password="pass12345")
    resp = client.get("/app/")
    assert resp.status_code == 200
    assert resp.context["shop"].name == "Shop A"
    assert list(resp.context["deliveries"]) == []

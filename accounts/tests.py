import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from deliveries.models import Shop

pytestmark = pytest.mark.django_db


def test_create_shop_command():
    """AC#1/#2: команда create_shop заводит пользователя и магазин."""
    call_command(
        "create_shop",
        email="milan@pizza.rs",
        password="pass12345",
        name="Pizza Napoli",
    )
    user = get_user_model().objects.get(email="milan@pizza.rs")
    assert user.check_password("pass12345")
    assert Shop.objects.get(owner=user).name == "Pizza Napoli"


def test_email_login(client):
    """AC#2: вход по email + паролю."""
    call_command("create_shop", email="a@shop.rs", password="pass12345", name="A")
    assert client.login(username="a@shop.rs", password="pass12345")

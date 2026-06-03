from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from deliveries.models import Shop


class Command(BaseCommand):
    help = "Создать магазин: пользователя (email+пароль) и связанный Shop."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--name", required=True, help="Название магазина")

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()
        email = options["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise CommandError(f"Пользователь {email} уже существует")
        user = User.objects.create_user(email=email, password=options["password"])
        shop = Shop.objects.create(owner=user, name=options["name"])
        self.stdout.write(self.style.SUCCESS(f"Создан магазин «{shop.name}» ({email})"))

from django.conf import settings
from django.db import models


class Shop(models.Model):
    """Магазин — арендатор Javi. 1:1 с пользователем."""

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shop",
    )
    name = models.CharField("название", max_length=200)

    # origin (адрес магазина) — точка отсчёта ETA. Заполняется в Story 1.2.
    origin_address = models.CharField("адрес магазина", max_length=300, blank=True)
    origin_lat = models.FloatField("широта", null=True, blank=True)
    origin_lng = models.FloatField("долгота", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

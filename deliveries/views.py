from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class DeliveryListView(LoginRequiredMixin, TemplateView):
    """Кабинет магазина: список доставок дня (в 1.1 — пустой, скоуплен по магазину)."""

    template_name = "deliveries/delivery_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        shop = getattr(self.request.user, "shop", None)
        # Изоляция арендаторов: показываем только доставки текущего магазина.
        # Модель Delivery появится в Story 1.3 — пока список пуст.
        ctx["shop"] = shop
        ctx["deliveries"] = []
        return ctx

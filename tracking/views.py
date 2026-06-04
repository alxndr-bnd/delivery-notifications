from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from common.timewindow import format_eta
from deliveries.models import Delivery, TrackingToken

# Порядок шагов степпера и какой статус доставки на каком шаге.
_STEPS = [
    ("Primljeno", Delivery.Status.CREATED),
    ("U dostavi", Delivery.Status.ON_THE_WAY),
    ("Isporučeno", Delivery.Status.DELIVERED),
]


def _stepper(status: str) -> list[dict]:
    """Список шагов с состояниями done/active/future для серверного рендера."""
    order = [s for _, s in _STEPS]
    current = order.index(status) if status in order else 0
    steps = []
    for idx, (label, _s) in enumerate(_STEPS):
        state = "done" if idx < current else "active" if idx == current else "future"
        steps.append({"label": label, "state": state})
    return steps


def _rate_limited(request) -> bool:
    """Простой лимитер по IP на Django cache (окно 60 c)."""
    ip = request.META.get("REMOTE_ADDR", "") or "unknown"
    key = f"track_rl:{ip}"
    count = cache.get(key, 0)
    if count >= settings.TRACKING_RATE_LIMIT:
        return True
    cache.set(key, count + 1, timeout=60)
    return False


def status(request, token):
    """Публичная брендовая страница статуса (без логина). Минимум данных (NFR-3)."""
    if _rate_limited(request):
        return HttpResponse("Previše zahteva. Pokušajte kasnije.", status=429)

    token_obj = get_object_or_404(TrackingToken, token=token)
    if token_obj.expires_at and token_obj.expires_at < timezone.now():
        return render(request, "tracking/status.html", {"expired": True}, status=410)

    delivery = token_obj.delivery
    ctx = {
        "shop_name": delivery.shop.name,
        "status": delivery.status,
        "steps": _stepper(delivery.status),
        "dest_city": delivery.dest_city,
        "eta": format_eta(delivery.eta_at) if delivery.eta_at else None,
    }
    return render(request, "tracking/status.html", ctx)

"""Защищённые колбэки Cloud Tasks (HTTP). Здесь — отправка запроса оценки."""

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from deliveries.models import Delivery
from deliveries.services import send_rating_request


@csrf_exempt
def send_rating(request, delivery_id):
    """POST от Cloud Tasks по ETA+30 → запрос оценки. Защита — общий секрет (fail-closed)."""
    secret = request.GET.get("secret") or request.headers.get("X-Tasks-Secret", "")
    if not settings.TASKS_SECRET or secret != settings.TASKS_SECRET:
        return HttpResponseForbidden("forbidden")
    delivery = get_object_or_404(Delivery, pk=delivery_id)
    send_rating_request(delivery)  # идемпотентно
    return HttpResponse(status=200)

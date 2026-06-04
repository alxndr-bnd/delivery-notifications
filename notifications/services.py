"""Блоклист отписки (OptOut)."""

from __future__ import annotations

from .models import OptOut


def opt_out(phone: str) -> None:
    """Добавляет номер в блоклист (идемпотентно)."""
    if phone:
        OptOut.objects.get_or_create(phone=phone)


def is_opted_out(phone: str) -> bool:
    return bool(phone) and OptOut.objects.filter(phone=phone).exists()

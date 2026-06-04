"""Отложенные задачи через Cloud Tasks (scheduleTime). Абстракция + Noop + Cloud Tasks."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime

from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger(__name__)


class TaskScheduler(ABC):
    @abstractmethod
    def schedule_rating_request(self, delivery_id: int, run_at: datetime) -> None:
        """Запланировать отправку запроса оценки на run_at (aware-datetime)."""
        raise NotImplementedError


class NoopTaskScheduler(TaskScheduler):
    """Локальный/дефолтный планировщик: ничего не ставит, только логирует."""

    def schedule_rating_request(self, delivery_id: int, run_at: datetime) -> None:
        logger.info("Noop schedule rating for delivery %s at %s", delivery_id, run_at)


class CloudTasksScheduler(TaskScheduler):
    """Cloud Tasks: HTTP-задача POST на колбэк с scheduleTime (lazy-import библиотеки)."""

    def schedule_rating_request(self, delivery_id: int, run_at: datetime) -> None:
        from google.cloud import tasks_v2  # lazy: нужна только в проде
        from google.protobuf import timestamp_pb2

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(
            settings.CLOUD_TASKS_PROJECT,
            settings.CLOUD_TASKS_LOCATION,
            settings.CLOUD_TASKS_QUEUE,
        )
        url = (
            f"{settings.CLOUD_TASKS_SERVICE_URL.rstrip('/')}"
            f"/tasks/send-rating/{delivery_id}/?secret={settings.TASKS_SECRET}"
        )
        ts = timestamp_pb2.Timestamp()
        ts.FromDatetime(run_at)
        client.create_task(
            request={
                "parent": parent,
                "task": {
                    "http_request": {
                        "http_method": tasks_v2.HttpMethod.POST,
                        "url": url,
                    },
                    "schedule_time": ts,
                },
            }
        )
        logger.info("Scheduled rating for delivery %s at %s", delivery_id, run_at)


def get_task_scheduler() -> TaskScheduler:
    return import_string(settings.TASK_SCHEDULER)()

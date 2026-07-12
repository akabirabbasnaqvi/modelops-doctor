from celery import Celery
from celery.schedules import crontab

from app.core.config import settings


celery_app = Celery(
    "modelops_doctor",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,
)

celery_app.conf.beat_schedule = {
    "scheduled-health-check-dispatch": {
        "task": "app.workers.tasks.dispatch_scheduled_health_checks",
        "schedule": crontab(hour=2, minute=0),
    }
}

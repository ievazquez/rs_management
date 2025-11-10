"""
Configuración de Celery
"""
from celery import Celery
from ..config import settings

# Crear aplicación Celery
celery_app = Celery(
    "social_media_manager",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.celery_tasks"]
)

# Configuración de Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Configurar tareas periódicas
celery_app.conf.beat_schedule = {
    "check-scheduled-posts-every-minute": {
        "task": "app.tasks.celery_tasks.check_scheduled_posts",
        "schedule": 60.0,  # Cada 60 segundos
    },
}

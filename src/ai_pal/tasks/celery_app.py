"""
Celery Application Configuration

Configures Celery for distributed task processing with:
- Redis broker and result backend
- Task routing and priority
- Retry logic and timeouts
- Task monitoring and logging
"""

import os
from celery import Celery
from kombu import Exchange, Queue
from loguru import logger

# Create Celery app
app = Celery("ai_pal")

# Load configuration from environment or use defaults
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Configure Celery
app.conf.update(
    # Broker settings
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,

    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task settings
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit

    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,

    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,

    # Queue settings
    task_default_queue="default",
    task_default_exchange="tasks",
    task_default_exchange_type="direct",
    task_default_routing_key="default",

    # Define task queues with priorities
    task_queues=(
        Queue("default", Exchange("tasks"), routing_key="default", queue_arguments={"x-max-priority": 10}),
        Queue("ari_analysis", Exchange("tasks"), routing_key="ari_analysis", queue_arguments={"x-max-priority": 10}),
        Queue("ffe_planning", Exchange("tasks"), routing_key="ffe_planning", queue_arguments={"x-max-priority": 10}),
        Queue("edm_analysis", Exchange("tasks"), routing_key="edm_analysis", queue_arguments={"x-max-priority": 10}),
        Queue("model_training", Exchange("tasks"), routing_key="model_training", queue_arguments={"x-max-priority": 10}),
        Queue("maintenance", Exchange("tasks"), routing_key="maintenance", queue_arguments={"x-max-priority": 5}),
    ),

    # Task routing
    task_routes={
        "ai_pal.tasks.ari_tasks.*": {"queue": "ari_analysis", "routing_key": "ari_analysis"},
        "ai_pal.tasks.ffe_tasks.*": {"queue": "ffe_planning", "routing_key": "ffe_planning"},
        "ai_pal.tasks.edm_tasks.*": {"queue": "edm_analysis", "routing_key": "edm_analysis"},
        "ai_pal.tasks.model_tasks.*": {"queue": "model_training", "routing_key": "model_training"},
        "ai_pal.tasks.maintenance_tasks.*": {"queue": "maintenance", "routing_key": "maintenance"},
    },
)

# Auto-discover tasks from task modules
app.autodiscover_tasks([
    "ai_pal.tasks.ari_tasks",
    "ai_pal.tasks.ffe_tasks",
    "ai_pal.tasks.edm_tasks",
    "ai_pal.tasks.model_tasks",
    "ai_pal.tasks.maintenance_tasks",
])

logger.info(f"Celery app configured with broker: {CELERY_BROKER_URL}")

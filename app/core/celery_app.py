from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "lazarus_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Optional configuration, see the application user guide.
celery_app.conf.update(
    result_expires=3600,
    # Upstash Redis configuration (SSL support)
    broker_use_ssl={'ssl_cert_reqs': 'none'} if 'rediss://' in settings.REDIS_URL else None,
    redis_backend_use_ssl={'ssl_cert_reqs': 'none'} if 'rediss://' in settings.REDIS_URL else None,
)

# Auto-discover tasks from these modules
celery_app.autodiscover_tasks(['app.tasks.chat_tasks'])

if __name__ == '__main__':
    celery_app.start()

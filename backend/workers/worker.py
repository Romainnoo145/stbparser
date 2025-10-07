"""
Background worker for processing sync jobs from Redis queue.

Uses Celery for task management with Redis as broker and backend.
"""

import asyncio
from celery import Celery
from loguru import logger

from backend.services.proposal_sync import process_proposal_sync
from backend.core.settings import settings

# Configure Celery app
celery_app = Celery(
    "offorte_sync_worker",
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Amsterdam",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
)


@celery_app.task(bind=True, max_retries=3)
def sync_proposal_task(self, proposal_id: int):
    """
    Background task to sync proposal from Offorte to Airtable.

    Args:
        self: Celery task instance
        proposal_id: Offorte proposal ID

    Returns:
        Sync result dictionary
    """
    job_id = self.request.id
    logger.info(f"Starting sync task {job_id} for proposal {proposal_id}")

    try:
        # Run async code in sync context
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            process_proposal_sync(proposal_id=proposal_id, job_id=job_id)
        )

        if result.get("success"):
            logger.info(f"Task {job_id} completed successfully")
        else:
            logger.warning(f"Task {job_id} completed with errors: {result.get('errors')}")

        return result

    except Exception as exc:
        logger.error(f"Task {job_id} failed: {exc}")

        # Retry with exponential backoff
        countdown = 2 ** self.request.retries  # 2s, 4s, 8s
        logger.info(f"Retrying task {job_id} in {countdown} seconds (attempt {self.request.retries + 1}/3)")

        raise self.retry(exc=exc, countdown=countdown)


# Celery beat schedule (optional - for periodic tasks)
celery_app.conf.beat_schedule = {
    # Example: reconciliation task
    # "daily-reconciliation": {
    #     "task": "worker.reconcile_syncs",
    #     "schedule": crontab(hour=2, minute=0),
    # },
}


if __name__ == "__main__":
    # Run worker: celery -A worker worker --loglevel=info
    celery_app.start()

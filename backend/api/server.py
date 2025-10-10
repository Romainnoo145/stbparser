"""
FastAPI webhook server for receiving Offorte events.

CRITICAL: Must respond within 5 seconds to avoid timeout.
"""

import json
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from loguru import logger
import redis.asyncio as redis

from backend.core.settings import settings
from backend.agent.tools import validate_webhook
from backend.workers.worker import sync_proposal_task

app = FastAPI(
    title="Offorte-Airtable Sync Server",
    description="Webhook receiver for Offorte proposal events",
    version="1.0.0"
)

# Global Redis client
redis_client = None


@app.on_event("startup")
async def startup():
    """Initialize Redis connection on startup."""
    global redis_client
    logger.info(f"Connecting to Redis at {settings.redis_url}")
    redis_client = await redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    logger.info("Redis connection established")


@app.on_event("shutdown")
async def shutdown():
    """Close Redis connection on shutdown."""
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Offorte-Airtable Sync",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    redis_status = "connected" if redis_client else "disconnected"
    return {
        "status": "healthy",
        "redis": redis_status,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/webhook/offorte")
async def receive_webhook(request: Request):
    """
    Receive Offorte webhook and queue for processing.

    CRITICAL: Must respond < 5 seconds.

    Returns:
        200 OK immediately after queueing job
    """
    try:
        # Parse payload
        payload = await request.json()

        # Log the raw webhook data for debugging
        logger.info(f"Raw webhook payload: {json.dumps(payload, indent=2)}")
        logger.info(f"Headers: {dict(request.headers)}")

        # Extract event type and proposal ID from Offorte payload format
        # Format: {"type": "proposal_won", "date_created": "...", "data": {...}}
        event_type = payload.get("type", "")
        proposal_data = payload.get("data", {})
        proposal_id = proposal_data.get("id")

        if not proposal_id:
            logger.error("No proposal ID in webhook payload")
            raise HTTPException(status_code=400, detail="Missing proposal ID")

        # Convert proposal_id to int if it's a string
        try:
            proposal_id = int(proposal_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid proposal ID format: {proposal_id}")
            raise HTTPException(status_code=400, detail="Invalid proposal ID")

        logger.info(f"Received webhook: event={event_type}, proposal={proposal_id}")

        # Queue for background processing (only for proposal_won events)
        if event_type == "proposal_won":
            # Trigger Celery task directly
            task = sync_proposal_task.delay(proposal_id)
            logger.info(f"Triggered Celery task {task.id} for proposal {proposal_id}")

            return {
                "status": "accepted",
                "proposal_id": proposal_id,
                "task_id": task.id,
                "queued": True
            }

        # Acknowledge other event types without processing
        return {
            "status": "acknowledged",
            "event_type": event_type,
            "queued": False
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/queue/status")
async def queue_status():
    """Check Redis queue status."""
    try:
        queue_length = await redis_client.llen("sync_queue")
        return {
            "queue_length": queue_length,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Queue status error: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.server_host,
        port=settings.server_port,
        log_level=settings.log_level.lower()
    )

import logging
import json
from typing import Dict, Any, Optional
from arq import create_pool
from arq.connections import RedisSettings, ArqRedis
from fastapi import BackgroundTasks

from app.core.config import settings
from app.worker import run_trace_job

logger = logging.getLogger("chainnetra.services.queue")

_arq_pool: Optional[ArqRedis] = None

async def get_arq_pool() -> Optional[ArqRedis]:
    global _arq_pool
    if _arq_pool is not None:
        return _arq_pool
    try:
        redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
        _arq_pool = await create_pool(redis_settings)
        return _arq_pool
    except Exception as e:
        logger.warning(f"Could not connect to Redis for arq queue ({e}). Running in synchronous/background task fallback mode.")
        return None

async def enqueue_trace_job(
    case_id: int,
    job_id: str,
    params: Dict[str, Any],
    actor_email: str,
    background_tasks: Optional[BackgroundTasks] = None,
    db: Optional[Any] = None
) -> str:
    """
    Enqueues a trace job to arq Redis pool if available,
    otherwise falls back to FastAPI BackgroundTasks for local/test environments.
    """
    pool = await get_arq_pool()
    if pool is not None:
        try:
            await pool.enqueue_job("run_trace_job", case_id, job_id, params, actor_email, _job_id=job_id)
            logger.info(f"Enqueued trace job {job_id} to arq Redis queue")
            return "queued"
        except Exception as e:
            logger.warning(f"Failed to enqueue to arq ({e}). Falling back to local BackgroundTasks.")

    if background_tasks is not None:
        ctx = {"db": db} if db is not None else {}
        background_tasks.add_task(run_trace_job, ctx, case_id, job_id, params, actor_email)
        logger.info(f"Scheduled trace job {job_id} via local BackgroundTasks")
        return "queued"

    return "queued"

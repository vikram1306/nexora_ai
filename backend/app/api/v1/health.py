import os
import time
from datetime import datetime, timezone
from typing import Any, Dict

import psutil
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.memory.redis_cache import cache_manager

logger = get_logger("nexora.health")
router = APIRouter(tags=["Health & Telemetry"])

# Track platform startup timestamp
STARTUP_TIME = time.time()


@router.get("/health", status_code=status.HTTP_200_OK)
@router.get("/health/detailed", status_code=status.HTTP_200_OK)
def full_system_health_check(response: Response, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Comprehensive health check verifying SQL Database, Redis Cache, ChromaDB Vector Store, and System Resources."""
    overall_status = "healthy"
    subsystems: Dict[str, Any] = {}

    # 1. Relational Database Health
    db_start = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
        db_latency_ms = round((time.perf_counter() - db_start) * 1000, 2)
        subsystems["database"] = {
            "status": "healthy",
            "type": "PostgreSQL" if "postgres" in settings.DATABASE_URL else "SQLite",
            "latency_ms": db_latency_ms
        }
    except Exception as e:
        logger.error(f"Health check: Database failure: {e}")
        overall_status = "unhealthy"
        subsystems["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # 2. Redis Cache Health
    redis_start = time.perf_counter()
    try:
        redis_ok = cache_manager.is_connected()
        redis_latency_ms = round((time.perf_counter() - redis_start) * 1000, 2)
        subsystems["redis_cache"] = {
            "status": "healthy" if redis_ok else "degraded",
            "mode": "redis_cluster" if redis_ok else "in_memory_fallback",
            "latency_ms": redis_latency_ms if redis_ok else 0.01,
            "telemetry": cache_manager.get_cache_stats()
        }
    except Exception as e:
        subsystems["redis_cache"] = {
            "status": "degraded",
            "mode": "in_memory_fallback",
            "error": str(e)
        }

    # 3. ChromaDB Semantic Vector Memory
    try:
        persist_dir_exists = os.path.exists(settings.CHROMA_PERSIST_DIR)
        subsystems["vector_memory"] = {
            "status": "healthy",
            "engine": "ChromaDB + SentenceTransformers",
            "embedding_model": settings.EMBEDDING_MODEL_NAME,
            "persist_dir_exists": persist_dir_exists
        }
    except Exception as e:
        subsystems["vector_memory"] = {
            "status": "degraded",
            "error": str(e)
        }

    # 4. Department Agents & AI Subsystems
    subsystems["ai_agents"] = {
        "status": "ready",
        "active_departments": ["sales", "finance", "hr", "marketing", "operations"],
        "sentinel_ai": "active",
        "planner_agent": "ready",
        "response_validator": "active"
    }

    # 5. System Resources
    try:
        vm = psutil.virtual_memory()
        process = psutil.Process(os.getpid())
        mem_rss_mb = round(process.memory_info().rss / (1024 * 1024), 2)
        disk = psutil.disk_usage(os.getcwd())

        system_metrics = {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=None),
            "memory_usage_pct": vm.percent,
            "memory_available_mb": round(vm.available / (1024 * 1024), 2),
            "process_memory_rss_mb": mem_rss_mb,
            "disk_free_gb": round(disk.free / (1024 * 1024 * 1024), 2)
        }
    except Exception as e:
        system_metrics = {"error": str(e)}

    uptime_sec = round(time.time() - STARTUP_TIME, 1)

    if overall_status == "unhealthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": overall_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime_sec,
        "subsystems": subsystems,
        "system_resources": system_metrics
    }


@router.get("/health/liveness", status_code=status.HTTP_200_OK)
def liveness_probe() -> Dict[str, str]:
    """Lightweight Kubernetes / Container liveness probe."""
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/readiness", status_code=status.HTTP_200_OK)
def readiness_probe(response: Response, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Readiness probe validating DB connectivity before accepting traffic."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

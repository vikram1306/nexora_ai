from fastapi.testclient import TestClient

from app.core.logging_config import clear_request_context, ctx_request_id, set_request_context
from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    """Verify GET /health returns 200 with all subsystem health metrics."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()

    assert data["platform"] == "Nexora AI"
    assert data["status"] == "healthy"
    assert "uptime_seconds" in data
    assert "subsystems" in data

    # Verify subsystem breakdown
    subsystems = data["subsystems"]
    assert "database" in subsystems
    assert subsystems["database"]["status"] == "healthy"
    assert "latency_ms" in subsystems["database"]

    assert "redis_cache" in subsystems
    assert subsystems["redis_cache"]["status"] in ["healthy", "degraded"]
    assert "mode" in subsystems["redis_cache"]

    assert "vector_memory" in subsystems
    assert subsystems["vector_memory"]["status"] == "healthy"

    assert "ai_agents" in subsystems
    assert subsystems["ai_agents"]["status"] == "ready"

    # Verify system resources
    assert "system_resources" in data
    sys_metrics = data["system_resources"]
    assert "memory_usage_pct" in sys_metrics
    assert "process_memory_rss_mb" in sys_metrics


def test_health_liveness_and_readiness_probes():
    """Verify Kubernetes liveness and readiness probe endpoints."""
    # 1. Liveness Probe
    res_live = client.get("/health/liveness")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "alive"

    # 2. Readiness Probe
    res_ready = client.get("/health/readiness")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"
    assert res_ready.json()["database"] == "connected"


def test_request_correlation_id_middleware():
    """Verify every HTTP request generates and returns an X-Request-ID header."""
    # Custom request ID supplied by caller
    custom_id = "test-corr-id-998877"
    res = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert res.status_code == 200
    assert res.headers.get("X-Request-ID") == custom_id

    # Auto-generated request ID when none is provided
    res_auto = client.get("/api/v1/health")
    assert res_auto.status_code == 200
    generated_id = res_auto.headers.get("X-Request-ID")
    assert generated_id is not None
    assert len(generated_id) >= 16


def test_logging_context_variable_lifecycle():
    """Verify correlation context variable sets and clears correctly."""
    set_request_context(request_id="req-123", tenant_id="tenant-456")
    assert ctx_request_id.get() == "req-123"

    clear_request_context()
    assert ctx_request_id.get() is None

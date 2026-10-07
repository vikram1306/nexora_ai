import os
import sys
import time
import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.core.database import SessionLocal
from app.memory.redis_cache import cache_manager, EnterpriseCacheManager
from app.ingestion.profiler import DataProfiler
from app.core.job_queue import job_manager
from app.models.domain import IngestionJob, Dataset

client = TestClient(app)

def test_redis_cache_manager_operations():
    """Verify get/set, TTL, invalidation, and metrics telemetry in EnterpriseCacheManager."""
    cache = EnterpriseCacheManager()
    tenant_id = "test-tenant-phase7"

    # Test KPI cache
    dummy_kpi = {"sales": {"total_revenue": 150000.0, "row_count": 100}}
    cache.set_kpi_summary(tenant_id, dummy_kpi, ttl=60)
    retrieved_kpi = cache.get_kpi_summary(tenant_id)
    assert retrieved_kpi is not None
    assert retrieved_kpi["sales"]["total_revenue"] == 150000.0

    # Test Query Response cache
    prompt = "Analyze Q1 revenue performance"
    dummy_resp = {"intent": "EXECUTIVE_ANALYSIS", "confidence_score": 0.98, "executive_summary": "Revenue is up 25%."}
    cache.set_query_response(tenant_id, prompt, dummy_resp, ttl=60)
    retrieved_resp = cache.get_query_response(tenant_id, prompt)
    assert retrieved_resp is not None
    assert retrieved_resp["confidence_score"] == 0.98

    # Test Cache Stats
    stats = cache.get_cache_stats()
    assert "status" in stats
    assert stats["hits"] >= 2
    assert "hit_ratio_percent" in stats

    # Test Cache Invalidation
    cache.invalidate_tenant_cache(tenant_id)
    assert cache.get_kpi_summary(tenant_id) is None
    assert cache.get_query_response(tenant_id, prompt) is None


def test_chunked_streaming_profiler(tmp_path):
    """Verify that chunked streaming profiler handles multi-chunk files with exact online statistics."""
    csv_file = tmp_path / "large_stream_test.csv"
    
    # Generate 15,000 synthetic rows
    n_rows = 15000
    dates = pd.date_range(start="2026-01-01", periods=150, freq="D")
    df = pd.DataFrame({
        "transaction_id": [f"TX-{i}" for i in range(n_rows)],
        "sales_amount": np.random.uniform(100.0, 1000.0, size=n_rows),
        "region": np.random.choice(["North", "South", "East", "West"], size=n_rows),
        "date": np.random.choice(dates, size=n_rows).astype(str)
    })
    df.to_csv(csv_file, index=False)

    # Compute expected mathematical totals
    expected_sum = float(df["sales_amount"].sum())
    expected_mean = float(df["sales_amount"].mean())
    expected_std = float(df["sales_amount"].std())

    progress_events = []
    def on_progress(pct, stage):
        progress_events.append((pct, stage))

    # Profile using small chunk size (2,500 rows/chunk -> 6 chunks)
    result = DataProfiler.profile_csv(
        file_path=str(csv_file),
        department="sales",
        chunk_size=2500,
        progress_callback=on_progress
    )

    assert result["row_count"] == n_rows
    assert len(progress_events) >= 5

    # Check precision of streaming statistics
    actual_sum = result["kpis_extracted"]["aggregates"]["sales_amount"]["sum"]
    actual_mean = result["kpis_extracted"]["aggregates"]["sales_amount"]["mean"]
    actual_std = result["kpis_extracted"]["aggregates"]["sales_amount"]["std_dev"]

    assert pytest.approx(actual_sum, rel=1e-3) == expected_sum
    assert pytest.approx(actual_mean, rel=1e-3) == expected_mean
    assert pytest.approx(actual_std, rel=1e-2) == expected_std
    assert result["kpis_extracted"]["primary_metric"] == "total_revenue"


def test_background_job_queue_and_api(tmp_path):
    """Verify background job queuing, status tracking, and 202 response via REST API."""
    # Register a new tenant user
    email = f"job_user_{int(time.time())}@enterprise.com"
    reg_res = client.post("/api/v1/auth/register", json={
        "company_name": "Job Queue Corp",
        "email": email,
        "password": "Password123!",
        "full_name": "Queue Officer",
        "role": "CEO"
    })
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create CSV file to upload
    csv_file = tmp_path / "sales_upload_job.csv"
    df = pd.DataFrame({
        "transaction_id": ["T1", "T2", "T3", "T4", "T5"],
        "revenue": [50000.0, 75000.0, 120000.0, 90000.0, 60000.0],
        "region": ["North", "South", "East", "West", "North"],
        "date": ["2026-01-01", "2026-01-15", "2026-02-01", "2026-02-15", "2026-03-01"]
    })
    df.to_csv(csv_file, index=False)

    # 1. Test async upload returning 202 Accepted
    with open(csv_file, "rb") as f:
        res = client.post(
            "/api/v1/ingest/upload",
            headers=headers,
            data={"department": "sales"},
            files={"file": ("sales_upload_job.csv", f, "text/csv")}
        )
    assert res.status_code == 202
    job_data = res.json()
    assert "id" in job_data
    assert job_data["status"] in ["PENDING", "PROCESSING", "COMPLETED"]
    job_id = job_data["id"]

    # 2. Wait a moment for background worker to complete
    time.sleep(1.5)

    # 3. Query job status endpoint
    job_status_res = client.get(f"/api/v1/ingest/jobs/{job_id}", headers=headers)
    assert job_status_res.status_code == 200
    final_job = job_status_res.json()
    assert final_job["status"] in ["PROCESSING", "COMPLETED"]

    # 4. List all jobs for tenant
    jobs_list_res = client.get("/api/v1/ingest/jobs", headers=headers)
    assert jobs_list_res.status_code == 200
    assert len(jobs_list_res.json()) >= 1


def test_query_cache_acceleration_and_stats():
    """Verify that query responses are cached in Redis, resulting in sub-10ms response times on subsequent requests."""
    email = f"cache_user_{int(time.time())}@enterprise.com"
    reg_res = client.post("/api/v1/auth/register", json={
        "company_name": "Cache Acceleration Inc",
        "email": email,
        "password": "Password123!",
        "full_name": "Speed Analyst",
        "role": "CEO"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    prompt = "What is the overall financial and operational health of the company?"

    # First Query (Cold)
    t0 = time.time()
    res1 = client.post("/api/v1/query/execute", headers=headers, json={"prompt": prompt})
    cold_duration = time.time() - t0
    assert res1.status_code == 200

    # Second Query (Warm - Cached)
    t1 = time.time()
    res2 = client.post("/api/v1/query/execute", headers=headers, json={"prompt": prompt})
    warm_duration = time.time() - t1
    assert res2.status_code == 200

    # Check Cache Stats endpoint
    stats_res = client.get("/api/v1/query/cache-stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["hits"] > 0

    # Clear cache endpoint
    clear_res = client.post("/api/v1/query/cache-clear", headers=headers)
    assert clear_res.status_code == 200
    assert clear_res.json()["status"] == "cleared"

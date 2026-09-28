import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.models.domain import User, Tenant, Dataset, SentinelAlert
from app.services.memory.enterprise_memory import EnterpriseMemoryManager
from app.services.sentinel.sentinel_service import SentinelAIService
from app.services.agents.planner import PlannerAgent

from tests.conftest import TestingSessionLocal

client = TestClient(app)

def create_test_user_and_token(db, email, role, tenant_id):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        tenant = Tenant(id=tenant_id, name=f"Company {tenant_id}", slug=f"company-{tenant_id}")
        db.add(tenant)
        db.commit()
    
    user = User(
        email=email,
        hashed_password=hash_password("Password123!"),
        full_name=f"User {email}",
        role=role,
        tenant_id=tenant_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, tenant_id=tenant_id, role=role)
    return user, token

def save_dataset(db, tmp_path, tenant_id, department, df, name="data.csv"):
    csv_path = tmp_path / f"{tenant_id}_{department}_{name}"
    df.to_csv(csv_path, index=False)
    ds = Dataset(
        tenant_id=tenant_id,
        name=name,
        department=department,
        file_path=str(csv_path),
        row_count=len(df)
    )
    db.add(ds)
    db.commit()
    return ds


def test_task8_sentinel_hardening(tmp_path):
    """Task 8: Verify Sentinel excludes ID columns, respects min sample size (>=10), and uses MAD anomaly detection."""
    db = TestingSessionLocal()
    tenant_id = "sentinel_hardened_tenant"

    # Small sample (<10 rows) with outlier -> should be skipped by MIN_SAMPLE_SIZE
    df_small = pd.DataFrame({
        "sku_id": range(1, 6),
        "sales_amount": [100.0, 102.0, 101.0, 99.0, 10000.0]
    })
    save_dataset(db, tmp_path, tenant_id, "sales", df_small, "small.csv")
    sentinel = SentinelAIService(db, tenant_id)
    alerts_small = sentinel.scan_tenant_memory_for_anomalies()
    assert len(alerts_small) == 0 # Skipped due to MIN_SAMPLE_SIZE = 10

    # Adequate sample (>=10 rows) with outlier in sales_amount
    sales_vals = [100.0] * 12 + [5000.0] # 13 rows, massive outlier
    df_large = pd.DataFrame({
        "transaction_id": range(1, 14),
        "user_uuid": [f"uuid-{i}" for i in range(1, 14)],
        "sales_amount": sales_vals
    })
    save_dataset(db, tmp_path, tenant_id, "marketing", df_large, "large.csv")

    alerts_large = sentinel.scan_tenant_memory_for_anomalies()
    assert len(alerts_large) >= 1
    # ID columns must be excluded
    assert not any(a.metric_name in ["transaction_id", "user_uuid"] for a in alerts_large)
    # Target metric must be sales_amount with robust Z-score
    assert any(a.metric_name == "sales_amount" for a in alerts_large)
    db.close()


def test_task9_pdf_export_endpoint(tmp_path):
    """Task 9: Verify REST endpoint POST /api/v1/query/export-pdf streams binary PDF report."""
    db = TestingSessionLocal()
    tenant_id = "pdf_test_tenant"
    _, token = create_test_user_and_token(db, "ceo_pdf@test.com", "CEO", tenant_id)

    sales_df = pd.DataFrame({"sales_amount": [500000.0] * 10})
    save_dataset(db, tmp_path, tenant_id, "sales", sales_df, "sales.csv")

    response = client.post(
        "/api/v1/query/export-pdf",
        json={"prompt": "Generate executive sales intelligence report"},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-")
    db.close()


def test_task10_rbac_alerts_enforcement(tmp_path):
    """Task 10: Verify RBAC role hierarchy genuinely restricts Employee from viewing CEO/Director alerts."""
    db = TestingSessionLocal()
    tenant_id = "rbac_test_tenant"

    ceo_user, ceo_token = create_test_user_and_token(db, "ceo@rbac.com", "CEO", tenant_id)
    emp_user, emp_token = create_test_user_and_token(db, "employee@rbac.com", "Employee", tenant_id)

    # Log CEO alert (CRITICAL) and Employee alert (LOW)
    alert_ceo = SentinelAlert(
        tenant_id=tenant_id,
        department="finance",
        metric_name="actual_expense",
        severity="CRITICAL",
        target_role="CEO",
        title="Critical Cost Spike",
        description="Massive expense anomaly",
        root_cause="Unplanned software procurement"
    )
    alert_emp = SentinelAlert(
        tenant_id=tenant_id,
        department="marketing",
        metric_name="clicks",
        severity="LOW",
        target_role="Employee",
        title="Minor Click Drop",
        description="Slight campaign drop",
        root_cause="Weekend dip"
    )
    db.add_all([alert_ceo, alert_emp])
    db.commit()

    # CEO Query -> Sees BOTH alerts
    res_ceo = client.get("/api/v1/sentinel/alerts", headers={"Authorization": f"Bearer {ceo_token}"})
    assert res_ceo.status_code == 200
    ceo_alerts = res_ceo.json()
    assert len(ceo_alerts) == 2

    # Employee Query -> Sees ONLY Employee alert (restricted from CEO alert)
    res_emp = client.get("/api/v1/sentinel/alerts", headers={"Authorization": f"Bearer {emp_token}"})
    assert res_emp.status_code == 200
    emp_alerts = res_emp.json()
    assert len(emp_alerts) == 1
    assert emp_alerts[0]["target_role"] == "Employee"
    assert emp_alerts[0]["severity"] == "LOW"
    db.close()


def test_task11_multi_tenant_isolation(tmp_path):
    """Task 11: Verify strict multi-tenant isolation (Tenant A never sees Tenant B data)."""
    db = TestingSessionLocal()
    tenant_a = "tenant_alpha"
    tenant_b = "tenant_beta"

    user_a, token_a = create_test_user_and_token(db, "user@alpha.com", "CEO", tenant_a)
    user_b, token_b = create_test_user_and_token(db, "user@beta.com", "CEO", tenant_b)

    # Tenant A uploaded dataset: Sales = $100,000
    df_a = pd.DataFrame({"sales_amount": [100000.0] * 10})
    save_dataset(db, tmp_path, tenant_a, "sales", df_a, "alpha_sales.csv")

    # Tenant B uploaded dataset: Sales = $9,999,999
    df_b = pd.DataFrame({"sales_amount": [9999999.0] * 10})
    save_dataset(db, tmp_path, tenant_b, "sales", df_b, "beta_sales.csv")

    # Tenant A query
    planner_a = PlannerAgent(db, tenant_a)
    res_a = planner_a.execute_query("Analyze total sales revenue")
    summary_a = res_a.executive_summary
    assert "$1,000,000.00" in summary_a or "$100,000.00" in summary_a
    assert "$9,999,999" not in summary_a
    assert "99,999,990" not in summary_a

    # Tenant B query
    planner_b = PlannerAgent(db, tenant_b)
    res_b = planner_b.execute_query("Analyze total sales revenue")
    summary_b = res_b.executive_summary
    assert "$99,999,990.00" in summary_b or "9,999,999" in summary_b
    assert "$1,000,000.00" not in summary_b
    db.close()

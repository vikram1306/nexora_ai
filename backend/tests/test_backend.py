import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import hash_password, verify_password
from app.ingestion.profiler import DataProfiler

client = TestClient(app)

def test_password_security():
    pwd = "EnterpriseSuperSecretPassword123"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed)
    assert not verify_password("WrongPassword", hashed)

def test_auth_flow():
    # Register
    res = client.post("/api/v1/auth/register", json={
        "company_name": "Acme Global Enterprise",
        "email": "ceo@acme.com",
        "password": "Password123!",
        "full_name": "Jane Doe",
        "role": "CEO"
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    token = data["access_token"]

    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": "ceo@acme.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Me Endpoint
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "ceo@acme.com"

def test_data_profiler_and_ingestion(tmp_path):
    # Create sample CSV
    csv_file = tmp_path / "sales_data.csv"
    df = pd.DataFrame({
        "transaction_id": ["T001", "T002", "T003"],
        "sales_amount": [15000.0, 25000.0, 10000.0],
        "region": ["North", "South", "East"],
        "date": ["2026-01-01", "2026-01-02", "2026-01-03"]
    })
    df.to_csv(csv_file, index=False)

    # Test Profiler
    schema_info = DataProfiler.profile_csv(str(csv_file), "sales")
    assert schema_info["row_count"] == 3
    assert len(schema_info["columns_metadata"]) == 4
    assert schema_info["kpis_extracted"]["total_revenue"] == 50000.0

def test_out_of_domain_query():
    reg_res = client.post("/api/v1/auth/register", json={
        "company_name": "OmniCorp Inc",
        "email": "exec@omnicorp.com",
        "password": "Password123!",
        "full_name": "Executive Smith",
        "role": "CEO"
    })
    token = reg_res.json()["access_token"]

    res = client.post("/api/v1/query/execute", json={
        "prompt": "What is the weather forecast today in Tokyo?"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_out_of_domain"] is True
    assert "non-business topic" in data["executive_summary"]

def test_valid_executive_query():
    reg_res = client.post("/api/v1/auth/register", json={
        "company_name": "Stark Industries",
        "email": "tony@stark.com",
        "password": "Password123!",
        "full_name": "Tony Stark",
        "role": "CEO"
    })
    token = reg_res.json()["access_token"]

    res = client.post("/api/v1/query/execute", json={
        "prompt": "Analyze sales revenue performance and regional deal growth"
    }, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_out_of_domain"] is False
    assert data["confidence_score"] > 0
    assert len(data["department_outputs"]) > 0

import os
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password, verify_password
from app.services.ingestion.profiler import DataProfiler

# Setup Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_nexora.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
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
    csv_file = tmp_path / "sales_test.csv"
    df = pd.DataFrame({
        "transaction_id": [101, 102, 103, 104, 105],
        "sales_amount": [1200.0, 4500.0, 3100.0, 8900.0, 25000.0],
        "region": ["North", "South", "North", "East", "West"]
    })
    df.to_csv(csv_file, index=False)

    profile = DataProfiler.profile_csv(str(csv_file), "sales")
    assert profile["row_count"] == 5
    assert profile["kpis_extracted"]["total_revenue"] == 42700.0

def test_out_of_domain_query():
    reg = client.post("/api/v1/auth/register", json={
        "company_name": "Test Enterprise",
        "email": "admin@test.com",
        "password": "Password123!",
        "full_name": "Admin User",
        "role": "CEO"
    })
    token = reg.json()["access_token"]

    res = client.post("/api/v1/query/execute", json={"prompt": "Who won the political election?"}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["is_out_of_domain"] is True
    assert json_data["intent"] == "OUT_OF_DOMAIN"

def test_valid_executive_query():
    reg = client.post("/api/v1/auth/register", json={
        "company_name": "OmniCorp",
        "email": "exec@omnicorp.com",
        "password": "Password123!",
        "full_name": "Exec Officer",
        "role": "CEO"
    })
    token = reg.json()["access_token"]

    res = client.post("/api/v1/query/execute", json={"prompt": "Provide sales revenue and financial profit summary"}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_out_of_domain"] is False
    assert len(data["department_outputs"]) > 0
    assert data["confidence_score"] > 0.0

def teardown_module():
    engine.dispose()
    if os.path.exists("./test_nexora.db"):
        try:
            os.remove("./test_nexora.db")
        except Exception:
            pass

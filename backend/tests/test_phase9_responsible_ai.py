import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.domain import RecommendationDecision, Tenant, User
from app.schemas.agents import (
    StrategicRecommendation,
)

client = TestClient(app)


def create_user_and_auth_header(db, email: str, role: str, tenant_id: str):
    """Helper to provision test tenant, user and generate bearer token header."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        tenant = Tenant(id=tenant_id, name=f"Company {tenant_id}", slug=f"co-{tenant_id}")
        db.add(tenant)
        db.commit()

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password=hash_password("StrongPass123!"),
            full_name=f"Executive {email}",
            role=role,
            tenant_id=tenant_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(subject=user.id, tenant_id=tenant_id, role=role)
    return user, {"Authorization": f"Bearer {token}"}


def test_strategic_recommendation_schema_responsible_ai_attributes():
    """Verify StrategicRecommendation includes Responsible AI fields: confidence, urgency, status."""
    rec = StrategicRecommendation(
        title="Reduce CAC by Reallocating Ad Spend",
        action_item="Shift $20k budget from Display to Google Search",
        target_department="marketing",
        expected_impact="Improve overall ROAS from 3.2x to 4.1x",
        supporting_evidence=["Display ROAS is 1.8x", "Search ROAS is 4.5x"],
        confidence_score=0.94,
        impact_urgency="High"
    )

    assert rec.status == "PROPOSED"
    assert rec.confidence_score == 0.94
    assert rec.impact_urgency == "High"
    assert rec.id.startswith("rec_")


def test_log_human_accept_decision(db_session):
    """Test human executive accepting an AI recommendation logs to database with audit trail."""
    _, auth_headers = create_user_and_auth_header(
        db_session, "ceo@enterprise-a.com", "CEO", "tenant_phase9_a"
    )

    payload = {
        "recommendation_id": "rec_sales_expand_01",
        "recommendation_title": "Expand High-Yield Enterprise Sales Pipeline",
        "department": "sales",
        "action_type": "ACCEPTED",
        "action_plan": "Authorized Q3 sales team hiring and enterprise target reallocation",
        "feedback_notes": "Validated against Q2 pipeline conversion metrics",
        "confidence_score": 0.96,
        "impact_urgency": "Critical"
    }

    res = client.post(
        "/api/v1/query/recommendations/decisions",
        json=payload,
        headers=auth_headers
    )

    assert res.status_code == 201
    data = res.json()
    assert data["recommendation_id"] == "rec_sales_expand_01"
    assert data["action_type"] == "ACCEPTED"
    assert data["department"] == "sales"
    assert data["confidence_score"] == 0.96
    assert data["impact_urgency"] == "Critical"
    assert data["tenant_id"] == "tenant_phase9_a"
    assert "id" in data
    assert "created_at" in data

    # Verify persisted in database
    db_rec = db_session.query(RecommendationDecision).filter_by(id=data["id"]).first()
    assert db_rec is not None
    assert db_rec.action_type == "ACCEPTED"
    assert db_rec.recommendation_title == "Expand High-Yield Enterprise Sales Pipeline"


def test_log_human_reject_decision(db_session):
    """Test human executive rejecting an AI recommendation logs reason and feedback for RL/fine-tuning."""
    _, auth_headers = create_user_and_auth_header(
        db_session, "cfo@enterprise-a.com", "Director", "tenant_phase9_a"
    )

    payload = {
        "recommendation_id": "rec_fin_cost_cut_99",
        "recommendation_title": "Aggressive R&D Budget Freeze",
        "department": "finance",
        "action_type": "REJECTED",
        "action_plan": "Hold freeze pending Q4 revenue reconciliation",
        "feedback_notes": "Too aggressive for current product launch window",
        "confidence_score": 0.72,
        "impact_urgency": "High"
    }

    res = client.post(
        "/api/v1/query/recommendations/decisions",
        json=payload,
        headers=auth_headers
    )

    assert res.status_code == 201
    data = res.json()
    assert data["action_type"] == "REJECTED"
    assert data["department"] == "finance"
    assert data["feedback_notes"] == "Too aggressive for current product launch window"


def test_list_recommendation_decisions_with_filters(db_session):
    """Test listing logged decisions with department and action_type filters."""
    _, auth_headers = create_user_and_auth_header(
        db_session, "coo@enterprise-a.com", "Director", "tenant_phase9_a"
    )

    # 1. List all decisions
    res = client.get("/api/v1/query/recommendations/decisions", headers=auth_headers)
    assert res.status_code == 200
    all_decisions = res.json()
    assert len(all_decisions) >= 2

    # 2. Filter by department=sales
    res_sales = client.get(
        "/api/v1/query/recommendations/decisions?department=sales",
        headers=auth_headers
    )
    assert res_sales.status_code == 200
    sales_decisions = res_sales.json()
    assert all(d["department"] == "sales" for d in sales_decisions)
    assert len(sales_decisions) >= 1

    # 3. Filter by action_type=REJECTED
    res_rej = client.get(
        "/api/v1/query/recommendations/decisions?action_type=REJECTED",
        headers=auth_headers
    )
    assert res_rej.status_code == 200
    rej_decisions = res_rej.json()
    assert all(d["action_type"] == "REJECTED" for d in rej_decisions)
    assert len(rej_decisions) >= 1


def test_governance_stats_and_acceptance_rate(db_session):
    """Test aggregation of governance metrics, acceptance rate %, and department breakdown."""
    _, auth_headers = create_user_and_auth_header(
        db_session, "ceo@enterprise-stats.com", "CEO", "tenant_phase9_stats"
    )

    # Log 3 accepted and 1 rejected decision
    items = [
        ("rec_1", "Marketing optimization", "marketing", "ACCEPTED"),
        ("rec_2", "Sales territory expansion", "sales", "ACCEPTED"),
        ("rec_3", "HR retention program", "hr", "ACCEPTED"),
        ("rec_4", "Operations facility move", "operations", "REJECTED"),
    ]

    for rec_id, title, dept, action in items:
        client.post(
            "/api/v1/query/recommendations/decisions",
            json={
                "recommendation_id": rec_id,
                "recommendation_title": title,
                "department": dept,
                "action_type": action,
                "action_plan": f"Action for {title}",
                "confidence_score": 0.91,
                "impact_urgency": "High"
            },
            headers=auth_headers
        )

    res = client.get("/api/v1/query/recommendations/stats", headers=auth_headers)
    assert res.status_code == 200
    stats = res.json()

    assert stats["total_decisions"] == 4
    assert stats["accepted_count"] == 3
    assert stats["rejected_count"] == 1
    assert stats["modified_count"] == 0
    # Acceptance rate = 3 / 4 * 100 = 75.0%
    assert stats["acceptance_rate_pct"] == 75.0

    dept_breakdown = stats["department_breakdown"]
    assert dept_breakdown["marketing"]["ACCEPTED"] == 1
    assert dept_breakdown["sales"]["ACCEPTED"] == 1
    assert dept_breakdown["hr"]["ACCEPTED"] == 1
    assert dept_breakdown["operations"]["REJECTED"] == 1
    assert len(stats["recent_decisions"]) == 4


def test_multi_tenant_decision_isolation(db_session):
    """Verify Tenant B cannot view or tamper with Tenant A's logged decisions."""
    _, auth_a = create_user_and_auth_header(
        db_session, "user@tenant-alpha.com", "CEO", "tenant_alpha_isolated"
    )
    _, auth_b = create_user_and_auth_header(
        db_session, "user@tenant-beta.com", "CEO", "tenant_beta_isolated"
    )

    # Tenant Alpha logs an accepted recommendation
    client.post(
        "/api/v1/query/recommendations/decisions",
        json={
            "recommendation_id": "rec_alpha_secret_01",
            "recommendation_title": "Alpha Confidential Restructure",
            "department": "finance",
            "action_type": "ACCEPTED",
            "action_plan": "Alpha internal plan only",
            "confidence_score": 0.99
        },
        headers=auth_a
    )

    # Tenant Beta queries decisions and stats
    res_b_list = client.get("/api/v1/query/recommendations/decisions", headers=auth_b)
    assert res_b_list.status_code == 200
    assert len(res_b_list.json()) == 0

    res_b_stats = client.get("/api/v1/query/recommendations/stats", headers=auth_b)
    assert res_b_stats.status_code == 200
    assert res_b_stats.json()["total_decisions"] == 0
    assert res_b_stats.json()["acceptance_rate_pct"] == 0.0

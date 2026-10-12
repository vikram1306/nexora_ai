from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.models.domain import User
from app.planner.planner import PlannerAgent
from app.schemas.agents import (
    ExecutiveQueryRequest,
    ExecutiveQueryResponse,
    RecommendationDecisionCreate,
    RecommendationDecisionResponse,
    RecommendationGovernanceStats,
)

router = APIRouter(prefix="/query", tags=["Multi-Agent Intelligence Query"])

@router.post("/execute", response_model=ExecutiveQueryResponse)
@limiter.limit(settings.RATE_LIMIT_QUERY)
def execute_executive_query(
    request: Request,
    body: ExecutiveQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not body.prompt.strip():
        raise HTTPException(status_code=400, detail="Query prompt cannot be empty")

    planner = PlannerAgent(db, current_user.tenant_id)
    return planner.execute_query(body.prompt)


@router.post("/export-pdf")
def export_executive_pdf(
    request: ExecutiveQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Executes query and streams back a formatted PDF executive intelligence report."""
    from fastapi.responses import Response

    from app.reporting.pdf_exporter import generate_executive_pdf_bytes

    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Query prompt cannot be empty")

    planner = PlannerAgent(db, current_user.tenant_id)
    query_res = planner.execute_query(request.prompt)
    pdf_bytes = generate_executive_pdf_bytes(query_res)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=Nexora_Executive_Report.pdf"}
    )

@router.get("/ollama-status")
def check_ollama_status():
    """Check if local Ollama (Llama 3) service is active on host machine."""
    try:
        with httpx.Client(timeout=1.5) as client:
            res = client.get("http://localhost:11434/api/tags")
            if res.status_code == 200:
                models = res.json().get("models", [])
                model_names = [m.get("name") for m in models]
                return {
                    "status": "online",
                    "local_models": model_names,
                    "active_llm": "Llama 3 / Mistral (Local Ollama)"
                }
    except Exception:
        pass
    return {
        "status": "offline",
        "active_llm": "Built-in Deterministic Engine",
        "info": "Start Ollama locally ('ollama run llama3') to enable Llama 3 text synthesis."
    }

@router.get("/cache-stats")
def get_redis_cache_stats():
    """Returns Redis cache hit/miss metrics and connectivity status."""
    from app.memory.redis_cache import cache_manager
    return cache_manager.get_cache_stats()

@router.post("/cache-clear")
def clear_redis_cache(
    current_user: User = Depends(get_current_user)
):
    """Flushes cached queries, metrics, and KPI summaries for current tenant."""
    from app.memory.redis_cache import cache_manager
    cache_manager.invalidate_tenant_cache(current_user.tenant_id)
    return {
        "status": "cleared",
        "tenant_id": current_user.tenant_id,
        "message": "Tenant cache invalidated successfully"
    }


# --- Responsible AI: Human-in-the-Loop Decision Logging Endpoints ---

@router.post("/recommendations/decisions", response_model=RecommendationDecisionResponse, status_code=201)
def log_recommendation_decision(
    decision_in: RecommendationDecisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Logs human executive accept/reject decisions on AI strategic recommendations for auditability and feedback loops."""
    from app.models.domain import RecommendationDecision

    decision = RecommendationDecision(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        recommendation_id=decision_in.recommendation_id,
        recommendation_title=decision_in.recommendation_title,
        department=decision_in.department.lower().strip(),
        action_type=decision_in.action_type.upper().strip(),
        action_plan=decision_in.action_plan,
        feedback_notes=decision_in.feedback_notes,
        confidence_score=decision_in.confidence_score,
        impact_urgency=decision_in.impact_urgency
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


@router.get("/recommendations/decisions", response_model=List[RecommendationDecisionResponse])
def list_recommendation_decisions(
    limit: int = 50,
    department: Optional[str] = None,
    action_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists logged human accept/reject decisions for the current tenant."""
    from app.models.domain import RecommendationDecision

    q = db.query(RecommendationDecision).filter(RecommendationDecision.tenant_id == current_user.tenant_id)
    if department:
        q = q.filter(RecommendationDecision.department == department.lower().strip())
    if action_type:
        q = q.filter(RecommendationDecision.action_type == action_type.upper().strip())

    return q.order_by(RecommendationDecision.created_at.desc()).limit(limit).all()


@router.get("/recommendations/stats", response_model=RecommendationGovernanceStats)
def get_recommendation_governance_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns acceptance rate and governance telemetry for AI-assisted executive recommendations."""
    from app.models.domain import RecommendationDecision

    decisions = db.query(RecommendationDecision).filter(
        RecommendationDecision.tenant_id == current_user.tenant_id
    ).order_by(RecommendationDecision.created_at.desc()).all()

    total = len(decisions)
    accepted = sum(1 for d in decisions if d.action_type == "ACCEPTED")
    rejected = sum(1 for d in decisions if d.action_type == "REJECTED")
    modified = sum(1 for d in decisions if d.action_type == "MODIFIED")
    acceptance_rate = round((accepted / total * 100), 1) if total > 0 else 0.0

    dept_breakdown: Dict[str, Dict[str, int]] = {}
    for d in decisions:
        dept = d.department
        if dept not in dept_breakdown:
            dept_breakdown[dept] = {"ACCEPTED": 0, "REJECTED": 0, "MODIFIED": 0}
        if d.action_type in dept_breakdown[dept]:
            dept_breakdown[dept][d.action_type] += 1

    return RecommendationGovernanceStats(
        total_decisions=total,
        accepted_count=accepted,
        rejected_count=rejected,
        modified_count=modified,
        acceptance_rate_pct=acceptance_rate,
        department_breakdown=dept_breakdown,
        recent_decisions=decisions[:10]
    )



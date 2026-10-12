import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class MetricDetail(BaseModel):
    name: str
    value: float
    unit: str = ""
    change_pct: Optional[float] = None


class DepartmentAgentOutput(BaseModel):
    department: str  # sales, finance, hr, marketing, operations
    metrics: List[MetricDetail]
    sql_executed: str
    trends: List[Dict[str, Any]]
    evidence: List[str]
    insights: List[str]
    confidence_score: float


class StrategicRecommendation(BaseModel):
    id: str = Field(default_factory=lambda: f"rec_{uuid.uuid4().hex[:10]}")
    title: str
    action_item: str
    target_department: str
    expected_impact: str
    supporting_evidence: List[str]
    confidence_score: float = 0.95
    impact_urgency: str = "High"  # Low, Medium, High, Critical
    status: str = "PROPOSED"  # PROPOSED, ACCEPTED, REJECTED, MODIFIED


class PlannerTaskPlan(BaseModel):
    intent: str
    target_departments: List[str]
    is_out_of_domain: bool = False
    rejection_reason: Optional[str] = None
    timeframe: Optional[str] = None
    key_metrics_requested: List[str] = []


class ExecutiveQueryRequest(BaseModel):
    prompt: str


class ExecutiveQueryResponse(BaseModel):
    prompt: str
    is_out_of_domain: bool
    intent: str
    confidence_score: float
    executive_summary: str
    department_outputs: List[DepartmentAgentOutput]
    strategic_recommendations: List[StrategicRecommendation]
    evidence_citations: List[str]
    chart_config: Optional[Dict[str, Any]] = None


# --- Human-in-the-Loop Governance & Recommendation Decision Schemas ---

class RecommendationDecisionCreate(BaseModel):
    recommendation_id: str
    recommendation_title: str
    department: str
    action_type: str = "ACCEPTED"  # ACCEPTED, REJECTED, MODIFIED
    action_plan: Optional[str] = None
    feedback_notes: Optional[str] = None
    confidence_score: float = 0.95
    impact_urgency: Optional[str] = "High"


class RecommendationDecisionResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    recommendation_id: str
    recommendation_title: str
    department: str
    action_type: str
    action_plan: Optional[str] = None
    feedback_notes: Optional[str] = None
    confidence_score: float
    impact_urgency: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationGovernanceStats(BaseModel):
    total_decisions: int
    accepted_count: int
    rejected_count: int
    modified_count: int
    acceptance_rate_pct: float
    department_breakdown: Dict[str, Dict[str, int]]
    recent_decisions: List[RecommendationDecisionResponse]

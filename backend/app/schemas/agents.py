from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

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
    title: str
    action_item: str
    target_department: str
    expected_impact: str
    supporting_evidence: List[str]

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

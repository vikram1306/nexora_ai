from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class SentinelAlertResponse(BaseModel):
    id: str
    tenant_id: str
    department: str
    metric_name: str
    severity: str
    target_role: str
    title: str
    description: str
    root_cause: str
    confidence_level: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    baseline_value: Optional[float] = None
    anomaly_value: Optional[float] = None
    acknowledged: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

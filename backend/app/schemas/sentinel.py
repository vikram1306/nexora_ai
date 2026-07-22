from pydantic import BaseModel
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
    acknowledged: bool
    created_at: datetime

    class Config:
        from_attributes = True

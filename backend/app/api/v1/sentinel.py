from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.domain import SentinelAlert, User
from app.schemas.sentinel import SentinelAlertResponse
from app.sentinel.sentinel_service import SentinelAIService

router = APIRouter(prefix="/sentinel", tags=["Sentinel AI Monitoring"])

ROLE_HIERARCHY = {
    "Employee": ["Employee"],
    "Manager": ["Employee", "Manager"],
    "Director": ["Employee", "Manager", "Director"],
    "CEO": ["Employee", "Manager", "Director", "CEO"]
}

@router.get("/alerts", response_model=List[SentinelAlertResponse])
def get_sentinel_alerts(
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    allowed_roles = ROLE_HIERARCHY.get(current_user.role, ["Employee"])
    query = db.query(SentinelAlert).filter(
        SentinelAlert.tenant_id == current_user.tenant_id,
        SentinelAlert.target_role.in_(allowed_roles)
    )
    if severity:
        query = query.filter(SentinelAlert.severity == severity.upper())
    if acknowledged is not None:
        query = query.filter(SentinelAlert.acknowledged == acknowledged)
    return query.order_by(SentinelAlert.created_at.desc()).all()

@router.post("/trigger", response_model=List[SentinelAlertResponse])
def trigger_sentinel_scan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    sentinel = SentinelAIService(db, current_user.tenant_id)
    alerts = sentinel.scan_tenant_memory_for_anomalies()
    return alerts

@router.patch("/alerts/{alert_id}/acknowledge", response_model=SentinelAlertResponse)
def acknowledge_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(SentinelAlert).filter(
        SentinelAlert.id == alert_id,
        SentinelAlert.tenant_id == current_user.tenant_id
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Sentinel alert not found")

    alert.acknowledged = True
    db.commit()
    db.refresh(alert)
    return alert

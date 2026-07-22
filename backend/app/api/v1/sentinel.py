from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.domain import User, SentinelAlert
from app.schemas.sentinel import SentinelAlertResponse
from app.api.deps import get_current_user
from app.services.sentinel.sentinel_service import SentinelAIService

router = APIRouter(prefix="/sentinel", tags=["Sentinel AI Monitoring"])

@router.get("/alerts", response_model=List[SentinelAlertResponse])
def get_sentinel_alerts(
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(SentinelAlert).filter(SentinelAlert.tenant_id == current_user.tenant_id)
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

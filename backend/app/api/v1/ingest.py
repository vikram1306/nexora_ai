import os
import shutil
import uuid
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.job_queue import job_manager
from app.core.limiter import limiter
from app.ingestion.schema_intelligence import SchemaIntelligenceEngine
from app.memory.redis_cache import cache_manager
from app.models.domain import Dataset, User
from app.schemas.ingestion import (
    DatasetResponse,
    IngestionJobResponse,
    SchemaAnalysisResponse,
    SchemaConfirmationRequest,
)

router = APIRouter(prefix="/ingest", tags=["Data Ingestion & Memory"])

ALLOWED_DEPARTMENTS = ["sales", "finance", "hr", "marketing", "operations"]
DATA_STORAGE_DIR = "./data_uploads"
STAGING_DIR = "./data_uploads/staging"


@router.post("/analyze-schema", response_model=SchemaAnalysisResponse)
@limiter.limit(settings.RATE_LIMIT_INGEST)
async def analyze_csv_schema(
    request: Request,
    department: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    department_clean = department.lower().strip()
    if department_clean not in ALLOWED_DEPARTMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid department '{department}'. Must be one of: {ALLOWED_DEPARTMENTS}"
        )

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    tenant_stage_dir = os.path.join(STAGING_DIR, current_user.tenant_id)
    os.makedirs(tenant_stage_dir, exist_ok=True)

    temp_file_id = str(uuid.uuid4())
    temp_file_path = os.path.join(tenant_stage_dir, f"{temp_file_id}_{file.filename}")

    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        analysis = SchemaIntelligenceEngine.propose_schema_mapping(temp_file_path, department_clean)
        return SchemaAnalysisResponse(
            department=department_clean,
            filename=file.filename,
            temp_file_id=temp_file_id,
            total_columns=analysis["total_columns"],
            proposed_mappings=analysis["proposed_mappings"],
            canonical_fields_available=analysis["canonical_fields_available"]
        )
    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=400, detail=f"Failed to analyze CSV schema: {str(e)}")


@router.post("/confirm-and-ingest", response_model=IngestionJobResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_INGEST)
def confirm_and_ingest_dataset(
    request: Request,
    req: SchemaConfirmationRequest,
    sync: bool = Query(False, description="Run synchronously if True (default: background job)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    department_clean = req.department.lower().strip()
    if department_clean not in ALLOWED_DEPARTMENTS:
        raise HTTPException(status_code=400, detail=f"Invalid department '{req.department}'")

    tenant_stage_dir = os.path.join(STAGING_DIR, current_user.tenant_id)
    matching_files = [f for f in os.listdir(tenant_stage_dir) if f.startswith(req.temp_file_id)] if os.path.exists(tenant_stage_dir) else []

    if not matching_files:
        raise HTTPException(status_code=404, detail="Staged upload session not found or expired.")

    staged_filename = matching_files[0]
    staged_path = os.path.join(tenant_stage_dir, staged_filename)
    original_filename = staged_filename.replace(f"{req.temp_file_id}_", "")

    tenant_dir = os.path.join(DATA_STORAGE_DIR, current_user.tenant_id)
    os.makedirs(tenant_dir, exist_ok=True)
    final_file_path = os.path.join(tenant_dir, f"{department_clean}_{original_filename}")

    job = job_manager.create_and_enqueue_job(
        tenant_id=current_user.tenant_id,
        department=department_clean,
        filename=original_filename,
        source_file_path=staged_path,
        target_file_path=final_file_path,
        confirmed_mapping=req.confirmed_mapping,
        db=db
    )

    if sync:
        job_manager._run_ingestion_worker(
            job_id=job.id,
            tenant_id=current_user.tenant_id,
            department=department_clean,
            filename=original_filename,
            source_file_path=staged_path,
            target_file_path=final_file_path,
            confirmed_mapping=req.confirmed_mapping,
            db_session=db
        )
        db.refresh(job)

    return job


@router.post("/upload", response_model=IngestionJobResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(settings.RATE_LIMIT_INGEST)
async def upload_csv_dataset(

    request: Request,
    department: str = Form(...),
    file: UploadFile = File(...),
    sync: bool = Query(False, description="Run synchronously if True (default: background job)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    department_clean = department.lower().strip()
    if department_clean not in ALLOWED_DEPARTMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid department '{department}'. Must be one of: {ALLOWED_DEPARTMENTS}"
        )

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # Save to staging
    tenant_stage_dir = os.path.join(STAGING_DIR, current_user.tenant_id)
    os.makedirs(tenant_stage_dir, exist_ok=True)
    temp_file_id = str(uuid.uuid4())
    staged_path = os.path.join(tenant_stage_dir, f"{temp_file_id}_{file.filename}")

    with open(staged_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    proposal = SchemaIntelligenceEngine.propose_schema_mapping(staged_path, department_clean)
    confirmed_map = {item["user_column"]: item["proposed_canonical"] for item in proposal["proposed_mappings"]}

    tenant_dir = os.path.join(DATA_STORAGE_DIR, current_user.tenant_id)
    os.makedirs(tenant_dir, exist_ok=True)
    final_file_path = os.path.join(tenant_dir, f"{department_clean}_{file.filename}")

    job = job_manager.create_and_enqueue_job(
        tenant_id=current_user.tenant_id,
        department=department_clean,
        filename=file.filename,
        source_file_path=staged_path,
        target_file_path=final_file_path,
        confirmed_mapping=confirmed_map,
        db=db
    )

    if sync:
        job_manager._run_ingestion_worker(
            job_id=job.id,
            tenant_id=current_user.tenant_id,
            department=department_clean,
            filename=file.filename,
            source_file_path=staged_path,
            target_file_path=final_file_path,
            confirmed_mapping=confirmed_map,
            db_session=db
        )
        db.refresh(job)

    return job


@router.get("/jobs", response_model=List[IngestionJobResponse])
def list_ingestion_jobs(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists background ingestion jobs for current tenant."""
    return job_manager.list_tenant_jobs(current_user.tenant_id, db, limit=limit)


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
def get_ingestion_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns real-time status & progress of a background ingestion job (checking Redis + SQL)."""
    # 1. Ultra-fast Redis status check
    cached_state = cache_manager.get_job_state(job_id)

    # 2. Database lookup
    job = job_manager.get_job_status(job_id, db)
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")

    if job.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access forbidden to job")

    if cached_state and isinstance(cached_state, dict):
        job.progress = cached_state.get("progress", job.progress)
        job.stage = cached_state.get("stage", job.stage)
        job.status = cached_state.get("status", job.status)

    return job


@router.get("/datasets", response_model=List[DatasetResponse])
def list_tenant_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Dataset).filter(Dataset.tenant_id == current_user.tenant_id).all()


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
def get_dataset_details(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.tenant_id == current_user.tenant_id
    ).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset

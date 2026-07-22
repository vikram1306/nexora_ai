import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.domain import User, Dataset, DatasetSchema
from app.schemas.ingestion import DatasetResponse
from app.api.deps import get_current_user
from app.services.ingestion.profiler import DataProfiler
from app.services.memory.vector_store import vector_memory_store

router = APIRouter(prefix="/ingest", tags=["Data Ingestion & Memory"])

ALLOWED_DEPARTMENTS = ["sales", "finance", "hr", "marketing", "operations"]
DATA_STORAGE_DIR = "./data_uploads"

@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_csv_dataset(
    department: str = Form(...),
    file: UploadFile = File(...),
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

    # Ensure storage dir exists
    tenant_dir = os.path.join(DATA_STORAGE_DIR, current_user.tenant_id)
    os.makedirs(tenant_dir, exist_ok=True)

    file_path = os.path.join(tenant_dir, f"{department_clean}_{file.filename}")
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Ingestion Pipeline: Clean, Schema Detect, KPI & Trend Generation
    try:
        profile_data = DataProfiler.profile_csv(file_path, department_clean)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Failed to process CSV: {str(e)}")

    # Store into PostgreSQL
    dataset = Dataset(
        tenant_id=current_user.tenant_id,
        name=file.filename,
        department=department_clean,
        row_count=profile_data["row_count"],
        file_path=file_path
    )
    db.add(dataset)
    db.flush()

    dataset_schema = DatasetSchema(
        dataset_id=dataset.id,
        columns_metadata=profile_data["columns_metadata"],
        kpis_extracted=profile_data["kpis_extracted"],
        trends_detected=profile_data["trends_detected"],
        relationships=profile_data["relationships"]
    )
    db.add(dataset_schema)
    db.commit()
    db.refresh(dataset)

    # Index into ChromaDB Vector Store
    vector_memory_store.index_dataset_metadata(
        tenant_id=current_user.tenant_id,
        dataset_id=dataset.id,
        department=department_clean,
        profile_data=profile_data
    )

    return dataset

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

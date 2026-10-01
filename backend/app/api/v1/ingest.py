import os
import uuid
import shutil
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.domain import User, Dataset, DatasetSchema
from app.schemas.ingestion import DatasetResponse, SchemaAnalysisResponse, SchemaConfirmationRequest
from app.api.deps import get_current_user
from app.ingestion.profiler import DataProfiler
from app.ingestion.schema_intelligence import SchemaIntelligenceEngine
from app.memory.vector_store import vector_memory_store

router = APIRouter(prefix="/ingest", tags=["Data Ingestion & Memory"])

ALLOWED_DEPARTMENTS = ["sales", "finance", "hr", "marketing", "operations"]
DATA_STORAGE_DIR = "./data_uploads"
STAGING_DIR = "./data_uploads/staging"

@router.post("/analyze-schema", response_model=SchemaAnalysisResponse)
async def analyze_csv_schema(
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


@router.post("/confirm-and-ingest", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def confirm_and_ingest_dataset(
    req: SchemaConfirmationRequest,
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

    try:
        # Load CSV and apply confirmed column renames/canonical mapping
        df = pd.read_csv(staged_path)
        
        # Filter mapping to valid non-ignore targets
        rename_map = {orig: target for orig, target in req.confirmed_mapping.items() if target and target != "ignore" and orig in df.columns}
        if rename_map:
            df = df.rename(columns=rename_map)

        df.to_csv(final_file_path, index=False)

        profile_data = DataProfiler.profile_csv(final_file_path, department_clean)
        profile_data["kpis_extracted"]["confirmed_mapping"] = req.confirmed_mapping
    except Exception as e:
        if os.path.exists(final_file_path):
            os.remove(final_file_path)
        raise HTTPException(status_code=400, detail=f"Failed to process confirmed dataset: {str(e)}")
    finally:
        if os.path.exists(staged_path):
            os.remove(staged_path)

    # Store into PostgreSQL
    dataset = Dataset(
        tenant_id=current_user.tenant_id,
        name=original_filename,
        department=department_clean,
        row_count=profile_data["row_count"],
        file_path=final_file_path
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
        proposal = SchemaIntelligenceEngine.propose_schema_mapping(file_path, department_clean)
        confirmed_map = {item["user_column"]: item["proposed_canonical"] for item in proposal["proposed_mappings"]}
        
        df = pd.read_csv(file_path)
        rename_map = {orig: target for orig, target in confirmed_map.items() if target and target != "ignore" and orig in df.columns}
        if rename_map:
            df = df.rename(columns=rename_map)
        df.to_csv(file_path, index=False)

        profile_data = DataProfiler.profile_csv(file_path, department_clean)
        profile_data["kpis_extracted"]["confirmed_mapping"] = confirmed_map
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

import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.ingestion.profiler import DataProfiler
from app.memory.redis_cache import cache_manager
from app.memory.vector_store import vector_memory_store
from app.models.domain import Dataset, DatasetSchema, IngestionJob
from app.sentinel.sentinel_service import SentinelAIService

logger = logging.getLogger(__name__)

class IngestionJobManager:
    """Enterprise Background Ingestion Job Queue coordinating chunked streaming CSV processing, vector indexing, Redis caching, and Sentinel AI scans."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(IngestionJobManager, cls).__new__(cls)
            cls._instance._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="nexora-ingest-worker")
        return cls._instance

    def create_and_enqueue_job(
        self,
        tenant_id: str,
        department: str,
        filename: str,
        source_file_path: str,
        target_file_path: str,
        confirmed_mapping: Optional[Dict[str, str]] = None,
        db: Optional[Session] = None
    ) -> IngestionJob:
        """Creates an IngestionJob record and dispatches background processing worker."""
        job_id = str(uuid.uuid4())
        should_close_db = False
        if db is None:
            db = SessionLocal()
            should_close_db = True

        try:
            job = IngestionJob(
                id=job_id,
                tenant_id=tenant_id,
                department=department.lower().strip(),
                filename=filename,
                status="PENDING",
                progress=0,
                stage="Queued in background worker pool",
                row_count=0,
                job_metadata={"confirmed_mapping": confirmed_mapping or {}},
                created_at=datetime.utcnow()
            )
            db.add(job)
            db.commit()
            db.refresh(job)

            # Store in Redis for sub-millisecond status polling
            cache_manager.set_job_state(job_id, {
                "id": job_id,
                "tenant_id": tenant_id,
                "filename": filename,
                "department": department,
                "status": "PENDING",
                "progress": 0,
                "stage": "Queued in background worker pool",
                "row_count": 0,
                "dataset_id": None,
                "error_message": None,
                "created_at": str(job.created_at)
            })

            # Submit to background executor
            self._executor.submit(
                self._run_ingestion_worker,
                job_id=job_id,
                tenant_id=tenant_id,
                department=department,
                filename=filename,
                source_file_path=source_file_path,
                target_file_path=target_file_path,
                confirmed_mapping=confirmed_mapping
            )

            return job
        finally:
            if should_close_db:
                db.close()

    def _update_job_progress(self, job_id: str, progress: int, stage: str, db: Session, extra: Optional[Dict[str, Any]] = None):
        try:
            job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
            if job:
                job.progress = progress
                job.stage = stage
                if extra:
                    meta = dict(job.job_metadata or {})
                    meta.update(extra)
                    job.job_metadata = meta
                db.commit()

            cached = cache_manager.get_job_state(job_id) or {"id": job_id}
            cached.update({
                "progress": progress,
                "stage": stage
            })
            if extra:
                cached.update(extra)
            cache_manager.set_job_state(job_id, cached)
        except Exception as e:
            logger.warning(f"Error updating job progress: {e}")

    def _run_ingestion_worker(
        self,
        job_id: str,
        tenant_id: str,
        department: str,
        filename: str,
        source_file_path: str,
        target_file_path: str,
        confirmed_mapping: Optional[Dict[str, str]],
        db_session: Optional[Session] = None
    ):
        """Worker executing streaming chunked profiling, database persistence, vector store indexing, and Redis cache update."""
        owns_db = False
        if db_session is not None:
            db = db_session
        else:
            db = SessionLocal()
            owns_db = True
        try:
            # 1. Update to PROCESSING
            job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
            if job:
                job.status = "PROCESSING"
                job.progress = 10
                job.stage = "Streaming chunked CSV ingestion & cleaning"
                db.commit()

            cache_manager.set_job_state(job_id, {
                "id": job_id,
                "tenant_id": tenant_id,
                "filename": filename,
                "department": department,
                "status": "PROCESSING",
                "progress": 10,
                "stage": "Streaming chunked CSV ingestion & cleaning"
            })

            # Progress callback for profiler
            def on_progress(pct: int, stg: str):
                self._update_job_progress(job_id, pct, stg, db)

            # 2. Execute Chunked Streaming Profiling
            profile_data = DataProfiler.profile_csv(
                file_path=source_file_path,
                department=department,
                confirmed_mapping=confirmed_mapping,
                output_file_path=target_file_path,
                progress_callback=on_progress
            )
            if confirmed_mapping:
                profile_data["kpis_extracted"]["confirmed_mapping"] = confirmed_mapping

            # Remove source staging file if different from target
            if os.path.exists(source_file_path) and os.path.abspath(source_file_path) != os.path.abspath(target_file_path):
                try:
                    os.remove(source_file_path)
                except Exception:
                    pass

            # 3. Store Dataset in SQL Database
            self._update_job_progress(job_id, 80, "Persisting structured metadata to database", db)
            dataset = Dataset(
                tenant_id=tenant_id,
                name=filename,
                department=department,
                row_count=profile_data["row_count"],
                file_path=target_file_path
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

            # 4. Index in Vector Store
            self._update_job_progress(job_id, 88, "Indexing ChromaDB semantic memory", db)
            vector_memory_store.index_dataset_metadata(
                tenant_id=tenant_id,
                dataset_id=dataset.id,
                department=department,
                profile_data=profile_data
            )

            # 5. Invalidate & Warm Redis Cache
            self._update_job_progress(job_id, 94, "Warming Redis KPI cache & invalidating stale views", db)
            cache_manager.invalidate_tenant_cache(tenant_id, department)

            # 6. Trigger Background Sentinel Anomaly Scan
            self._update_job_progress(job_id, 97, "Triggering Sentinel AI anomaly scan", db)
            try:
                sentinel = SentinelAIService(db, tenant_id)
                sentinel.scan_tenant_memory_for_anomalies()
            except Exception as se:
                logger.warning(f"Sentinel scan notice during ingestion: {se}")

            # 7. Complete Job
            now = datetime.utcnow()
            job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
            if job:
                job.status = "COMPLETED"
                job.progress = 100
                job.stage = f"Successfully ingested {profile_data['row_count']:,} rows into {department.upper()} Memory"
                job.dataset_id = dataset.id
                job.row_count = profile_data["row_count"]
                job.completed_at = now
                db.commit()

            cache_manager.set_job_state(job_id, {
                "id": job_id,
                "tenant_id": tenant_id,
                "filename": filename,
                "department": department,
                "status": "COMPLETED",
                "progress": 100,
                "stage": f"Successfully ingested {profile_data['row_count']:,} rows into {department.upper()} Memory",
                "dataset_id": dataset.id,
                "row_count": profile_data["row_count"],
                "completed_at": str(now)
            })

        except Exception as e:
            logger.exception(f"Ingestion job {job_id} failed: {e}")
            now = datetime.utcnow()
            job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
            if job:
                job.status = "FAILED"
                job.progress = 100
                job.stage = "Failed"
                job.error_message = str(e)
                job.completed_at = now
                db.commit()

            cache_manager.set_job_state(job_id, {
                "id": job_id,
                "tenant_id": tenant_id,
                "filename": filename,
                "department": department,
                "status": "FAILED",
                "progress": 100,
                "stage": "Failed",
                "error_message": str(e),
                "completed_at": str(now)
            })
        finally:
            if owns_db:
                db.close()

    def get_job_status(self, job_id: str, db: Session) -> Optional[IngestionJob]:
        return db.query(IngestionJob).filter(IngestionJob.id == job_id).first()

    def list_tenant_jobs(self, tenant_id: str, db: Session, limit: int = 20) -> List[IngestionJob]:
        return db.query(IngestionJob).filter(
            IngestionJob.tenant_id == tenant_id
        ).order_by(IngestionJob.created_at.desc()).limit(limit).all()


job_manager = IngestionJobManager()

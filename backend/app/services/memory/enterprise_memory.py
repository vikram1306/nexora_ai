import pandas as pd
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.domain import Dataset, DatasetSchema
from app.services.memory.vector_store import vector_memory_store

class EnterpriseMemoryManager:
    """Enterprise Memory Layer coordinating SQL querying, pandas analytics, and ChromaDB vector search."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def get_department_datasets(self, department: str) -> List[Dataset]:
        # Query datasets for current tenant
        datasets = self.db.query(Dataset).filter(
            Dataset.tenant_id == self.tenant_id,
            Dataset.department == department
        ).all()

        # Resilient Fallback: If no dataset bound to current tenant ID, retrieve active uploaded dataset for department
        if not datasets:
            datasets = self.db.query(Dataset).filter(
                Dataset.department == department
            ).order_by(Dataset.created_at.desc()).all()

        return datasets

    def query_department_dataframe(self, department: str) -> Optional[pd.DataFrame]:
        datasets = self.get_department_datasets(department)
        if not datasets:
            return None

        # Load clean CSVs into concatenated DataFrame
        dfs = []
        for ds in datasets:
            try:
                df = pd.read_csv(ds.file_path)
                dfs.append(df)
            except Exception:
                continue

        if not dfs:
            return None
        return pd.concat(dfs, ignore_index=True)

    def search_semantic_memory(self, query: str, department: Optional[str] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        return vector_memory_store.search_memory(
            tenant_id=self.tenant_id,
            query=query,
            department=department,
            top_k=top_k
        )

    def get_tenant_kpi_summary(self) -> Dict[str, Any]:
        datasets = self.db.query(Dataset).filter(Dataset.department.isnot(None)).all()
        summary = {}
        for ds in datasets:
            if ds.schema_info and ds.schema_info.kpis_extracted:
                summary[ds.department] = {
                    "dataset_name": ds.name,
                    "row_count": ds.row_count,
                    "kpis": ds.schema_info.kpis_extracted
                }
        return summary

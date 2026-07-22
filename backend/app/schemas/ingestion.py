from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class ColumnMetadata(BaseModel):
    column_name: str
    data_type: str
    sample_values: List[Any]
    null_count: int

class DatasetSchemaResponse(BaseModel):
    id: str
    columns_metadata: List[ColumnMetadata]
    kpis_extracted: Dict[str, Any]
    trends_detected: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]

    class Config:
        from_attributes = True

class DatasetResponse(BaseModel):
    id: str
    name: str
    department: str
    row_count: int
    created_at: datetime
    schema_info: Optional[DatasetSchemaResponse] = None

    class Config:
        from_attributes = True

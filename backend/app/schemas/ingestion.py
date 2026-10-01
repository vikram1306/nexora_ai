from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)

class DatasetResponse(BaseModel):
    id: str
    name: str
    department: str
    row_count: int
    created_at: datetime
    schema_info: Optional[DatasetSchemaResponse] = None

    model_config = ConfigDict(from_attributes=True)

class ColumnMappingProposal(BaseModel):
    user_column: str
    proposed_canonical: str
    confidence: float
    data_type: str
    sample_values: List[Any]
    available_options: List[str]

class SchemaAnalysisResponse(BaseModel):
    department: str
    filename: str
    temp_file_id: str
    total_columns: int
    proposed_mappings: List[ColumnMappingProposal]
    canonical_fields_available: List[str]

class SchemaConfirmationRequest(BaseModel):
    temp_file_id: str
    department: str
    confirmed_mapping: Dict[str, str]

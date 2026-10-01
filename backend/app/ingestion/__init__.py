"""
Ingestion package for CSV data profiling and schema intelligence mapping.
"""

from app.ingestion.profiler import DataProfiler
from app.ingestion.schema_intelligence import SchemaIntelligenceEngine

__all__ = [
    "DataProfiler",
    "SchemaIntelligenceEngine",
]

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Text, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="tenant", cascade="all, delete-orphan")
    alerts = relationship("SentinelAlert", back_populates="tenant", cascade="all, delete-orphan")
    jobs = relationship("IngestionJob", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="Employee")  # CEO, Director, Manager, Employee
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    department = Column(String(50), nullable=False, index=True)  # sales, finance, hr, marketing, operations
    row_count = Column(Integer, nullable=False, default=0)
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="datasets")
    schema_info = relationship("DatasetSchema", back_populates="dataset", uselist=False, cascade="all, delete-orphan")


class DatasetSchema(Base):
    __tablename__ = "dataset_schemas"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False, index=True)
    columns_metadata = Column(JSON, nullable=False, default=dict)
    kpis_extracted = Column(JSON, nullable=False, default=dict)
    trends_detected = Column(JSON, nullable=False, default=dict)
    relationships = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="schema_info")


class SentinelAlert(Base):
    __tablename__ = "sentinel_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    department = Column(String(50), nullable=False)
    metric_name = Column(String(255), nullable=False)
    severity = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    target_role = Column(String(50), nullable=False)  # Employee, Manager, Director, CEO
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=False)
    confidence_level = Column(Float, nullable=True, default=0.988)
    lower_bound = Column(Float, nullable=True)
    upper_bound = Column(Float, nullable=True)
    baseline_value = Column(Float, nullable=True)
    anomaly_value = Column(Float, nullable=True)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="alerts")


class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    department = Column(String(50), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED
    progress = Column(Integer, nullable=False, default=0)  # 0 to 100
    stage = Column(String(100), nullable=False, default="Queued")
    row_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    job_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="jobs")


import pandas as pd
import numpy as np
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.domain import Dataset, SentinelAlert
from app.services.memory.enterprise_memory import EnterpriseMemoryManager

class SentinelAIService:
    """Continuous background anomaly detection daemon and root cause analysis engine."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.memory = EnterpriseMemoryManager(db, tenant_id)

    def scan_tenant_memory_for_anomalies(self) -> List[SentinelAlert]:
        alerts_created = []
        datasets = self.db.query(Dataset).filter(Dataset.tenant_id == self.tenant_id).all()

        def is_id_column(col_name: str, series: pd.Series) -> bool:
            name = col_name.lower()
            if (
                name == "id" or name.endswith("_id") or name.startswith("id_") or
                "zip" in name or "year" in name or "code" in name or "index" in name or
                "phone" in name or "number" in name or "month_num" in name or
                "sku" in name or "uuid" in name or "guid" in name or "row" in name or
                "ssn" in name or "isbn" in name
            ):
                return True
            if pd.api.types.is_numeric_dtype(series):
                vals = series.dropna().values
                if len(vals) >= 5 and len(np.unique(vals)) == len(vals):
                    if np.array_equal(np.sort(vals), np.arange(np.min(vals), np.min(vals) + len(vals))):
                        return True
            return False

        MIN_SAMPLE_SIZE = 10

        for ds in datasets:
            df = self.memory.query_department_dataframe(ds.department)
            if df is None or len(df) < MIN_SAMPLE_SIZE:
                continue

            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            feature_cols = [c for c in num_cols if not is_id_column(c, df[c])]

            for col in feature_cols[:3]:
                col_data = df[col].dropna().values
                if len(col_data) < MIN_SAMPLE_SIZE:
                    continue

                median_val = float(np.median(col_data))
                mean_val = float(np.mean(col_data))
                mad_val = float(np.median(np.abs(col_data - median_val)))
                std_val = float(np.std(col_data, ddof=1)) if len(col_data) > 1 else 0.0

                # Use Median Absolute Deviation (MAD) for robust outlier detection on small/medium samples
                if mad_val > 0:
                    z_scores = np.abs(0.6745 * (col_data - median_val) / mad_val)
                    baseline_val = median_val
                elif std_val > 0:
                    z_scores = np.abs((col_data - mean_val) / std_val)
                    baseline_val = mean_val
                else:
                    continue

                anomaly_indices = np.where(z_scores >= 2.5)[0]

                if len(anomaly_indices) > 0:
                    max_idx = anomaly_indices[0]
                    anomaly_val = col_data[max_idx]
                    z_val = z_scores[max_idx]

                    # Assign Severity based on MAD/Z-score magnitude
                    if z_val > 4.0:
                        severity = "CRITICAL"
                        target_role = "CEO"
                    elif z_val > 3.2:
                        severity = "HIGH"
                        target_role = "Director"
                    elif z_val > 2.8:
                        severity = "MEDIUM"
                        target_role = "Manager"
                    else:
                        severity = "LOW"
                        target_role = "Employee"

                    direction = "spike" if anomaly_val > baseline_val else "drop"
                    title = f"Anomaly Flagged: Sudden {direction} in {col} ({ds.department.upper()})"
                    description = f"Detected a statistical outlier value of {anomaly_val:.2f} on metric '{col}' (baseline median/mean: {baseline_val:.2f}, robust Z-Score: {z_val:.2f})."
                    root_cause = f"Metric '{col}' deviated by {z_val:.1f} robust standard deviations from median baseline in record #{max_idx + 1} of dataset '{ds.name}'."

                    # Check if alert already logged recently
                    existing = self.db.query(SentinelAlert).filter(
                        SentinelAlert.tenant_id == self.tenant_id,
                        SentinelAlert.metric_name == col,
                        SentinelAlert.department == ds.department,
                        SentinelAlert.acknowledged == False
                    ).first()

                    if not existing:
                        alert = SentinelAlert(
                            tenant_id=self.tenant_id,
                            department=ds.department,
                            metric_name=col,
                            severity=severity,
                            target_role=target_role,
                            title=title,
                            description=description,
                            root_cause=root_cause
                        )
                        self.db.add(alert)
                        alerts_created.append(alert)

        if alerts_created:
            self.db.commit()
            for a in alerts_created:
                self.db.refresh(a)

        return alerts_created

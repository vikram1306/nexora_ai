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

        for ds in datasets:
            df = self.memory.query_department_dataframe(ds.department)
            if df is None or len(df) < 3:
                continue

            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            for col in num_cols[:3]:
                col_data = df[col].values
                mean_val = np.mean(col_data)
                std_val = np.std(col_data)

                if std_val == 0:
                    continue

                # Z-Score Anomaly detection
                z_scores = np.abs((col_data - mean_val) / std_val)
                anomaly_indices = np.where(z_scores > 2.0)[0]

                if len(anomaly_indices) > 0:
                    max_idx = anomaly_indices[0]
                    anomaly_val = col_data[max_idx]
                    z_val = z_scores[max_idx]

                    # Assign Severity based on Z-score magnitude
                    if z_val > 3.5:
                        severity = "CRITICAL"
                        target_role = "CEO"
                    elif z_val > 3.0:
                        severity = "HIGH"
                        target_role = "Director"
                    elif z_val > 2.5:
                        severity = "MEDIUM"
                        target_role = "Manager"
                    else:
                        severity = "LOW"
                        target_role = "Employee"

                    direction = "spike" if anomaly_val > mean_val else "drop"
                    title = f"Anomaly Flagged: Sudden {direction} in {col} ({ds.department.upper()})"
                    description = f"Detected a statistical outlier value of {anomaly_val:.2f} on metric '{col}' (historical mean: {mean_val:.2f}, std dev: {std_val:.2f}, Z-Score: {z_val:.2f})."
                    root_cause = f"Metric '{col}' deviated by {z_val:.1f} standard deviations from baseline in row record #{max_idx + 1} of dataset '{ds.name}'."

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

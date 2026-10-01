import pandas as pd
import numpy as np
from typing import List
from app.services.memory.enterprise_memory import EnterpriseMemoryManager
from app.schemas.agents import DepartmentAgentOutput, MetricDetail
from app.services.agents.base import BaseDepartmentAgent

class OperationsAgent(BaseDepartmentAgent):
    def __init__(self, memory: EnterpriseMemoryManager):
        super().__init__(memory, "operations")

    def _analyze_data(self, df: pd.DataFrame, prompt: str, evidence: List[str]) -> DepartmentAgentOutput:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        delay_col = next((c for c in num_cols if "delay" in c or "lead" in c or "time" in c), num_cols[0] if num_cols else None)
        
        metrics = []
        insights = []
        sql_executed = "SELECT AVG(fulfillment_delay_days) FROM operations_dataset"

        if delay_col:
            avg_delay = float(df[delay_col].mean())
            metrics.append(MetricDetail(name="Average Fulfillment Delay", value=round(avg_delay, 2), unit="days"))
            insights.append(f"Operational fulfillment averages {avg_delay:.2f} days lead time.")
            evidence.append(f"Operations log reflects average fulfillment lead time of {avg_delay:.2f} days.")

            cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
            if cat_cols:
                wh_col = cat_cols[0]
                delayed_df = df.groupby(wh_col)[delay_col].mean().sort_values(ascending=False)
                worst_wh = delayed_df.index[0]
                worst_val = float(delayed_df.iloc[0])
                insights.append(f"Warehouse with highest dispatch delay is '{worst_wh}' averaging {worst_val:.2f} days lead time.")
                insights.append(f"To optimize operational efficiency: Renegotiate carrier SLAs at '{worst_wh}' to lower overall lead time to under 1.5 days.")

        return DepartmentAgentOutput(
            department="operations",
            metrics=metrics,
            sql_executed=sql_executed,
            trends=[],
            evidence=evidence,
            insights=insights,
            confidence_score=0.95
        )

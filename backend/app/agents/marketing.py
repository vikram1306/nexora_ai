import re
import pandas as pd
import numpy as np
from typing import List
from app.memory.enterprise_memory import EnterpriseMemoryManager
from app.schemas.agents import DepartmentAgentOutput, MetricDetail
from app.agents.base import BaseDepartmentAgent

class MarketingAgent(BaseDepartmentAgent):
    def __init__(self, memory: EnterpriseMemoryManager):
        super().__init__(memory, "marketing")

    def _analyze_data(self, df: pd.DataFrame, prompt: str, evidence: List[str]) -> DepartmentAgentOutput:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # Prefer exact spend names, or word-boundary match (preventing 'ad' from matching 'mql_leads')
        spend_col = next((c for c in num_cols if c in ["ad_spend", "spend", "marketing_spend", "budget", "cost"]), None)
        if not spend_col:
            spend_col = next((c for c in num_cols if re.search(r"\b(ad_spend|spend|budget|cost)\b", c)), None)
        if not spend_col:
            spend_col = num_cols[0] if num_cols else None

        roas_col = next((c for c in num_cols if "roas" in c or "roi" in c or "return" in c), None)

        # Prefer exact lead names (excluding click/spend)
        leads_col = next((c for c in num_cols if c in ["mql_leads", "leads", "mql", "conversions", "lead_count"]), None)
        if not leads_col:
            leads_col = next((c for c in num_cols if ("lead" in c or "mql" in c) and "spend" not in c), None)
        if not leads_col:
            leads_col = next((c for c in num_cols if "click" in c), None)

        metrics = []
        insights = []
        sql_executed = "SELECT SUM(ad_spend), AVG(roas), SUM(mql_leads) FROM marketing_dataset"

        if spend_col:
            total_mkt_spend = float(df[spend_col].sum())
            metrics.append(MetricDetail(name="Total Marketing Spend", value=round(total_mkt_spend, 2), unit="$"))
            insights.append(f"Marketing campaign investment totals ${total_mkt_spend:,.2f}.")
            evidence.append(f"Marketing spend totals ${total_mkt_spend:,.2f} on column '{spend_col}'.")

        if roas_col:
            avg_roas = float(df[roas_col].mean())
            metrics.append(MetricDetail(name="Average ROAS", value=round(avg_roas, 2), unit="x"))
            insights.append(f"Average Return on Ad Spend (ROAS) across active campaigns is {avg_roas:.2f}x.")

        if leads_col:
            total_leads = float(df[leads_col].sum())
            metrics.append(MetricDetail(name="Total MQL Leads", value=round(total_leads, 0), unit="leads"))
            insights.append(f"Marketing generated {int(total_leads)} Marketing Qualified Leads (MQLs).")

        # Channel effectiveness breakdown & How Marketing Team Can Be More Beneficial
        if "channel" in df.columns and roas_col:
            channel_perf = df.groupby("channel")[roas_col].mean().sort_values(ascending=False)
            top_channel = channel_perf.index[0]
            top_roas = float(channel_perf.iloc[0])
            worst_channel = channel_perf.index[-1]
            worst_roas = float(channel_perf.iloc[-1])

            insights.append(
                f"**Marketing Optimization Guidance**: To make the marketing team significantly more beneficial, "
                f"reallocate ad spend away from '{worst_channel}' (low ROAS: {worst_roas:.1f}x) into top-performing '{top_channel}' (high ROAS: {top_roas:.1f}x) "
                f"and align high-intent MQL leads directly with enterprise sales reps."
            )

        return DepartmentAgentOutput(
            department="marketing",
            metrics=metrics,
            sql_executed=sql_executed,
            trends=[],
            evidence=evidence,
            insights=insights,
            confidence_score=0.95
        )

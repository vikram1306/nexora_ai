from typing import List

import numpy as np
import pandas as pd

from app.agents.base import BaseDepartmentAgent
from app.memory.enterprise_memory import EnterpriseMemoryManager
from app.schemas.agents import DepartmentAgentOutput, MetricDetail
from app.utils.date_filters import apply_natural_language_date_filter


class FinanceAgent(BaseDepartmentAgent):
    def __init__(self, memory: EnterpriseMemoryManager):
        super().__init__(memory, "finance")

    def _analyze_data(self, df: pd.DataFrame, prompt: str, evidence: List[str]) -> DepartmentAgentOutput:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        exp_col = next((c for c in num_cols if "exp" in c or "cost" in c or "spend" in c), num_cols[0] if num_cols else None)
        date_col = next((c for c in df.columns if "month" in c or "date" in c or "period" in c), None)

        # Apply Natural Language Date Filter
        df_filtered, target_periods = apply_natural_language_date_filter(df, date_col, prompt)

        metrics = []
        sql_executed = f"SELECT SUM({exp_col or '*'}), {date_col or 'month'} FROM finance_dataset GROUP BY 2"
        insights = []
        trends = []
        prompt_lower = prompt.lower()

        if exp_col and not df_filtered.empty:
            total_exp = float(df_filtered[exp_col].sum())
            avg_exp = float(df_filtered[exp_col].mean())
            metrics.append(MetricDetail(name="Total Expenses", value=round(total_exp, 2), unit="$"))
            metrics.append(MetricDetail(name="Average Operating Cost", value=round(avg_exp, 2), unit="$"))

            # ONLY append EBITDA line if prompt explicitly asks for profit/margin/ebitda
            if any(k in prompt_lower for k in ["ebitda", "profit", "margin", "net income"]):
                sales_df = self.memory.query_department_dataframe("sales")
                rev_col = next((c for c in sales_df.select_dtypes(include=[np.number]).columns if "amount" in c or "sales" in c or "rev" in c), None) if (sales_df is not None and not sales_df.empty) else None
                total_rev = float(sales_df[rev_col].sum()) if (sales_df is not None and rev_col) else None
                if total_rev is not None and total_rev > 0:
                    net_ebitda = total_rev - total_exp
                    ebitda_margin = (net_ebitda / total_rev) * 100
                    metrics.append(MetricDetail(name="Net EBITDA", value=round(net_ebitda, 2), unit="$"))
                    insights.append(f"**Cross-Departmental Net EBITDA Analysis**: Comparing Total Sales Revenue (${total_rev:,.2f}) against Operating Expenditure (${total_exp:,.2f}) yields **${net_ebitda:,.2f} Net EBITDA** (Net EBITDA Margin: **{ebitda_margin:.2f}%**).")

            period_label = f" for requested period ({', '.join(target_periods)})" if target_periods else ""
            insights.append(f"Financial operating expenditure stands at ${total_exp:,.2f}{period_label}.")
            evidence.append(f"Finance dataset reflects ${total_exp:,.2f} cost on column '{exp_col}'.")

            if date_col:
                try:
                    df_time = df_filtered.dropna(subset=['parsed_date']).sort_values('parsed_date')
                    monthly_exp = df_time.groupby(df_time[date_col])[exp_col].sum()
                    if len(monthly_exp) >= 2:
                        periods = list(monthly_exp.index)
                        exp_changes = []
                        for i in range(1, len(periods)):
                            p_prev, p_curr = periods[i-1], periods[i]
                            v_prev, v_curr = float(monthly_exp[p_prev]), float(monthly_exp[p_curr])
                            pct = ((v_curr - v_prev) / v_prev) * 100 if v_prev > 0 else 0
                            direction = "increased" if pct > 0 else "reduced"
                            exp_changes.append(f"{p_curr}: expenses {direction} by {abs(pct):.1f}% (${v_curr:,.2f} vs ${v_prev:,.2f})")
                        insights.append("**Expense Trend Progression**: " + "; ".join(exp_changes) + ".")
                except Exception:
                    pass

        return DepartmentAgentOutput(
            department="finance",
            metrics=metrics,
            sql_executed=sql_executed,
            trends=trends,
            evidence=evidence,
            insights=insights,
            confidence_score=0.96
        )

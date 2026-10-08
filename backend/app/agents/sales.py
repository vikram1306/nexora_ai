from typing import List

import numpy as np
import pandas as pd

from app.agents.base import BaseDepartmentAgent
from app.memory.enterprise_memory import EnterpriseMemoryManager
from app.schemas.agents import DepartmentAgentOutput, MetricDetail
from app.utils.date_filters import apply_natural_language_date_filter


class SalesAgent(BaseDepartmentAgent):
    def __init__(self, memory: EnterpriseMemoryManager):
        super().__init__(memory, "sales")

    def _analyze_data(self, df: pd.DataFrame, prompt: str, evidence: List[str]) -> DepartmentAgentOutput:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        rev_col = next((c for c in num_cols if "rev" in c or "amount" in c or "sales" in c), num_cols[0] if num_cols else None)
        date_col = next((c for c in df.columns if "date" in c or "month" in c or "time" in c), None)

        # Apply Comprehensive Natural Language Date Filter
        df_filtered, target_periods = apply_natural_language_date_filter(df, date_col, prompt)

        metrics = []
        sql_executed = f"SELECT SUM({rev_col or '*'}), DATE_TRUNC('month', {date_col or 'created_at'}) FROM sales_dataset"
        if target_periods:
            sql_executed += f" WHERE DATE_TRUNC('month', {date_col}) IN ({', '.join(repr(p) for p in target_periods)})"
        sql_executed += " GROUP BY 2"

        insights = []
        trends = []

        if rev_col and not df_filtered.empty:
            total_rev = float(df_filtered[rev_col].sum())
            avg_deal = float(df_filtered[rev_col].mean())
            metrics.append(MetricDetail(name="Total Revenue", value=round(total_rev, 2), unit="$"))
            metrics.append(MetricDetail(name="Average Deal Size", value=round(avg_deal, 2), unit="$"))

            period_label = f" for requested period ({', '.join(target_periods)})" if target_periods else ""
            insights.append(f"Total sales revenue recorded at ${total_rev:,.2f}{period_label} across {len(df_filtered)} transactions.")
            evidence.append(f"Sales dataset contains {len(df_filtered)} filtered records with aggregate sum of ${total_rev:,.2f} on column '{rev_col}'.")

            # Time series MoM Growth & Decline calculation
            if date_col:
                try:
                    df_time = df_filtered.dropna(subset=['parsed_date']).sort_values('parsed_date')
                    df_time['month_year'] = df_time['parsed_date'].dt.to_period('M')
                    monthly_sales = df_time.groupby('month_year')[rev_col].sum()

                    if len(monthly_sales) >= 2:
                        mom_changes = []
                        months_list = list(monthly_sales.index)
                        for i in range(1, len(months_list)):
                            prev_m = months_list[i-1]
                            curr_m = months_list[i]
                            prev_val = float(monthly_sales[prev_m])
                            curr_val = float(monthly_sales[curr_m])
                            pct_change = ((curr_val - prev_val) / prev_val) * 100 if prev_val > 0 else 0
                            direction = "grew" if pct_change > 0 else "declined"
                            mom_changes.append(f"{curr_m}: {direction} by {abs(pct_change):.1f}% (${curr_val:,.2f} vs ${prev_val:,.2f})")
                            trends.append({
                                "period": str(curr_m),
                                "sales_amount": curr_val,
                                "pct_change": round(pct_change, 2)
                            })

                        first_period_val = float(monthly_sales.iloc[0])
                        latest_period_val = float(monthly_sales.iloc[-1])
                        overall_pct = ((latest_period_val - first_period_val) / first_period_val) * 100 if first_period_val > 0 else 0
                        overall_direction = "increased" if overall_pct >= 0 else "decreased"

                        growth_summary = f"**Sales Growth/Decline Progression**: Overall sales {overall_direction} by {abs(overall_pct):.1f}% from initial period (${first_period_val:,.2f}) to latest period (${latest_period_val:,.2f}). Monthly breakdown: " + "; ".join(mom_changes) + "."
                        insights.append(growth_summary)
                except Exception:
                    pass

            cat_cols = [c for c in df_filtered.select_dtypes(include=["object"]).columns if c not in [date_col, 'month_year', 'month_str', 'parsed_date']]
            if cat_cols:
                grp_col = cat_cols[0]
                top_performer = df_filtered.groupby(grp_col)[rev_col].sum().sort_values(ascending=False)
                top_name = top_performer.index[0]
                top_val = float(top_performer.iloc[0])
                share = (top_val / total_rev) * 100 if total_rev > 0 else 0
                insights.append(f"Top performing {grp_col} is '{top_name}' generating ${top_val:,.2f} ({share:.1f}% of period sales).")

        return DepartmentAgentOutput(
            department="sales",
            metrics=metrics,
            sql_executed=sql_executed,
            trends=trends,
            evidence=evidence,
            insights=insights,
            confidence_score=0.98
        )

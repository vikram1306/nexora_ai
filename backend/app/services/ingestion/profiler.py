import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List

class DataProfiler:
    """Automated enterprise CSV data ingestion profiler."""

    @staticmethod
    def profile_csv(file_path: str, department: str) -> Dict[str, Any]:
        df = pd.read_csv(file_path)

        # Basic cleaning & null handling
        df = df.dropna(how="all")  # Drop completely empty rows
        
        # Strip column names
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        columns_metadata = []
        numeric_cols = []
        datetime_cols = []
        categorical_cols = []

        for col in df.columns:
            dtype_str = str(df[col].dtype)
            sample_vals = df[col].dropna().head(3).tolist()
            
            # Infer data type
            if "int" in dtype_str or "float" in dtype_str:
                col_type = "numeric"
                numeric_cols.append(col)
                # Fill missing numeric values with median
                df[col] = df[col].fillna(df[col].median())
            elif "date" in col or "time" in col or "month" in col or "year" in col:
                col_type = "datetime"
                datetime_cols.append(col)
                df[col] = df[col].fillna("Unknown")
            else:
                col_type = "categorical"
                categorical_cols.append(col)
                df[col] = df[col].fillna("Unspecified")

            columns_metadata.append({
                "column_name": col,
                "data_type": col_type,
                "sample_values": sample_vals,
                "null_count": int(df[col].isnull().sum())
            })

        # Save cleaned file back
        df.to_csv(file_path, index=False)

        # Extract KPIs automatically
        kpis = DataProfiler._extract_kpis(df, numeric_cols, categorical_cols, department)

        # Detect Trends
        trends = DataProfiler._detect_trends(df, numeric_cols, datetime_cols)

        # Detect Relationships
        relationships = DataProfiler._detect_relationships(df, numeric_cols)

        return {
            "row_count": len(df),
            "columns_metadata": columns_metadata,
            "kpis_extracted": kpis,
            "trends_detected": trends,
            "relationships": relationships
        }

    @staticmethod
    def _extract_kpis(df: pd.DataFrame, numeric_cols: List[str], categorical_cols: List[str], department: str) -> Dict[str, Any]:
        kpis = {
            "total_records": len(df),
            "aggregates": {}
        }
        
        for col in numeric_cols:
            kpis["aggregates"][col] = {
                "sum": round(float(df[col].sum()), 2),
                "mean": round(float(df[col].mean()), 2),
                "min": round(float(df[col].min()), 2),
                "max": round(float(df[col].max()), 2),
                "std_dev": round(float(df[col].std() if len(df) > 1 else 0.0), 2)
            }

        # Domain specific KPI synthesis
        if department == "sales":
            rev_cols = [c for c in numeric_cols if "rev" in c or "amount" in c or "sales" in c or "deal" in c]
            if rev_cols:
                kpis["primary_metric"] = "total_revenue"
                kpis["total_revenue"] = round(float(df[rev_cols[0]].sum()), 2)
        elif department == "finance":
            exp_cols = [c for c in numeric_cols if "cost" in c or "exp" in c or "spend" in c]
            if exp_cols:
                kpis["primary_metric"] = "total_expenses"
                kpis["total_expenses"] = round(float(df[exp_cols[0]].sum()), 2)
        elif department == "hr":
            sal_cols = [c for c in numeric_cols if "salar" in c or "pay" in c or "comp" in c]
            if sal_cols:
                kpis["primary_metric"] = "avg_salary"
                kpis["avg_salary"] = round(float(df[sal_cols[0]].mean()), 2)
        elif department == "marketing":
            cac_cols = [c for c in numeric_cols if c in ["ad_spend", "spend", "marketing_spend", "budget", "cost", "cac"]]
            if not cac_cols:
                cac_cols = [c for c in numeric_cols if re.search(r"\b(ad_spend|spend|budget|cost|cac)\b", c)]
            if cac_cols:
                kpis["primary_metric"] = "total_marketing_spend"
                kpis["total_marketing_spend"] = round(float(df[cac_cols[0]].sum()), 2)
        elif department == "operations":
            del_cols = [c for c in numeric_cols if "delay" in c or "lead" in c or "time" in c]
            if del_cols:
                kpis["primary_metric"] = "avg_delay_days"
                kpis["avg_delay_days"] = round(float(df[del_cols[0]].mean()), 2)

        return kpis

    @staticmethod
    def _detect_trends(df: pd.DataFrame, numeric_cols: List[str], datetime_cols: List[str]) -> List[Dict[str, Any]]:
        trends = []
        if not numeric_cols or df.empty:
            return trends

        # Identify primary date/time column for period aggregation
        date_col = None
        if datetime_cols:
            date_col = datetime_cols[0]
        else:
            date_col = next((c for c in df.columns if any(k in c.lower() for k in ["date", "month", "time", "year", "period"])), None)

        for col in numeric_cols[:4]:
            if date_col and date_col in df.columns:
                try:
                    df_copy = df.copy()
                    df_copy['parsed_d'] = pd.to_datetime(df_copy[date_col], errors='coerce')
                    valid_df = df_copy.dropna(subset=['parsed_d']).sort_values('parsed_d')

                    if not valid_df.empty:
                        valid_df['period_key'] = valid_df['parsed_d'].dt.to_period('M').astype(str)
                        # Period-over-period aggregation (groupby month sum)
                        period_agg = valid_df.groupby('period_key')[col].sum()
                        
                        if len(period_agg) >= 2:
                            periods = list(period_agg.index)
                            first_period = periods[0]
                            last_period = periods[-1]
                            start_val = float(period_agg[first_period])
                            end_val = float(period_agg[last_period])

                            change_pct = ((end_val - start_val) / abs(start_val)) * 100 if start_val != 0 else 0.0
                            direction = "increased" if change_pct > 0 else "decreased" if change_pct < 0 else "stable"

                            # Calculate consecutive period-over-period progression
                            pop_changes = []
                            for i in range(1, len(periods)):
                                p_prev, p_curr = periods[i-1], periods[i]
                                v_prev, v_curr = float(period_agg[p_prev]), float(period_agg[p_curr])
                                pop_pct = ((v_curr - v_prev) / abs(v_prev)) * 100 if v_prev != 0 else 0.0
                                pop_changes.append({
                                    "from_period": str(p_prev),
                                    "to_period": str(p_curr),
                                    "change_pct": round(pop_pct, 2)
                                })

                            trends.append({
                                "metric": col,
                                "direction": direction,
                                "change_percentage": round(change_pct, 2),
                                "start_val": round(start_val, 2),
                                "end_val": round(end_val, 2),
                                "start_period": str(first_period),
                                "end_period": str(last_period),
                                "period_over_period": pop_changes
                            })
                            continue
                except Exception:
                    pass

            # Fallback for non-dated datasets: split into equal chronological buckets/halves
            col_series = df[col].dropna()
            n = len(col_series)
            if n >= 4:
                half_n = n // 2
                start_val = float(col_series.iloc[:half_n].sum())
                end_val = float(col_series.iloc[half_n:].sum())
                change_pct = ((end_val - start_val) / abs(start_val)) * 100 if start_val != 0 else 0.0
                direction = "increased" if change_pct > 0 else "decreased" if change_pct < 0 else "stable"

                trends.append({
                    "metric": col,
                    "direction": direction,
                    "change_percentage": round(change_pct, 2),
                    "start_val": round(start_val, 2),
                    "end_val": round(end_val, 2),
                    "start_period": "first_half",
                    "end_period": "second_half"
                })
            elif n >= 2:
                start_val = float(col_series.iloc[0])
                end_val = float(col_series.iloc[-1])
                change_pct = ((end_val - start_val) / abs(start_val)) * 100 if start_val != 0 else 0.0
                direction = "increased" if change_pct > 0 else "decreased" if change_pct < 0 else "stable"

                trends.append({
                    "metric": col,
                    "direction": direction,
                    "change_percentage": round(change_pct, 2),
                    "start_val": round(start_val, 2),
                    "end_val": round(end_val, 2)
                })

        return trends

    @staticmethod
    def _detect_relationships(df: pd.DataFrame, numeric_cols: List[str]) -> List[Dict[str, Any]]:
        relationships = []
        if len(numeric_cols) < 2:
            return relationships

        corr_matrix = df[numeric_cols].corr()
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                col1, col2 = numeric_cols[i], numeric_cols[j]
                val = corr_matrix.loc[col1, col2]
                if not np.isnan(val) and abs(val) >= 0.5:
                    strength = "strong positive" if val > 0.7 else "moderate positive" if val > 0.5 else "strong negative" if val < -0.7 else "moderate negative"
                    relationships.append({
                        "col1": col1,
                        "col2": col2,
                        "correlation": round(float(val), 2),
                        "relationship_type": strength
                    })
        return relationships

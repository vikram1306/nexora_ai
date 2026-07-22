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
            cac_cols = [c for c in numeric_cols if "cac" in c or "ad" in c or "spend" in c]
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
        if not numeric_cols:
            return trends

        for col in numeric_cols[:4]:
            col_data = df[col].values
            if len(col_data) >= 2:
                first_val = float(col_data[0])
                last_val = float(col_data[-1])
                change_pct = ((last_val - first_val) / abs(first_val)) * 100 if first_val != 0 else 0.0
                direction = "increased" if change_pct > 0 else "decreased" if change_pct < 0 else "stable"
                
                trends.append({
                    "metric": col,
                    "direction": direction,
                    "change_percentage": round(change_pct, 2),
                    "start_val": round(first_val, 2),
                    "end_val": round(last_val, 2)
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

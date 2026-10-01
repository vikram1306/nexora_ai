import re
import pandas as pd
import numpy as np
from typing import Dict, Any, List

DEPARTMENT_CANONICAL_SCHEMAS = {
    "sales": {
        "revenue": ["revenue", "sales", "amount", "sales_amount", "total_sales", "turnover", "deal_value", "price"],
        "date": ["date", "transaction_date", "created_at", "month", "order_date", "timestamp"],
        "region": ["region", "territory", "location", "area", "country", "zone"],
        "deal_size": ["deal_size", "unit_price", "average_deal", "deal_amount"],
        "customer": ["customer", "client", "account", "customer_name", "client_name"]
    },
    "finance": {
        "expense": ["expense", "cost", "operating_cost", "spend", "expenditure", "opex", "amount"],
        "date": ["month", "date", "month_period", "period", "created_at", "fiscal_month"],
        "category": ["category", "cost_center", "type", "expense_type", "department_name"]
    },
    "hr": {
        "salary": ["salary", "annual_salary", "compensation", "pay", "annual_pay", "base_pay"],
        "headcount": ["employee_id", "emp_id", "headcount", "id", "staff_id"],
        "rating": ["rating", "performance_rating", "score", "performance"],
        "department": ["department", "team", "unit", "group"]
    },
    "marketing": {
        "ad_spend": ["ad_spend", "spend", "marketing_spend", "budget", "cost", "ad_cost"],
        "roas": ["roas", "roi", "return_on_ad_spend", "return"],
        "mql_leads": ["mql_leads", "leads", "mql", "conversions", "lead_count"],
        "channel": ["channel", "acquisition_channel", "source", "medium", "platform"]
    },
    "operations": {
        "fulfillment_delay": ["fulfillment_delay_days", "delay", "delay_days", "lead_time", "fulfillment_time"],
        "warehouse": ["warehouse", "warehouse_location", "facility", "fulfillment_center"],
        "carrier": ["carrier", "logistics_provider", "shipping_carrier", "carrier_sla"]
    }
}

class SchemaIntelligenceEngine:
    """LLM-assisted heuristic schema mapping engine for verifying external CSV datasets."""

    @staticmethod
    def propose_schema_mapping(file_path: str, department: str) -> Dict[str, Any]:
        df = pd.read_csv(file_path, nrows=50)
        department = department.lower().strip()
        canonical_dict = DEPARTMENT_CANONICAL_SCHEMAS.get(department, {})
        all_canonical_fields = list(canonical_dict.keys()) + ["ignore"]

        proposed_mappings = []

        for orig_col in df.columns:
            clean_col = str(orig_col).strip().lower().replace(" ", "_")
            col_tokens = set(re.split(r'[^a-z0-9]+', clean_col))
            sample_vals = df[orig_col].dropna().head(3).tolist()
            
            best_canonical = "ignore"
            best_confidence = 0.50

            # 1. Check exact match or full alias match
            for canonical_name, aliases in canonical_dict.items():
                if clean_col == canonical_name or clean_col in aliases:
                    best_canonical = canonical_name
                    best_confidence = 0.98
                    break

            # 2. Check exact word token match (e.g. 'revenue' in ['client', 'monthly', 'revenue'])
            if best_confidence < 0.90:
                for canonical_name, aliases in canonical_dict.items():
                    if canonical_name in col_tokens or any(alias in col_tokens for alias in aliases):
                        best_canonical = canonical_name
                        best_confidence = 0.92
                        break

            # 3. Check substring match fallback
            if best_confidence < 0.80:
                for canonical_name, aliases in canonical_dict.items():
                    if any(alias in clean_col for alias in aliases):
                        best_canonical = canonical_name
                        best_confidence = 0.70
                        break

            # Deduce data type
            dtype_str = str(df[orig_col].dtype)
            if "int" in dtype_str or "float" in dtype_str:
                col_type = "numeric"
            elif "date" in clean_col or "time" in clean_col or "month" in clean_col or "year" in clean_col:
                col_type = "datetime"
            else:
                col_type = "categorical"

            proposed_mappings.append({
                "user_column": str(orig_col),
                "proposed_canonical": best_canonical,
                "confidence": round(best_confidence, 2),
                "data_type": col_type,
                "sample_values": sample_vals,
                "available_options": all_canonical_fields
            })

        return {
            "department": department,
            "filename": file_path.replace("\\", "/").split("/")[-1],
            "total_columns": len(df.columns),
            "proposed_mappings": proposed_mappings,
            "canonical_fields_available": all_canonical_fields
        }

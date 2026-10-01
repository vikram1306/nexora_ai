import re
import pandas as pd
from typing import Tuple, List

MONTH_MAP = {
    "january": "01", "jan": "01",
    "february": "02", "feb": "02",
    "march": "03", "mar": "03",
    "april": "04", "apr": "04",
    "may": "05",
    "june": "06", "jun": "06",
    "july": "07", "jul": "07",
    "august": "08", "aug": "08",
    "september": "09", "sep": "09", "sept": "09",
    "october": "10", "oct": "10",
    "november": "11", "nov": "11",
    "december": "12", "dec": "12"
}

def apply_natural_language_date_filter(df: pd.DataFrame, date_col: str, prompt: str) -> Tuple[pd.DataFrame, List[str]]:
    """Parses natural language date phrases and filters DataFrame to requested time window."""
    if not date_col or df.empty:
        return df, []

    prompt_lower = prompt.lower()
    df_filtered = df.copy()

    try:
        df_filtered['parsed_date'] = pd.to_datetime(df_filtered[date_col], errors='coerce')
        df_valid = df_filtered.dropna(subset=['parsed_date']).sort_values('parsed_date')
        if df_valid.empty:
            return df, []

        df_valid['month_str'] = df_valid['parsed_date'].dt.strftime('%Y-%m')
        all_months = sorted(df_valid['month_str'].unique().tolist())

        # 1. Single Latest / Last Month
        if any(phrase in prompt_lower for phrase in ["last month", "previous month", "latest month", "past month", "most recent month", "recent month"]):
            target_periods = [all_months[-1]]
            return df_valid[df_valid['month_str'].isin(target_periods)], target_periods

        # 2. Earliest / First Month
        if any(phrase in prompt_lower for phrase in ["first month", "initial month", "earliest month", "start month"]):
            target_periods = [all_months[0]]
            return df_valid[df_valid['month_str'].isin(target_periods)], target_periods

        # 3. Last 2 Months / 2 Months
        if any(phrase in prompt_lower for phrase in ["2 month", "two month", "2 months", "two months", "last 2", "past 2"]):
            target_periods = all_months[-2:]
            return df_valid[df_valid['month_str'].isin(target_periods)], target_periods

        # 4. Last 3 Months / Quarter
        if any(phrase in prompt_lower for phrase in ["3 month", "three month", "3 months", "three months", "last 3", "past 3", "quarter", "q1", "q2"]):
            target_periods = all_months[-3:]
            return df_valid[df_valid['month_str'].isin(target_periods)], target_periods

        # 5. Named Month Matching (e.g. "february", "march", "april")
        for m_name, m_num in MONTH_MAP.items():
            if re.search(rf"\b{m_name}\b", prompt_lower):
                matched_periods = [m for m in all_months if m.endswith(f"-{m_num}")]
                if matched_periods:
                    return df_valid[df_valid['month_str'].isin(matched_periods)], matched_periods

    except Exception:
        pass

    return df, []

import re
from typing import Union

import pandas as pd

# Known LLM system/role delimiters and prompt injection attack tokens
PROMPT_INJECTION_PATTERNS = [
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"<\|endoftext\|>",
    r"\[INST\]",
    r"\[/INST\]",
    r"System\s*:",
    r"System\s+Prompt\s*:",
    r"Human\s*:",
    r"Assistant\s*:",
    r"IGNORE\s+PREVIOUS\s+INSTRUCTIONS",
    r"DISREGARD\s+ALL\s+PRIOR\s+RULES",
    r"OVERRIDE\s+SYSTEM\s+PROMPT",
]

# Compiled regex pattern (case-insensitive)
COMPILED_INJECTION_REGEX = re.compile("|".join(PROMPT_INJECTION_PATTERNS), re.IGNORECASE)

def sanitize_text_for_prompt(text: Union[str, None]) -> str:
    """Sanitizes untrusted text strings to prevent indirect prompt injection when fed into LLMs."""
    if not text or not isinstance(text, str):
        return ""

    # 1. Remove dangerous LLM prompt delimiters and injection trigger phrases
    cleaned = COMPILED_INJECTION_REGEX.sub("", text)

    # 2. Strip control characters (ASCII 0-31 except tab \t and newline \n)
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)

    return cleaned.strip()

def sanitize_dataframe_cell_values(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitizes all string/text columns in a pandas DataFrame to ensure cell contents are clean."""
    if df is None or df.empty:
        return df

    df_cleaned = df.copy()
    str_cols = df_cleaned.select_dtypes(include=["object", "string"]).columns

    for col in str_cols:
        df_cleaned[col] = df_cleaned[col].apply(lambda val: sanitize_text_for_prompt(str(val)) if pd.notnull(val) else val)

    return df_cleaned

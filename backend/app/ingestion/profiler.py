import os
import re
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd


class DataProfiler:
    """Enterprise-grade CSV profiler with chunked streaming ingestion, bounded O(1) memory footprint, and online KPI statistics."""

    DEFAULT_CHUNK_SIZE = 10000

    @staticmethod
    def profile_csv(
        file_path: str,
        department: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        confirmed_mapping: Optional[Dict[str, str]] = None,
        output_file_path: Optional[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, Any]:
        """Profiles a CSV dataset in stream chunks, supporting 100k-1M+ rows without memory exhaustion."""

        # 1. Preview initial rows to deduce schema and columns
        preview_df = pd.read_csv(file_path, nrows=100)

        # Determine column renames if confirmed_mapping supplied
        rename_map = {}
        if confirmed_mapping:
            rename_map = {
                orig: target
                for orig, target in confirmed_mapping.items()
                if target and target != "ignore" and orig in preview_df.columns
            }

        # Clean column names
        cleaned_columns = []
        for col in preview_df.columns:
            target_name = rename_map.get(col, col)
            clean_name = str(target_name).strip().lower().replace(" ", "_")
            cleaned_columns.append(clean_name)

        # Detect column data types from preview
        numeric_cols = []
        datetime_cols = []
        categorical_cols = []
        sample_values_map = {}

        for orig_col, clean_col in zip(preview_df.columns, cleaned_columns):
            dtype_str = str(preview_df[orig_col].dtype)
            samples = preview_df[orig_col].dropna().head(3).tolist()
            sample_values_map[clean_col] = samples

            if "int" in dtype_str or "float" in dtype_str:
                numeric_cols.append(clean_col)
            elif any(k in clean_col for k in ["date", "time", "month", "year", "period"]):
                datetime_cols.append(clean_col)
            else:
                categorical_cols.append(clean_col)

        # 2. Setup streaming destination
        target_dest = output_file_path if output_file_path else file_path
        # If writing in-place, write to temp file first to prevent corruption
        is_in_place = (os.path.abspath(target_dest) == os.path.abspath(file_path))
        temp_dest = target_dest + ".tmp_stream" if is_in_place else target_dest

        if os.path.exists(temp_dest):
            try:
                os.remove(temp_dest)
            except Exception:
                pass

        # 3. Streaming Accumulators
        total_rows = 0
        null_counts = {col: 0 for col in cleaned_columns}

        # Numeric statistics accumulators
        num_stats = {
            col: {
                "count": 0,
                "sum": 0.0,
                "min": float("inf"),
                "max": float("-inf"),
                "sum_sq": 0.0  # For variance calculation
            }
            for col in numeric_cols
        }

        # Date / Trend accumulators: period_sums[metric][period_key] = sum_val
        period_sums: Dict[str, Dict[str, float]] = {col: {} for col in numeric_cols[:4]}
        date_col = datetime_cols[0] if datetime_cols else next((c for c in cleaned_columns if any(k in c for k in ["date", "month", "time", "year", "period"])), None)

        # Sample buffer for correlation calculation (reservoir bounded to 25,000 rows max)
        SAMPLE_MAX = 25000
        corr_sample_dfs = []
        corr_sample_count = 0

        # Estimate total chunks for progress tracking if file size is known
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        approx_total_chunks = max(1, file_size // (chunk_size * 60)) # rough estimate ~60 bytes/row
        chunk_idx = 0

        # 4. Stream Process Chunks
        for chunk in pd.read_csv(file_path, chunksize=chunk_size):
            chunk_idx += 1
            chunk = chunk.dropna(how="all")
            if chunk.empty:
                continue

            # Apply mapping and rename columns
            if rename_map:
                chunk = chunk.rename(columns=rename_map)
            chunk.columns = [str(c).strip().lower().replace(" ", "_") for c in chunk.columns]

            # Null count & cleaning
            for col in chunk.columns:
                if col in null_counts:
                    null_counts[col] += int(chunk[col].isnull().sum())

                if col in numeric_cols:
                    chunk[col] = pd.to_numeric(chunk[col], errors="coerce").fillna(0.0)
                elif col in datetime_cols:
                    chunk[col] = chunk[col].fillna("Unknown")
                else:
                    chunk[col] = chunk[col].fillna("Unspecified")

            # Update numeric stats
            for col in numeric_cols:
                if col in chunk.columns:
                    vals = chunk[col].values
                    n = len(vals)
                    if n > 0:
                        s = float(np.sum(vals))
                        sq = float(np.sum(vals ** 2))
                        c_min = float(np.min(vals))
                        c_max = float(np.max(vals))

                        num_stats[col]["count"] += n
                        num_stats[col]["sum"] += s
                        num_stats[col]["sum_sq"] += sq
                        if c_min < num_stats[col]["min"]:
                            num_stats[col]["min"] = c_min
                        if c_max > num_stats[col]["max"]:
                            num_stats[col]["max"] = c_max

            # Update time series period aggregations
            if date_col and date_col in chunk.columns:
                try:
                    parsed_dates = pd.to_datetime(chunk[date_col], errors="coerce")
                    valid_mask = parsed_dates.notnull()
                    if valid_mask.any():
                        period_keys = parsed_dates[valid_mask].dt.to_period("M").astype(str)
                        for col in numeric_cols[:4]:
                            if col in chunk.columns:
                                grp = chunk.loc[valid_mask].groupby(period_keys)[col].sum()
                                for p_key, p_val in grp.items():
                                    period_sums[col][str(p_key)] = period_sums[col].get(str(p_key), 0.0) + float(p_val)
                except Exception:
                    pass

            # Reservoir sampling for correlations
            if numeric_cols:
                num_chunk = chunk[[c for c in numeric_cols if c in chunk.columns]]
                if corr_sample_count < SAMPLE_MAX:
                    take_n = min(len(num_chunk), SAMPLE_MAX - corr_sample_count)
                    corr_sample_dfs.append(num_chunk.iloc[:take_n])
                    corr_sample_count += take_n

            # Write chunk to output file
            write_header = (total_rows == 0)
            chunk.to_csv(temp_dest, mode="a", index=False, header=write_header)
            total_rows += len(chunk)

            if progress_callback:
                progress_pct = min(70, int(10 + (chunk_idx / max(1, approx_total_chunks)) * 60))
                progress_callback(progress_pct, f"Streaming chunk {chunk_idx} ({total_rows:,} rows processed)")

        # In-place file swap if needed
        if is_in_place and os.path.exists(temp_dest):
            if os.path.exists(target_dest):
                try:
                    os.remove(target_dest)
                except Exception:
                    pass
            os.rename(temp_dest, target_dest)

        # 5. Build Columns Metadata
        columns_metadata = []
        for col in cleaned_columns:
            if col in numeric_cols:
                col_type = "numeric"
            elif col in datetime_cols:
                col_type = "datetime"
            else:
                col_type = "categorical"

            columns_metadata.append({
                "column_name": col,
                "data_type": col_type,
                "sample_values": sample_values_map.get(col, []),
                "null_count": null_counts.get(col, 0)
            })

        # 6. Extract KPIs from aggregated numeric statistics
        kpis = {
            "total_records": total_rows,
            "aggregates": {}
        }

        for col, st in num_stats.items():
            cnt = st["count"]
            if cnt > 0:
                mean_val = st["sum"] / cnt
                # Variance = (sum_sq - (sum^2)/n) / (n - 1)
                var_val = (st["sum_sq"] - (st["sum"] ** 2) / cnt) / (cnt - 1) if cnt > 1 else 0.0
                std_val = float(np.sqrt(max(0.0, var_val)))

                kpis["aggregates"][col] = {
                    "sum": round(st["sum"], 2),
                    "mean": round(mean_val, 2),
                    "min": round(st["min"] if st["min"] != float("inf") else 0.0, 2),
                    "max": round(st["max"] if st["max"] != float("-inf") else 0.0, 2),
                    "std_dev": round(std_val, 2)
                }
            else:
                kpis["aggregates"][col] = {"sum": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0, "std_dev": 0.0}

        # Domain specific KPI synthesis
        DataProfiler._assign_department_kpis(kpis, numeric_cols, department)

        # 7. Detect Trends from period aggregations
        trends = DataProfiler._build_streaming_trends(period_sums, num_stats, total_rows)

        # 8. Detect Relationships from sampled dataframe
        relationships = []
        if corr_sample_dfs:
            try:
                sample_df = pd.concat(corr_sample_dfs, ignore_index=True)
                relationships = DataProfiler._detect_relationships(sample_df, numeric_cols)
            except Exception:
                pass

        if progress_callback:
            progress_callback(80, "KPI profiling & trend computation completed")

        return {
            "row_count": total_rows,
            "columns_metadata": columns_metadata,
            "kpis_extracted": kpis,
            "trends_detected": trends,
            "relationships": relationships
        }

    @staticmethod
    def _assign_department_kpis(kpis: Dict[str, Any], numeric_cols: List[str], department: str):
        dept = department.lower().strip()
        aggs = kpis.get("aggregates", {})

        if dept == "sales":
            rev_cols = [c for c in numeric_cols if any(k in c for k in ["rev", "amount", "sales", "deal"])]
            if rev_cols and rev_cols[0] in aggs:
                kpis["primary_metric"] = "total_revenue"
                kpis["total_revenue"] = aggs[rev_cols[0]]["sum"]
        elif dept == "finance":
            exp_cols = [c for c in numeric_cols if any(k in c for k in ["cost", "exp", "spend"])]
            if exp_cols and exp_cols[0] in aggs:
                kpis["primary_metric"] = "total_expenses"
                kpis["total_expenses"] = aggs[exp_cols[0]]["sum"]
        elif dept == "hr":
            sal_cols = [c for c in numeric_cols if any(k in c for k in ["salar", "pay", "comp"])]
            if sal_cols and sal_cols[0] in aggs:
                kpis["primary_metric"] = "avg_salary"
                kpis["avg_salary"] = aggs[sal_cols[0]]["mean"]
        elif dept == "marketing":
            cac_cols = [c for c in numeric_cols if c in ["ad_spend", "spend", "marketing_spend", "budget", "cost", "cac"]]
            if not cac_cols:
                cac_cols = [c for c in numeric_cols if re.search(r"\b(ad_spend|spend|budget|cost|cac)\b", c)]
            if cac_cols and cac_cols[0] in aggs:
                kpis["primary_metric"] = "total_marketing_spend"
                kpis["total_marketing_spend"] = aggs[cac_cols[0]]["sum"]
        elif dept == "operations":
            del_cols = [c for c in numeric_cols if any(k in c for k in ["delay", "lead", "time"])]
            if del_cols and del_cols[0] in aggs:
                kpis["primary_metric"] = "avg_delay_days"
                kpis["avg_delay_days"] = aggs[del_cols[0]]["mean"]

    @staticmethod
    def _build_streaming_trends(
        period_sums: Dict[str, Dict[str, float]],
        num_stats: Dict[str, Dict[str, Any]],
        total_rows: int
    ) -> List[Dict[str, Any]]:
        trends = []
        for col, p_dict in period_sums.items():
            if len(p_dict) >= 2:
                # Sorted by chronological month key
                sorted_periods = sorted(p_dict.keys())
                first_p = sorted_periods[0]
                last_p = sorted_periods[-1]
                start_val = p_dict[first_p]
                end_val = p_dict[last_p]

                change_pct = ((end_val - start_val) / abs(start_val)) * 100 if start_val != 0 else 0.0
                direction = "increased" if change_pct > 0 else "decreased" if change_pct < 0 else "stable"

                pop_changes = []
                for i in range(1, len(sorted_periods)):
                    prev_p, curr_p = sorted_periods[i-1], sorted_periods[i]
                    v_prev, v_curr = p_dict[prev_p], p_dict[curr_p]
                    pop_pct = ((v_curr - v_prev) / abs(v_prev)) * 100 if v_prev != 0 else 0.0
                    pop_changes.append({
                        "from_period": str(prev_p),
                        "to_period": str(curr_p),
                        "change_pct": round(pop_pct, 2)
                    })

                trends.append({
                    "metric": col,
                    "direction": direction,
                    "change_percentage": round(change_pct, 2),
                    "start_val": round(start_val, 2),
                    "end_val": round(end_val, 2),
                    "start_period": str(first_p),
                    "end_period": str(last_p),
                    "period_over_period": pop_changes
                })
            elif col in num_stats and total_rows >= 2:
                # Fallback non-dated trend
                st = num_stats[col]
                trends.append({
                    "metric": col,
                    "direction": "stable",
                    "change_percentage": 0.0,
                    "start_val": round(st["min"] if st["min"] != float("inf") else 0.0, 2),
                    "end_val": round(st["max"] if st["max"] != float("-inf") else 0.0, 2)
                })
        return trends

    @staticmethod
    def _detect_relationships(df: pd.DataFrame, numeric_cols: List[str]) -> List[Dict[str, Any]]:
        relationships = []
        valid_cols = [c for c in numeric_cols if c in df.columns]
        if len(valid_cols) < 2 or df.empty:
            return relationships

        corr_matrix = df[valid_cols].corr()
        for i in range(len(valid_cols)):
            for j in range(i + 1, len(valid_cols)):
                col1, col2 = valid_cols[i], valid_cols[j]
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

    @staticmethod
    def _detect_trends(df: pd.DataFrame, numeric_cols: List[str], datetime_cols: List[str]) -> List[Dict[str, Any]]:
        period_sums = {col: {} for col in numeric_cols}
        date_col = datetime_cols[0] if datetime_cols else None
        if date_col and date_col in df.columns:
            try:
                parsed = pd.to_datetime(df[date_col], errors="coerce")
                valid = parsed.notnull()
                if valid.any():
                    keys = parsed[valid].dt.to_period("M").astype(str)
                    for col in numeric_cols:
                        if col in df.columns:
                            grp = df.loc[valid].groupby(keys)[col].sum()
                            for k, v in grp.items():
                                period_sums[col][str(k)] = float(v)
            except Exception:
                pass

        num_stats = {
            col: {
                "min": float(df[col].min()) if col in df.columns and not df[col].empty else 0.0,
                "max": float(df[col].max()) if col in df.columns and not df[col].empty else 0.0,
                "count": len(df)
            }
            for col in numeric_cols if col in df.columns
        }
        return DataProfiler._build_streaming_trends(period_sums, num_stats, len(df))


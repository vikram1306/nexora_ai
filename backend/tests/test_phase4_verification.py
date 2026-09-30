import pytest
import pandas as pd
import numpy as np
from app.services.ingestion.profiler import DataProfiler
from app.services.sentinel.sentinel_service import SentinelAIService
from app.models.domain import Dataset, SentinelAlert
from tests.test_phase2_verification import save_dataset

def test_task14_period_over_period_trend_detection(tmp_path):
    # Create an unsorted multi-row dataset per month where naive first-vs-last fails
    # Jan sum: 1000 + 5000 = 6000
    # Feb sum: 2000 + 1000 = 3000
    # Naive raw first (1000) vs last (1000) shows 0% change.
    # Real groupby(month).sum() shows 6000 -> 3000 (-50.0% decline).
    df = pd.DataFrame({
        'transaction_date': ['2026-01-05', '2026-01-20', '2026-02-10', '2026-02-25'],
        'revenue': [1000.0, 5000.0, 2000.0, 1000.0]
    })

    trends = DataProfiler._detect_trends(df, numeric_cols=['revenue'], datetime_cols=['transaction_date'])

    assert len(trends) == 1
    t = trends[0]
    assert t['metric'] == 'revenue'
    assert t['direction'] == 'decreased'
    assert t['change_percentage'] == -50.0
    assert t['start_val'] == 6000.0
    assert t['end_val'] == 3000.0
    assert t['start_period'] == '2026-01'
    assert t['end_period'] == '2026-02'
    assert 'period_over_period' in t
    assert len(t['period_over_period']) == 1
    assert t['period_over_period'][0]['from_period'] == '2026-01'
    assert t['period_over_period'][0]['to_period'] == '2026-02'
    assert t['period_over_period'][0]['change_pct'] == -50.0


def test_task15_sentinel_confidence_bounds(db_session, tmp_path):
    tenant_id = "test_phase4_sentinel_tenant"
    
    # 12 records: 11 normal around 100, 1 spike outlier at 500
    normal_vals = [100.0, 102.0, 98.0, 101.0, 99.0, 100.0, 103.0, 97.0, 100.0, 101.0, 99.0]
    all_vals = normal_vals + [500.0]
    df = pd.DataFrame({'operating_expense': all_vals})

    save_dataset(db_session, tmp_path, tenant_id, 'finance', df, name="fin_outliers.csv")

    sentinel = SentinelAIService(db_session, tenant_id)
    alerts = sentinel.scan_tenant_memory_for_anomalies()

    assert len(alerts) >= 1
    alert = alerts[0]

    assert alert.metric_name == 'operating_expense'
    assert alert.confidence_level == 0.988
    assert alert.lower_bound is not None
    assert alert.upper_bound is not None
    assert alert.baseline_value is not None
    assert alert.anomaly_value == 500.0

    # Bounds check: baseline median is 100.0, upper bound is around 100 + 2.5 * (1.4826 * MAD) ~ 105.0
    assert alert.upper_bound < 500.0
    assert alert.lower_bound < alert.upper_bound

    # Check descriptive confidence bound inclusion
    assert "98.8% confidence interval" in alert.description
    assert f"[{alert.lower_bound:,.2f}, {alert.upper_bound:,.2f}]" in alert.description
    assert "upper confidence bound" in alert.root_cause

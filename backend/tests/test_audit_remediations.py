import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.memory.enterprise_memory import EnterpriseMemoryManager
from app.agents.finance import FinanceAgent
from app.agents.marketing import MarketingAgent
from app.utils.date_filters import apply_natural_language_date_filter
from app.planner.planner import PlannerAgent
from app.sentinel.sentinel_service import SentinelAIService
from app.models.domain import Dataset, SentinelAlert

from tests.conftest import TestingSessionLocal

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_test_dataset(db, tmp_path, tenant_id, department, df, name="test.csv"):
    csv_file = tmp_path / name
    df.to_csv(csv_file, index=False)
    ds = Dataset(
        tenant_id=tenant_id,
        name=name,
        department=department,
        file_path=str(csv_file),
        row_count=len(df)
    )
    db.add(ds)
    db.commit()
    return ds

def test_dynamic_ebitda_calculation(db_session, tmp_path):
    tenant_id = "test_ebitda_tenant"

    sales_df = pd.DataFrame({
        "transaction_id": ["T1", "T2"],
        "sales_amount": [600000.0, 400000.0]
    })
    save_test_dataset(db_session, tmp_path, tenant_id, "sales", sales_df, "sales.csv")

    fin_df = pd.DataFrame({
        "month": ["2026-01", "2026-02"],
        "actual_expense": [150000.0, 250000.0]
    })
    save_test_dataset(db_session, tmp_path, tenant_id, "finance", fin_df, "finance.csv")

    memory = EnterpriseMemoryManager(db_session, tenant_id)
    finance_agent = FinanceAgent(memory)
    output = finance_agent.execute("Calculate Net EBITDA profit margin")

    ebitda_insight = next((i for i in output.insights if "Net EBITDA Analysis" in i), "")
    assert "$600,000.00 Net EBITDA" in ebitda_insight
    assert "$1,256,000.00" not in ebitda_insight
    assert "Net EBITDA Margin: **60.00%**" in ebitda_insight

def test_month_matching_word_boundary():
    df = pd.DataFrame({
        "month": ["2026-01", "2026-02", "2026-03"],
        "actual_expense": [100.0, 200.0, 300.0]
    })

    df_filtered, target_periods = apply_natural_language_date_filter(df, "month", "full business overview with profit margin")
    assert target_periods == []
    assert len(df_filtered) == 3

    df_filtered_mar, target_periods_mar = apply_natural_language_date_filter(df, "month", "show expenses for march")
    assert target_periods_mar == ["2026-03"]
    assert len(df_filtered_mar) == 1

def test_marketing_column_selection(db_session, tmp_path):
    tenant_id = "test_mkt_tenant"

    mkt_df = pd.DataFrame({
        "campaign_id": ["C1", "C2"],
        "mql_leads": [500, 1000],
        "ad_spend": [50000.0, 70000.0],
        "clicks": [10000, 20000],
        "roas": [3.5, 4.0]
    })
    save_test_dataset(db_session, tmp_path, tenant_id, "marketing", mkt_df, "marketing.csv")

    memory = EnterpriseMemoryManager(db_session, tenant_id)
    mkt_agent = MarketingAgent(memory)
    output = mkt_agent.execute("Analyze marketing campaign spend and leads")

    spend_metric = next((m for m in output.metrics if m.name == "Total Marketing Spend"), None)
    leads_metric = next((m for m in output.metrics if m.name == "Total MQL Leads"), None)

    assert spend_metric is not None
    assert spend_metric.value == 120000.0

    assert leads_metric is not None
    assert leads_metric.value == 1500

def test_sentinel_skips_id_columns(db_session, tmp_path):
    tenant_id = "test_sentinel_tenant"

    df = pd.DataFrame({
        "transaction_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 99999],
        "sales_amount": [100.0, 102.0, 101.0, 99.0, 100.0, 103.0, 101.0, 100.0, 98.0, 102.0]
    })
    save_test_dataset(db_session, tmp_path, tenant_id, "sales", df, "sales.csv")

    sentinel = SentinelAIService(db_session, tenant_id)
    sentinel.scan_tenant_memory_for_anomalies()

    logged_alerts = db_session.query(SentinelAlert).filter(SentinelAlert.tenant_id == tenant_id).all()
    assert not any(a.metric_name == "transaction_id" for a in logged_alerts)

def test_planner_ebitda_and_spike_analysis(tmp_path):
    db_file = tmp_path / "planner_test.db"
    test_engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestSession()

    tenant_id = "test_planner_tenant"
    sales_df = pd.DataFrame({"sales_amount": [500000.0]})
    fin_df = pd.DataFrame({
        "month": ["2026-01", "2026-02"],
        "actual_expense": [100000.0, 200000.0]
    })
    save_test_dataset(db, tmp_path, tenant_id, "sales", sales_df, "sales.csv")
    save_test_dataset(db, tmp_path, tenant_id, "finance", fin_df, "finance.csv")

    planner = PlannerAgent(db, tenant_id)
    res = planner.execute_query("Analyze our sales revenue and operating expenses to determine Net EBITDA margin")

    assert "$500,000.00" in res.executive_summary
    assert "$300,000.00" in res.executive_summary
    assert "$200,000.00" in res.executive_summary
    assert "2026-02" in res.executive_summary
    db.close()
    test_engine.dispose()

def test_regression_ebitda_output_changes_with_input_data(db_session, tmp_path):
    """Regression Test 1: Assert EBITDA changes dynamically when input dataset changes, and is omitted if Sales dataset is missing."""
    tenant_id = "test_dynamic_change_tenant"

    fin_df = pd.DataFrame({
        "month": ["2026-01"],
        "actual_expense": [300000.0]
    })
    save_test_dataset(db_session, tmp_path, tenant_id, "finance", fin_df, "finance.csv")
    memory = EnterpriseMemoryManager(db_session, tenant_id)
    finance_agent = FinanceAgent(memory)

    # Case A: Missing Sales dataset -> EBITDA insight must NOT be generated (no hardcoded fallback)
    output_no_sales = finance_agent.execute("Calculate Net EBITDA margin")
    ebitda_insight_none = next((i for i in output_no_sales.insights if "Net EBITDA Analysis" in i), None)
    assert ebitda_insight_none is None

    # Case B: Add Sales = 1,000,000 -> EBITDA must equal $700,000 (70%)
    tenant_id_b = "test_ebitda_tenant_b"
    save_test_dataset(db_session, tmp_path, tenant_id_b, "finance", fin_df, "finance.csv")
    sales_df1 = pd.DataFrame({"sales_amount": [1000000.0]})
    save_test_dataset(db_session, tmp_path, tenant_id_b, "sales", sales_df1, "sales1.csv")
    mem_b = EnterpriseMemoryManager(db_session, tenant_id_b)
    output1 = FinanceAgent(mem_b).execute("Calculate Net EBITDA margin")
    ebitda_insight1 = next((i for i in output1.insights if "Net EBITDA Analysis" in i), "")
    assert "$700,000.00 Net EBITDA" in ebitda_insight1
    assert "70.00%" in ebitda_insight1

    # Case C: Change Sales = 2,500,000 -> EBITDA must dynamically change to $2,200,000 (88%)
    tenant_id_c = "test_ebitda_tenant_c"
    save_test_dataset(db_session, tmp_path, tenant_id_c, "finance", fin_df, "finance.csv")
    sales_df2 = pd.DataFrame({"sales_amount": [2500000.0]})
    save_test_dataset(db_session, tmp_path, tenant_id_c, "sales", sales_df2, "sales2.csv")
    mem_c = EnterpriseMemoryManager(db_session, tenant_id_c)
    output2 = FinanceAgent(mem_c).execute("Calculate Net EBITDA margin")
    ebitda_insight2 = next((i for i in output2.insights if "Net EBITDA Analysis" in i), "")
    assert "$2,200,000.00 Net EBITDA" in ebitda_insight2
    assert "88.00%" in ebitda_insight2

def test_regression_strategic_recommendation_data_derived(db_session, tmp_path):
    """Regression Test 2: Assert Strategic Recommendations use real data baselines instead of hardcoded numbers."""
    from app.intelligence import StrategicIntelligenceAgent
    from app.agents.marketing import MarketingAgent
    from app.agents.hr import HRAgent

    tenant_id = "test_strategic_data_tenant"

    mkt_df = pd.DataFrame({
        "mql_leads": [400],
        "ad_spend": [20000.0]
    })
    save_test_dataset(db_session, tmp_path, tenant_id, "marketing", mkt_df, "marketing.csv")
    memory = EnterpriseMemoryManager(db_session, tenant_id)
    mkt_agent = MarketingAgent(memory)
    mkt_output = mkt_agent.execute("Analyze marketing spend and leads")

    recs = StrategicIntelligenceAgent.generate_recommendations("Evaluate marketing efficiency", [mkt_output])
    assert len(recs) >= 1
    # Check that CAC baseline is dynamically derived ($20,000 / 400 = $50.00)
    assert "$50.00/lead" in recs[0].expected_impact or "400" in recs[1].expected_impact
    assert "-22%" not in recs[0].expected_impact


import pandas as pd
import pytest

from app.agents.finance import FinanceAgent
from app.agents.marketing import MarketingAgent
from app.agents.sales import SalesAgent
from app.memory.enterprise_memory import EnterpriseMemoryManager
from app.memory.redis_cache import cache_manager
from app.models.domain import Dataset
from app.sentinel.sentinel_service import SentinelAIService
from app.utils.date_filters import apply_natural_language_date_filter
from tests.conftest import TestingSessionLocal


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_test_dataset(db, tmp_path, tenant_id, department, df, name="data.csv"):
    csv_file = tmp_path / f"{tenant_id}_{department}_{name}"
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
    cache_manager.invalidate_tenant_cache(tenant_id, department)
    return ds


def test_regression_sales_output_strictly_changes_with_input_data(db_session, tmp_path):
    """REGRESSION TEST: Verify SalesAgent output is purely dynamic and strictly changes when input revenue changes."""
    tenant_1 = "tenant_dyn_sales_1"
    tenant_2 = "tenant_dyn_sales_2"

    # Dataset 1: Low sales ($100k)
    df1 = pd.DataFrame({"sales_amount": [50000.0, 50000.0]})
    save_test_dataset(db_session, tmp_path, tenant_1, "sales", df1, "s1.csv")
    mem1 = EnterpriseMemoryManager(db_session, tenant_1)
    agent1 = SalesAgent(mem1)
    out1 = agent1.execute("Analyze total sales revenue")

    # Dataset 2: High sales ($950k)
    df2 = pd.DataFrame({"sales_amount": [450000.0, 500000.0]})
    save_test_dataset(db_session, tmp_path, tenant_2, "sales", df2, "s2.csv")
    mem2 = EnterpriseMemoryManager(db_session, tenant_2)
    agent2 = SalesAgent(mem2)
    out2 = agent2.execute("Analyze total sales revenue")

    # Assert outputs strictly differ and match input computations
    rev1 = next(m.value for m in out1.metrics if m.name == "Total Revenue")
    rev2 = next(m.value for m in out2.metrics if m.name == "Total Revenue")

    assert rev1 == 100000.0
    assert rev2 == 950000.0
    assert rev1 != rev2
    assert "$100,000.00" in out1.insights[0]
    assert "$950,000.00" in out2.insights[0]


def test_regression_finance_ebitda_and_margins_vary_dynamically(db_session, tmp_path):
    """REGRESSION TEST: Verify EBITDA calculation is strictly dynamic and recalculates dynamically when OPEX changes."""
    tenant_profit = "tenant_dyn_profit"
    tenant_loss = "tenant_dyn_loss"

    # Profitable Scenario: Sales $1M, OPEX $200k -> EBITDA +$800k (80%)
    save_test_dataset(db_session, tmp_path, tenant_profit, "sales", pd.DataFrame({"sales_amount": [1000000.0]}), "s.csv")
    save_test_dataset(db_session, tmp_path, tenant_profit, "finance", pd.DataFrame({"operating_cost": [200000.0]}), "f.csv")

    mem_p = EnterpriseMemoryManager(db_session, tenant_profit)
    fin_agent_p = FinanceAgent(mem_p)
    out_p = fin_agent_p.execute("Calculate EBITDA and profit margin")
    ebitda_p_str = next((i for i in out_p.insights if "Net EBITDA Analysis" in i), "")

    assert "$800,000.00 Net EBITDA" in ebitda_p_str
    assert "80.00%" in ebitda_p_str

    # Unprofitable Scenario: Sales $1M, OPEX $1.5M -> EBITDA -$500k (-50%)
    save_test_dataset(db_session, tmp_path, tenant_loss, "sales", pd.DataFrame({"sales_amount": [1000000.0]}), "s.csv")
    save_test_dataset(db_session, tmp_path, tenant_loss, "finance", pd.DataFrame({"operating_cost": [1500000.0]}), "f.csv")

    mem_l = EnterpriseMemoryManager(db_session, tenant_loss)
    fin_agent_l = FinanceAgent(mem_l)
    out_l = fin_agent_l.execute("Calculate EBITDA and profit margin")
    ebitda_l_str = next((i for i in out_l.insights if "Net EBITDA Analysis" in i), "")

    assert "$-500,000.00 Net EBITDA" in ebitda_l_str or "-$500,000.00" in ebitda_l_str
    assert "-50.00%" in ebitda_l_str


def test_regression_marketing_ignores_string_columns_and_selects_numeric(db_session, tmp_path):
    """REGRESSION TEST: Verify Marketing agent selects numeric columns and is never fooled by string labels."""
    tenant = "tenant_mkt_regression"
    df = pd.DataFrame({
        "campaign_name": ["ROAS_Q1_PROMO", "LEADS_BOOST_2026"],
        "ad_spend": [40000.0, 60000.0],
        "mql_leads": [400, 600],
        "roas": [3.2, 4.8]
    })
    save_test_dataset(db_session, tmp_path, tenant, "marketing", df, "m.csv")
    mem = EnterpriseMemoryManager(db_session, tenant)
    mkt = MarketingAgent(mem)
    out = mkt.execute("Analyze marketing efficiency and spend")

    spend = next((m for m in out.metrics if m.name == "Total Marketing Spend"), None)
    leads = next((m for m in out.metrics if m.name == "Total MQL Leads"), None)
    roas = next((m for m in out.metrics if m.name == "Average ROAS"), None)

    assert spend is not None and spend.value == 100000.0
    assert leads is not None and leads.value == 1000.0
    assert roas is not None and roas.value == 4.0


def test_regression_month_filter_word_boundary_precision():
    """REGRESSION TEST: Verify regex word boundary in date filter prevents substring collisions (e.g., 'archer' matching 'march')."""
    df = pd.DataFrame({
        "month": ["2026-01", "2026-02", "2026-03"],
        "actual_expense": [100.0, 200.0, 300.0]
    })

    # Substring 'archer' or 'marching' should NOT match 'march'
    df_f, periods = apply_natural_language_date_filter(df, "month", "archer corporate strategy update")
    assert periods == []
    assert len(df_f) == 3

    # Exact word 'march' MUST match '2026-03'
    df_mar, periods_mar = apply_natural_language_date_filter(df, "month", "give me expenses for march 2026")
    assert periods_mar == ["2026-03"]
    assert len(df_mar) == 1
    assert float(df_mar["actual_expense"].iloc[0]) == 300.0


def test_regression_sentinel_skips_sequential_ids_and_flags_real_outliers(db_session, tmp_path):
    """REGRESSION TEST: Verify Sentinel AI excludes sequential ID/UUID columns from anomaly detection."""
    tenant = "tenant_sentinel_regression"

    # 15 rows with sequential transaction IDs (1..15) and static amount, but row 15 has an extreme spike in revenue
    df = pd.DataFrame({
        "transaction_id": list(range(1, 16)),
        "order_uuid": [f"uuid-00{i}" for i in range(1, 16)],
        "revenue_amount": [1000.0] * 14 + [250000.0]  # Massive outlier
    })
    save_test_dataset(db_session, tmp_path, tenant, "sales", df, "s.csv")

    sentinel = SentinelAIService(db_session, tenant)
    alerts = sentinel.scan_tenant_memory_for_anomalies()

    assert len(alerts) >= 1
    # Sentinel must NEVER flag transaction_id or order_uuid as an anomaly
    flagged_metrics = [a.metric_name for a in alerts]
    assert "transaction_id" not in flagged_metrics
    assert "order_uuid" not in flagged_metrics
    assert "revenue_amount" in flagged_metrics

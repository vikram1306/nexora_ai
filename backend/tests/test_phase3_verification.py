import time

import pandas as pd

from app.intelligence import ResponseValidator
from app.models.domain import Dataset
from app.planner.planner import PlannerAgent
from app.schemas.agents import DepartmentAgentOutput, MetricDetail


def save_test_dataset(db, tmp_path, tenant_id, department, df, name="data.csv"):
    csv_path = tmp_path / f"{tenant_id}_{department}_{name}"
    df.to_csv(csv_path, index=False)
    ds = Dataset(
        tenant_id=tenant_id,
        name=name,
        department=department,
        file_path=str(csv_path),
        row_count=len(df)
    )
    db.add(ds)
    db.commit()
    return ds

def seed_test_datasets(db_session, tmp_path, tenant_id: str):
    sales_df = pd.DataFrame({
        'sales_amount': [1500.0, 2500.0, 3500.0],
        'transaction_date': ['2026-01-15', '2026-02-15', '2026-03-15'],
        'region': ['North', 'South', 'North']
    })
    fin_df = pd.DataFrame({
        'operating_cost': [800.0, 1200.0, 1000.0],
        'month_period': ['2026-01-01', '2026-02-01', '2026-03-01']
    })
    hr_df = pd.DataFrame({
        'annual_salary': [85000, 95000, 110000],
        'employee_id': ['EMP-01', 'EMP-02', 'EMP-03']
    })
    mkt_df = pd.DataFrame({
        'ad_spend': [1200.0, 1800.0],
        'roas': [3.2, 4.1],
        'mql_leads': [45, 65]
    })
    ops_df = pd.DataFrame({
        'fulfillment_delay_days': [1.1, 1.4, 0.9]
    })

    save_test_dataset(db_session, tmp_path, tenant_id, 'sales', sales_df)
    save_test_dataset(db_session, tmp_path, tenant_id, 'finance', fin_df)
    save_test_dataset(db_session, tmp_path, tenant_id, 'hr', hr_df)
    save_test_dataset(db_session, tmp_path, tenant_id, 'marketing', mkt_df)
    save_test_dataset(db_session, tmp_path, tenant_id, 'operations', ops_df)

def test_task12_response_validator_confidence_scores(db_session, tmp_path):
    tenant_id = "test_phase3_val_tenant"
    seed_test_datasets(db_session, tmp_path, tenant_id)
    planner = PlannerAgent(db_session, tenant_id)

    # 1. Full 5-department executive query
    res_full = planner.execute_query("What is our overall company health, EBITDA, sales growth, and workforce metrics?")
    assert not res_full.is_out_of_domain
    assert res_full.confidence_score >= 0.90
    assert len(res_full.department_outputs) == 5

    # Check evidence citations note verification
    citations_str = " ".join(res_full.evidence_citations)
    assert "Verified" in citations_str

    # 2. Single department query
    res_sales = planner.execute_query("What is our total sales revenue and deal size?")
    assert res_sales.confidence_score >= 0.95
    assert len(res_sales.department_outputs) == 1
    assert res_sales.department_outputs[0].department == "sales"

    # 3. Partial / missing department dataset scenario
    tenant_partial = "test_phase3_partial_tenant"
    # Only seed sales, leaving other 4 departments empty
    save_test_dataset(db_session, tmp_path, tenant_partial, 'sales', pd.DataFrame({'sales_amount': [100.0, 200.0]}))
    planner_p = PlannerAgent(db_session, tenant_partial)
    res_p = planner_p.execute_query("Give me full company overall analysis across sales, finance, hr, marketing, operations")
    # Response validator penalizes empty/missing department outputs
    assert res_p.confidence_score < 0.90

    # 4. Out of domain precision confidence
    res_ood = planner.execute_query("How do I write a React component for dating advice?")
    assert res_ood.is_out_of_domain
    assert res_ood.confidence_score == 1.0

    # 5. Hand sanity check of ResponseValidator direct method
    outputs = [
        DepartmentAgentOutput(
            department="sales", metrics=[MetricDetail(name="Rev", value=100.0, unit="$")],
            sql_executed="", trends=[], evidence=["e1"], insights=["i1"], confidence_score=0.98
        ),
        DepartmentAgentOutput(
            department="finance", metrics=[],
            sql_executed="", trends=[], evidence=[], insights=[], confidence_score=0.96
        )
    ]
    score, notes = ResponseValidator.validate_outputs(outputs)
    # Finance output has no metrics and no insights -> penalized by 0.6 multiplier (0.96 * 0.6 = 0.576)
    # Average: (0.98 + 0.576) / 2 = 0.778 -> rounded to 0.78
    assert score == 0.78
    assert "Limited dataset records available" in notes[1]


def test_task13_query_resolution_time_kpi(db_session, tmp_path):
    tenant_id = "test_phase3_perf_tenant"
    seed_test_datasets(db_session, tmp_path, tenant_id)
    planner = PlannerAgent(db_session, tenant_id)

    queries = [
        "What is our total sales revenue and growth trend?",
        "What is our overall company health, EBITDA, and expense control?",
        "How can we optimize our marketing ad spend and MQL leads?",
        "What is the prescription for flu symptoms?" # Out of domain
    ]

    for q in queries:
        t0 = time.perf_counter()
        res = planner.execute_query(q)
        t1 = time.perf_counter()
        elapsed = t1 - t0

        # Assert performance strictly satisfies < 2.5s KPI
        assert elapsed < 2.5, f"Query '{q}' took {elapsed:.3f}s, exceeding 2.5s KPI threshold!"
        assert res is not None

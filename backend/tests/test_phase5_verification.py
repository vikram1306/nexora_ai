import pytest
import pandas as pd
from app.ingestion.schema_intelligence import SchemaIntelligenceEngine
from app.models.domain import Dataset, DatasetSchema
from tests.test_phase2_verification import create_test_user_and_token, client

def test_task16_schema_analysis_proposal(tmp_path):
    # Test file with non-standard column headers
    csv_path = tmp_path / "custom_sales.csv"
    df = pd.DataFrame({
        'client_monthly_revenue': [1500.0, 2500.0],
        'order_date_time': ['2026-01-15', '2026-02-15'],
        'territory_region': ['North', 'South']
    })
    df.to_csv(csv_path, index=False)

    proposal = SchemaIntelligenceEngine.propose_schema_mapping(str(csv_path), "sales")

    assert proposal['department'] == 'sales'
    assert proposal['total_columns'] == 3
    
    mappings = {m['user_column']: m for m in proposal['proposed_mappings']}
    
    assert mappings['client_monthly_revenue']['proposed_canonical'] == 'revenue'
    assert mappings['client_monthly_revenue']['confidence'] >= 0.75

    assert mappings['order_date_time']['proposed_canonical'] == 'date'
    assert mappings['order_date_time']['confidence'] >= 0.75

    assert mappings['territory_region']['proposed_canonical'] == 'region'
    assert mappings['territory_region']['confidence'] >= 0.75


def test_task17_confirm_and_ingest_pipeline(db_session, tmp_path):
    user, token = create_test_user_and_token(db_session, "schema_user@test.com", "CEO", "tenant_schema_p5")

    csv_path = tmp_path / "marketing_raw.csv"
    df = pd.DataFrame({
        'ad_budget_amount': [1200.0, 1800.0],
        'roas_multiplier': [3.2, 4.1],
        'mql_count': [45, 65]
    })
    df.to_csv(csv_path, index=False)

    with open(csv_path, "rb") as f:
        res_analyze = client.post(
            "/api/v1/ingest/analyze-schema",
            data={"department": "marketing"},
            files={"file": ("marketing_raw.csv", f, "text/csv")},
            headers={"Authorization": f"Bearer {token}"}
        )

    assert res_analyze.status_code == 200
    analysis_data = res_analyze.json()
    temp_file_id = analysis_data['temp_file_id']
    assert analysis_data['total_columns'] == 3

    confirmed_map = {
        'ad_budget_amount': 'ad_spend',
        'roas_multiplier': 'roas',
        'mql_count': 'mql_leads'
    }

    res_confirm = client.post(
        "/api/v1/ingest/confirm-and-ingest",
        json={
            "temp_file_id": temp_file_id,
            "department": "marketing",
            "confirmed_mapping": confirmed_map
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert res_confirm.status_code == 201
    dataset_data = res_confirm.json()
    assert dataset_data['department'] == 'marketing'
    assert dataset_data['row_count'] == 2

    # Verify DB record and confirmed schema info
    ds_db = db_session.query(Dataset).filter(Dataset.id == dataset_data['id']).first()
    assert ds_db is not None
    assert ds_db.schema_info is not None
    assert "total_marketing_spend" in ds_db.schema_info.kpis_extracted

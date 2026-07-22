# API Specification - Nexora AI

All endpoints are hosted under `/api/v1`. Authentication header: `Authorization: Bearer <JWT>`.

## 1. Authentication & Tenant Endpoints
- `POST /api/v1/auth/register`: Create organization tenant & admin user.
- `POST /api/v1/auth/login`: Authenticate user & return JWT token.
- `GET /api/v1/auth/me`: Get current authenticated user and tenant profile.

## 2. Ingestion & Memory Endpoints
- `POST /api/v1/ingest/upload`: Upload CSV dataset file with department tag (`sales`, `finance`, `hr`, `marketing`, `operations`).
- `GET /api/v1/ingest/datasets`: List uploaded datasets, schemas, detected KPIs, and status.
- `GET /api/v1/ingest/datasets/{dataset_id}`: Inspect detailed dataset schema, metadata, and trend summaries.

## 3. Query & Multi-Agent Intelligence Endpoints
- `POST /api/v1/query/execute`: Main intelligence endpoint. Takes user natural language prompt and returns synthesized executive analysis payload containing:
  - Intent classification.
  - Selected department agents.
  - Formatted executive response.
  - Evidence list (SQL queries executed, vector search snippets).
  - Confidence Score.
  - Interactive Recharts visual configuration.

## 4. Sentinel AI Anomaly Monitoring Endpoints
- `GET /api/v1/sentinel/alerts`: Fetch real-time background anomaly notifications filtered by severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- `POST /api/v1/sentinel/trigger`: Trigger manual Sentinel AI monitoring scan across tenant memory.
- `PATCH /api/v1/sentinel/alerts/{alert_id}/acknowledge`: Mark alert as reviewed/acknowledged.

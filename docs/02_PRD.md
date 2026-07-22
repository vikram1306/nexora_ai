# Product Requirements Document (PRD) - Nexora AI

## 1. Product Scope & Functional Architecture

### 1.1 Tenant & Authentication Management
- **Multi-Tenancy**: Organization-level isolation of database tables, ChromaDB collections, and cache namespaces.
- **Role-Based Access Control (RBAC)**: Roles: `CEO`, `Director`, `Manager`, `Employee`.
- **JWT & API Key Auth**: Secure JWT session handling for web users and API key validation for automated integrations.

### 1.2 Data Ingestion & Enterprise Memory
- **Supported Format**: CSV file uploads with multi-file department association.
- **Automated Data Processing Pipeline**:
  1. Validation & Header Normalization.
  2. Column Data Type Profiling (Numeric, Categorical, Datetime, Currency).
  3. Automatic Null Cleaning & Outlier Treatment.
  4. Automatic KPI Extraction (Revenue, Profit, CAC, Margin, Turnover, Headcount).
  5. Trend & Variance Identification (MoM Growth, Z-Scores).
  6. Hybrid Storage: Relational SQL tables (PostgreSQL), Key-Value Cache (Redis), Semantic Vector Embeddings (ChromaDB + SentenceTransformers `all-MiniLM-L6-v2`).

### 1.3 Multi-Agent Executive System
- **Planner Agent**:
  - Intent classification & Out-of-Domain rejection.
  - Entity, metric, and timeframe extraction.
  - Task decomposition & parallel dispatch to target department agents.
  - Synthesis of JSON outputs into unified user responses with dynamic charts.
- **Department Agents (5 Fixed Domains)**:
  - `Sales Agent`: Revenue streams, regional sales, pipeline velocity, deal conversion.
  - `Finance Agent`: EBITDA, profit margins, cost analysis, budget variance.
  - `HR Agent`: Headcount, attrition rate, department salary distribution, productivity indices.
  - `Marketing Agent`: CAC, ROAS, channel effectiveness, lead conversion rates.
  - `Operations Agent`: Fulfillment delays, inventory turnover, logistics cost per unit.
- **Response Validator**:
  - Cross-validates all numerical assertions against database metrics and vector snippets.
  - Assigns a Confidence Score (0% – 100%) to every response.
- **Strategic Intelligence Agent**:
  - Computes cross-departmental impact correlations (e.g. Marketing ROI vs Sales performance by region).
  - Formulates actionable, data-backed strategic recommendations.

### 1.4 Continuous Anomaly Monitoring Engine (Sentinel AI)
- **Background Daemon**: Async cron service periodically inspecting ingested dataset metrics.
- **Detection Algorithms**: Z-score deviation ($> 2.5\sigma$), moving average anomalies, threshold breaches.
- **Automated Root-Cause Analysis**: Identifies contributing dimensions for flagged anomalies.
- **Tiered Alerts**: Dispatches notifications based on severity: Low (Employee), Medium (Manager), High (Director), Critical (CEO).

---

## 2. Key Performance Indicators (KPIs)
- **Query Resolution Time**: $< 2.5$ seconds for multi-agent retrieval & response synthesis.
- **Ingestion Latency**: $< 5$ seconds for CSV files containing up to 100,000 records.
- **Hallucination Rate**: $0\%$ via Response Validator strict cross-checking.
- **System Availability**: $99.9\%$ up-time with async workers.

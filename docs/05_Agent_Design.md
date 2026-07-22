# Agent Design & Architecture - Nexora AI

## 1. Multi-Agent Design Principles
- **No Direct Inter-Agent Communication**: Department agents never call each other. All coordination is owned by the Planner Agent.
- **Strict JSON Standard**: Every agent method returns a Pydantic object representing structured metrics, SQL execution logs, trend analysis, and evidence arrays.
- **Zero Hallucination Contract**: Reasoning is built on actual data calculations (SQL aggregate functions, Pandas DataFrame metrics, ChromaDB embeddings).

---

## 2. Department Agent Specifications

### 2.1 Planner Agent (Brain)
- **Inputs**: User prompt, Tenant ID, Conversation History.
- **Outputs**: Target Departments, Sub-Task Breakdown, Intent Type (`SUPPORT`, `KPI`, `COMPARISON`, `TREND`, `ROOT_CAUSE`, `FORECAST`, `RECOMMENDATION`, `EXECUTIVE_REPORT`), Merged Synthesized JSON, Confidence Score.

### 2.2 Sales Agent
- **Domain**: Revenue streams, pipeline velocity, closed deals, rep quota attainment, geographical revenue split.
- **Tools**: SQL Querying Engine, Sales Trend Calculator, Revenue Forecasting Engine.

### 2.3 Finance Agent
- **Domain**: Income statement, operating expenses (OpEx), EBITDA, gross margins, cash burn rate.
- **Tools**: Variance Analysis Tool, Profit Margin Calculator, Cash Flow Projector.

### 2.4 HR Agent
- **Domain**: Employee headcount, voluntary/involuntary turnover, salary distribution, department cost per employee, productivity scores.
- **Tools**: Attrition Predictor, Salary Distribution Profiler.

### 2.5 Marketing Agent
- **Domain**: Customer Acquisition Cost (CAC), Return on Ad Spend (ROAS), lead-to-MQL conversion rates, marketing campaign efficiency across channels (LinkedIn, Google, Meta).
- **Tools**: ROAS Profiler, CAC Calculator, Channel Efficiency Index.

### 2.6 Operations Agent
- **Domain**: Order fulfillment speed, logistics delay rates, supply chain turnover, inventory status, warehouse utilization.
- **Tools**: Delay Anomaly Detector, Inventory Velocity Calculator.

---

## 3. Support & Validation Agents

### 3.1 Strategic Intelligence Agent
- Combines insights from multiple department outputs to provide data-backed strategic pivot advice (e.g. shift budget from underperforming marketing channels into high-margin regional product inventories).

### 3.2 Response Validator Agent
- Performs automated cross-checking of all generated response statements against stored dataset facts. Computes a Confidence Score metric ($0.0 \dots 1.0$) attached to the final UI payload.

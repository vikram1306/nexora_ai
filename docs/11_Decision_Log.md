# Architectural Decision Log (ADR) - Nexora AI

## ADR 001: Centralized Planner Orchestration over Autonomous Agent Chatter
- **Context**: Department agents need to combine datasets to answer complex executive questions.
- **Decision**: Disallow direct agent-to-agent communication. Force all communication to route through the central **Planner Agent** using Pydantic JSON contracts.
- **Rationale**: Direct chat between autonomous agents leads to non-deterministic loops, elevated latency, unparseable logs, and difficulty auditing financial/business calculations.

---

## ADR 002: PostgreSQL + ChromaDB + Redis Hybrid Storage Architecture
- **Context**: Datasets contain tabular numerical records, unstructured column descriptions, and high-frequency metric queries.
- **Decision**: Split data persistence into three stores: PostgreSQL for relational tables/SQL queries; ChromaDB for vector similarity over column metadata & summaries; Redis for fast metric caching.
- **Rationale**: Single vector databases lack complex SQL aggregation capabilities (SUM, AVG, GROUP BY), while raw relational databases lack semantic similarity search.

---

## ADR 003: Standalone Sentinel AI Anomaly Monitoring Background Service
- **Context**: Executive platforms must proactively surface anomalies before users manually run queries.
- **Decision**: Implement an independent async background service (`Sentinel AI`) using moving average and Z-score statistical bounds to continuously scan ingested tables and dispatch tiered alerts.
- **Rationale**: Keeps monitoring decoupled from user-initiated HTTP request lifecycles.

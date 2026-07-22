# System Architecture - Nexora AI

## 1. High-Level Data Flow

```
[ Next.js Executive Dashboard ]
               │
               ▼ HTTP / REST
    [ FastAPI API Gateway ]
               │
               ├──► [ Auth & Tenant Context Middleware ]
               │
               ▼
     [ Planner Agent (Brain) ]
               │
      ┌────────┴────────┐
      ▼                 ▼
[ OOD Filter ]   [ Agent Task Planner ]
                        │
                        ▼ Parallel Dispatch
      ┌─────────────────┼─────────────────┬─────────────────┬─────────────────┐
      ▼                 ▼                 ▼                 ▼                 ▼
[Sales Agent]   [Finance Agent]     [HR Agent]     [Marketing Agent] [Operations Agent]
      │                 │                 │                 │                 │
      └─────────────────┴─────────────────┼─────────────────┴─────────────────┘
                                          │ Structured Pydantic JSON Outputs
                                          ▼
                             [ Enterprise Memory Layer ]
                        ┌─────────────────┼─────────────────┐
                        ▼                 ▼                 ▼
                 [PostgreSQL]          [Redis]         [ChromaDB]
                   (Relational)        (Cache)          (Vectors)
                                          │
                                          ▼
                            [ Response Synthesizer ]
                                          │
                                          ▼
                           [ Response Validator ]
                             (Confidence Score)
                                          │
                                          ▼
                             [ Final Dynamic Payload ]
                                (JSON + Visuals)
```

## 2. Layered Architecture Principles
1. **API Gateway / Presentation Layer**: Exposes FastAPI endpoints for authentication, data ingestion, query processing, and alert management.
2. **Orchestration & Agent Layer**: Centralized control through the Planner Agent. Department agents operate as decoupled services returning validated Pydantic models.
3. **Enterprise Memory Layer**: Unified query interface delegating queries to PostgreSQL (SQL analytical aggregations), Redis (cached metrics and query state), and ChromaDB (semantic similarity over chunked dataset metadata).
4. **Sentinel AI Service**: Independent background daemon continuously reading metrics from Enterprise Memory and writing anomaly notifications to PostgreSQL and Redis.

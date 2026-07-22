# Nexora AI - Enterprise Intelligence AI Operating System

> **Enterprise Intelligence. Autonomous Decisions.**

Nexora AI is a production-grade SaaS AI Operating System built for modern enterprises. It allows companies to upload departmental datasets (Sales, Finance, HR, Marketing, Operations), automatically cleans and indexes the data into an Enterprise Memory Engine, and deploys a coordinated team of specialized Department Agents, a central Planner Agent, a Strategic Intelligence Agent, and an autonomous continuous monitoring daemon called **Sentinel AI**.

---

## 🌟 Key Features

- 🏢 **Multi-Tenant SaaS Architecture**: Complete organizational isolation across database schemas, vector collections, and tenant sessions.
- ⚡ **Automated CSV Ingestion Pipeline**: Auto-schema detection, column data profiling, null handling, automatic KPI extraction, trend detection, and multi-tier persistence.
- 🧠 **Enterprise Memory Layer**: Hybrid architecture utilizing PostgreSQL (analytical SQL queries), ChromaDB + SentenceTransformers (local vector embeddings), and Redis (caching & query state).
- 🎯 **Centralized Multi-Agent Planner**: Intent detection, entity/metric extraction, out-of-domain guardrails, parallel department agent execution, and dynamic response synthesis.
- 📊 **5 Department-Specific AI Agents**:
  - **Sales**: Pipeline velocity, regional revenue, rep performance.
  - **Finance**: Operating margins, EBITDA, OpEx variance, profit drivers.
  - **HR**: Headcount growth, voluntary turnover, salary distribution, productivity indices.
  - **Marketing**: Customer Acquisition Cost (CAC), ROAS, channel conversion rates.
  - **Operations**: Fulfillment delays, inventory turnover, operational efficiency.
- 🛡️ **Response Validator & Confidence Scoring**: Ensures zero hallucinations by cross-checking all numerical assertions against database metrics and generating confidence scores.
- 🚀 **Strategic Intelligence Engine**: Cross-departmental recommendation generator yielding data-backed actionable executive insights.
- 🚨 **Sentinel AI (Continuous Anomaly Monitoring)**: Background service detecting spikes, drops, threshold violations, and executing automated root-cause analysis with multi-tier alerts (`Employee` $\rightarrow$ `CEO`).
- 💎 **Luxury Executive UI**: Minimal obsidian dark mode theme (`#08080A`), glassmorphism, Framer Motion dynamic animations, keyboard command palette (`Ctrl+K`), and interactive Recharts visuals.

---

## 🏗️ Architecture & Technology Stack

- **Frontend**: Next.js 14, React 18, TypeScript, TailwindCSS, Framer Motion, Recharts, Lucide Icons.
- **Backend**: FastAPI, Python 3.11+, Pydantic v2, SQLAlchemy 2.0, Asyncpg, Pandas, NumPy, Scikit-Learn.
- **Enterprise Memory**: PostgreSQL, Redis, ChromaDB, SentenceTransformers (`all-MiniLM-L6-v2`).
- **AI Infrastructure**: 100% Local / Open-Source Models (Llama 3, Mistral, Phi-3, Ollama / HuggingFace local pipelines).

---

## 📁 Documentation Suite

Detailed architecture and design documentation is available in the [`docs/`](./docs) directory:
- [01_Project_Vision.md](./docs/01_Project_Vision.md)
- [02_PRD.md](./docs/02_PRD.md)
- [03_SRS.md](./docs/03_SRS.md)
- [04_System_Architecture.md](./docs/04_System_Architecture.md)
- [05_Agent_Design.md](./docs/05_Agent_Design.md)
- [06_API_Specification.md](./docs/06_API_Specification.md)
- [07_Database_Design.md](./docs/07_Database_Design.md)
- [08_Frontend_Design.md](./docs/08_Frontend_Design.md)
- [09_Development_Roadmap.md](./docs/09_Development_Roadmap.md)
- [10_AI_Development_Guide.md](./docs/10_AI_Development_Guide.md)
- [11_Decision_Log.md](./docs/11_Decision_Log.md)

---

## 🛠️ Quick Start

### 1. Run via Docker Compose
```bash
docker-compose up --build
```
Access the application at `http://localhost:3000` and API docs at `http://localhost:8000/docs`.

### 2. Local Manual Setup
#### Backend Setup:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```

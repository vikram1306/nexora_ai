# AI Development Guide & Open-Source LLM Architecture - Nexora AI

## 1. Local AI Ecosystem Principles
Nexora AI is strictly designed to operate on **100% open-source, locally hosted AI infrastructure**. Zero paid cloud API dependencies (no OpenAI, Anthropic, or external API keys required).

---

## 2. Model Selection Matrix

| Task Domain | Recommended Local Model | Execution Context | Backup / Fallback Model |
|---|---|---|---|
| **Planner & Routing** | `Mistral-7B-Instruct` / `Llama-3-8B` | Ollama / HuggingFace Pipeline | `Phi-3-Mini` |
| **Department JSON Reasoning** | `Llama-3-8B-Instruct` | Ollama JSON Mode | `DeepSeek-Coder-7B` |
| **Strategic Recommendations** | `Llama-3-8B-Instruct` | Local Transformers / Ollama | `Mistral-7B` |
| **Sentence Embeddings** | `SentenceTransformers` (`all-MiniLM-L6-v2`) | Local CPU/GPU Python Execution | `bge-small-en-v1.5` |

---

## 3. Pydantic Enforcement & JSON Schema Contracts
All agent responses must strictly pass Pydantic validation before being handed back to the Planner Agent.

Example JSON output model contract:
```python
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AgentMetric(BaseModel):
    name: str
    value: float
    unit: str
    change_pct: Optional[float] = None

class DepartmentAgentOutput(BaseModel):
    department: str
    metrics: List[AgentMetric]
    sql_executed: str
    trends: List[Dict[str, Any]]
    evidence: List[str]
    confidence: float
```

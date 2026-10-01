import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.domain import User
from app.schemas.agents import ExecutiveQueryRequest, ExecutiveQueryResponse
from app.api.deps import get_current_user
from app.planner.planner import PlannerAgent

router = APIRouter(prefix="/query", tags=["Multi-Agent Intelligence Query"])

@router.post("/execute", response_model=ExecutiveQueryResponse)
def execute_executive_query(
    request: ExecutiveQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Query prompt cannot be empty")

    planner = PlannerAgent(db, current_user.tenant_id)
    return planner.execute_query(request.prompt)

@router.post("/export-pdf")
def export_executive_pdf(
    request: ExecutiveQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Executes query and streams back a formatted PDF executive intelligence report."""
    from fastapi.responses import Response
    from app.reporting.pdf_exporter import generate_executive_pdf_bytes

    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Query prompt cannot be empty")

    planner = PlannerAgent(db, current_user.tenant_id)
    query_res = planner.execute_query(request.prompt)
    pdf_bytes = generate_executive_pdf_bytes(query_res)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Nexora_Executive_Report.pdf"}
    )

@router.get("/ollama-status")
def check_ollama_status():
    """Check if local Ollama (Llama 3) service is active on host machine."""
    try:
        with httpx.Client(timeout=1.5) as client:
            res = client.get("http://localhost:11434/api/tags")
            if res.status_code == 200:
                models = res.json().get("models", [])
                model_names = [m.get("name") for m in models]
                return {
                    "status": "online",
                    "local_models": model_names,
                    "active_llm": "Llama 3 / Mistral (Local Ollama)"
                }
    except Exception:
        pass
    return {
        "status": "offline",
        "active_llm": "Built-in Deterministic Engine",
        "info": "Start Ollama locally ('ollama run llama3') to enable Llama 3 text synthesis."
    }

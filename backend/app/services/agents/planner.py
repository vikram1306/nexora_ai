import concurrent.futures
import httpx
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.memory.enterprise_memory import EnterpriseMemoryManager
from app.schemas.agents import (
    PlannerTaskPlan, DepartmentAgentOutput, ExecutiveQueryResponse
)
from app.services.agents.department_agents import (
    SalesAgent, FinanceAgent, HRAgent, MarketingAgent, OperationsAgent
)
from app.services.agents.strategic_and_validator import ResponseValidator, StrategicIntelligenceAgent

OOD_KEYWORDS = [
    "politics", "election", "president", "vote", "medical", "doctor", "symptom",
    "prescription", "python code", "debug this error", "react component", "javascript",
    "dating advice", "weather forecast today", "who won the match", "recipe",
    "create app", "create an app", "build app", "build an app", "make an app", "how to create an app",
    "app development", "create website", "code an app", "flutter app", "android app", "ios app", "how to code"
]

class PlannerAgent:
    """Central Brain of Nexora AI. Coordinates parallel department agents, dynamic LLM synthesis, statistical precision, and glass card formatting."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.memory = EnterpriseMemoryManager(db, tenant_id)

    def analyze_intent_and_plan(self, prompt: str) -> PlannerTaskPlan:
        prompt_lower = prompt.lower()

        # Check for Out-Of-Domain topics
        for kw in OOD_KEYWORDS:
            if kw in prompt_lower:
                return PlannerTaskPlan(
                    intent="OUT_OF_DOMAIN",
                    target_departments=[],
                    is_out_of_domain=True,
                    rejection_reason=f"Nexora AI is strictly configured as an Enterprise Intelligence OS. The requested query contains a non-business topic or general software development request ('{kw}')."
                )

        target_departments = []

        if any(k in prompt_lower for k in ["sale", "revenue", "deal", "pipeline", "region", "customer", "grow", "decline", "increase", "decrease", "trend", "client", "product"]):
            target_departments.append("sales")

        if any(k in prompt_lower for k in ["finance", "expense", "cost", "profit", "margin", "budget", "ebitda", "money", "spending", "burn", "opex"]):
            target_departments.append("finance")

        if any(k in prompt_lower for k in ["hr", "employee", "headcount", "salary", "pay", "attrition", "turnover", "workforce", "manage", "staff", "people", "team", "hire", "productivity", "culture"]):
            target_departments.append("hr")

        if any(k in prompt_lower for k in ["marketing", "cac", "roas", "campaign", "lead", "ad", "market", "beneficial", "brand", "acquisition", "channel", "mql", "conversion"]):
            target_departments.append("marketing")

        if any(k in prompt_lower for k in ["operation", "delay", "fulfillment", "inventory", "warehouse", "logistics", "shipping", "carrier", "supply", "order"]):
            target_departments.append("operations")

        # If broad company query, execute ALL 5 department agents
        if not target_departments or any(k in prompt_lower for k in ["company", "business", "overall", "health", "strategy", "improve", "entire", "all"]):
            target_departments = ["sales", "finance", "hr", "marketing", "operations"]

        return PlannerTaskPlan(
            intent="EXECUTIVE_ANALYSIS",
            target_departments=list(set(target_departments)),
            is_out_of_domain=False
        )

    def _execute_agent_threadsafe(self, dept_name: str, prompt: str) -> DepartmentAgentOutput:
        """Helper to execute department agent in its database session."""
        db_thread = self.db if self.db is not None else SessionLocal()
        try:
            memory_thread = EnterpriseMemoryManager(db_thread, self.tenant_id)
            agent_map = {
                "sales": SalesAgent(memory_thread),
                "finance": FinanceAgent(memory_thread),
                "hr": HRAgent(memory_thread),
                "marketing": MarketingAgent(memory_thread),
                "operations": OperationsAgent(memory_thread)
            }
            agent = agent_map[dept_name]
            return agent.execute(prompt)
        finally:
            if db_thread != self.db:
                db_thread.close()

    def execute_query(self, prompt: str) -> ExecutiveQueryResponse:
        plan = self.analyze_intent_and_plan(prompt)

        if plan.is_out_of_domain:
            return ExecutiveQueryResponse(
                prompt=prompt,
                is_out_of_domain=True,
                intent="OUT_OF_DOMAIN",
                confidence_score=1.0,
                executive_summary=plan.rejection_reason,
                department_outputs=[],
                strategic_recommendations=[],
                evidence_citations=["System Policy Enforcement: Non-enterprise domain query rejected."]
            )

        # Execute agents in parallel with thread-safe DB sessions
        department_outputs: List[DepartmentAgentOutput] = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_dept = {executor.submit(self._execute_agent_threadsafe, d, prompt): d for d in plan.target_departments}
            for future in concurrent.futures.as_completed(future_to_dept):
                dept_name = future_to_dept[future]
                try:
                    res = future.result()
                    department_outputs.append(res)
                except Exception as e:
                    department_outputs.append(DepartmentAgentOutput(
                        department=dept_name,
                        metrics=[],
                        sql_executed="-- Error during execution",
                        trends=[],
                        evidence=[f"Execution exception: {str(e)}"],
                        insights=[f"Agent failed with error: {str(e)}"],
                        confidence_score=0.0
                    ))

        # Cross-Departmental EBITDA & Margin Calculation (ONLY if explicitly requested)
        ebitda_summary = self._calculate_cross_departmental_ebitda(prompt, department_outputs)

        # Validate outputs & compute confidence score
        confidence_score, validation_citations = ResponseValidator.validate_outputs(department_outputs)

        # Generate Strategic Recommendations based on user prompt and department outputs
        recommendations = StrategicIntelligenceAgent.generate_recommendations(prompt, department_outputs)

        # Synthesize Structured Executive Summary
        summary_paragraphs = []
        all_evidence = list(validation_citations)

        if ebitda_summary:
            summary_paragraphs.append(ebitda_summary)

        for out in department_outputs:
            if out.insights:
                formatted_insights = "\n• " + "\n• ".join(out.insights)
                summary_paragraphs.append(f"### {out.department.upper()} INTELLIGENCE{formatted_insights}")
            all_evidence.extend(out.evidence)

        base_summary = "\n\n".join(summary_paragraphs) if summary_paragraphs else "Executive intelligence completed. Inspect metric cards below for details."

        # Dynamic LLM Synthesis with Zero Data Loss
        final_summary = self._synthesize_dynamic_llm_response(prompt, base_summary, department_outputs)

        # Build Chart Config for Recharts
        chart_config = self._build_chart_config(department_outputs)

        return ExecutiveQueryResponse(
            prompt=prompt,
            is_out_of_domain=False,
            intent=plan.intent,
            confidence_score=confidence_score,
            executive_summary=final_summary,
            department_outputs=department_outputs,
            strategic_recommendations=recommendations,
            evidence_citations=all_evidence,
            chart_config=chart_config
        )

    def _synthesize_dynamic_llm_response(self, prompt: str, base_summary: str, department_outputs: List[DepartmentAgentOutput]) -> str:
        """Synthesizes dynamic LLM responses via Ollama Llama 3 while strictly preserving statistical accuracy and markdown glass card formatting."""
        try:
            with httpx.Client(timeout=2.5) as client:
                ollama_req = {
                    "model": "llama3",
                    "prompt": (
                        f"You are Nexora AI, an Enterprise Intelligence AI OS.\n"
                        f"Synthesize a dynamic executive response to the user's specific prompt: \"{prompt}\"\n\n"
                        f"STRICT RULES:\n"
                        f"1. Directly answer the user's question in crisp executive language.\n"
                        f"2. YOU MUST PRESERVE ALL NUMBERS AND STATISTICAL METRICS FROM THE DATA EVIDENCE BELOW.\n"
                        f"3. FORMAT OUTPUT BEAUTIFULLY WITH MARKDOWN SECTION HEADERS `### SECTION_TITLE` AND BULLET POINTS `•`.\n\n"
                        f"DATA EVIDENCE:\n{base_summary}"
                    ),
                    "stream": False
                }
                res = client.post("http://localhost:11434/api/generate", json=ollama_req)
                if res.status_code == 200:
                    text = res.json().get("response", "").strip()
                    if text and "###" in text and len(text) > 50:
                        return text
        except Exception:
            pass

        return base_summary

    def _calculate_cross_departmental_ebitda(self, prompt: str, department_outputs: List[DepartmentAgentOutput]) -> Optional[str]:
        prompt_lower = prompt.lower()
        has_ebitda_keywords = any(k in prompt_lower for k in ["ebitda", "net margin", "net profit", "revenue vs expense", "revenue vs cost"])
        
        sales_out = next((d for d in department_outputs if d.department == "sales"), None)
        finance_out = next((d for d in department_outputs if d.department == "finance"), None)

        if has_ebitda_keywords and sales_out and finance_out:
            total_rev = None
            total_exp = None

            # Get revenue from sales output metrics
            if sales_out and sales_out.metrics:
                rev_m = next((m for m in sales_out.metrics if "Revenue" in m.name or "Sales" in m.name), sales_out.metrics[0])
                if rev_m and rev_m.value:
                    total_rev = float(rev_m.value)

            # Get expenses from finance output metrics
            if finance_out and finance_out.metrics:
                exp_m = next((m for m in finance_out.metrics if "Expense" in m.name or "Cost" in m.name), finance_out.metrics[0])
                if exp_m and exp_m.value:
                    total_exp = float(exp_m.value)

            # Fallback to direct dataframe query if metrics missed them
            if total_rev is None:
                sales_df = self.memory.query_department_dataframe("sales")
                if sales_df is not None and not sales_df.empty:
                    rev_col = next((c for c in sales_df.select_dtypes(include=[np.number]).columns if "amount" in c or "sales" in c or "rev" in c), None)
                    if rev_col:
                        total_rev = float(sales_df[rev_col].sum())

            if total_exp is None:
                fin_df = self.memory.query_department_dataframe("finance")
                if fin_df is not None and not fin_df.empty:
                    exp_col = next((c for c in fin_df.select_dtypes(include=[np.number]).columns if "exp" in c or "cost" in c or "spend" in c), None)
                    if exp_col:
                        total_exp = float(fin_df[exp_col].sum())

            if total_rev is not None and total_exp is not None and total_rev > 0:
                net_ebitda = total_rev - total_exp
                margin_pct = (net_ebitda / total_rev) * 100

                # Dynamic Expense Spike Analysis from Finance time series
                spike_line = ""
                fin_df = self.memory.query_department_dataframe("finance")
                if fin_df is not None and not fin_df.empty:
                    date_col = next((c for c in fin_df.columns if "month" in c or "date" in c or "period" in c), None)
                    exp_col = next((c for c in fin_df.select_dtypes(include=[np.number]).columns if "exp" in c or "cost" in c or "spend" in c), None)
                    if date_col and exp_col:
                        try:
                            fin_df['parsed_d'] = pd.to_datetime(fin_df[date_col], errors='coerce')
                            valid_fin = fin_df.dropna(subset=['parsed_d']).sort_values('parsed_d')
                            monthly = valid_fin.groupby(valid_fin[date_col])[exp_col].sum()
                            if len(monthly) >= 2:
                                max_pct = -999.0
                                max_period = None
                                max_val = 0.0
                                periods = list(monthly.index)
                                for i in range(1, len(periods)):
                                    p_prev, p_curr = periods[i-1], periods[i]
                                    v_prev, v_curr = float(monthly[p_prev]), float(monthly[p_curr])
                                    if v_prev > 0:
                                        pct = ((v_curr - v_prev) / v_prev) * 100
                                        if pct > max_pct:
                                            max_pct = pct
                                            max_period = p_curr
                                            max_val = v_curr
                                if max_period and max_pct > 0:
                                    spike_line = f"\n• **Expense Spike Analysis**: Period {max_period} expenditure increased to ${max_val:,.2f} (+{max_pct:.1f}% MoM)."
                        except Exception:
                            pass

                return (
                    f"### FINANCIAL & EBITDA OVERVIEW\n"
                    f"• **Total Sales Revenue**: ${total_rev:,.2f}\n"
                    f"• **Total Operating Expenditure**: ${total_exp:,.2f}\n"
                    f"• **Net EBITDA**: **${net_ebitda:,.2f}** (Net EBITDA Margin: **{margin_pct:.2f}%**)"
                    f"{spike_line}"
                )
        return None

    def _build_chart_config(self, department_outputs: List[DepartmentAgentOutput]) -> Dict[str, Any]:
        chart_data = []
        for out in department_outputs:
            for m in out.metrics:
                chart_data.append({
                    "name": f"{out.department.capitalize()} - {m.name}",
                    "value": m.value,
                    "unit": m.unit
                })

        return {
            "chart_type": "bar",
            "title": "Cross-Departmental Metric Breakdown",
            "data": chart_data
        }

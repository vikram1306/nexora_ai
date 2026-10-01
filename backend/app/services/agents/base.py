import pandas as pd
from typing import List
from app.services.memory.enterprise_memory import EnterpriseMemoryManager
from app.schemas.agents import DepartmentAgentOutput

class BaseDepartmentAgent:
    def __init__(self, memory: EnterpriseMemoryManager, department_name: str):
        self.memory = memory
        self.department_name = department_name

    def execute(self, prompt: str) -> DepartmentAgentOutput:
        df = self.memory.query_department_dataframe(self.department_name)
        vector_hits = self.memory.search_semantic_memory(prompt, department=self.department_name)
        
        evidence = [hit["content"] for hit in vector_hits]
        
        if df is None or df.empty:
            return DepartmentAgentOutput(
                department=self.department_name,
                metrics=[],
                sql_executed=f"SELECT * FROM {self.department_name}_datasets -- [No ingested records]",
                trends=[],
                evidence=evidence or [f"No uploaded dataset available for {self.department_name} department."],
                insights=[f"No dataset found for {self.department_name} in enterprise memory."],
                confidence_score=0.5
            )

        return self._analyze_data(df, prompt, evidence)

    def _analyze_data(self, df: pd.DataFrame, prompt: str, evidence: List[str]) -> DepartmentAgentOutput:
        raise NotImplementedError

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.database import SessionLocal
from app.services.agents.planner import PlannerAgent

db = SessionLocal()
planner = PlannerAgent(db, "demo_tenant")
res = planner.execute_query("Analyze our sales revenue against operating expenses to determine net EBITDA margin and identify cost spikes")

print("==================================================")
print("EXECUTION OUTPUT:")
print("==================================================")
print(res.executive_summary)
print("==================================================")

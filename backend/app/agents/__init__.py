"""
Department agents package providing domain-specific intelligence analyzers.
"""

from app.agents.base import BaseDepartmentAgent
from app.agents.finance import FinanceAgent
from app.agents.hr import HRAgent
from app.agents.marketing import MarketingAgent
from app.agents.operations import OperationsAgent
from app.agents.sales import SalesAgent

__all__ = [
    "BaseDepartmentAgent",
    "SalesAgent",
    "FinanceAgent",
    "HRAgent",
    "MarketingAgent",
    "OperationsAgent",
]

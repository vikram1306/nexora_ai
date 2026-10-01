"""
Department agents package providing domain-specific intelligence analyzers.
"""

from app.services.agents.base import BaseDepartmentAgent
from app.services.agents.sales import SalesAgent
from app.services.agents.finance import FinanceAgent
from app.services.agents.hr import HRAgent
from app.services.agents.marketing import MarketingAgent
from app.services.agents.operations import OperationsAgent

__all__ = [
    "BaseDepartmentAgent",
    "SalesAgent",
    "FinanceAgent",
    "HRAgent",
    "MarketingAgent",
    "OperationsAgent",
]

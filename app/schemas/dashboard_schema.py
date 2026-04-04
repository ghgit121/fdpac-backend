from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class DashboardSummaryResponse(BaseModel):
    total_income: float
    total_expense: float
    net_balance: float


class CategoryBreakdownItem(BaseModel):
    category: str
    total: float


class MonthlyTrendItem(BaseModel):
    month: str
    income: float
    expense: float


class AdminRecordBrief(BaseModel):
    id: int
    amount: float
    type: str
    category: str
    description: Optional[str] = None
    date: date


class AdminInsightsResponse(BaseModel):
    highest_transaction_30d: Optional[AdminRecordBrief] = None
    top_5_expenses: List[AdminRecordBrief]
    expense_to_income_ratio: float
    unusual_transactions: List[AdminRecordBrief]
    total_income: float
    net_balance: float
    recent_transactions: List[AdminRecordBrief]

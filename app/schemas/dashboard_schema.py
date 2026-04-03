from pydantic import BaseModel


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

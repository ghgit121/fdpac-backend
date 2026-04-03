from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.financial_record import FinancialRecord, RecordType
from app.services.record_service import sum_by_type


def get_summary(db: Session) -> dict:
    total_income = sum_by_type(db, RecordType.income)
    total_expense = sum_by_type(db, RecordType.expense)
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": total_income - total_expense,
    }


def get_category_breakdown(db: Session) -> list[dict]:
    rows = db.query(FinancialRecord).filter(FinancialRecord.deleted_at.is_(None)).all()
    totals = defaultdict(float)
    for row in rows:
        totals[row.category] += float(row.amount)
    return [{"category": category, "total": total} for category, total in sorted(totals.items())]


def get_monthly_trends(db: Session) -> list[dict]:
    rows = db.query(FinancialRecord).filter(FinancialRecord.deleted_at.is_(None)).all()
    trends = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for row in rows:
        key = row.date.strftime("%Y-%m")
        bucket = trends[key]
        if row.type == RecordType.income:
            bucket["income"] += float(row.amount)
        else:
            bucket["expense"] += float(row.amount)

    results = []
    for month in sorted(trends.keys()):
        values = trends[month]
        results.append({"month": month, "income": values["income"], "expense": values["expense"]})
    return results


def get_recent_activity(db: Session) -> list[FinancialRecord]:
    return (
        db.query(FinancialRecord)
        .filter(FinancialRecord.deleted_at.is_(None))
        .order_by(FinancialRecord.created_at.desc())
        .limit(10)
        .all()
    )

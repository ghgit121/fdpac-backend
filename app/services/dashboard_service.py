from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial_record import FinancialRecord, RecordType
from app.services.record_service import sum_by_type


async def get_summary(db: AsyncSession) -> dict:
    total_income = await sum_by_type(db, RecordType.income)
    total_expense = await sum_by_type(db, RecordType.expense)
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": total_income - total_expense,
    }


async def get_category_breakdown(db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(
            FinancialRecord.category,
            func.coalesce(func.sum(FinancialRecord.amount), 0.0),
        )
        .where(FinancialRecord.deleted_at.is_(None))
        .group_by(FinancialRecord.category)
        .order_by(FinancialRecord.category.asc())
    )
    return [{"category": category, "total": float(total)} for category, total in result.all()]


async def get_monthly_trends(db: AsyncSession) -> list[dict]:
    rows = await db.execute(
        select(FinancialRecord.date, FinancialRecord.type, FinancialRecord.amount).where(
            FinancialRecord.deleted_at.is_(None)
        )
    )
    trends = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for row in rows.all():
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


async def get_recent_activity(db: AsyncSession) -> list[FinancialRecord]:
    result = await db.execute(
        select(FinancialRecord)
        .where(FinancialRecord.deleted_at.is_(None))
        .order_by(FinancialRecord.created_at.desc())
        .limit(10)
    )
    return list(result.scalars().all())

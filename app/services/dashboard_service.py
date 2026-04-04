from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial_record import FinancialRecord, RecordType
from app.services.record_service import sum_by_type


async def get_summary(db: AsyncSession) -> dict:
    total_income = await sum_by_type(db, RecordType.income)
    total_expense = await sum_by_type(db, RecordType.expense)
    
    tx_count_res = await db.execute(select(func.count(FinancialRecord.id)).where(FinancialRecord.deleted_at.is_(None)))
    tx_count = tx_count_res.scalar_one_or_none() or 0
    
    avg_expense_res = await db.execute(
        select(func.avg(FinancialRecord.amount))
        .where(FinancialRecord.deleted_at.is_(None), FinancialRecord.type == RecordType.expense)
    )
    avg_expense = float(avg_expense_res.scalar_one_or_none() or 0.0)
    
    highest_cat_res = await db.execute(
        select(FinancialRecord.category, func.sum(FinancialRecord.amount).label("total"))
        .where(FinancialRecord.deleted_at.is_(None), FinancialRecord.type == RecordType.expense)
        .group_by(FinancialRecord.category)
        .order_by(func.sum(FinancialRecord.amount).desc())
        .limit(1)
    )
    highest_cat_row = highest_cat_res.first()
    highest_expense_category = highest_cat_row.category if highest_cat_row else None

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": total_income - total_expense,
        "tx_count": tx_count,
        "avg_expense": avg_expense,
        "highest_expense_category": highest_expense_category,
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


async def get_weekly_trends(db: AsyncSession) -> list[dict]:
    rows = await db.execute(
        select(FinancialRecord.date, FinancialRecord.type, FinancialRecord.amount).where(
            FinancialRecord.deleted_at.is_(None)
        )
    )
    trends = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for row in rows.all():
        # ISO calendar gives (year, week, weekday)
        iso_year, iso_week, _ = row.date.isocalendar()
        key = f"{iso_year}-W{iso_week:02d}"
        bucket = trends[key]
        if row.type == RecordType.income:
            bucket["income"] += float(row.amount)
        else:
            bucket["expense"] += float(row.amount)

    results = []
    for week in sorted(trends.keys()):
        values = trends[week]
        results.append({"week": week, "income": values["income"], "expense": values["expense"]})
    return results


async def get_recent_activity(db: AsyncSession) -> list[FinancialRecord]:
    result = await db.execute(
        select(FinancialRecord)
        .where(FinancialRecord.deleted_at.is_(None))
        .order_by(FinancialRecord.created_at.desc())
        .limit(10)
    )
    return list(result.scalars().all())

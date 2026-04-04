import datetime
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.financial_record import FinancialRecord, RecordType
from app.models.user import User
from app.services.record_service import sum_by_type


def _get_base_query(current_user: User, *columns):
    is_viewer = current_user.role.name == 'viewer'
    # Start with base query selecting columns or full entity
    query = select(*columns) if columns else select(FinancialRecord)
    query = query.where(FinancialRecord.deleted_at.is_(None))
    if is_viewer:
        query = query.where(FinancialRecord.created_by == current_user.id)
    return query

async def get_summary(db: AsyncSession, current_user: User) -> dict:
    inc_query = _get_base_query(current_user, func.coalesce(func.sum(FinancialRecord.amount), 0.0)).where(FinancialRecord.type == RecordType.income)
    exp_query = _get_base_query(current_user, func.coalesce(func.sum(FinancialRecord.amount), 0.0)).where(FinancialRecord.type == RecordType.expense)
    
    total_income = (await db.execute(inc_query)).scalar_one()
    total_expense = (await db.execute(exp_query)).scalar_one()

    tx_count_res = await db.execute(_get_base_query(current_user, func.count(FinancialRecord.id)))
    tx_count = tx_count_res.scalar_one() or 0

    avg_expense_res = await db.execute(
        _get_base_query(current_user, func.avg(FinancialRecord.amount))
        .where(FinancialRecord.type == RecordType.expense)
    )
    avg_expense = float(avg_expense_res.scalar_one_or_none() or 0.0)

    highest_cat_res = await db.execute(
        _get_base_query(current_user, FinancialRecord.category, func.sum(FinancialRecord.amount).label("total"))
        .where(FinancialRecord.type == RecordType.expense)
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


async def get_category_breakdown(db: AsyncSession, current_user: User) -> list[dict]:
    result = await db.execute(
        _get_base_query(current_user, FinancialRecord.category, func.coalesce(func.sum(FinancialRecord.amount), 0.0))
        .group_by(FinancialRecord.category)
        .order_by(FinancialRecord.category.asc())
    )
    return [{"category": category, "total": float(total)} for category, total in result.all()]


async def get_monthly_trends(db: AsyncSession, current_user: User) -> list[dict]:
    rows = await db.execute(
        _get_base_query(current_user, FinancialRecord.date, FinancialRecord.type, FinancialRecord.amount)
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


async def get_weekly_trends(db: AsyncSession, current_user: User) -> list[dict]:
    rows = await db.execute(
        _get_base_query(current_user, FinancialRecord.date, FinancialRecord.type, FinancialRecord.amount)
    )
    trends = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for row in rows.all():
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


async def get_recent_activity(db: AsyncSession, current_user: User) -> list[FinancialRecord]:
    result = await db.execute(
        _get_base_query(current_user)
        .order_by(FinancialRecord.created_at.desc())
        .limit(10)
    )
    return list(result.scalars().all())


async def get_admin_insights(db: AsyncSession) -> dict:
    # Basic Totals
    inc_query = select(func.coalesce(func.sum(FinancialRecord.amount), 0.0)).where(FinancialRecord.type == RecordType.income, FinancialRecord.deleted_at.is_(None))
    exp_query = select(func.coalesce(func.sum(FinancialRecord.amount), 0.0)).where(FinancialRecord.type == RecordType.expense, FinancialRecord.deleted_at.is_(None))

    total_inc = (await db.execute(inc_query)).scalar_one()
    total_exp = (await db.execute(exp_query)).scalar_one()
    platform_net_balance = total_inc - total_exp
    
    expense_to_income_ratio = float(total_exp / total_inc) if total_inc > 0 else 0.0

    # Highest Transaction in Last 30 Days
    thirty_days_ago = datetime.date.today() - datetime.timedelta(days=30)
    highest_tx_res = await db.execute(
        select(FinancialRecord)
        .where(FinancialRecord.deleted_at.is_(None), FinancialRecord.date >= thirty_days_ago)
        .order_by(FinancialRecord.amount.desc())
        .limit(1)
    )
    highest_tx = highest_tx_res.scalar_one_or_none()

    # Top 5 Expense Transactions
    top_5_exp_res = await db.execute(
        select(FinancialRecord)
        .where(FinancialRecord.deleted_at.is_(None), FinancialRecord.type == RecordType.expense)
        .order_by(FinancialRecord.amount.desc())
        .limit(5)
    )
    top_5_exp = top_5_exp_res.scalars().all()

    # Unusual/High-Value Transactions
    unusual_res = await db.execute(
        select(FinancialRecord)
        .where(FinancialRecord.deleted_at.is_(None), FinancialRecord.amount > 1000)
        .order_by(FinancialRecord.amount.desc())
    )
    unusual_tx = unusual_res.scalars().all()

    # Recent Transactions
    recent_res = await db.execute(
        select(FinancialRecord)
        .where(FinancialRecord.deleted_at.is_(None))
        .order_by(FinancialRecord.date.desc(), FinancialRecord.created_at.desc())
        .limit(5)
    )
    recent_tx = recent_res.scalars().all()

    def map_record(r: FinancialRecord):
        if not r: return None
        return {
            "id": r.id,
            "amount": float(r.amount),
            "type": r.type.value,
            "category": r.category,
            "description": r.notes,
            "date": r.date
        }

    return {
        "highest_transaction_30d": map_record(highest_tx),
        "top_5_expenses": [map_record(r) for r in top_5_exp],
        "expense_to_income_ratio": expense_to_income_ratio,
        "unusual_transactions": [map_record(r) for r in unusual_tx],
        "total_income": float(total_inc),
        "net_balance": float(platform_net_balance),
        "recent_transactions": [map_record(r) for r in recent_tx],
    }

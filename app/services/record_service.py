from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.financial_record import FinancialRecord, RecordType
from app.schemas.record_schema import RecordCreateRequest, RecordListQuery, RecordUpdateRequest
from app.utils.pagination import build_page_meta, to_offset


async def create_record(payload: RecordCreateRequest, user_id: int, db: AsyncSession) -> FinancialRecord:
    record = FinancialRecord(
        amount=payload.amount,
        type=payload.type,
        category=payload.category,
        date=payload.date,
        notes=payload.notes,
        created_by=user_id,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_record_or_404(record_id: int, db: AsyncSession) -> FinancialRecord:
    result = await db.execute(
        select(FinancialRecord).where(
            FinancialRecord.id == record_id,
            FinancialRecord.deleted_at.is_(None),
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return record


async def list_records(filters: RecordListQuery, db: AsyncSession) -> dict:
    conditions = [FinancialRecord.deleted_at.is_(None)]
    if filters.type:
        conditions.append(FinancialRecord.type == filters.type)
    if filters.category:
        conditions.append(FinancialRecord.category.ilike(f"%{filters.category}%"))
    if filters.start_date:
        conditions.append(FinancialRecord.date >= filters.start_date)
    if filters.end_date:
        conditions.append(FinancialRecord.date <= filters.end_date)
    if filters.notes:
        conditions.append(FinancialRecord.notes.ilike(f"%{filters.notes}%"))

    where_clause = and_(*conditions)

    count_result = await db.execute(
        select(func.count(FinancialRecord.id)).where(where_clause)
    )
    total = count_result.scalar_one()

    items_result = await db.execute(
        select(FinancialRecord)
        .where(where_clause)
        .order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc())
        .offset(to_offset(filters.page, filters.page_size))
        .limit(filters.page_size)
    )
    records = list(items_result.scalars().all())

    return {
        "items": records,
        "pagination": build_page_meta(filters.page, filters.page_size, total),
    }


async def update_record(record_id: int, payload: RecordUpdateRequest, db: AsyncSession) -> FinancialRecord:
    record = await get_record_or_404(record_id, db)

    if payload.amount is not None:
        record.amount = payload.amount
    if payload.type is not None:
        record.type = payload.type
    if payload.category is not None:
        record.category = payload.category
    if payload.date is not None:
        record.date = payload.date
    if payload.notes is not None:
        record.notes = payload.notes

    await db.commit()
    await db.refresh(record)
    return record


async def soft_delete_record(record_id: int, db: AsyncSession):
    record = await get_record_or_404(record_id, db)
    record.deleted_at = datetime.now(timezone.utc)
    await db.commit()


async def sum_by_type(db: AsyncSession, record_type: RecordType) -> float:
    total_result = await db.execute(
        select(func.coalesce(func.sum(FinancialRecord.amount), 0.0)).where(
            FinancialRecord.type == record_type,
            FinancialRecord.deleted_at.is_(None),
        )
    )
    return float(total_result.scalar_one() or 0.0)

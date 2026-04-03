from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.financial_record import FinancialRecord, RecordType
from app.schemas.record_schema import RecordCreateRequest, RecordListQuery, RecordUpdateRequest
from app.utils.pagination import build_page_meta, to_offset


def create_record(payload: RecordCreateRequest, user_id: int, db: Session) -> FinancialRecord:
    record = FinancialRecord(
        amount=payload.amount,
        type=payload.type,
        category=payload.category,
        date=payload.date,
        notes=payload.notes,
        created_by=user_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_record_or_404(record_id: int, db: Session) -> FinancialRecord:
    record = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.id == record_id, FinancialRecord.deleted_at.is_(None))
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return record


def list_records(filters: RecordListQuery, db: Session) -> dict:
    query = db.query(FinancialRecord).filter(FinancialRecord.deleted_at.is_(None))

    conditions = []
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

    if conditions:
        query = query.filter(and_(*conditions))

    total = query.count()
    records = (
        query.order_by(FinancialRecord.date.desc(), FinancialRecord.id.desc())
        .offset(to_offset(filters.page, filters.page_size))
        .limit(filters.page_size)
        .all()
    )
    return {
        "items": records,
        "pagination": build_page_meta(filters.page, filters.page_size, total),
    }


def update_record(record_id: int, payload: RecordUpdateRequest, db: Session) -> FinancialRecord:
    record = get_record_or_404(record_id, db)

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

    db.commit()
    db.refresh(record)
    return record


def soft_delete_record(record_id: int, db: Session):
    record = get_record_or_404(record_id, db)
    record.deleted_at = datetime.now(timezone.utc)
    db.commit()


def sum_by_type(db: Session, record_type: RecordType) -> float:
    rows = (
        db.query(FinancialRecord)
        .filter(FinancialRecord.type == record_type, FinancialRecord.deleted_at.is_(None))
        .all()
    )
    return float(sum(row.amount for row in rows))

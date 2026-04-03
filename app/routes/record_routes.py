from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.role_checker import require_roles
from app.database import get_db
from app.models.financial_record import RecordType
from app.models.user import User
from app.schemas.record_schema import RecordCreateRequest, RecordListQuery, RecordUpdateRequest
from app.services import record_service
from app.utils.response import success_response

router = APIRouter(prefix="/records", tags=["records"])


@router.post("", dependencies=[Depends(require_roles("admin"))])
async def create_record(
    payload: RecordCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    record = await record_service.create_record(payload, current_user.id, db)
    return success_response(
        "Record created successfully",
        {
            "id": record.id,
            "amount": record.amount,
            "type": record.type.value,
            "category": record.category,
            "date": record.date.isoformat(),
            "notes": record.notes,
            "created_by": record.created_by,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        },
        status_code=status.HTTP_201_CREATED,
    )


@router.get("", dependencies=[Depends(require_roles("admin", "analyst"))])
async def list_records(
    type: RecordType | None = Query(default=None),
    category: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    notes: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    filters = RecordListQuery(
        type=type,
        category=category,
        start_date=start_date,
        end_date=end_date,
        notes=notes,
        page=page,
        page_size=page_size,
    )
    result = await record_service.list_records(filters, db)
    data = {
        "items": [
            {
                "id": item.id,
                "amount": item.amount,
                "type": item.type.value,
                "category": item.category,
                "date": item.date.isoformat(),
                "notes": item.notes,
                "created_by": item.created_by,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in result["items"]
        ],
        "pagination": result["pagination"],
    }
    return success_response("Records fetched successfully", data)


@router.get("/{record_id}", dependencies=[Depends(require_roles("admin", "analyst"))])
async def get_record(record_id: int, db: AsyncSession = Depends(get_db)):
    record = await record_service.get_record_or_404(record_id, db)
    return success_response(
        "Record fetched successfully",
        {
            "id": record.id,
            "amount": record.amount,
            "type": record.type.value,
            "category": record.category,
            "date": record.date.isoformat(),
            "notes": record.notes,
            "created_by": record.created_by,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        },
    )


@router.put("/{record_id}", dependencies=[Depends(require_roles("admin"))])
async def update_record(record_id: int, payload: RecordUpdateRequest, db: AsyncSession = Depends(get_db)):
    record = await record_service.update_record(record_id, payload, db)
    return success_response(
        "Record updated successfully",
        {
            "id": record.id,
            "amount": record.amount,
            "type": record.type.value,
            "category": record.category,
            "date": record.date.isoformat(),
            "notes": record.notes,
            "created_by": record.created_by,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        },
    )


@router.delete("/{record_id}", dependencies=[Depends(require_roles("admin"))])
async def delete_record(record_id: int, db: AsyncSession = Depends(get_db)):
    await record_service.soft_delete_record(record_id, db)
    return success_response("Record deleted successfully", None)

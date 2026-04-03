from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.role_checker import require_roles
from app.database import get_db
from app.services import dashboard_service
from app.utils.response import success_response

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", dependencies=[Depends(require_roles("viewer", "analyst", "admin"))])
def summary(db: Session = Depends(get_db)):
    return success_response("Dashboard summary fetched", dashboard_service.get_summary(db))


@router.get("/category-breakdown", dependencies=[Depends(require_roles("viewer", "analyst", "admin"))])
def category_breakdown(db: Session = Depends(get_db)):
    return success_response("Category breakdown fetched", dashboard_service.get_category_breakdown(db))


@router.get("/monthly-trends", dependencies=[Depends(require_roles("viewer", "analyst", "admin"))])
def monthly_trends(db: Session = Depends(get_db)):
    return success_response("Monthly trends fetched", dashboard_service.get_monthly_trends(db))


@router.get("/recent-activity", dependencies=[Depends(require_roles("viewer", "analyst", "admin"))])
def recent_activity(db: Session = Depends(get_db)):
    records = dashboard_service.get_recent_activity(db)
    data = [
        {
            "id": row.id,
            "amount": row.amount,
            "type": row.type.value,
            "category": row.category,
            "date": row.date.isoformat(),
            "notes": row.notes,
            "created_by": row.created_by,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in records
    ]
    return success_response("Recent activity fetched", data)

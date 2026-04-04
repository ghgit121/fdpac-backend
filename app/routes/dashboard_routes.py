from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.role_checker import require_roles
from app.database import get_db
from app.models.user import User
from app.services import dashboard_service
from app.utils.response import success_response

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", dependencies=[Depends(require_roles("viewer", "analyst", "admin"))])
async def summary(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response("Dashboard summary fetched", await dashboard_service.get_summary(db, current_user))


@router.get("/category-breakdown", dependencies=[Depends(require_roles("viewer", "analyst", "admin"))])
async def category_breakdown(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response("Category breakdown fetched", await dashboard_service.get_category_breakdown(db, current_user))


@router.get("/monthly-trends", dependencies=[Depends(require_roles("viewer", "analyst", "admin"))])
async def monthly_trends(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response("Monthly trends fetched", await dashboard_service.get_monthly_trends(db, current_user))


@router.get("/weekly-trends", dependencies=[Depends(require_roles("viewer", "analyst", "admin"))])
async def weekly_trends(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return success_response("Weekly trends fetched", await dashboard_service.get_weekly_trends(db, current_user))


@router.get("/recent-activity", dependencies=[Depends(require_roles("viewer", "analyst", "admin"))])
async def recent_activity(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    records = await dashboard_service.get_recent_activity(db, current_user)
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


@router.get("/admin-insights", dependencies=[Depends(require_roles("admin", "analyst"))])
async def admin_insights(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = await dashboard_service.get_admin_insights(db)
    return success_response("Admin insights fetched successfully", data)


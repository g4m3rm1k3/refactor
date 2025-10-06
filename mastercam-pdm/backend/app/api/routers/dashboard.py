# backend/app/api/routers/dashboard.py
from fastapi import APIRouter, Depends
from app.models import schemas
from app.api.dependencies import get_lock_manager, get_current_user
from app.services.lock_service import MetadataManager

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_user)]  # Protect all routes in this file
)


@router.get("/stats", response_model=schemas.DashboardStats)
async def get_dashboard_stats(
    lock_manager: MetadataManager = Depends(get_lock_manager)
):
    """Retrieves statistics for the dashboard, like active checkouts."""
    active_checkouts = lock_manager.get_all_locks()

    # We need to convert the data to the Pydantic model format
    checkout_info_list = [
        schemas.CheckoutInfo(
            filename=lock.get('file', '').split('/')[-1],
            path=lock.get('file'),
            locked_by=lock.get('user'),
            locked_at=lock.get('timestamp'),
            duration_seconds=lock.get('duration_seconds', 0)
        ) for lock in active_checkouts
    ]

    return schemas.DashboardStats(active_checkouts=checkout_info_list)

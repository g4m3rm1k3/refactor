# backend/app/api/routers/dashboard.py
from fastapi import APIRouter, Depends, Query
from app.models import schemas
from app.api.dependencies import get_lock_manager, get_current_user, get_git_repo
from app.services.lock_service import MetadataManager
from app.services.git_service import GitRepository
import json
import logging

logger = logging.getLogger(__name__)

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


@router.get("/activity", response_model=schemas.ActivityFeed)
async def get_activity_feed(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of activities to return"),
    offset: int = Query(0, ge=0, description="Number of activities to skip"),
    git_repo: GitRepository = Depends(get_git_repo)
):
    """
    Retrieves recent Git activity (commits) from the repository.

    This endpoint returns a feed of recent commits, which shows what users
    have been checking in files, canceling checkouts, etc.
    """
    if not git_repo:
        return schemas.ActivityFeed(activities=[])

    try:
        # Get commit history from Git
        # The git_repo should have a method to get commits
        commits = git_repo.get_recent_commits(limit=limit + offset)

        # Skip the offset commits
        commits = commits[offset:offset + limit]

        activities = []
        for commit in commits:
            # Parse commit message to determine event type
            message = commit.get('message', '')
            event_type = 'commit'

            if 'CHECK-IN' in message or 'checkin' in message.lower():
                event_type = 'checkin'
            elif 'CHECK-OUT' in message or 'checkout' in message.lower() or 'LOCK' in message:
                event_type = 'checkout'
            elif 'UNLOCK' in message or 'cancel' in message.lower():
                event_type = 'cancel_checkout'
            elif 'DELETE' in message:
                event_type = 'delete'

            # Extract filename from message if possible
            # Format is usually like "CHECK-IN: filename.mcam - message"
            filename = "unknown"
            for part in message.split():
                if any(ext in part.lower() for ext in ['.mcam', '.vnc', '.emcam', '.link']):
                    filename = part.strip(':,.-')
                    break

            # Try to get revision from metadata in commit if available
            revision = None
            # We could parse the commit diff to see if .meta.json was updated

            activities.append(schemas.ActivityItem(
                event_type=event_type,
                filename=filename,
                user=commit.get('author', 'unknown'),
                timestamp=commit.get('timestamp', ''),
                commit_hash=commit.get('hash', ''),
                message=message,
                revision=revision
            ))

        return schemas.ActivityFeed(activities=activities)

    except Exception as e:
        logger.error(f"Failed to retrieve activity feed: {e}", exc_info=True)
        # Return empty feed instead of error to gracefully handle missing repo
        return schemas.ActivityFeed(activities=[])

"""
GitLab Users Management Router
Endpoints for managing auto-discovered GitLab users
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from app.api.dependencies import get_current_admin_user
from app.models.gitlab_users import get_gitlab_user_registry, GitLabUser

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/gitlab/users",
    tags=["GitLab Users"],
    dependencies=[Depends(get_current_admin_user)]  # Admin only
)


class GitLabUserResponse(BaseModel):
    """Response model for GitLab user"""
    username: str
    gitlab_id: Optional[int]
    email: Optional[str]
    display_name: Optional[str]
    first_seen: str  # ISO datetime string
    last_seen: str   # ISO datetime string
    is_active: bool
    is_admin: bool
    repository_access: List[str]


class UpdateUserRepositories(BaseModel):
    """Request to update user's repository access"""
    repository_ids: List[str]


@router.get("", response_model=List[GitLabUserResponse])
async def list_gitlab_users(
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get all GitLab users who have connected to the system

    Returns list of users sorted by last_seen (most recent first)
    """
    try:
        registry = get_gitlab_user_registry()
        users = registry.get_all_users()

        # Sort by last_seen descending
        users.sort(key=lambda u: u.last_seen, reverse=True)

        # Convert to response format
        response = []
        for user in users:
            response.append(GitLabUserResponse(
                username=user.username,
                gitlab_id=user.gitlab_id,
                email=user.email,
                display_name=user.display_name,
                first_seen=user.first_seen.isoformat(),
                last_seen=user.last_seen.isoformat(),
                is_active=user.is_active,
                is_admin=user.is_admin,
                repository_access=user.repository_access
            ))

        admin_username = current_user.get('sub', 'unknown')
        logger.info(f"Admin {admin_username} listed {len(response)} GitLab users")
        return response
    except Exception as e:
        logger.error(f"Error listing GitLab users: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load GitLab users: {str(e)}"
        )


@router.get("/new", response_model=List[GitLabUserResponse])
async def get_new_users(
    hours: int = 24,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Get users who registered in the last N hours

    Default: 24 hours
    """
    registry = get_gitlab_user_registry()
    users = registry.get_new_users(since_hours=hours)

    response = []
    for user in users:
        response.append(GitLabUserResponse(
            username=user.username,
            gitlab_id=user.gitlab_id,
            email=user.email,
            display_name=user.display_name,
            first_seen=user.first_seen.isoformat(),
            last_seen=user.last_seen.isoformat(),
            is_active=user.is_active,
            is_admin=user.is_admin,
            repository_access=user.repository_access
        ))

    admin_username = current_user.get('sub', 'unknown')
    logger.info(f"Admin {admin_username} checked for new users: found {len(response)}")
    return response


@router.patch("/{username}/repositories")
async def update_user_repositories(
    username: str,
    update: UpdateUserRepositories,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Update which repositories a user can access
    """
    registry = get_gitlab_user_registry()

    # Check if user exists
    user = registry.get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )

    # Update repository access
    success = registry.update_repository_access(username, update.repository_ids)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update repository access"
        )

    admin_username = current_user.get('sub', 'unknown')
    logger.info(f"Admin {admin_username} updated repositories for {username}: {update.repository_ids}")

    return {
        "status": "success",
        "message": f"Repository access updated for {username}",
        "repository_ids": update.repository_ids
    }


@router.patch("/{username}/admin")
async def toggle_admin_status(
    username: str,
    is_admin: bool,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Grant or revoke admin privileges for a user
    """
    registry = get_gitlab_user_registry()

    # Check if user exists
    user = registry.get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )

    # Prevent revoking your own admin
    if username == current_user['username'] and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot revoke your own admin privileges"
        )

    success = registry.set_admin(username, is_admin)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update admin status"
        )

    action = "granted" if is_admin else "revoked"
    logger.info(f"Admin {current_user['username']} {action} admin privileges for {username}")

    return {
        "status": "success",
        "message": f"Admin privileges {action} for {username}",
        "is_admin": is_admin
    }


@router.delete("/{username}")
async def deactivate_user(
    username: str,
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Deactivate a user (soft delete)
    User can still login but won't appear in active user lists
    """
    registry = get_gitlab_user_registry()

    # Check if user exists
    user = registry.get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )

    # Prevent deactivating yourself
    if username == current_user['username']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account"
        )

    success = registry.deactivate_user(username)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )

    logger.info(f"Admin {current_user['username']} deactivated user {username}")

    return {
        "status": "success",
        "message": f"User {username} has been deactivated"
    }

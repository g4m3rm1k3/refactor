"""
Admin Configuration Router - Endpoints for managing PDM configuration

Provides endpoints for:
- Getting current configuration
- Updating configuration (admin only)
- Managing filename patterns
- Managing repository configurations
- Managing user access control
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.models.schemas import (
    PDMAdminConfig,
    AdminConfigUpdateRequest,
    FileNamePattern,
    RepositoryConfig,
    UserRepositoryAccess,
    StandardResponse
)
from app.services.admin_config_service import AdminConfigService
from app.api.dependencies import get_current_admin_user, get_admin_config_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/config", tags=["admin-config"])


@router.get("/", response_model=PDMAdminConfig)
async def get_admin_config(
    current_user: dict = Depends(get_current_admin_user),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """
    Get current admin configuration (admin only)

    Returns complete PDM configuration including:
    - Filename patterns
    - Repository configurations
    - User access control
    - Revision settings
    """
    try:
        config = config_service.get_config()
        return config
    except Exception as e:
        logger.error(f"Error getting admin config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load configuration: {str(e)}"
        )


@router.post("/", response_model=StandardResponse)
async def update_admin_config(
    request: AdminConfigUpdateRequest,
    current_user: dict = Depends(get_current_admin_user),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """
    Update admin configuration (admin only)

    Validates and saves configuration to GitLab repository.
    All users will receive updates via polling.
    """
    try:
        # Validate configuration
        is_valid, error_msg = config_service.validate_config(request.config)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid configuration: {error_msg}"
            )

        # Save configuration
        success = config_service.save_config(request.config, request.admin_user)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save configuration"
            )

        return StandardResponse(
            status="success",
            message=f"Configuration updated by {request.admin_user}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating admin config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.get("/patterns", response_model=List[FileNamePattern])
async def get_filename_patterns(
    current_user: dict = Depends(get_current_admin_user),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """Get all filename patterns (admin only)"""
    try:
        config = config_service.get_config()
        return config.filename_patterns
    except Exception as e:
        logger.error(f"Error getting filename patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/patterns", response_model=StandardResponse)
async def add_filename_pattern(
    pattern: FileNamePattern,
    current_user: dict = Depends(get_current_admin_user),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """Add a new filename pattern (admin only)"""
    try:
        config = config_service.get_config()

        # Check if pattern name already exists
        if any(p.name == pattern.name for p in config.filename_patterns):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pattern '{pattern.name}' already exists"
            )

        # Validate regex patterns
        import re
        try:
            re.compile(pattern.link_pattern)
            re.compile(pattern.file_pattern)
        except re.error as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid regex pattern: {e}"
            )

        # Add pattern
        config.filename_patterns.append(pattern)

        # Save
        success = config_service.save_config(config, current_user["username"])
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save pattern"
            )

        return StandardResponse(
            status="success",
            message=f"Pattern '{pattern.name}' added successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding filename pattern: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/repositories", response_model=List[RepositoryConfig])
async def get_repositories(
    current_user: dict = Depends(get_current_admin_user),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """Get all repository configurations (admin only)"""
    try:
        config = config_service.get_config()
        return config.repositories
    except Exception as e:
        logger.error(f"Error getting repositories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/repositories", response_model=StandardResponse)
async def add_or_update_repository(
    repository: RepositoryConfig,
    current_user: dict = Depends(get_current_admin_user),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """Add or update repository configuration (admin only) - acts as upsert"""
    try:
        config = config_service.get_config()

        # Validate filename pattern exists
        if not config_service.get_filename_pattern(repository.filename_pattern_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Filename pattern '{repository.filename_pattern_id}' not found"
            )

        # Check if repository ID already exists
        existing_index = None
        for i, r in enumerate(config.repositories):
            if r.id == repository.id:
                existing_index = i
                break

        if existing_index is not None:
            # Update existing repository
            config.repositories[existing_index] = repository
            action = "updated"
            logger.info(f"Repository '{repository.id}' updated by {current_user['username']}")
        else:
            # Add new repository
            config.repositories.append(repository)
            action = "added"
            logger.info(f"Repository '{repository.id}' added by {current_user['username']}")

        # Save
        success = config_service.save_config(config, current_user["username"])
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save repository"
            )

        return StandardResponse(
            status="success",
            message=f"Repository '{repository.name}' {action} successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving repository: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/user-access", response_model=List[UserRepositoryAccess])
async def get_user_access(
    current_user: dict = Depends(get_current_admin_user),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """Get all user repository access configurations (admin only)"""
    try:
        config = config_service.get_config()
        return config.user_access
    except Exception as e:
        logger.error(f"Error getting user access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/user-access", response_model=StandardResponse)
async def update_user_access(
    user_access: UserRepositoryAccess,
    current_user: dict = Depends(get_current_admin_user),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """Add or update user repository access (admin only)"""
    try:
        config = config_service.get_config()

        # Validate repository IDs exist
        repo_ids = {r.id for r in config.repositories}
        for repo_id in user_access.repository_ids:
            if repo_id not in repo_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Repository ID '{repo_id}' not found"
                )

        # Validate default repository
        if user_access.default_repository_id:
            if user_access.default_repository_id not in user_access.repository_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Default repository must be in user's access list"
                )

        # Update or add user access
        found = False
        for i, access in enumerate(config.user_access):
            if access.username == user_access.username:
                config.user_access[i] = user_access
                found = True
                break

        if not found:
            config.user_access.append(user_access)

        # Save
        success = config_service.save_config(config, current_user["username"])
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save user access"
            )

        return StandardResponse(
            status="success",
            message=f"User access updated for '{user_access.username}'"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/user-access/{username}", response_model=StandardResponse)
async def remove_user_access(
    username: str,
    current_user: dict = Depends(get_current_admin_user),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """Remove user repository access (admin only)"""
    try:
        config = config_service.get_config()

        # Find and remove user access
        original_len = len(config.user_access)
        config.user_access = [a for a in config.user_access if a.username != username]

        if len(config.user_access) == original_len:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User access for '{username}' not found"
            )

        # Save
        success = config_service.save_config(config, current_user["username"])
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save configuration"
            )

        return StandardResponse(
            status="success",
            message=f"User access removed for '{username}'"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing user access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/patterns/{pattern_name}", response_model=StandardResponse)
async def delete_pattern(
    pattern_name: str,
    current_user: dict = Depends(get_current_admin_user),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """Delete a filename pattern (admin only)

    NOTE: You cannot delete a pattern if it would leave zero patterns,
    or if any repository is using it. Add a replacement pattern first."""
    try:
        config = config_service.get_config()

        # Check if pattern exists
        if not any(p.name == pattern_name for p in config.filename_patterns):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pattern '{pattern_name}' not found"
            )

        # Check if this would leave zero patterns
        if len(config.filename_patterns) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last pattern. Add a new pattern first."
            )

        # Check if any repository is using this pattern
        repos_using = [r.name for r in config.repositories if r.filename_pattern_id == pattern_name]
        if repos_using:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete pattern '{pattern_name}'. Used by repositories: {', '.join(repos_using)}. Change their patterns first."
            )

        # Remove pattern
        config.filename_patterns = [p for p in config.filename_patterns if p.name != pattern_name]

        # Save
        success = config_service.save_config(config, current_user["username"])
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save configuration"
            )

        return StandardResponse(
            status="success",
            message=f"Pattern '{pattern_name}' deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pattern: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/repositories/{repo_id}", response_model=StandardResponse)
async def delete_repository(
    repo_id: str,
    current_user: dict = Depends(get_current_admin_user),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """Delete a repository configuration (admin only)

    NOTE: You cannot delete a repository if it would leave zero repositories.
    Add a new repository first."""
    try:
        config = config_service.get_config()

        # Check if repository exists
        if not any(r.id == repo_id for r in config.repositories):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository '{repo_id}' not found"
            )

        # CRITICAL: Prevent deleting the main repository
        if repo_id == "main":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the main repository. It is the default entry point for all users."
            )

        # Check if this would leave zero repositories
        if len(config.repositories) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last repository. Add a new repository first."
            )

        # Check if any users have this as their default repo
        users_with_default = [a.username for a in config.user_access if a.default_repository_id == repo_id]
        if users_with_default:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete repository '{repo_id}'. It's the default for users: {', '.join(users_with_default)}. Change their defaults first."
            )

        # Remove repository
        config.repositories = [r for r in config.repositories if r.id != repo_id]

        # Remove repo from user access lists
        for access in config.user_access:
            if repo_id in access.repository_ids:
                access.repository_ids.remove(repo_id)

        # Save
        success = config_service.save_config(config, current_user["username"])
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save configuration"
            )

        return StandardResponse(
            status="success",
            message=f"Repository '{repo_id}' deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting repository: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/my-repositories", response_model=List[str])
async def get_my_repositories(
    current_user: dict = Depends(get_current_admin_user),
    config_service: AdminConfigService = Depends(get_admin_config_service)
):
    """
    Get repositories accessible to current user

    Returns list of repository IDs the user can access
    """
    try:
        repo_ids = config_service.get_user_repositories(current_user["username"])
        return repo_ids
    except Exception as e:
        logger.error(f"Error getting user repositories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

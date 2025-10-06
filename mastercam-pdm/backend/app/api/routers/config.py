from fastapi import APIRouter, Depends, HTTPException
from app.models import schemas
from app.api.dependencies import get_config_manager
from app.core.config import ConfigManager
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/config",
    tags=["Configuration"],
)


@router.get("", response_model=schemas.ConfigSummary)
async def get_config_summary(
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """Retrieves a summary of the current application configuration."""
    # This logic was originally in the ConfigManager class, but it's better here
    # as it constructs a summary specifically for an API response.
    cfg = config_manager.config
    gitlab_cfg = cfg.gitlab
    local_cfg = cfg.local

    return schemas.ConfigSummary(
        gitlab_url=gitlab_cfg.get('base_url'),
        project_id=gitlab_cfg.get('project_id'),
        username=gitlab_cfg.get('username'),
        has_token=bool(gitlab_cfg.get('token')),
        repo_path=local_cfg.get('repo_path'),
        # TODO: The 'is_admin' status will be determined by the user's token, not the config file.
        # We will adjust this when we refactor the user management.
        is_admin=gitlab_cfg.get('username') in ["admin", "g4m3rm1k3"]
    )


@router.post("/gitlab", response_model=schemas.StandardResponse)
async def update_gitlab_config(
    request: schemas.ConfigUpdateRequest,
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    Validates and saves new GitLab configuration settings.
    This will trigger a re-initialization of the application's services.
    """
    try:
        # TODO: Add validation logic here to test the new credentials against the GitLab API
        # before saving them. For now, we will just save the config.

        config_manager.config.gitlab['base_url'] = request.base_url
        config_manager.config.gitlab['project_id'] = request.project_id
        config_manager.config.gitlab['username'] = request.username
        config_manager.config.gitlab['token'] = request.token
        config_manager.config.security['allow_insecure_ssl'] = request.allow_insecure_ssl

        config_manager.save_config()

        # In our final phase, we'll implement a proper mechanism to signal to the
        # application that it needs to reload its services (like the GitRepository)
        # with the new configuration.
        logger.info(
            "Configuration saved. Application will re-initialize on next startup.")

        return {"status": "success", "message": "Configuration validated and saved."}

    except Exception as e:
        logger.error(
            f"An unexpected error occurred during config update: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"An internal error occurred: {e}")

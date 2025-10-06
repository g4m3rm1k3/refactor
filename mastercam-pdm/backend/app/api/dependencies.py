from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Generator

# Import the managers and services we've created
from app.core.config import ConfigManager
from app.services.lock_service import MetadataManager, ImprovedFileLockManager
from app.services.git_service import GitRepository
from app.core.security import UserAuth

# --- Dependency Provider Functions ---

# This function will be a singleton factory for the ConfigManager.
# It ensures we only create one instance of it for the entire application life.
_config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    return _config_manager

# The following functions depend on the ConfigManager to get settings.
# FastAPI will automatically resolve this chain of dependencies.


def get_lock_manager(config: ConfigManager = Depends(get_config_manager)) -> Generator[MetadataManager, None, None]:
    # This is a placeholder for now. We will wire this up properly once the full
    # application initialization logic is moved to main.py's lifespan event.
    # For now, this structure allows our code to be organized correctly.
    yield MetadataManager(repo_path=Path(config.config.local.get("repo_path", "./temp_repo")))


def get_git_repo(config: ConfigManager = Depends(get_config_manager)) -> Generator[GitRepository, None, None]:
    # Placeholder similar to the one above.
    yield GitRepository(...)


def get_user_auth(git_repo: GitRepository = Depends(get_git_repo)) -> Generator[UserAuth, None, None]:
    yield UserAuth(git_repo=git_repo)


# --- Security and Authentication Dependencies ---

reusable_oauth2 = HTTPBearer(
    scheme_name="Bearer"
)


def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
    auth_service: UserAuth = Depends(get_user_auth)
) -> dict:
    """
    Dependency to verify the JWT token from the Authorization header and return the user payload.
    This will protect our endpoints.
    """
    payload = auth_service.verify_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def get_current_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency that requires the user to be an admin.
    """
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have administrative privileges",
        )
    return current_user

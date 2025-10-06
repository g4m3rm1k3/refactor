# backend/app/api/dependencies.py

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# We no longer need to import the services themselves here,
# as we're just retrieving them from the app's state.

# Reusable security scheme
reusable_oauth2 = HTTPBearer(scheme_name="Bearer")

# --- Service Provider Functions ---


def get_config_manager(request: Request):
    return request.app.state.config_manager


def get_lock_manager(request: Request):
    return request.app.state.metadata_manager


def get_git_repo(request: Request):
    return request.app.state.git_repo


def get_user_auth(request: Request):
    return request.app.state.user_auth

# --- Security and Authentication Dependencies ---


def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
    auth_service=Depends(get_user_auth)
) -> dict:
    """Dependency to verify a token and return the user payload."""
    payload = auth_service.verify_token(token.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return payload


def get_current_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency that requires the user to be an admin."""
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have administrative privileges.",
        )
    return current_user

# backend/app/api/dependencies.py

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import UserAuth  # <-- THIS LINE WAS MISSING

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
    request: Request,  # We now depend on the Request object
    auth_service: UserAuth = Depends(get_user_auth)
) -> dict:
    """
    Dependency to get the token from the request's cookie,
    verify it, and return the user payload.
    """
    token = request.cookies.get("auth_token")  # Read the token from the cookie
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = auth_service.verify_token(token)
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

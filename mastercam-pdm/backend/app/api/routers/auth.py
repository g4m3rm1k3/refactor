from fastapi import APIRouter, Depends, HTTPException, Response, status, Form
from app.core.security import UserAuth, ADMIN_USERS
from app.api.dependencies import get_user_auth, get_current_user
from app.models import schemas
import requests
from app.api.dependencies import get_config_manager
from app.core.config import ConfigManager

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# In backend/app/api/routers/auth.py

@router.post("/login", response_model=schemas.Token)  # Changed response_model
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    auth_service: UserAuth = Depends(get_user_auth)
):
    """Handles user login, sets a cookie, and returns an access token."""
    if not auth_service.verify_user(username, password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token = auth_service.create_access_token(username)

    # We will still set the secure cookie for web-based sessions
    response.set_cookie(
        key="auth_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=28800
    )

    # NEW: We also return the token in the response body, just like the setup endpoint
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": username,
        "is_admin": username in ADMIN_USERS
    }


@router.post("/setup_password")
async def setup_password(
    username: str = Form(...),
    password: str = Form(...),
    auth_service: UserAuth = Depends(get_user_auth)
):
    """Allows a new user to set their initial password."""
    # In a real app, you might add more validation here, e.g., using a one-time setup token.
    if auth_service.create_user_password(username, password):
        token = auth_service.create_access_token(username)
        # Note: We are returning the token directly here. The login endpoint is preferred
        # as it sets a secure cookie. This endpoint is for initial setup.
        return {"status": "success", "access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create password for user."
        )


@router.post("/check_password")
async def check_password(
    username: str = Form(...),
    auth_service: UserAuth = Depends(get_user_auth)
):
    """Checks if a password has been set for a given username."""
    users = auth_service._load_users(
        # Accessing a "private" method is okay here as it's part of the same logical domain.
    )
    return {"has_password": username in users}


@router.post("/validate")
async def validate_token(current_user: dict = Depends(get_current_user)):
    """Validates a token. The dependency 'get_current_user' does all the work."""
    # If get_current_user succeeds, the token is valid. It will raise an exception if not.
    return {"valid": True, "user": current_user}


@router.post("/request_reset")
async def request_password_reset(
    username: str = Form(...),
    auth_service: UserAuth = Depends(get_user_auth)
):
    """Generates a password reset token for a user."""
    try:
        reset_token = auth_service.reset_password_request(username)
        # In a real application, you would email this token to the user.
        # For this app, we return it directly for the user to copy/paste.
        return {"status": "success", "reset_token": reset_token}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/reset_password")
async def reset_password(
    username: str = Form(...),
    reset_token: str = Form(...),
    new_password: str = Form(...),
    auth_service: UserAuth = Depends(get_user_auth)
):
    """Resets a user's password using a valid reset token."""
    success = auth_service.reset_password(username, reset_token, new_password)
    if success:
        return {"status": "success", "message": "Password has been reset successfully."}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )


# In backend/app/api/routers/auth.py

@router.post("/setup-initial-user", response_model=schemas.Token)
async def setup_initial_user(
    setup_data: schemas.InitialUserSetup,
    auth_service: UserAuth = Depends(get_user_auth),
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    Verifies a user's GitLab token and creates the initial application password.
    This is a one-time setup endpoint for the first user.
    """
    gitlab_url = config_manager.config.gitlab.get("base_url")
    if not gitlab_url:
        raise HTTPException(
            status_code=500, detail="GitLab URL not configured on server.")

    # --- THIS IS THE FIX ---
    # We need to extract the base domain (e.g., "https://gitlab.com") from the full project URL.
    try:
        base_gitlab_url = "/".join(gitlab_url.rstrip('/').split('/')[:3])
    except Exception:
        raise HTTPException(
            status_code=400, detail="Invalid GitLab URL format in configuration.")

    # Step 1: Verify the provided GitLab token is valid and matches the user
    api_url = f"{base_gitlab_url}/api/v4/user"  # Use the corrected base URL
    headers = {"Private-Token": setup_data.gitlab_token}
    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        gitlab_user = response.json()

        if gitlab_user.get("username") != setup_data.username:
            raise HTTPException(
                status_code=403, detail="GitLab token is valid, but does not belong to the configured user.")

    except requests.exceptions.RequestException as e:
        # We'll return a more specific error message to the user.
        error_detail = str(e)
        if "401" in error_detail:
            error_detail = "The provided GitLab token is invalid or has expired."
        elif "403" in error_detail:
            error_detail = "The provided GitLab token does not have the required 'api' scope."
        else:
            error_detail = f"Could not connect to GitLab: {e}"
        raise HTTPException(status_code=401, detail=error_detail)

    # Step 2: If verification passes, create the application password
    auth_service.create_user_password(
        setup_data.username, setup_data.new_password)

    # Step 3: Automatically log the user in
    access_token = auth_service.create_access_token(setup_data.username)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": setup_data.username,
        "is_admin": setup_data.username in ADMIN_USERS
    }
# Add to the end of backend/app/api/routers/auth.py


@router.get("/me", response_model=schemas.Token)
async def get_current_session_user(current_user: dict = Depends(get_current_user)):
    """
    Endpoint to validate the cookie and get current user info.
    This is used by the frontend on startup to check for a valid session.
    """
    # The get_current_user dependency does all the work. If it succeeds, the user is authenticated.
    return {
        # Token is not resent, this is just for schema validation
        "access_token": "from_cookie",
        "token_type": "bearer",
        "username": current_user.get("sub"),
        "is_admin": current_user.get("is_admin")
    }

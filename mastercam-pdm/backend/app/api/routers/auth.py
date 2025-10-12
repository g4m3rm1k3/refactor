"""
Authentication router - Handles user login, password management, and session validation.

Endpoints:
- POST /auth/login - Standard login with username/password
- POST /auth/setup-initial-user - First-time setup with GitLab verification
- POST /auth/check_password - Check if user has password set
- GET /auth/me - Validate current session
- POST /auth/request_reset - Request password reset token
- POST /auth/reset_password - Reset password with token

Authentication methods:
1. Cookie-based (for web browsers) - httpOnly, secure cookie with JWT
2. Bearer token (for API clients) - JWT in Authorization header
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status, Form
from app.core.security import UserAuth, ADMIN_USERS
from app.api.dependencies import get_user_auth, get_current_user, get_config_manager
from app.models import schemas
from app.core.config import ConfigManager
import requests
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/login", response_model=schemas.Token)
async def login(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    auth_service: UserAuth = Depends(get_user_auth)
):
    """
    Standard login endpoint for users who have already set up their password.

    Flow:
    1. Verify username/password against local database
    2. Create JWT token
    3. Set secure httpOnly cookie
    4. Return token (for API clients) and user info

    Args:
        response: FastAPI Response object (for setting cookies)
        username: User's username (from form data)
        password: User's password (from form data)
        auth_service: UserAuth service (injected via dependency)

    Returns:
        Token object with access_token, username, and is_admin flag

    Raises:
        401: If username/password is incorrect
    """
    # Verify credentials against local password database
    # This checks bcrypt hash in .auth/users.json
    if not auth_service.verify_user(username, password):
        logger.warning(f"Failed login attempt for user: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Create JWT token with username and expiration
    access_token = auth_service.create_access_token(username)

    logger.info(f"User logged in: {username}")

    # Set secure httpOnly cookie for web browser authentication
    # This cookie is automatically sent on subsequent requests
    response.set_cookie(
        key="auth_token",
        value=access_token,
        httponly=True,     # JavaScript cannot access (XSS protection)
        secure=False,      # MUST be True in production (HTTPS only)
        samesite="lax",    # CSRF protection
        max_age=28800      # 8 hours (28800 seconds)
    )

    # Also return token in response body for API clients
    # This supports both browser and API authentication methods
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": username,
        "is_admin": username in ADMIN_USERS
    }


@router.post("/check_password")
async def check_password(
    username: str = Form(...),
    auth_service: UserAuth = Depends(get_user_auth)
):
    """
    Check if a user has already set up their password.

    Used by frontend to determine which form to show:
    - If has_password=true: Show login form (username + password)
    - If has_password=false: Show setup form (username + GitLab token + new password)

    Args:
        username: Username to check
        auth_service: UserAuth service (injected)

    Returns:
        {"has_password": bool}
    """
    # Load users from .auth/users.json and check if username exists
    users = auth_service._load_users()
    has_password = username in users

    logger.debug(f"Password check for {username}: {has_password}")
    return {"has_password": has_password}


@router.post("/setup-initial-user", response_model=schemas.Token)
async def setup_initial_user(
    response: Response,  # CRITICAL: Needed to set cookie
    setup_data: schemas.InitialUserSetup,
    auth_service: UserAuth = Depends(get_user_auth),
    config_manager: ConfigManager = Depends(get_config_manager)
):
    """
    Initial user setup endpoint - verifies GitLab identity and creates local password.

    This is the first-time user flow:
    1. User provides their username, GitLab Personal Access Token, and desired password
    2. Backend verifies the token is valid and belongs to that username (via GitLab API)
    3. If valid, creates a local password hash and stores it
    4. Automatically logs the user in

    Security:
    - Prevents impersonation (token must belong to the claimed username)
    - GitLab token is used ONLY for verification, not stored
    - Local password is hashed with bcrypt

    Args:
        response: FastAPI Response (for setting auth cookie)
        setup_data: Object containing username, gitlab_token, and new_password
        auth_service: UserAuth service (injected)
        config_manager: ConfigManager service (injected)

    Returns:
        Token object with access_token and user info

    Raises:
        500: If GitLab not configured
        400: If GitLab URL format invalid
        401: If GitLab token invalid or API unreachable
        403: If token doesn't belong to claimed username
    """
    # Get GitLab base URL from server config
    gitlab_url = config_manager.config.gitlab.get("base_url")
    if not gitlab_url:
        logger.error("Attempt to setup user, but GitLab URL not configured")
        raise HTTPException(
            status_code=500,
            detail="GitLab URL not configured on server."
        )

    # Extract base domain from potentially full project URL
    # Example: "https://gitlab.com/mygroup/myproject" → "https://gitlab.com"
    try:
        # Split by /, take first 3 parts (https:, , gitlab.com), rejoin
        base_gitlab_url = "/".join(gitlab_url.rstrip('/').split('/')[:3])
        logger.debug(f"Extracted base GitLab URL: {base_gitlab_url}")
    except Exception as e:
        logger.error(f"Invalid GitLab URL format: {gitlab_url}")
        raise HTTPException(
            status_code=400,
            detail="Invalid GitLab URL format in configuration."
        )

    # Step 1: Verify the GitLab token with GitLab's API
    # Call GitLab's "get current user" endpoint
    api_url = f"{base_gitlab_url}/api/v4/user"
    headers = {"Private-Token": setup_data.gitlab_token}

    logger.info(f"Verifying GitLab token for user: {setup_data.username}")

    try:
        response_gl = requests.get(api_url, headers=headers, timeout=10)
        response_gl.raise_for_status()  # Raises for 4xx/5xx status codes
        gitlab_user = response_gl.json()

        # Verify the token belongs to the claimed username
        if gitlab_user.get("username") != setup_data.username:
            logger.warning(
                f"Token mismatch: Token belongs to {gitlab_user.get('username')}, "
                f"but user claimed to be {setup_data.username}"
            )
            raise HTTPException(
                status_code=403,
                detail="GitLab token is valid, but does not belong to the configured user."
            )

        logger.info(f"GitLab token verified for {setup_data.username}")

    except requests.exceptions.RequestException as e:
        # Convert technical errors to user-friendly messages
        error_detail = str(e)

        if "401" in error_detail:
            error_detail = "The provided GitLab token is invalid or has expired."
        elif "403" in error_detail:
            error_detail = "The provided GitLab token does not have the required 'api' scope."
        else:
            error_detail = f"Could not connect to GitLab: {e}"

        logger.error(f"GitLab API error during setup: {error_detail}")
        raise HTTPException(status_code=401, detail=error_detail)

    # Step 2: Token is valid, create the local password
    # This hashes the password with bcrypt and saves to .auth/users.json
    auth_service.create_user_password(
        setup_data.username,
        setup_data.new_password
    )
    logger.info(f"Password created for user: {setup_data.username}")

    # Step 3: Automatically log the user in
    access_token = auth_service.create_access_token(setup_data.username)

    # CRITICAL: Set the auth cookie so user stays logged in
    # This was the missing piece causing the bug!
    response.set_cookie(
        key="auth_token",
        value=access_token,
        httponly=True,
        secure=False,  # Must be True in production with HTTPS
        samesite="lax",
        max_age=28800  # 8 hours
    )

    logger.info(f"User setup complete and logged in: {setup_data.username}")

    # Return token and user info
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": setup_data.username,
        "is_admin": setup_data.username in ADMIN_USERS
    }


@router.get("/me", response_model=schemas.Token)
async def get_current_session_user(current_user: dict = Depends(get_current_user)):
    """
    Validate current session and return user info.

    This endpoint is called by the frontend on page load to check if the user
    is already logged in (via cookie).

    Flow:
    1. Frontend calls GET /auth/me
    2. get_current_user dependency reads auth_token cookie
    3. Verifies JWT is valid and not expired
    4. If valid, returns user info
    5. If invalid, dependency raises 401

    Args:
        current_user: User payload from JWT (injected by dependency)

    Returns:
        Token object with user info

    Raises:
        401: If no cookie or invalid/expired token (raised by dependency)
    """
    # The get_current_user dependency does all the validation work
    # If we get here, the user is authenticated
    return {
        "access_token": "from_cookie",  # Not resent for security
        "token_type": "bearer",
        "username": current_user.get("sub"),
        "is_admin": current_user.get("is_admin", False)
    }


@router.post("/validate")
async def validate_token(current_user: dict = Depends(get_current_user)):
    """
    Explicit token validation endpoint.

    Similar to /me but simpler response. Can be used by API clients
    to check if their token is still valid.

    Args:
        current_user: User payload (injected by dependency)

    Returns:
        {"valid": true, "user": {...}}
    """
    return {"valid": True, "user": current_user}


@router.post("/logout")
async def logout(response: Response):
    """
    Logout endpoint - clears the authentication cookie.

    This invalidates the session by removing the auth_token cookie
    from the browser.

    Args:
        response: FastAPI Response object (for clearing cookies)

    Returns:
        {"status": "success", "message": "Logged out successfully"}
    """
    # Clear the auth cookie by setting it to expire immediately
    response.delete_cookie(
        key="auth_token",
        httponly=True,
        secure=False,  # Must match the cookie creation settings
        samesite="lax"
    )

    logger.info("User logged out successfully")

    return {
        "status": "success",
        "message": "Logged out successfully"
    }


@router.post("/request_reset")
async def request_password_reset(
    username: str = Form(...),
    auth_service: UserAuth = Depends(get_user_auth)
):
    """
    Generate a password reset token for a user.

    In a real application, this token would be emailed to the user.
    For this app, it's returned directly for the user to copy/paste.

    Args:
        username: User requesting reset
        auth_service: UserAuth service (injected)

    Returns:
        {"status": "success", "reset_token": "..."}

    Raises:
        404: If user not found
    """
    try:
        reset_token = auth_service.reset_password_request(username)
        logger.info(f"Password reset requested for: {username}")

        # TODO: In production, email this token instead of returning it
        return {"status": "success", "reset_token": reset_token}

    except ValueError as e:
        logger.warning(f"Reset request failed for {username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/reset_password")
async def reset_password(
    username: str = Form(...),
    reset_token: str = Form(...),
    new_password: str = Form(...),
    auth_service: UserAuth = Depends(get_user_auth)
):
    """
    Reset a user's password using a valid reset token.

    Args:
        username: User whose password is being reset
        reset_token: Token from /request_reset
        new_password: New password to set
        auth_service: UserAuth service (injected)

    Returns:
        {"status": "success", "message": "..."}

    Raises:
        400: If token is invalid or expired
    """
    success = auth_service.reset_password(username, reset_token, new_password)

    if success:
        logger.info(f"Password reset successful for: {username}")
        return {
            "status": "success",
            "message": "Password has been reset successfully."
        }
    else:
        logger.warning(f"Password reset failed for {username}: Invalid token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )


# Deprecated endpoint - should be removed or protected
# Currently allows anyone to create a password for any username (security risk)
@router.post("/setup_password")
async def setup_password(
    username: str = Form(...),
    password: str = Form(...),
    auth_service: UserAuth = Depends(get_user_auth)
):
    """
    DEPRECATED: Allows setting a password without verification.

    Security issue: Anyone can create a password for any username.
    Use /setup-initial-user instead which verifies GitLab identity.

    TODO: Remove this endpoint or add proper protection.
    """
    logger.warning(
        f"DEPRECATED endpoint /setup_password used for {username}. "
        "This endpoint should be removed!"
    )

    if auth_service.create_user_password(username, password):
        token = auth_service.create_access_token(username)
        return {
            "status": "success",
            "access_token": token,
            "token_type": "bearer"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create password for user."
        )

"""
API dependencies module - Provides reusable dependency injection functions.

This module contains functions that FastAPI uses to inject services and
validate authentication into route handlers. Instead of each route
manually accessing app.state or checking auth, they use these dependencies.

Key concepts:
- Dependency Injection: FastAPI calls these functions and passes results to routes
- Separation of Concerns: Auth logic lives here, not scattered in every route
- Testability: Easy to mock these for testing

Dependencies provided:
1. Service retrievers: get_config_manager, get_git_repo, etc.
2. Auth validators: get_current_user, get_current_admin_user
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import UserAuth
import logging

logger = logging.getLogger(__name__)

# HTTPBearer is a security scheme for the /docs page
# It tells FastAPI "this API uses Bearer token authentication"
# This is optional - just for documentation purposes
reusable_oauth2 = HTTPBearer(scheme_name="Bearer", auto_error=False)


# ============================================================================
# SERVICE PROVIDER DEPENDENCIES
# ============================================================================
# These functions retrieve services from app.state and make them available
# to route handlers. They handle the case where services might not be
# initialized (e.g., if GitLab isn't configured yet).


def get_config_manager(request: Request):
    """
    Retrieve the ConfigManager service from app state.

    The ConfigManager handles loading/saving config.json and encrypting
    sensitive data like GitLab tokens.

    Args:
        request: FastAPI Request object (automatically provided)

    Returns:
        ConfigManager instance

    Raises:
        503: If ConfigManager not initialized (should never happen)

    Usage in route:
        @router.get("/config")
        def get_config(config_mgr: ConfigManager = Depends(get_config_manager)):
            return config_mgr.config
    """
    config_manager = request.app.state.config_manager

    # ConfigManager is always initialized (even if GitLab isn't configured)
    # But we check just in case of startup failure
    if config_manager is None:
        logger.error("ConfigManager not initialized in app state")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Configuration service not available"
        )

    return config_manager


def get_metadata_manager(request: Request):
    """
    Retrieve the MetadataManager service from app state.

    The MetadataManager handles reading/writing .meta.json files that
    store file descriptions, revision numbers, etc.

    Args:
        request: FastAPI Request object

    Returns:
        MetadataManager instance or None if not initialized

    Note: Returns None instead of raising exception because some routes
    need to work even when GitLab isn't configured (e.g., config page).
    Routes that REQUIRE this service should check if it's None.

    Usage in route:
        @router.get("/files")
        def list_files(metadata_mgr = Depends(get_metadata_manager)):
            if not metadata_mgr:
                raise HTTPException(503, "GitLab not configured")
            # Use metadata_mgr...
    """
    metadata_manager = request.app.state.metadata_manager

    # This can be None if GitLab isn't configured
    # Routes should check and handle appropriately
    if metadata_manager is None:
        logger.debug("MetadataManager not available - GitLab not configured")

    return metadata_manager


def get_git_repo(request: Request):
    """
    Retrieve the GitRepository service from app state.

    The GitRepository handles all Git operations: clone, commit, push, pull,
    checkout specific versions, etc.

    Args:
        request: FastAPI Request object

    Returns:
        GitRepository instance or None if not initialized

    Note: Like metadata_manager, this can be None if GitLab isn't configured.

    Usage in route:
        @router.post("/files/{filename}/checkout")
        def checkout(filename: str, git_repo = Depends(get_git_repo)):
            if not git_repo:
                raise HTTPException(503, "GitLab not configured")
            git_repo.checkout_file(filename)
    """
    git_repo = request.app.state.git_repo

    if git_repo is None:
        logger.debug("GitRepository not available - GitLab not configured")

    return git_repo


def get_user_auth(request: Request):
    """
    Retrieve the UserAuth service from app state.

    The UserAuth service handles:
    - Password verification (checking bcrypt hashes)
    - JWT token creation and verification
    - Password reset tokens

    Args:
        request: FastAPI Request object

    Returns:
        UserAuth instance or None if not initialized

    Note: This can be None if GitLab isn't configured. However, the auth
    endpoints need this service, so they should raise an error if None.

    Usage in route:
        @router.post("/login")
        def login(auth_service: UserAuth = Depends(get_user_auth)):
            if not auth_service:
                raise HTTPException(503, "Authentication not available")
            # Use auth_service...
    """
    user_auth = request.app.state.user_auth

    if user_auth is None:
        logger.debug("UserAuth not available - GitLab not configured")

    return user_auth


def get_lock_manager(request: Request):
    """
    Retrieve the MetadataManager service from app state.

    The MetadataManager handles user-level file locks (checkouts) and
    metadata for files. This is different from the repo-level lock manager
    which prevents concurrent Git operations.

    Args:
        request: FastAPI Request object

    Returns:
        MetadataManager instance or None if not initialized

    Note: Like other services, this can be None if GitLab isn't configured.

    Usage in route:
        @router.post("/files/{filename}/checkout")
        def checkout(
            filename: str,
            lock_manager: MetadataManager = Depends(get_lock_manager)
        ):
            if not lock_manager:
                raise HTTPException(503, "Service not available")
            # Use lock_manager...
    """
    # This should return metadata_manager, not the repo lock manager
    # The naming is confusing but this is what the routes expect
    metadata_manager = request.app.state.metadata_manager

    if metadata_manager is None:
        logger.debug("MetadataManager not available - GitLab not configured")

    return metadata_manager


# ============================================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================================
# These functions validate authentication and return user information.
# If auth fails, they raise HTTPException (route handler never runs).


def get_current_user(
    request: Request,
    auth_service: UserAuth = Depends(get_user_auth)
) -> dict:
    """
    Dependency to extract and validate the current user from their JWT cookie.

    This is the main authentication dependency. Most protected routes use this.

    Process:
    1. Read 'auth_token' cookie from request
    2. If no cookie, user is not logged in → 401 error
    3. Verify JWT signature and expiration
    4. If invalid/expired → 401 error
    5. If valid, return user payload

    The returned payload contains:
    {
        "sub": "username",       # Subject (the username)
        "exp": 1234567890,       # Expiration timestamp
        "is_admin": false        # Admin flag
    }

    Args:
        request: FastAPI Request object (contains cookies)
        auth_service: UserAuth service (injected via Depends)

    Returns:
        dict: User payload from JWT

    Raises:
        503: If auth service not initialized (GitLab not configured)
        401: If no cookie or invalid/expired token

    Usage in route:
        @router.get("/protected")
        def protected_route(user: dict = Depends(get_current_user)):
            username = user.get("sub")
            return {"message": f"Hello {username}"}

    How FastAPI uses this:
        1. User requests GET /protected
        2. FastAPI sees Depends(get_current_user)
        3. FastAPI calls get_current_user(request, auth_service)
        4. If get_current_user raises exception, request stops, error returned
        5. If get_current_user succeeds, returns user dict
        6. FastAPI passes user dict to protected_route as 'user' parameter
        7. Route handler runs with validated user
    """
    # Check if auth service is available
    if not auth_service:
        logger.error("Auth service not available for user validation")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available. Please configure GitLab first."
        )

    # Extract JWT token from cookie
    # Cookies are automatically sent by browser on every request
    token = request.cookies.get("auth_token")

    if not token:
        # No cookie means user is not logged in
        logger.debug("No auth token found in request cookies")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
            # WWW-Authenticate header tells client what auth method to use
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify the JWT token
    # This checks:
    # - Signature is valid (not tampered with)
    # - Token hasn't expired
    # - Token was created by our server
    payload = auth_service.verify_token(token)

    if not payload:
        # Token is invalid or expired
        logger.warning("Invalid or expired token in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Token is valid! Return the user payload
    logger.debug(f"User authenticated: {payload.get('sub')}")
    return payload


def get_current_admin_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Dependency that requires the user to be an admin.

    This dependency CHAINS on get_current_user:
    1. get_current_user runs first (validates auth)
    2. Then this function checks if user is admin
    3. If not admin, raises 403 Forbidden
    4. If admin, returns user info

    This is dependency chaining - one dependency uses another.

    Args:
        current_user: User payload (injected from get_current_user)

    Returns:
        dict: User payload (same as current_user, but guaranteed to be admin)

    Raises:
        403: If user is authenticated but not an admin
        (401: If not authenticated - raised by get_current_user)

    Usage in route:
        @router.delete("/admin/files/{filename}")
        def delete_file(
            filename: str,
            admin: dict = Depends(get_current_admin_user)
        ):
            # Only admins can reach this code
            # Regular users get 403 error
            delete_file_logic(filename)

    How the chain works:
        User requests DELETE /admin/files/test.mcam
        ↓
        FastAPI sees Depends(get_current_admin_user)
        ↓
        get_current_admin_user depends on get_current_user
        ↓
        FastAPI calls get_current_user first
        ↓
        get_current_user validates token → returns user payload
        ↓
        FastAPI passes user payload to get_current_admin_user
        ↓
        get_current_admin_user checks is_admin flag
        ↓
        If not admin → 403 error, route never runs
        If admin → returns user payload, route runs
    """
    # Check if user has admin flag in their JWT payload
    is_admin = current_user.get("is_admin", False)

    if not is_admin:
        username = current_user.get("sub", "unknown")
        logger.warning(
            f"Non-admin user {username} attempted to access admin endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required for this action.",
        )

    # User is admin, allow access
    logger.debug(
        f"Admin user {current_user.get('sub')} accessing admin endpoint")
    return current_user


# ============================================================================
# OPTIONAL: BEARER TOKEN AUTHENTICATION (for API clients)
# ============================================================================
# This is an alternative to cookie authentication for API clients that
# send tokens in the Authorization header instead of cookies.


def get_current_user_from_bearer(
    credentials: HTTPAuthorizationCredentials = Depends(reusable_oauth2),
    auth_service: UserAuth = Depends(get_user_auth)
) -> dict:
    """
    Alternative auth dependency for API clients using Bearer tokens.

    Instead of reading from cookie, this reads from Authorization header:
        Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

    This is useful for:
    - API clients (scripts, mobile apps)
    - Testing with curl/Postman
    - Services that can't use cookies

    Args:
        credentials: Bearer token from Authorization header
        auth_service: UserAuth service

    Returns:
        dict: User payload

    Raises:
        503: If auth service not available
        401: If no token or invalid token

    Usage in route:
        # Use this instead of get_current_user for API-only endpoints
        @router.get("/api/data")
        def get_data(user: dict = Depends(get_current_user_from_bearer)):
            return {"data": "..."}

    How to use as API client:
        curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
             http://localhost:8000/api/data
    """
    if not auth_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service not available"
        )

    # HTTPBearer extracts token from "Authorization: Bearer <token>" header
    # If header missing or wrong format, credentials will be None
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No bearer token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # credentials.credentials contains the token string
    token = credentials.credentials

    # Verify token (same as cookie auth)
    payload = auth_service.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload

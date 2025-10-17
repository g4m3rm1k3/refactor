"""
Main application module - The FastAPI application core.

This file:
1. Creates the FastAPI application instance
2. Initializes all services (Git, auth, locking) during startup
3. Registers all API routers
4. Serves the frontend static files
5. Handles graceful shutdown

Architecture:
- Services are initialized once at startup and stored in app.state
- Route handlers access services via dependency injection
- Lifespan context manager ensures proper startup/shutdown
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
from pathlib import Path

# Import all our components
from app.core.config import ConfigManager
from app.services.lock_service import MetadataManager, ImprovedFileLockManager
from app.services.git_service import GitRepository, setup_git_lfs_path
from app.services.admin_config_service import AdminConfigService
from app.core.security import UserAuth
from app.api.routers import auth, files, admin, config, websocket, dashboard, admin_config, gitlab_users

# Configure logging for this module
# Note: basicConfig should really only be in run.py, but keeping for backwards compat
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def resource_path(relative_path):
    """
    Calculate absolute path to a resource relative to this file.

    This ensures paths work regardless of where the app is run from.

    Args:
        relative_path: Path relative to the backend/ directory

    Returns:
        Path object pointing to the resource

    Example:
        resource_path("static") -> /full/path/to/backend/static
        resource_path("static/index.html") -> /full/path/to/backend/static/index.html
    """
    # __file__ is this file (app/main.py)
    # .resolve() makes it an absolute path
    # .parents[1] goes up to backend/ directory
    base_path = Path(__file__).resolve().parents[1]
    return base_path / relative_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown.

    This is an async context manager. Code before 'yield' runs at startup,
    code after 'yield' runs at shutdown.

    Startup sequence:
    1. Configure Git LFS
    2. Load configuration from disk
    3. If GitLab is configured, initialize all services
    4. Store services in app.state for access by routes

    Shutdown sequence:
    1. Save any config changes to disk

    Note: If initialization fails, app runs in "limited mode" with services=None.
    Routes must check if services exist before using them.
    """
    logger.info("Application starting up...")

    # === STARTUP ===

    # 1. Setup Git LFS path environment
    # This configures Git to work with Large File Storage
    # Your spec requires "LFS On-Demand" - only download files when needed
    setup_git_lfs_path()

    # 2. Initialize the Config Manager and attach it to the app state
    # ConfigManager handles loading/saving config.json and encryption
    config_manager = ConfigManager(base_dir=resource_path(""))
    app.state.config_manager = config_manager

    # app.state is a special FastAPI namespace for storing shared data
    # Anything stored here is accessible in all route handlers via request.app.state

    # 3. Check if GitLab is configured
    # If user hasn't configured GitLab yet, we run in "limited mode"
    cfg = config_manager.config
    gitlab_cfg = cfg.gitlab

    # Check if all required GitLab settings exist and are not empty
    if all(gitlab_cfg.get(k) for k in ['base_url', 'token', 'project_id']):
        try:
            # === FULL INITIALIZATION MODE ===

            # Determine where the Git repository should be stored locally
            repo_path_str = gitlab_cfg.get("repo_path")
            if not repo_path_str:
                # First-time setup: use default location in user's home directory
                # e.g., ~/MastercamGitRepo/12345 (where 12345 is the project ID)
                repo_path = Path.home() / 'MastercamGitRepo' / \
                    gitlab_cfg['project_id']

                # Save this default for next time
                config_manager.config.local["repo_path"] = str(repo_path)
            else:
                # Use the saved path from config
                repo_path = Path(repo_path_str)

            logger.info(f"Initializing repository services at {repo_path}")

            # Initialize services in dependency order (bottom-up)

            # 1. File lock manager - prevents concurrent Git operations
            #    Uses a lock file in .git/repo.lock
            repo_lock_manager = ImprovedFileLockManager(
                repo_path / ".git" / "repo.lock"
            )

            # 2. Metadata manager - tracks file descriptions, revisions, etc.
            #    Reads/writes .meta.json files alongside each tracked file
            metadata_manager = MetadataManager(repo_path=repo_path)

            # 3. Git repository - handles all Git operations (clone, commit, push, etc.)
            #    Depends on: lock manager (to prevent concurrent ops)
            git_repo = GitRepository(
                repo_path=repo_path,
                remote_url=gitlab_cfg['base_url'],
                token=gitlab_cfg['token'],
                config_manager=config_manager,
                lock_manager=repo_lock_manager
            )

            # 4. User authentication - validates users and manages sessions
            #    Depends on: git_repo (to validate against GitLab)
            user_auth = UserAuth(git_repo=git_repo)

            # 5. Admin configuration service - manages PDM configuration in GitLab
            #    Handles filename patterns, repo configs, user access control
            admin_config_service = AdminConfigService(
                repo_path=repo_path,
                git_repo=git_repo
            )
            # Load or create default config
            admin_config_service.load_config()

            # Start polling for config updates from GitLab
            await admin_config_service.start_polling(git_service=git_repo)

            # Store all initialized services on app.state
            # Route handlers will access these via dependency injection
            app.state.metadata_manager = metadata_manager
            app.state.git_repo = git_repo
            app.state.user_auth = user_auth
            app.state.admin_config_service = admin_config_service

            logger.info("Application fully initialized.")

        except Exception as e:
            # If initialization fails (e.g., can't reach GitLab, bad token, etc.)
            # log the error and run in limited mode
            logger.error(f"Full initialization failed: {e}", exc_info=True)

            # Set services to None so routes know to show config page or error
            app.state.metadata_manager = None
            app.state.git_repo = None
            app.state.user_auth = None
            app.state.admin_config_service = None
    else:
        # === LIMITED MODE ===
        # GitLab not configured yet - user needs to visit config page
        logger.warning("Running in limited mode - GitLab is not configured.")
        app.state.metadata_manager = None
        app.state.git_repo = None
        app.state.user_auth = None
        app.state.admin_config_service = None

    yield  # === APPLICATION RUNS HERE ===

    # Everything after this point is SHUTDOWN logic

    # === SHUTDOWN ===
    logger.info("Application shutting down.")

    # Stop admin config polling if running
    if hasattr(app.state, 'admin_config_service') and app.state.admin_config_service:
        await app.state.admin_config_service.stop_polling()
        logger.info("Admin config polling stopped.")

    # Save any config changes that happened during runtime
    # hasattr check protects against startup failures
    if hasattr(app.state, 'config_manager'):
        app.state.config_manager.save_config()
        logger.info("Configuration saved.")


# === CREATE THE FASTAPI APPLICATION ===

app = FastAPI(
    title="Mastercam GitLab Interface",  # Shows in /docs
    version="2.0.0",                      # Shows in /docs
    lifespan=lifespan                     # Connect our startup/shutdown logic
)

# === MOUNT STATIC FILE SERVING ===

# Serve files from backend/static/ at the /static URL path
# Example: /static/css/styles.css -> backend/static/css/styles.css
app.mount(
    "/static",
    StaticFiles(directory=resource_path("static")),
    name="static"
)

# === ADD CORS MIDDLEWARE ===

# CORS (Cross-Origin Resource Sharing) allows frontend to call API
# even if they're on different ports/domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # ⚠️ Allow from any origin (dev only!)
    allow_credentials=True,     # Allow cookies/auth headers
    allow_methods=["*"],        # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],        # Allow any headers
)

# TODO: In production, replace allow_origins=["*"] with specific domain:
# allow_origins=["https://your-production-domain.com"]

# === REGISTER API ROUTERS ===

# Each router groups related endpoints
# Routes are prefixed and tagged for organization in /docs
app.include_router(auth.router)         # /api/auth/* - Login, logout
app.include_router(files.router)        # /api/files/* - File operations
app.include_router(admin.router)        # /api/admin/* - Admin actions
app.include_router(config.router)       # /api/config/* - Configuration
app.include_router(admin_config.router) # /api/admin/config/* - Admin configuration
app.include_router(gitlab_users.router) # /api/gitlab/users/* - GitLab user management
app.include_router(websocket.router)    # /ws - Real-time updates
app.include_router(dashboard.router)    # /api/dashboard/* - Statistics

# === ROOT ENDPOINT ===


@app.get("/")
async def root():
    """
    Serve the main frontend HTML page.

    When user visits http://localhost:8000/, they get the index.html file.
    The HTML then loads CSS/JS from /static/ and calls /api/ endpoints.
    """
    return FileResponse(resource_path("static/index.html"))

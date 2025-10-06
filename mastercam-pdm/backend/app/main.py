# backend/app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from pathlib import Path

# Import all our components
from app.core.config import ConfigManager
from app.services.lock_service import MetadataManager, ImprovedFileLockManager
from app.services.git_service import GitRepository, setup_git_lfs_path
from app.core.security import UserAuth
from app.api.routers import auth, files, admin, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events. This is where we
    initialize our services and make them available to the rest of
    the application.
    """
    logger.info("Application starting up...")

    # 1. Setup Git LFS
    setup_git_lfs_path()

    # 2. Initialize Config Manager (Singleton)
    config_manager = ConfigManager()
    app.state.config_manager = config_manager

    cfg = config_manager.config
    gitlab_cfg = cfg.gitlab

    # 3. Initialize Services if configured
    if all(gitlab_cfg.get(k) for k in ['base_url', 'token', 'project_id']):
        try:
            # Simplified for this refactor
            repo_path_str = gitlab_cfg.get("repo_path")
            if not repo_path_str:
                raise ValueError("Repository path not configured.")
            repo_path = Path(repo_path_str)

            # Initialize all services
            repo_lock_manager = ImprovedFileLockManager(
                repo_path / ".git" / "repo.lock")
            metadata_manager = MetadataManager(repo_path=repo_path)
            git_repo = GitRepository(
                repo_path=repo_path,
                remote_url=gitlab_cfg['base_url'],
                token=gitlab_cfg['token'],
                config_manager=config_manager,
                lock_manager=repo_lock_manager
            )
            user_auth = UserAuth(git_repo=git_repo)

            # 4. Store services on the app state object
            app.state.metadata_manager = metadata_manager
            app.state.git_repo = git_repo
            app.state.user_auth = user_auth

            logger.info("Application fully initialized.")
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            # Set services to None so the app can start in a limited state
            app.state.metadata_manager = None
            app.state.git_repo = None
            app.state.user_auth = None
    else:
        logger.warning("Running in limited mode - GitLab is not configured.")
        app.state.metadata_manager = None
        app.state.git_repo = None
        app.state.user_auth = None

    yield  # The application runs here

    # --- Shutdown Logic ---
    logger.info("Application shutting down.")
    if hasattr(app.state, 'config_manager'):
        app.state.config_manager.save_config()


app = FastAPI(
    title="Mastercam GitLab Interface",
    description="A comprehensive file management system for Mastercam and GitLab.",
    version="2.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Authentication", "description": "User login and token management."},
        {"name": "File Management", "description": "Core file operations."},
        {"name": "Administration", "description": "Privileged, admin-only operations."},
        {"name": "Configuration",
            "description": "Getting and setting application configuration."},
    ]
)

app.add_middleware(CORSMiddleware, allow_origins=[
                   "*"], allow_credentials=True, methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(files.router)
app.include_router(admin.router)
app.include_router(config.router)


@app.get("/")
async def root(request: Request):
    if request.app.state.git_repo:
        return {"message": "Welcome! The API is configured and running."}
    return {"message": "Welcome! The API is running in limited mode. Please configure GitLab credentials."}

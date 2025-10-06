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
from app.core.security import UserAuth
from app.api.routers import auth, files, admin, config, websocket, dashboard

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def resource_path(relative_path):
    base_path = Path(__file__).resolve().parents[1]
    return base_path / relative_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup. This is where we initialize our services
    and make them available to the rest of the application via app.state.
    """
    logger.info("Application starting up...")

    # 1. Setup Git LFS path environment
    setup_git_lfs_path()

    # 2. Initialize the Config Manager and attach it to the app state
    config_manager = ConfigManager(base_dir=resource_path(""))
    app.state.config_manager = config_manager

    # 3. Read the config to see if we can initialize the other services
    cfg = config_manager.config
    gitlab_cfg = cfg.gitlab

    if all(gitlab_cfg.get(k) for k in ['base_url', 'token', 'project_id']):
        try:
            # This is a key step: get the repo path from the config
            # We will configure this via the UI
            repo_path_str = gitlab_cfg.get("repo_path")
            if not repo_path_str:
                # Fallback for first-time setup
                repo_path = Path.home() / 'MastercamGitRepo' / \
                    gitlab_cfg['project_id']
                config_manager.config.local["repo_path"] = str(repo_path)
            else:
                repo_path = Path(repo_path_str)

            logger.info(f"Initializing repository services at {repo_path}")

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

            # Store the initialized services on the app state object
            app.state.metadata_manager = metadata_manager
            app.state.git_repo = git_repo
            app.state.user_auth = user_auth

            logger.info("Application fully initialized.")
        except Exception as e:
            logger.error(f"Full initialization failed: {e}", exc_info=True)
            # Ensure services are set to None so the app can start in a limited state
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


app = FastAPI(title="Mastercam GitLab Interface",
              version="2.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=resource_path("static")), name="static")

# (Middleware and Routers remain the same)
app.add_middleware(CORSMiddleware, allow_origins=[
                   "*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(admin.router)
app.include_router(config.router)
app.include_router(websocket.router)  # <-- ADD THIS LINE
app.include_router(dashboard.router)  # <-- ADD THIS LINE


@app.get("/")
async def root():
    return FileResponse(resource_path("static/index.html"))

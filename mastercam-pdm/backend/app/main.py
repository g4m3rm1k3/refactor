from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse  # <-- CORRECTED IMPORT
from contextlib import asynccontextmanager
import logging
from pathlib import Path

# Import our application components
from app.api.routers import auth, files, admin, config
# ... (and other service imports for the lifespan function)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def resource_path(relative_path):
    # This correctly points to the 'backend' folder as the base
    return Path(__file__).resolve().parents[1] / relative_path


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Your lifespan initialization logic remains the same
    logger.info("Application starting up...")
    # ...
    yield
    logger.info("Application shutting down.")

app = FastAPI(title="Mastercam GitLab Interface",
              version="2.0.0", lifespan=lifespan)

# Mount the entire 'static' folder to serve CSS, JS, etc.
app.mount("/static", StaticFiles(directory=resource_path("static")), name="static")

# All other API routes are handled by our routers below.
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(admin.router)
app.include_router(config.router)

# The root endpoint now directly serves the static index.html file.


@app.get("/")
async def root():
    """Serves the main index.html file for the Single Page Application."""
    return FileResponse(resource_path("static/index.html"))

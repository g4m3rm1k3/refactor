from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Import all of our routers
from app.api.routers import auth, files, admin, config


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Application starting up...")
    # In our final phase, we will add the full application initialization logic here.
    yield
    logging.info("Application shutting down.")

app = FastAPI(
    title="Mastercam GitLab Interface",
    description="A comprehensive file management system for Mastercam and GitLab.",
    version="2.0.0",
    lifespan=lifespan,
    # You can also add OpenAPI tags metadata here for better documentation
    openapi_tags=[
        {"name": "Authentication", "description": "User login and token management."},
        {"name": "File Management", "description": "Core file operations."},
        {"name": "Administration", "description": "Privileged, admin-only operations."},
        {"name": "Configuration",
            "description": "Getting and setting application configuration."},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    methods=["*"],
    allow_headers=["*"],
)

# Include all routers in our main application
app.include_router(auth.router)
app.include_router(files.router)
app.include_router(admin.router)
app.include_router(config.router)


@app.get("/")
async def root():
    return {"message": "Welcome to the Mastercam PDM Refactored API"}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Import both of our new routers
from app.api.routers import auth, files, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Application starting up...")
    yield
    logging.info("Application shutting down.")

app = FastAPI(
    title="Mastercam GitLab Interface",
    description="A comprehensive file management system for Mastercam and GitLab.",
    version="2.0.0",
    lifespan=lifespan
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


@app.get("/")
async def root():
    return {"message": "Welcome to the Mastercam PDM Refactored API"}

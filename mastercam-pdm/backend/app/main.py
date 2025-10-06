from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
import sys

# --- NOTE ---
# We will add the 'initialize_application' function back in a later step.
# For now, we are just setting up the structure.


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    logging.info("Application starting up...")
    # await initialize_application() # We'll re-enable this later
    yield
    logging.info("Application shutting down.")


# --- FastAPI App Definition ---
app = FastAPI(
    title="Mastercam GitLab Interface",
    description="A comprehensive file management system for Mastercam and GitLab.",
    version="2.0.0",  # Let's call our refactored version 2.0!
    lifespan=lifespan
)


# --- Middleware ---
# CORS (Cross-Origin Resource Sharing) allows the frontend (running on a different "origin")
# to communicate with this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)


# --- Static Files ---
# This function helps locate the 'static' and 'templates' folders, especially when
# the app is bundled into an executable.
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

# This tells FastAPI to serve files from the 'static' directory (like css, js)
# under the '/static' URL path. We'll need to create this folder later.
# app.mount("/static", StaticFiles(directory=resource_path("static")), name="static")


# --- Root Endpoint ---
# This is a temporary simple endpoint to make sure our server runs.
@app.get("/")
async def root():
    return {"message": "Welcome to the Mastercam PDM Refactored API"}

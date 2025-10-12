"""
Application launcher - Finds an available port and starts the server.

This file is the entry point for running the application. It handles:
- Finding an available network port
- Starting the Uvicorn ASGI server
- Opening the browser automatically

Usage: python run.py
"""

import uvicorn
import webbrowser
import threading
import socket
import logging
import os

logger = logging.getLogger(__name__)


def find_available_port(start_port=8000, max_attempts=100):
    """
    Finds an available network port by checking sequentially.

    Args:
        start_port: Port to start checking from (default: 8000)
        max_attempts: How many ports to try before giving up (default: 100)

    Returns:
        int: An available port number

    Raises:
        IOError: If no available port is found within max_attempts

    How it works:
        - Tries to bind a socket to each port
        - If successful, that port is available
        - If OSError, port is in use, try next one
    """
    for port in range(start_port, start_port + max_attempts):
        # Create a TCP socket using IPv4
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                # Try to bind to this port on localhost
                s.bind(("127.0.0.1", port))
                logger.info(f"Port {port} is available")
                return port
            except OSError:
                # Port is in use, try next one
                logger.debug(f"Port {port} is in use, trying next...")

    # Exhausted all attempts
    raise IOError(
        f"Could not find an available port after {max_attempts} attempts. "
        f"Tried ports {start_port}-{start_port + max_attempts - 1}"
    )


def main():
    """
    Main entry point to run the application.

    This function:
    1. Finds an available port
    2. Schedules browser to open after server starts
    3. Starts the Uvicorn server
    4. Handles startup errors gracefully
    """
    try:
        # Find an available port (tries 8000 first, then 8001, 8002, etc.)
        port = find_available_port(8000)
        logger.info(f"Starting server on port {port}")

        # Determine if we're in development mode
        # In production, you'd set ENVIRONMENT=production
        is_dev = os.getenv("ENVIRONMENT", "development") == "development"

        # Open browser after server starts (2 seconds should be enough)
        # Only do this in development - production servers shouldn't open browsers!
        if is_dev:
            threading.Timer(
                2.0,  # Wait 2 seconds for server to fully start
                lambda: webbrowser.open(f"http://localhost:{port}")
            ).start()
            logger.info(
                f"Browser will open at http://localhost:{port} in 2 seconds...")

        # Start the Uvicorn server
        # NOTE: We pass "app.main:app" as a STRING, not imported directly
        # This is crucial for hot-reload to work properly
        uvicorn.run(
            "app.main:app",           # Module path to the FastAPI app
            # Only accept local connections (secure for dev)
            host="127.0.0.1",
            port=port,                # Use the port we found
            reload=is_dev,            # Auto-reload on code changes (dev only)
            log_level="info"          # Show INFO level logs and above
        )

    except IOError as e:
        # Couldn't find an available port
        logger.error(f"Port finding failed: {e}")
        logger.error(
            "Try closing other applications or specify a different port range.")
        return

    except Exception as e:
        # Catch any other unexpected errors
        logger.error(
            f"An unexpected error occurred during startup: {e}",
            exc_info=True  # Include full stack trace in logs
        )


if __name__ == "__main__":
    """
    Entry point guard - only runs when executing this file directly.

    If another module does 'import run', this block won't execute.
    This prevents the server from accidentally starting when imported.
    """

    # Configure logging for the entire application
    logging.basicConfig(
        level=logging.INFO,  # Show INFO, WARNING, ERROR, CRITICAL
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        # Added %(name)s to see which module logged each message
    )

    # Print a nice startup message
    logger.info("=" * 50)
    logger.info("Mastercam PDM Server Starting...")
    logger.info("=" * 50)

    # Start the application
    main()

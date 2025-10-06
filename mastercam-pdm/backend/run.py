import uvicorn
import webbrowser
import threading
import socket
import logging

# We no longer need to import 'app' here, as we're passing it as a string
# from app.main import app

logger = logging.getLogger(__name__)


def find_available_port(start_port=8000, max_attempts=100):
    """Finds an open network port by checking ports sequentially."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                logger.warning(f"Port {port} is in use, trying next...")
    raise IOError("Could not find an available port.")


def main():
    """Main entry point to run the application."""
    try:
        port = find_available_port(8000)
        logger.info(f"Found available port: {port}")

        threading.Timer(1.5, lambda: webbrowser.open(
            f"http://localhost:{port}")).start()

        # Pass the app location as a string
        uvicorn.run("app.main:app", host="127.0.0.1",
                    port=port, log_level="info")

    except IOError as e:
        logger.error(f"{e} Aborting startup.")
        return
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during startup: {e}", exc_info=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    main()

import json
import logging
import os
import re
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import psutil

logger = logging.getLogger(__name__)


class ImprovedFileLockManager:
    """
    Manages a repository-wide lock to prevent concurrent Git operations
    like 'git pull' and 'git commit' from conflicting.
    This is an OS-level lock for short, critical operations.
    """

    def __init__(self, lock_file_path: Path):
        self.lock_file_path = lock_file_path
        self.lock_file = None
        self.max_lock_age_seconds = 300  # 5 minutes

    def force_break_lock(self) -> bool:
        """Forcefully removes a lock file, terminating the process holding it if possible."""
        for attempt in range(3):
            try:
                self._kill_lock_holder()
                if self.lock_file:
                    self.lock_file.close()
                    self.lock_file = None
                if self.lock_file_path.exists():
                    self.lock_file_path.unlink()
                logger.info(f"Force-broke lock file at {self.lock_file_path}")
                return True
            except PermissionError as e:
                if attempt < 2:
                    time.sleep(0.5)
                    continue
                logger.error(
                    f"Failed to force-break lock after 3 attempts: {e}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error breaking lock: {e}")
                return False
        return not self.lock_file_path.exists()

    def _kill_lock_holder(self):
        """Finds the process ID from the lock file and terminates it."""
        if not self.lock_file_path.exists():
            return
        try:
            lock_data = json.loads(self.lock_file_path.read_text())
            pid = lock_data.get("pid")
            if pid and psutil.pid_exists(pid):
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=2)
                logger.info(f"Terminated stale lock holder PID {pid}")
        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
            pass  # Process already gone
        except Exception as e:
            logger.debug(f"Could not kill lock holder: {e}")

    def __enter__(self):
        """Acquires the lock, waiting if necessary and breaking stale locks."""
        timeout = 15  # seconds
        start_time = time.time()
        self.lock_file_path.parent.mkdir(parents=True, exist_ok=True)

        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"Could not acquire repository lock after {timeout}s.")

            try:
                # 'x' mode opens for exclusive creation, failing if the file already exists
                self.lock_file = open(self.lock_file_path, 'x')
                lock_info = {
                    "pid": os.getpid(),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "hostname": socket.gethostname()
                }
                self.lock_file.write(json.dumps(lock_info))
                self.lock_file.flush()
                logger.debug(
                    f"Acquired repository lock: {self.lock_file_path}")
                return self
            except FileExistsError:
                if self._is_stale_lock():
                    logger.warning("Detected stale lock, forcing break.")
                    self.force_break_lock()
                    continue  # Retry immediately
                time.sleep(0.2)
            except Exception as e:
                logger.error(f"Unexpected error acquiring lock: {e}")
                raise

    def _is_stale_lock(self) -> bool:
        """Checks if a lock is stale by age or if the owning process is dead."""
        try:
            if not self.lock_file_path.exists():
                return False

            # Check by age
            file_age = time.time() - self.lock_file_path.stat().st_mtime
            if file_age > self.max_lock_age_seconds:
                logger.warning(
                    f"Lock is stale (age: {file_age:.0f}s > max: {self.max_lock_age_seconds}s)")
                return True

            # Check if owning process is gone
            lock_data = json.loads(self.lock_file_path.read_text())
            pid = lock_data.get("pid")
            if pid and not psutil.pid_exists(pid):
                logger.warning(
                    f"Lock is stale (owning PID {pid} no longer exists)")
                return True
        except (json.JSONDecodeError, FileNotFoundError, psutil.Error):
            # If we can't read the file or check the process, assume it might be stale
            return True
        except Exception:
            return False
        return False

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Releases the lock."""
        try:
            if self.lock_file:
                self.lock_file.close()
                self.lock_file = None
            if self.lock_file_path.exists():
                self.lock_file_path.unlink()
            logger.debug(f"Released repository lock: {self.lock_file_path}")
        except OSError as e:
            logger.warning(f"Could not remove lock file on exit: {e}")


class MetadataManager:
    """
    Manages the application-level concept of file checkouts (user locks).
    This creates/deletes '.lock' files in a dedicated '.locks' directory
    to represent a user having "checked out" a file for editing.
    """

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.locks_dir = self.repo_path / '.locks'
        self.locks_dir.mkdir(parents=True, exist_ok=True)

    def _get_lock_file_path(self, file_path_str: str) -> Path:
        """Creates a sanitized, safe filename for the lock file."""
        sanitized = file_path_str.replace(os.path.sep, '_').replace('.', '_')
        return self.locks_dir / f"{sanitized}.lock"

    def create_lock(self, file_path: str, user: str, force: bool = False) -> Optional[Path]:
        """Creates a lock file for a user, indicating a checkout."""
        lock_file = self._get_lock_file_path(file_path)
        if lock_file.exists() and not force:
            logger.warning(
                f"Attempted to create lock for already-locked file: {file_path}")
            return None

        lock_data = {
            "file": file_path,
            "user": user,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        lock_file.write_text(json.dumps(lock_data, indent=2))
        return lock_file

    def release_lock(self, file_path: str):
        """Releases a lock by deleting the lock file."""
        self._get_lock_file_path(file_path).unlink(missing_ok=True)

    def get_lock_info(self, file_path: str) -> Optional[Dict]:
        """Reads and returns the contents of a lock file if it exists."""
        lock_file = self._get_lock_file_path(file_path)
        if not lock_file.exists():
            return None

        try:
            return json.loads(lock_file.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning(f"Could not read or parse lock file: {lock_file}")
            lock_file.unlink(missing_ok=True)
            return None

    def get_all_locks(self) -> list[dict]:
        """Scans the .locks directory and returns all active locks."""
        active_locks = []
        if not self.locks_dir.exists():
            return active_locks

        now_utc = datetime.now(timezone.utc)
        for lock_file in self.locks_dir.glob('*.lock'):
            try:
                lock_info = json.loads(lock_file.read_text())
                locked_at_dt = datetime.fromisoformat(
                    lock_info["timestamp"].replace('Z', '+00:00'))
                duration = (now_utc - locked_at_dt).total_seconds()
                lock_info['duration_seconds'] = duration
                active_locks.append(lock_info)
            except (json.JSONDecodeError, KeyError):
                logger.warning(
                    f"Corrupted lock file found and skipped: {lock_file.name}")
        return active_locks

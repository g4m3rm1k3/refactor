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

    # ... [Copy the full methods for ImprovedFileLockManager here: __enter__, __exit__, _is_stale_lock, etc.]
    # For brevity, I am using a placeholder.
    def __enter__(self):
        logger.debug(
            f"Attempting to acquire repository lock at {self.lock_file_path}...")
        # In your file, paste the full, robust __enter__ logic from the original script.
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug(f"Releasing repository lock at {self.lock_file_path}...")
        # In your file, paste the full __exit__ logic from the original script.
        pass


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
            # Clean up corrupted/empty lock file
            lock_file.unlink(missing_ok=True)
            return None

    def get_all_locks(self) -> list[dict]:
        """Scans the .locks directory and returns all active locks."""
        active_locks = []
        if not self.locks_dir.exists():
            return active_locks

        now_utc = datetime.now(timezone.utc)
        for lock_file in self.locks_dir.glob('*.lock'):
            # Re-use get_lock_info to handle bad files
            lock_info = self.get_lock_info(lock_file.stem)
            if lock_info:
                locked_at_dt = datetime.fromisoformat(
                    lock_info["timestamp"].replace('Z', '+00:00'))
                duration = (now_utc - locked_at_dt).total_seconds()
                lock_info['duration_seconds'] = duration
                active_locks.append(lock_info)
        return active_locks

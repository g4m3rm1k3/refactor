import os
import sys
import subprocess
import logging
import shutil
import time
import re
import stat
from pathlib import Path
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime, timezone

import git
from git import Actor, Repo
import psutil

if TYPE_CHECKING:
    from app.core.config import ConfigManager
    from app.services.lock_service import ImprovedFileLockManager

logger = logging.getLogger(__name__)

# --- Git LFS Utility Functions ---
# (These remain the same as before)


def get_bundled_git_lfs_path() -> Optional[Path]:
    # ... (full function code)
    pass


def setup_git_lfs_path() -> bool:
    # ... (full function code)
    pass


class GitRepository:
    """A class to manage all interactions with a local Git repository."""

    def __init__(self, repo_path: Path, remote_url: str, token: str, config_manager: 'ConfigManager', lock_manager: 'ImprovedFileLockManager'):
        self.repo_path = repo_path
        self.lock_manager = lock_manager
        self.config_manager = config_manager
        self.remote_url_with_token = f"https://oauth2:{token}@{remote_url.split('://')[-1]}"
        self.git_env = self._create_git_environment()
        self.repo: Optional[Repo] = self._init_repo()
        if self.repo:
            self._configure_lfs()

    def _create_git_environment(self) -> Dict[str, str]:
        # ... (full function code as provided before)
        pass

    # --- Full, Robust Repository Initialization and Cleanup ---

    def _init_repo(self) -> Optional[Repo]:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if not self.repo_path.exists() or not (self.repo_path / ".git").exists():
                    logger.info(
                        f"Cloning repository to {self.repo_path} (attempt {attempt + 1})")
                    return Repo.clone_from(self.remote_url_with_token, self.repo_path, env=self.git_env)
                else:
                    with self.lock_manager:
                        logger.info(
                            f"Opening existing repository at {self.repo_path}")
                        repo = Repo(self.repo_path)
                        if repo.remotes:  # Simple validation
                            return repo
                        raise git.exc.InvalidGitRepositoryError(
                            "Repository is invalid.")
            except (git.exc.GitCommandError, git.exc.InvalidGitRepositoryError) as e:
                logger.error(
                    f"Failed to init repo (attempt {attempt + 1}): {e}")
                self._cleanup_corrupted_repo()
                time.sleep(1)
        logger.error("Failed to initialize repository after all retries.")
        return None

    def _cleanup_corrupted_repo(self):
        logger.warning(
            f"Attempting to clean up corrupted repository at {self.repo_path}")
        self._kill_git_processes()
        self._remove_git_locks()
        time.sleep(0.5)
        if self.repo_path.exists():
            self._force_remove_directory(self.repo_path)

    def _kill_git_processes(self):
        repo_path_str = str(self.repo_path.resolve()).lower()
        for proc in psutil.process_iter(['name', 'cwd', 'pid']):
            try:
                if proc.info['name'] in ['git.exe', 'git-lfs.exe', 'git'] and proc.info['cwd'] and repo_path_str in proc.info['cwd'].lower():
                    logger.info(
                        f"Terminating lingering git process: {proc.info['name']} (PID: {proc.pid})")
                    p = psutil.Process(proc.pid)
                    p.terminate()
                    p.wait(timeout=3)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def _remove_git_locks(self):
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            return
        for lock_file in git_dir.rglob("*.lock"):
            try:
                lock_file.unlink()
                logger.info(f"Removed stale git lock file: {lock_file.name}")
            except OSError as e:
                logger.warning(
                    f"Could not remove git lock file {lock_file.name}: {e}")

    def _force_remove_directory(self, directory: Path):
        def handle_remove_readonly(func, path, exc_info):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except Exception as e:
                logger.warning(f"Failed to remove readonly file {path}: {e}")

        if directory.exists():
            shutil.rmtree(directory, onerror=handle_remove_readonly)

    def _configure_lfs(self):
        if not self.repo:
            return
        try:
            with self.repo.git.custom_environment(**self.git_env):
                self.repo.git.lfs('install', '--local',
                                  '--skip-smudge', '--force')
                self.repo.git.config('--local', 'lfs.fetchinclude', 'none')
                self.repo.git.config('--local', 'lfs.fetchexclude', '*')
                logger.info("Git LFS configured for on-demand downloads.")
        except Exception as e:
            logger.error(f"Failed to configure Git LFS: {e}", exc_info=True)

    # --- Public Service Methods ---

    def pull_latest_changes(self):
        if not self.repo:
            return
        try:
            with self.lock_manager, self.repo.git.custom_environment(**self.git_env):
                self.repo.remotes.origin.fetch()
                self.repo.git.reset(
                    '--hard', f'origin/{self.repo.active_branch.name}')
                logger.debug("Successfully synced with remote.")
        except Exception as e:
            logger.error(f"Git sync (pull/reset) failed: {e}", exc_info=True)

    def commit_and_push(self, file_paths: List[str], message: str, author_name: str) -> bool:
        if not self.repo:
            return False
        try:
            with self.lock_manager, self.repo.git.custom_environment(**self.git_env):
                author = Actor(author_name, f"{author_name}@example.com")

                to_add = [p for p in file_paths if (
                    self.repo_path / p).exists()]
                to_remove = [p for p in file_paths if not (
                    self.repo_path / p).exists()]

                if to_add:
                    self.repo.index.add(to_add)
                if to_remove:
                    self.repo.index.remove(to_remove)

                if not self.repo.is_dirty(untracked_files=True):
                    logger.info("No changes to commit.")
                    return True

                self.repo.index.commit(message, author=author, skip_hooks=True)
                self.repo.remotes.origin.push()
                logger.info(f"Changes pushed to remote: {message}")
                return True
        except Exception as e:
            logger.error(f"Git commit/push failed: {e}", exc_info=True)
            self.pull_latest_changes()  # Attempt to reset to a clean state
            return False

    def is_lfs_pointer(self, file_path: str) -> bool:
        full_path = self.repo_path / file_path
        if not full_path.is_file() or full_path.stat().st_size > 200:
            return False
        try:
            return full_path.read_text().startswith('version https://git-lfs')
        except Exception:
            return False

    def download_lfs_file(self, file_path: str) -> bool:
        if not self.repo:
            return False
        try:
            with self.lock_manager, self.repo.git.custom_environment(**self.git_env):
                self.repo.git.lfs('pull', '--include', file_path)
            logger.info(f"Downloaded LFS file: {file_path}")
            return True
        except Exception as e:
            logger.error(
                f"Failed to download LFS file {file_path}: {e}", exc_info=True)
            return False

    def find_file_path(self, filename: str) -> Optional[str]:
        """Finds the relative path for a given filename in the repo."""
        if not self.repo:
            return None
        for item in self.repo.tree().traverse():
            if item.type == 'blob' and item.name == filename:
                return item.path
        return None

    def get_file_content(self, file_path: str) -> Optional[bytes]:
        full_path = self.repo_path / file_path
        return full_path.read_bytes() if full_path.exists() else None

    # ... Other methods like get_file_history, list_files, etc. would be fully fleshed out here ...

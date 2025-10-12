import os
import sys
import subprocess
import logging
import shutil
import time
import re
import stat
import json
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


def get_bundled_git_lfs_path() -> Optional[Path]:
    try:
        if getattr(sys, "frozen", False) and hasattr(sys, '_MEIPASS'):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).resolve().parents[2]
        git_lfs_exe = base_path / "libs" / "git-lfs.exe"
        return git_lfs_exe if git_lfs_exe.is_file() else None
    except Exception as e:
        logger.error(f"Error finding bundled git-lfs: {e}")
        return None


def setup_git_lfs_path() -> bool:
    """Ensure git-lfs is in the system's PATH, preferring the bundled version."""
    bundled_lfs = get_bundled_git_lfs_path()
    if bundled_lfs:
        lfs_dir = str(bundled_lfs.parent)
        if lfs_dir not in os.environ.get('PATH', ''):
            os.environ['PATH'] = f"{lfs_dir}{os.pathsep}{os.environ['PATH']}"
            logger.info(
                f"Temporarily added bundled Git LFS directory to PATH: {lfs_dir}")

        try:
            result = subprocess.run(
                [str(bundled_lfs), "version"], capture_output=True, text=True, check=True, timeout=5
            )
            logger.info(f"Using bundled Git LFS: {result.stdout.strip()}")
            return True  # If bundled LFS works, we are done.
        except Exception as e:
            logger.warning(
                f"Bundled Git LFS was found but failed verification: {e}. Falling back to system LFS.")
            # DO NOT return False here. Let the function continue to the fallback below.

    # Fallback to checking for a system-wide installation
    try:
        result = subprocess.run(
            ["git-lfs", "version"], capture_output=True, text=True, check=True, timeout=5
        )
        logger.info(f"Using system Git LFS: {result.stdout.strip()}")
        return True
    except Exception as e:
        logger.error(f"FATAL: No Git LFS found on the system or bundled: {e}")
        return False


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
        git_env = os.environ.copy()
        bundled_lfs = get_bundled_git_lfs_path()
        if bundled_lfs:
            lfs_dir = str(bundled_lfs.parent)
            git_env["PATH"] = f"{lfs_dir}{os.pathsep}{git_env.get('PATH', '')}"
            git_env["GIT_LFS_PATH"] = str(bundled_lfs)
        allow_insecure = self.config_manager.config.security.get(
            "allow_insecure_ssl", False)
        if allow_insecure:
            git_env["GIT_SSL_NO_VERIFY"] = "true"
            logger.warning(
                "GIT_SSL_NO_VERIFY is enabled. SSL verification is turned off.")
        return git_env

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

    def _increment_revision(self, current_rev: str, rev_type: str, new_major_str: Optional[str] = None) -> str:
        major, minor = 0, 0
        if not current_rev:
            current_rev = "0.0"
        parts = current_rev.split('.')
        try:
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
        except (ValueError, IndexError):
            major, minor = 0, 0

        if rev_type == 'major':
            if new_major_str and new_major_str.isdigit():
                return f"{int(new_major_str)}.0"
            return f"{major + 1}.0"
        else:
            return f"{major}.{minor + 1}"

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

    def get_file_content_at_commit(self, file_path: str, commit_hash: str) -> Optional[bytes]:
        """
        Retrieves file content from a specific commit.

        Args:
            file_path: Relative path to the file in the repository
            commit_hash: Git commit hash to retrieve the file from

        Returns:
            File contents as bytes, or None if file doesn't exist at that commit
        """
        if not self.repo:
            return None
        try:
            commit = self.repo.commit(commit_hash)
            try:
                blob = commit.tree / file_path
                return blob.data_stream.read()
            except KeyError:
                # File doesn't exist in this commit
                logger.warning(f"File {file_path} not found in commit {commit_hash[:7]}")
                return None
        except Exception as e:
            logger.error(f"Failed to get file content at commit {commit_hash[:7]}: {e}")
            return None

    def save_file(self, file_path: str, content: bytes):
        """Saves raw byte content to a file in the repository."""
        full_path = self.repo_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(content)

    # In backend/app/services/git_service.py

    def list_files(self) -> List[Dict[str, Any]]:
        """Lists all relevant files tracked by Git based on configured file types."""
        if not self.repo:
            return []

        # NEW: Get the allowed types from the config manager!
        allowed_types = self.config_manager.config.allowed_file_types

        tracked_files = self.repo.git.ls_files().splitlines()

        files_data = []
        for file_path_str in tracked_files:
            # UPDATED: Use the configured list instead of a hardcoded one.
            if not any(file_path_str.endswith(ext) for ext in allowed_types):
                continue

            full_path = self.repo_path / file_path_str
            try:
                stat_result = full_path.stat()
                files_data.append({
                    "filename": full_path.name,
                    "path": file_path_str,
                    "size": stat_result.st_size,
                    "modified_at": datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc).isoformat()
                })
            except FileNotFoundError:
                continue
        return files_data

    def get_file_history(self, file_path: str, limit: int = 50) -> List[Dict]:
        if not self.repo:
            return []
        history = []
        meta_path_str = f"{file_path}.meta.json"
        try:
            commits = self.repo.iter_commits(
                paths=[file_path, meta_path_str], max_count=limit)
            for c in commits:
                revision = None
                try:
                    meta_blob = c.tree / meta_path_str
                    meta_content = json.loads(
                        meta_blob.data_stream.read().decode('utf-8'))
                    revision = meta_content.get("revision")
                except Exception:
                    pass
                history.append({
                    "commit_hash": c.hexsha,
                    "author_name": c.author.name if c.author else "Unknown",
                    "date": datetime.fromtimestamp(c.committed_date, tz=timezone.utc).isoformat(),
                    "message": c.message.strip(),
                    "revision": revision
                })
            return history
        except git.exc.GitCommandError as e:
            logger.error(
                f"Git command failed while getting history for {file_path}: {e}")
            return []

    def get_all_users_from_history(self) -> List[str]:
        if not self.repo:
            return []
        try:
            authors = {c.author.name for c in self.repo.iter_commits()
                       if c.author}
            return sorted(list(authors))
        except Exception as e:
            logger.error(
                f"Could not retrieve user list from repo history: {e}")
            return []

    def get_recent_commits(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves recent commits from the repository for activity feed.

        Args:
            limit: Maximum number of commits to retrieve

        Returns:
            List of commit dictionaries with hash, author, timestamp, and message
        """
        if not self.repo:
            return []
        try:
            commits = []
            for commit in self.repo.iter_commits(max_count=limit):
                commits.append({
                    'hash': commit.hexsha,
                    'author': commit.author.name if commit.author else 'Unknown',
                    'timestamp': datetime.fromtimestamp(commit.committed_date, tz=timezone.utc).isoformat(),
                    'message': commit.message.strip()
                })
            return commits
        except Exception as e:
            logger.error(f"Failed to retrieve recent commits: {e}", exc_info=True)
            return []

    def checkin_file(self, file_path: str, file_content: bytes, commit_message: str, rev_type: str, author_name: str, new_major_rev: Optional[str]) -> bool:
        """High-level service method to handle the logic of a file check-in."""
        # 1. Save the new file content
        self.save_file(file_path, file_content)

        # 2. Read, update, and write the metadata file
        meta_path = self.repo_path / f"{file_path}.meta.json"
        meta_content = {}
        if meta_path.exists():
            try:
                meta_content = json.loads(meta_path.read_text())
            except json.JSONDecodeError:
                logger.warning(f"Could not parse metadata for {file_path}")

        current_rev = meta_content.get("revision", "0.0")
        new_rev = self._increment_revision(
            current_rev, rev_type, new_major_rev)
        meta_content["revision"] = new_rev
        meta_path.write_text(json.dumps(meta_content, indent=2))

        # 3. Commit and push everything
        final_commit_message = f"REV {new_rev}: {commit_message}"
        files_to_commit = [file_path, str(
            meta_path.relative_to(self.repo_path))]

        return self.commit_and_push(files_to_commit, final_commit_message, author_name)

    def revert_local_file_changes(self, file_path: str):
        """Reverts a file in the working directory to its last committed state (HEAD)."""
        if not self.repo:
            return
        try:
            with self.lock_manager, self.repo.git.custom_environment(**self.git_env):
                self.repo.git.checkout('HEAD', '--', file_path)
            logger.info(f"Reverted local changes for: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to revert local file {file_path}: {e}")

    def delete_file_and_metadata(self, file_path: str) -> List[str]:
        """Deletes a file and its associated metadata file, returning a list of paths to be committed."""
        absolute_file_path = self.repo_path / file_path
        meta_path = self.repo_path / f"{file_path}.meta.json"

        files_to_remove_for_commit = []

        if absolute_file_path.exists():
            absolute_file_path.unlink()
            files_to_remove_for_commit.append(file_path)

        if meta_path.exists():
            meta_path.unlink()
            files_to_remove_for_commit.append(
                str(meta_path.relative_to(self.repo_path)))

        return files_to_remove_for_commit

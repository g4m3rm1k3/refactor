"""
Admin Configuration Service - Manages PDM configuration stored in GitLab

This service handles:
- Loading/saving admin configuration to GitLab repository
- Polling for configuration updates
- Providing default configuration
- Validating configuration changes
"""

import json
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from git import Repo, GitCommandError

from app.models.schemas import (
    PDMAdminConfig,
    FileNamePattern,
    RepositoryConfig,
    UserRepositoryAccess,
    RevisionHistorySettings
)

logger = logging.getLogger(__name__)


class AdminConfigService:
    """Manages admin configuration stored in GitLab repository"""

    CONFIG_FILE_NAME = ".pdm-config.json"

    def __init__(self, repo_path: str, git_repo: Optional[Repo] = None):
        """
        Initialize admin config service

        Args:
            repo_path: Path to the local Git repository
            git_repo: Optional GitRepository instance for Git operations
        """
        self.repo_path = Path(repo_path)
        self.git_repo = git_repo
        self.config_file_path = self.repo_path / self.CONFIG_FILE_NAME
        self._config: Optional[PDMAdminConfig] = None
        self._last_modified: Optional[float] = None
        self._polling_task: Optional[asyncio.Task] = None

    def get_default_config(self) -> PDMAdminConfig:
        """
        Create default admin configuration

        Returns:
            PDMAdminConfig with sensible defaults
        """
        # Default filename patterns
        default_patterns = [
            FileNamePattern(
                name="Standard Pattern",
                description="7 digits, optional underscore + 1-3 letters + 1-3 numbers",
                link_pattern=r"^\d{7}(_[A-Z]{3}\d{3})?$",
                file_pattern=r"^\d{7}(_[A-Z]{1,3}\d{1,3})?$",
                max_stem_length=15,
                example_valid=["1234567", "1234567_ABC123", "1234567_A1"],
                example_invalid=["123456", "1234567_ABCD123", "1234567_abc123"]
            ),
            FileNamePattern(
                name="Extended Pattern",
                description="7 digits, optional underscore + 2 letters + any numbers",
                link_pattern=r"^\d{7}(_[A-Z]{2}\d+)?$",
                file_pattern=r"^\d{7}(_[A-Z]{2}\d+)?$",
                max_stem_length=20,
                example_valid=["1234567", "1234567_AB123", "1234567_XY9999"],
                example_invalid=["123456", "1234567_A123", "1234567_ABC123"]
            ),
            FileNamePattern(
                name="Legacy Pattern",
                description="Any alphanumeric with underscores and hyphens",
                link_pattern=r"^[A-Za-z0-9_-]+$",
                file_pattern=r"^[A-Za-z0-9_-]+$",
                max_stem_length=50,
                example_valid=["Project-A", "CAD_File_2025", "Rev-1_Draft"],
                example_invalid=["file with spaces", "file@special", ""]
            )
        ]

        # Default repository config (from current setup)
        default_repo = RepositoryConfig(
            id="main",
            name="Main Repository",
            gitlab_url="https://gitlab.com/g4m3rm1k3-group/test",
            project_id="74609002",
            branch="main",
            allowed_file_types=[".mcam", ".vnc", ".emcam", ".link"],
            filename_pattern_id="Standard Pattern",
            description="Primary PDM repository"
        )

        return PDMAdminConfig(
            version="1.0.0",
            filename_patterns=default_patterns,
            repositories=[default_repo],
            user_access=[],
            revision_settings=RevisionHistorySettings(),
            polling_interval_seconds=30,
            last_updated_by=None,
            last_updated_at=None
        )

    def load_config(self) -> PDMAdminConfig:
        """
        Load configuration from GitLab repository

        Returns:
            PDMAdminConfig instance
        """
        try:
            if not self.config_file_path.exists():
                logger.info("No config file found, creating default configuration")
                self._config = self.get_default_config()
                self.save_config(self._config, system_user="system")
                return self._config

            # Read config file
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Parse into Pydantic model
            self._config = PDMAdminConfig(**config_data)
            self._last_modified = self.config_file_path.stat().st_mtime

            logger.info(f"Loaded admin configuration (version {self._config.version})")
            return self._config

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            logger.info("Falling back to default configuration")
            self._config = self.get_default_config()
            return self._config

        except Exception as e:
            logger.error(f"Error loading config: {e}")
            logger.info("Falling back to default configuration")
            self._config = self.get_default_config()
            return self._config

    def save_config(self, config: PDMAdminConfig, system_user: str) -> bool:
        """
        Save configuration to GitLab repository

        Args:
            config: PDMAdminConfig to save
            system_user: Username performing the save

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update metadata
            config.last_updated_by = system_user
            config.last_updated_at = datetime.now(timezone.utc).isoformat()

            # Write to file
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config.model_dump(), f, indent=2)

            self._config = config
            self._last_modified = self.config_file_path.stat().st_mtime

            # Commit and push to GitLab if git_repo is available
            if self.git_repo and hasattr(self.git_repo, 'repo'):
                try:
                    repo = self.git_repo.repo
                    repo.index.add([str(self.config_file_path)])
                    repo.index.commit(
                        f"PDM Config: Updated by {system_user}\n\n"
                        f"Configuration updated at {config.last_updated_at}"
                    )
                    origin = repo.remote('origin')
                    origin.push()
                    logger.info(f"Admin config saved and pushed to GitLab by {system_user}")
                except GitCommandError as e:
                    logger.error(f"Git operation failed: {e}")
                    # Config saved locally, but not pushed
                    return True

            logger.info(f"Admin config saved by {system_user}")
            return True

        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False

    def get_config(self) -> PDMAdminConfig:
        """
        Get current configuration (load if not cached)

        Returns:
            Current PDMAdminConfig instance
        """
        if self._config is None:
            return self.load_config()
        return self._config

    def check_for_updates(self) -> bool:
        """
        Check if configuration file has been updated

        Returns:
            True if config file was modified, False otherwise
        """
        try:
            if not self.config_file_path.exists():
                return False

            current_mtime = self.config_file_path.stat().st_mtime

            if self._last_modified is None or current_mtime > self._last_modified:
                logger.info("Configuration file updated, reloading...")
                self.load_config()
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking for config updates: {e}")
            return False

    async def start_polling(self, git_service=None):
        """
        Start polling for configuration updates from GitLab

        Args:
            git_service: GitRepository service to pull updates
        """
        if self._polling_task and not self._polling_task.done():
            logger.warning("Polling already running")
            return

        async def poll_loop():
            while True:
                try:
                    config = self.get_config()
                    interval = config.polling_interval_seconds

                    await asyncio.sleep(interval)

                    # Pull latest changes from GitLab
                    if git_service:
                        try:
                            # Check for remote updates
                            git_service.repo.remote('origin').fetch()

                            # Check if config file changed
                            local_hash = git_service.repo.git.hash_object(str(self.config_file_path))
                            remote_hash = git_service.repo.git.execute(
                                ['git', 'rev-parse', f'origin/{git_service.branch}:.pdm-config.json']
                            )

                            if local_hash != remote_hash:
                                logger.info("Remote config changed, pulling updates...")
                                git_service.pull_latest_changes()
                                self.check_for_updates()

                        except Exception as e:
                            logger.debug(f"Config polling check: {e}")

                except asyncio.CancelledError:
                    logger.info("Config polling cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in config polling: {e}")
                    await asyncio.sleep(30)  # Fallback interval on error

        self._polling_task = asyncio.create_task(poll_loop())
        logger.info("Started admin config polling")

    async def stop_polling(self):
        """Stop configuration polling"""
        if self._polling_task and not self._polling_task.done():
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped admin config polling")

    def get_repository_config(self, repo_id: str) -> Optional[RepositoryConfig]:
        """
        Get configuration for a specific repository

        Args:
            repo_id: Repository identifier

        Returns:
            RepositoryConfig if found, None otherwise
        """
        config = self.get_config()
        for repo in config.repositories:
            if repo.id == repo_id:
                return repo
        return None

    def get_user_repositories(self, username: str) -> list[str]:
        """
        Get list of repository IDs accessible by user

        Args:
            username: Username to check

        Returns:
            List of repository IDs
        """
        config = self.get_config()

        # Find user access entry
        for access in config.user_access:
            if access.username == username:
                return access.repository_ids

        # If no specific access defined, return all repositories (backward compatibility)
        return [repo.id for repo in config.repositories]

    def get_filename_pattern(self, pattern_id: str) -> Optional[FileNamePattern]:
        """
        Get filename pattern by ID

        Args:
            pattern_id: Pattern name/identifier

        Returns:
            FileNamePattern if found, None otherwise
        """
        config = self.get_config()
        for pattern in config.filename_patterns:
            if pattern.name == pattern_id:
                return pattern
        return None

    def validate_config(self, config: PDMAdminConfig) -> tuple[bool, Optional[str]]:
        """
        Validate admin configuration

        Args:
            config: Configuration to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # RULE 1: Must have at least one filename pattern
            if not config.filename_patterns or len(config.filename_patterns) == 0:
                return False, "Configuration must have at least one filename pattern"

            # RULE 2: Must have at least one repository
            if not config.repositories or len(config.repositories) == 0:
                return False, "Configuration must have at least one repository"

            # Check that all repositories reference valid filename patterns
            pattern_ids = {p.name for p in config.filename_patterns}
            for repo in config.repositories:
                if repo.filename_pattern_id not in pattern_ids:
                    return False, f"Repository '{repo.name}' references unknown pattern '{repo.filename_pattern_id}'"

            # Check that user access references valid repository IDs
            repo_ids = {r.id for r in config.repositories}
            for access in config.user_access:
                for repo_id in access.repository_ids:
                    if repo_id not in repo_ids:
                        return False, f"User '{access.username}' has access to unknown repository '{repo_id}'"

                # Check default repository is in user's access list
                if access.default_repository_id:
                    if access.default_repository_id not in access.repository_ids:
                        return False, f"User '{access.username}' default repo not in their access list"

            # Validate regex patterns compile
            import re
            for pattern in config.filename_patterns:
                try:
                    re.compile(pattern.link_pattern)
                    re.compile(pattern.file_pattern)
                except re.error as e:
                    return False, f"Invalid regex in pattern '{pattern.name}': {e}"

            return True, None

        except Exception as e:
            return False, f"Validation error: {str(e)}"

"""
GitLab Users Model
Tracks users who authenticate via GitLab
"""

from datetime import datetime
from typing import Optional, List, Dict
import json
from pathlib import Path
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class GitLabUser(BaseModel):
    """Represents a user authenticated via GitLab"""
    username: str
    gitlab_id: Optional[int] = None
    email: Optional[str] = None
    display_name: Optional[str] = None
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    is_admin: bool = False
    repository_access: List[str] = Field(default_factory=lambda: ["main"])  # Default to main repo


class GitLabUserRegistry:
    """
    Simple file-based registry for GitLab users
    Stores user info in JSON file for persistence
    """

    def __init__(self, storage_path: str = "data/gitlab_users.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._users: Dict[str, GitLabUser] = {}
        self._load()

    def _load(self):
        """Load users from JSON file"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    for username, user_data in data.items():
                        # Convert ISO strings back to datetime
                        if 'first_seen' in user_data:
                            user_data['first_seen'] = datetime.fromisoformat(user_data['first_seen'])
                        if 'last_seen' in user_data:
                            user_data['last_seen'] = datetime.fromisoformat(user_data['last_seen'])
                        self._users[username] = GitLabUser(**user_data)
                logger.info(f"Loaded {len(self._users)} GitLab users from registry")
            except Exception as e:
                logger.error(f"Failed to load GitLab users: {e}")
                self._users = {}

    def _save(self):
        """Save users to JSON file"""
        try:
            data = {}
            for username, user in self._users.items():
                user_dict = user.dict()
                # Convert datetime to ISO string
                user_dict['first_seen'] = user.first_seen.isoformat()
                user_dict['last_seen'] = user.last_seen.isoformat()
                data[username] = user_dict

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self._users)} GitLab users to registry")
        except Exception as e:
            logger.error(f"Failed to save GitLab users: {e}")

    def register_user(
        self,
        username: str,
        gitlab_id: Optional[int] = None,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
        is_admin: bool = False
    ) -> tuple[GitLabUser, bool]:
        """
        Register a GitLab user (or update if exists)

        Returns:
            (user, is_new) tuple
        """
        is_new = username not in self._users

        if is_new:
            # New user - create record
            user = GitLabUser(
                username=username,
                gitlab_id=gitlab_id,
                email=email,
                display_name=display_name,
                is_admin=is_admin,
                repository_access=["main"]  # All users start with main repo
            )
            self._users[username] = user
            logger.info(f"New GitLab user registered: {username}")
        else:
            # Existing user - update last_seen
            user = self._users[username]
            user.last_seen = datetime.utcnow()
            if gitlab_id:
                user.gitlab_id = gitlab_id
            if email:
                user.email = email
            if display_name:
                user.display_name = display_name
            logger.info(f"GitLab user updated: {username}")

        self._save()
        return user, is_new

    def get_user(self, username: str) -> Optional[GitLabUser]:
        """Get user by username"""
        return self._users.get(username)

    def get_all_users(self) -> List[GitLabUser]:
        """Get all registered users"""
        return list(self._users.values())

    def get_new_users(self, since_hours: int = 24) -> List[GitLabUser]:
        """Get users registered in the last N hours"""
        cutoff = datetime.utcnow().timestamp() - (since_hours * 3600)
        return [
            user for user in self._users.values()
            if user.first_seen.timestamp() > cutoff
        ]

    def update_repository_access(self, username: str, repository_ids: List[str]) -> bool:
        """Update user's repository access"""
        if username not in self._users:
            return False

        self._users[username].repository_access = repository_ids
        self._save()
        logger.info(f"Updated repository access for {username}: {repository_ids}")
        return True

    def set_admin(self, username: str, is_admin: bool = True) -> bool:
        """Set user's admin status"""
        if username not in self._users:
            return False

        self._users[username].is_admin = is_admin
        self._save()
        logger.info(f"Updated admin status for {username}: {is_admin}")
        return True

    def deactivate_user(self, username: str) -> bool:
        """Deactivate a user (soft delete)"""
        if username not in self._users:
            return False

        self._users[username].is_active = False
        self._save()
        logger.info(f"Deactivated user: {username}")
        return True


# Global registry instance
_gitlab_user_registry: Optional[GitLabUserRegistry] = None


def get_gitlab_user_registry() -> GitLabUserRegistry:
    """Get or create the global GitLab user registry"""
    global _gitlab_user_registry
    if _gitlab_user_registry is None:
        _gitlab_user_registry = GitLabUserRegistry()
    return _gitlab_user_registry

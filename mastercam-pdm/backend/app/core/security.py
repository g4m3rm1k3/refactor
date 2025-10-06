import json
import secrets
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, TYPE_CHECKING
import logging

# This is a special import used for type hinting to avoid circular dependencies.
# The GitRepository class (which we will create soon) will live in another file.
if TYPE_CHECKING:
    from app.services.git_service import GitRepository

logger = logging.getLogger(__name__)

# TODO: In a future step, we will move this to be loaded from a configuration file
# instead of being hardcoded. For now, it's better to have it here than in main.py.
ADMIN_USERS = ["admin", "g4m3rm1k3"]


class UserAuth:
    """Handles all user authentication, password management, and token generation."""

    def __init__(self, git_repo: 'GitRepository'):
        self.git_repo = git_repo
        self.auth_file = self.git_repo.repo_path / ".auth" / "users.json"
        self.auth_file.parent.mkdir(parents=True, exist_ok=True)
        self.jwt_secret = self._get_or_create_secret()

        # This will hold temporary password reset tokens in memory.
        self.reset_tokens: Dict[str, Dict] = {}

    def _get_or_create_secret(self) -> str:
        """
        Retrieves the JWT secret key from a file, or creates one if it doesn't exist.
        This ensures tokens remain valid even if the application restarts.
        """
        secret_file = self.git_repo.repo_path / ".auth" / "jwt_secret"
        if secret_file.exists():
            return secret_file.read_text()
        else:
            # Generate a cryptographically secure random string for the secret.
            secret = secrets.token_urlsafe(32)
            secret_file.write_text(secret)
            return secret

    def _load_users(self) -> dict:
        """Loads the user database from its JSON file."""
        if not self.auth_file.exists():
            return {}
        try:
            return json.loads(self.auth_file.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_users(self, users: dict):
        """Saves the user database to its JSON file."""
        self.auth_file.write_text(json.dumps(users, indent=2))

    def _hash_password(self, password: str) -> str:
        """Hashes a password using bcrypt."""
        # bcrypt has a 72-byte limit, so we truncate the password bytes if necessary.
        password_bytes = password.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw(password_bytes, salt)
        return hashed_pw.decode('utf-8')

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verifies a plain-text password against a stored bcrypt hash."""
        password_bytes = password.encode('utf-8')[:72]
        try:
            return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
        except (ValueError, TypeError):
            # This can happen if the stored hash is invalid.
            return False

    def create_user_password(self, username: str, password: str) -> bool:
        """Creates or updates a user's password in the database."""
        users = self._load_users()
        users[username] = {
            "gitlab_username": username,
            "password_hash": self._hash_password(password),
            "is_admin": username in ADMIN_USERS,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        self._save_users(users)
        return True

    def verify_user(self, username: str, password: str) -> bool:
        """Checks if a username exists and the provided password is correct."""
        users = self._load_users()
        user_data = users.get(username)
        if not user_data:
            return False
        return self._verify_password(password, user_data["password_hash"])

    def create_access_token(self, username: str) -> str:
        """Generates a JSON Web Token (JWT) for a user."""
        users = self._load_users()
        payload = {
            # 'sub' (subject) is the standard claim for the user ID.
            "sub": username,
            "is_admin": users.get(username, {}).get("is_admin", False),
            # Expiration time
            "exp": datetime.now(timezone.utc) + timedelta(hours=8)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def verify_token(self, token: str) -> Optional[dict]:
        """Decodes and validates a JWT, returning its payload if valid."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired.")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token provided.")
            return None

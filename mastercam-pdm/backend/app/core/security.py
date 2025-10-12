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

    def __init__(self, git_repo: 'GitRepository', auth_dir: Optional[Path] = None):
        self.git_repo = git_repo

        # IMPORTANT: Store auth data in app_data, NOT in the repo directory
        # This ensures user passwords persist even if repo is reset/deleted
        if auth_dir is None:
            # Default to backend/app_data/.auth (persistent location)
            # Go up from git_repo.repo_path to find app_data
            if hasattr(git_repo, 'config_manager'):
                # Use config manager's directory as base
                auth_dir = git_repo.config_manager.config_dir / ".auth"
            else:
                # Fallback: use app_data in backend directory
                backend_dir = Path(__file__).resolve().parents[2]
                auth_dir = backend_dir / "app_data" / ".auth"

        auth_dir.mkdir(parents=True, exist_ok=True)
        self.auth_file = auth_dir / "users.json"
        self.jwt_secret = self._get_or_create_secret(auth_dir)

        # This will hold temporary password reset tokens in memory.
        self.reset_tokens: Dict[str, Dict] = {}

    def _get_or_create_secret(self, auth_dir: Path) -> str:
        """
        Retrieves the JWT secret key from a file, or creates one if it doesn't exist.
        This ensures tokens remain valid even if the application restarts.
        """
        secret_file = auth_dir / "jwt_secret"
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

    def reset_password_request(self, username: str) -> str:
        """
        Generate a password reset token for a user.

        Args:
            username: The username requesting password reset

        Returns:
            A reset token string

        Raises:
            ValueError: If user doesn't exist
        """
        users = self._load_users()
        if username not in users:
            raise ValueError(f"User {username} not found")

        # Generate a secure random token
        reset_token = secrets.token_urlsafe(32)

        # Store token with expiration (1 hour from now)
        self.reset_tokens[username] = {
            "token": reset_token,
            "expires": datetime.now(timezone.utc) + timedelta(hours=1)
        }

        logger.info(f"Password reset token generated for user: {username}")
        return reset_token

    def reset_password(self, username: str, reset_token: str, new_password: str) -> bool:
        """
        Reset a user's password using a valid reset token.

        Args:
            username: The username
            reset_token: The reset token from reset_password_request()
            new_password: The new password to set

        Returns:
            True if successful, False if token invalid/expired
        """
        # Check if user has a reset token
        if username not in self.reset_tokens:
            logger.warning(f"No reset token found for user: {username}")
            return False

        token_data = self.reset_tokens[username]

        # Verify token matches and hasn't expired
        if token_data["token"] != reset_token:
            logger.warning(f"Invalid reset token for user: {username}")
            return False

        if datetime.now(timezone.utc) > token_data["expires"]:
            logger.warning(f"Expired reset token for user: {username}")
            del self.reset_tokens[username]
            return False

        # Token is valid, update password
        self.create_user_password(username, new_password)

        # Clean up the used token
        del self.reset_tokens[username]

        logger.info(f"Password successfully reset for user: {username}")
        return True

    def list_users(self) -> Dict[str, dict]:
        """
        Get all registered users (admin function).

        Returns:
            Dictionary of usernames to user data (without password hashes)
        """
        users = self._load_users()
        # Remove password hashes before returning
        safe_users = {}
        for username, data in users.items():
            safe_users[username] = {
                "username": username,
                "is_admin": data.get("is_admin", False),
                "created_at": data.get("created_at", "Unknown")
            }
        return safe_users

    def delete_user(self, username: str) -> bool:
        """
        Delete a user from the system (admin function).

        Args:
            username: The username to delete

        Returns:
            True if deleted, False if user didn't exist
        """
        users = self._load_users()
        if username in users:
            del users[username]
            self._save_users(users)
            logger.info(f"User deleted: {username}")
            return True
        return False

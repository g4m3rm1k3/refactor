import json
import logging
import base64
import os
import sys
from typing import List
from pathlib import Path

from cryptography.fernet import Fernet
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AppConfig(BaseModel):
    """Defines the structure of the application's configuration."""
    version: str = "2.0.0"
    gitlab: dict = Field(default_factory=dict)
    local: dict = Field(default_factory=dict)
    # ADD THIS NEW LINE:
    allowed_file_types: List[str] = Field(
        default=[".mcam", ".vnc", ".emcam", ".link"])
    # (The rest of the model stays the same)
    ui: dict = Field(default_factory=dict)
    security: dict = Field(default_factory=lambda: {
                           "allow_insecure_ssl": False})
    polling: dict = Field(default_factory=lambda: {
                          "enabled": True, "interval_seconds": 15, "check_on_activity": True})


class EncryptionManager:
    """Handles encryption and decryption of sensitive configuration data."""

    def __init__(self, config_dir: Path):
        self.key_file = config_dir / '.encryption_key'
        self._fernet: Fernet | None = None
        self._initialize_encryption()

    def _initialize_encryption(self):
        try:
            if self.key_file.exists():
                key = self.key_file.read_bytes()
            else:
                key = Fernet.generate_key()
                self.key_file.write_bytes(key)
                # Set file permissions to be readable only by the owner on non-Windows systems
                if os.name != 'nt':
                    os.chmod(self.key_file, 0o600)
            self._fernet = Fernet(key)
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")

    def encrypt(self, data: str) -> str:
        """Encrypts a string."""
        if self._fernet:
            return base64.b64encode(self._fernet.encrypt(data.encode())).decode()
        # Fallback if encryption fails to initialize (not ideal, but prevents crash)
        return data

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypts a string."""
        if self._fernet:
            try:
                return self._fernet.decrypt(base64.b64decode(encrypted_data.encode())).decode()
            except Exception:
                # If decryption fails (e.g., key changed, data corrupted), return the raw data
                logger.warning("Failed to decrypt data, returning raw value.")
                return encrypted_data
        return encrypted_data


class ConfigManager:
    """Manages loading, saving, and accessing the application configuration."""

    def __init__(self, base_dir: Path | None = None):
        if base_dir is None:
            # Determine the base directory based on whether running as a script or bundled executable
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys.executable).parent
            else:
                # Moves up from /app/core to /backend
                base_dir = Path(__file__).resolve().parents[2]

        self.config_dir = base_dir / 'app_data'
        self.config_file = self.config_dir / 'config.json'
        # Ensure the directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.encryption = EncryptionManager(self.config_dir)
        self.config = self._load_config()

    def _load_config(self) -> AppConfig:
        """Loads configuration from the JSON file."""
        if not self.config_file.exists() or not self.config_file.read_text():
            return AppConfig()

        try:
            data = json.loads(self.config_file.read_text())
            # Decrypt the token if it exists
            if token := data.get('gitlab', {}).get('token'):
                data['gitlab']['token'] = self.encryption.decrypt(token)
            return AppConfig(**data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(
                f"Failed to load or parse config file, creating a default config: {e}")
            return AppConfig()

    def save_config(self):
        """Saves the current configuration to the JSON file, encrypting sensitive data."""
        try:
            # model_dump() is the Pydantic v2 replacement for .dict()
            data = self.config.model_dump()
            # Encrypt the token before saving
            if token := data.get('gitlab', {}).get('token'):
                data['gitlab']['token'] = self.encryption.encrypt(token)

            self.config_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(
                f"CRITICAL: Failed to save config file at {self.config_file}: {e}")
            raise

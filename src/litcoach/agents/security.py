"""Secure key management for OpenAI Agents SDK."""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import secrets


class SecureKeyManager:
    """Securely manage API keys and sensitive configuration."""

    def __init__(self, env_file: str = ".env", key_file: str = ".keys"):
        self.env_file = Path(env_file)
        self.key_file = Path(key_file)
        self.encryption_key = self._get_or_create_key()
        self.fernet = Fernet(self.encryption_key)

    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key for sensitive data."""
        key_dir = Path.home() / ".literacy-coach"
        key_dir.mkdir(parents=True, exist_ok=True)

        key_file = key_dir / "encryption.key"

        if key_file.exists():
            return key_file.read_bytes()

        # Generate new key
        key = Fernet.generate_key()
        key_file.write_bytes(key)
        key_file.chmod(0o600)  # Read/write for owner only
        return key

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def encrypt_api_key(self, api_key: str, password: Optional[str] = None) -> str:
        """Encrypt and store API key securely."""
        if password:
            # Use password-based encryption
            salt = secrets.token_bytes(16)
            key = self._derive_key(password, salt)
            fernet = Fernet(key)
            encrypted = fernet.encrypt(api_key.encode())
            return f"pbkdf2:{salt.hex()}:{encrypted.decode()}"
        else:
            # Use file-based encryption
            encrypted = self.fernet.encrypt(api_key.encode())
            return f"file:{encrypted.decode()}"

    def decrypt_api_key(self, encrypted_key: str, password: Optional[str] = None) -> str:
        """Decrypt API key."""
        try:
            if encrypted_key.startswith("pbkdf2:"):
                # Password-based decryption
                parts = encrypted_key.split(":", 2)
                if len(parts) != 3:
                    raise ValueError("Invalid encrypted key format")

                salt = bytes.fromhex(parts[1])
                encrypted = parts[2].encode()
                key = self._derive_key(password or "", salt)
                fernet = Fernet(key)
                return fernet.decrypt(encrypted).decode()

            elif encrypted_key.startswith("file:"):
                # File-based decryption
                encrypted = encrypted_key[5:].encode()  # Remove "file:" prefix
                return self.fernet.decrypt(encrypted).decode()

            else:
                # Plain text (for backward compatibility)
                return encrypted_key

        except Exception as e:
            raise ValueError(f"Failed to decrypt API key: {str(e)}")

    def get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key from environment or encrypted storage."""
        # Check environment first
        env_key = os.environ.get("OPENAI_API_KEY")
        if env_key and not env_key.startswith(("pbkdf2:", "file:")):
            return env_key

        # Check .env file
        if self.env_file.exists():
            try:
                from dotenv import dotenv_values
                values = dotenv_values(self.env_file)
                encrypted_key = values.get("OPENAI_API_KEY")
                if encrypted_key:
                    return self.decrypt_api_key(encrypted_key)
            except ImportError:
                pass

        return None

    def set_openai_key(self, api_key: str, password: Optional[str] = None) -> None:
        """Set OpenAI API key with optional encryption."""
        encrypted = self.encrypt_api_key(api_key, password)

        # Update .env file
        env_content = ""
        if self.env_file.exists():
            env_content = self.env_file.read_text()

        # Remove existing OPENAI_API_KEY line
        lines = env_content.split('\n')
        filtered_lines = [line for line in lines if not line.startswith('OPENAI_API_KEY=')]

        # Add encrypted key
        filtered_lines.append(f"OPENAI_API_KEY={encrypted}")

        # Write back to file
        self.env_file.write_text('\n'.join(filtered_lines))

        # Set environment variable for current session
        os.environ["OPENAI_API_KEY"] = api_key

    def validate_key(self, api_key: str) -> bool:
        """Validate API key format."""
        if not api_key:
            return False

        # Basic validation - OpenAI keys start with sk-
        if api_key.startswith("sk-"):
            return len(api_key) > 20  # Basic length check

        return True

    def get_key_info(self) -> Dict[str, Any]:
        """Get information about current key status."""
        current_key = self.get_openai_key()

        return {
            "has_key": current_key is not None,
            "key_prefix": current_key[:7] + "..." if current_key else None,
            "is_encrypted": current_key.startswith(("pbkdf2:", "file:")) if current_key else False,
            "env_file_exists": self.env_file.exists(),
            "key_file_exists": self.key_file.exists()
        }

    def rotate_encryption_key(self, new_password: Optional[str] = None) -> None:
        """Rotate the encryption key (use with caution)."""
        if new_password:
            # For password-based rotation, we'd need to decrypt all existing keys
            # and re-encrypt with new password - this is complex and not implemented
            raise NotImplementedError("Password rotation not yet implemented")

        # Generate new file-based key
        new_key = Fernet.generate_key()
        key_dir = Path.home() / ".literacy-coach"
        key_file = key_dir / "encryption.key"
        key_file.write_bytes(new_key)
        key_file.chmod(0o600)

        # Reinitialize with new key
        self.encryption_key = new_key
        self.fernet = Fernet(new_key)

    def clear_keys(self) -> None:
        """Clear all stored keys (emergency function)."""
        if self.env_file.exists():
            # Remove OPENAI_API_KEY line
            content = self.env_file.read_text()
            lines = content.split('\n')
            filtered_lines = [line for line in lines if not line.startswith('OPENAI_API_KEY=')]
            self.env_file.write_text('\n'.join(filtered_lines))

        # Clear environment
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]


class EnvironmentManager:
    """Manage environment variables and configuration."""

    def __init__(self):
        self.env_file = Path(".env")
        self.example_file = Path(".env.example")

    def load_env_file(self) -> Dict[str, str]:
        """Load environment variables from .env file."""
        if not self.env_file.exists():
            return {}

        try:
            from dotenv import dotenv_values
            return dotenv_values(self.env_file)
        except ImportError:
            # Fallback: simple parsing
            result = {}
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        result[key.strip()] = value.strip().strip('"\'')
            return result

    def create_example_env(self) -> None:
        """Create .env.example file with template."""
        example_content = """# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Model Configuration
LITCOACH_AGENT_MODEL=gpt-4o-mini
LITCOACH_EMBED_MODEL=text-embedding-3-small
LITCOACH_TTS_MODEL=tts-1
LITCOACH_TRANSCRIBE_MODEL=whisper-1

# Service URLs
CONTENT_URL=http://localhost:8002
ASSESSMENT_URL=http://localhost:8003
TEACHER_URL=http://localhost:8004
AGENT_URL=http://localhost:8001
GATEWAY_URL=http://localhost:8000

# Database Paths
CONTENT_DB_PATH=/data/content.db
TEACHER_DB_PATH=/data/teacher.db

# Ollama Configuration (for local models)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3

# TUI Configuration
TUI_THEME=default
TUI_AUTO_SAVE=true
TUI_MAX_HISTORY=50
"""

        self.example_file.write_text(example_content)

    def validate_environment(self) -> Dict[str, Any]:
        """Validate current environment configuration."""
        issues = []
        warnings = []

        # Check for required keys
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            issues.append("OPENAI_API_KEY not set")
        elif not openai_key.startswith("sk-"):
            issues.append("OPENAI_API_KEY does not appear to be valid")

        # Check service URLs
        required_urls = ["CONTENT_URL", "ASSESSMENT_URL", "TEACHER_URL", "AGENT_URL"]
        for url_var in required_urls:
            url = os.environ.get(url_var)
            if not url:
                warnings.append(f"{url_var} not set, using default")

        # Check model configurations
        model_vars = ["LITCOACH_AGENT_MODEL", "LITCOACH_EMBED_MODEL"]
        for model_var in model_vars:
            model = os.environ.get(model_var)
            if not model:
                warnings.append(f"{model_var} not set, using default")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "has_openai_key": bool(openai_key),
            "has_ollama_config": bool(os.environ.get("OLLAMA_BASE_URL"))
        }
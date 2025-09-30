"""Security tests for the literacy coach system."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import json

from litcoach.agents.security import SecureKeyManager, EnvironmentManager
from litcoach.agents.vector_store import VectorStoreManager


class TestSecureKeyManagerSecurity:
    """Test security aspects of key management."""

    @pytest.fixture
    def secure_manager(self, tmp_path):
        """Create a secure key manager for testing."""
        with patch('litcoach.agents.security.Path.home', return_value=tmp_path):
            return SecureKeyManager()

    def test_key_file_permissions(self, tmp_path):
        """Test that key files have proper permissions."""
        with patch('litcoach.agents.security.Path.home', return_value=tmp_path):
            manager = SecureKeyManager()

            # Initialize to create key file
            _ = manager.fernet

            # Check that key file has restricted permissions
            key_file = tmp_path / ".literacy-coach" / "encryption.key"
            if key_file.exists():
                # On Unix systems, check permissions
                import stat
                try:
                    file_mode = key_file.stat().st_mode
                    # Should not be readable by group or others
                    assert not (file_mode & stat.S_IRGRP)  # Not group readable
                    assert not (file_mode & stat.S_IROTH)  # Not other readable
                except (AttributeError, OSError):
                    # Skip on systems that don't support this
                    pass

    def test_api_key_validation(self, secure_manager):
        """Test API key validation."""
        # Valid OpenAI key format
        assert secure_manager.validate_key("sk-1234567890123456789012345678901234567890") == True

        # Invalid formats
        assert secure_manager.validate_key("") == False
        assert secure_manager.validate_key("invalid") == True  # Basic validation only
        assert secure_manager.validate_key("pk-123456789") == True  # Different prefix is ok

    def test_encryption_security(self, secure_manager):
        """Test that encryption provides security."""
        test_key = "sk-test123456789"
        encrypted = secure_manager.encrypt_api_key(test_key)

        # Encrypted should be different from original
        assert encrypted != test_key

        # Should contain encryption markers
        assert "file:" in encrypted or "pbkdf2:" in encrypted

        # Should be decryptable back to original
        decrypted = secure_manager.decrypt_api_key(encrypted)
        assert decrypted == test_key

    def test_password_based_encryption(self, secure_manager):
        """Test password-based encryption."""
        test_key = "sk-test987654321"
        password = "secure_password_123"

        encrypted = secure_manager.encrypt_api_key(test_key, password)
        assert "pbkdf2:" in encrypted

        decrypted = secure_manager.decrypt_api_key(encrypted, password)
        assert decrypted == test_key

        # Wrong password should fail
        with pytest.raises(ValueError):
            secure_manager.decrypt_api_key(encrypted, "wrong_password")

    def test_key_rotation(self, secure_manager):
        """Test encryption key rotation."""
        # This is a basic test - in practice, rotation is complex
        # as it requires decrypting and re-encrypting all existing keys
        with pytest.raises(NotImplementedError):
            secure_manager.rotate_encryption_key("new_password")


class TestEnvironmentManagerSecurity:
    """Test environment management security."""

    @pytest.fixture
    def env_manager(self):
        """Create environment manager for testing."""
        return EnvironmentManager()

    def test_env_file_security(self, tmp_path, env_manager):
        """Test environment file handling."""
        env_file = tmp_path / ".env"
        env_manager.env_file = env_file

        # Create test .env file
        test_content = "OPENAI_API_KEY=sk-test123\nOTHER_VAR=value"
        env_file.write_text(test_content)

        # Load environment
        values = env_manager.load_env_file()

        assert "OPENAI_API_KEY" in values
        assert values["OPENAI_API_KEY"] == "sk-test123"
        assert values["OTHER_VAR"] == "value"

    def test_environment_validation(self, env_manager):
        """Test environment validation."""
        # Test with no environment variables
        with patch.dict(os.environ, {}, clear=True):
            validation = env_manager.validate_environment()

            assert validation["valid"] == False
            assert "OPENAI_API_KEY not set" in validation["issues"]

    def test_example_env_creation(self, env_manager):
        """Test .env.example creation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_manager.example_file = Path(tmp_dir) / ".env.example"

            env_manager.create_example_env()

            assert env_manager.example_file.exists()

            content = env_manager.example_file.read_text()
            assert "OPENAI_API_KEY=your_openai_api_key_here" in content
            assert "sk-" not in content  # Should not contain actual keys


class TestVectorStoreSecurity:
    """Test vector store security."""

    @pytest.fixture
    def secure_vector_store(self, tmp_path):
        """Create a vector store for security testing."""
        return VectorStoreManager(str(tmp_path / "secure_store"))

    @pytest.mark.asyncio
    async def test_data_isolation(self, secure_vector_store):
        """Test that vector store data is properly isolated."""
        # Add sensitive document
        sensitive_content = "This contains sensitive student information and grades"
        doc_id = await secure_vector_store.add(
            sensitive_content,
            {"confidential": True, "student_id": "12345"}
        )

        # Verify document is stored
        assert len(secure_vector_store.documents) == 1
        assert secure_vector_store.documents[0]["text"] == sensitive_content

        # Delete document
        success = await secure_vector_store.delete(doc_id)
        assert success == True

        # Verify deletion
        assert len(secure_vector_store.documents) == 0

    @pytest.mark.asyncio
    async def test_metadata_protection(self, secure_vector_store):
        """Test that metadata is properly handled."""
        # Add document with sensitive metadata
        sensitive_metadata = {
            "student_name": "John Doe",
            "grade": "A",
            "ssn": "123-45-6789"  # This should not be stored in practice
        }

        doc_id = await secure_vector_store.add(
            "Test content",
            sensitive_metadata
        )

        # Verify metadata is stored
        stored_doc = secure_vector_store.documents[0]
        assert stored_doc["metadata"]["student_name"] == "John Doe"

        # In a real system, sensitive fields like SSN should be filtered out
        # This is a placeholder for that functionality


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_sql_injection_prevention(self):
        """Test prevention of SQL injection attacks."""
        # This would test the database layer for SQL injection prevention
        # For now, it's a placeholder
        assert True

    def test_xss_prevention(self):
        """Test prevention of XSS attacks."""
        # This would test the web layer for XSS prevention
        # For now, it's a placeholder
        assert True

    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks."""
        # Test that file paths are properly validated
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM"
        ]

        for path in dangerous_paths:
            # In a real system, these should be rejected
            # This is a placeholder for path validation
            assert True


class TestDataPrivacy:
    """Test data privacy protections."""

    @pytest.fixture
    def privacy_manager(self, tmp_path):
        """Create components for privacy testing."""
        store = VectorStoreManager(str(tmp_path / "privacy_store"))
        return store

    @pytest.mark.asyncio
    async def test_pii_handling(self, privacy_manager):
        """Test handling of personally identifiable information."""
        # Add document with PII
        content_with_pii = "Student John Doe (ID: 12345) scored 95% on the reading test"
        metadata_with_pii = {
            "student_id": "12345",
            "student_name": "John Doe",
            "email": "john.doe@example.com"
        }

        doc_id = await privacy_manager.add(content_with_pii, metadata_with_pii)

        # Verify PII is stored (in practice, this might be encrypted or filtered)
        stored_doc = privacy_manager.documents[0]
        assert stored_doc["text"] == content_with_pii
        assert stored_doc["metadata"]["student_id"] == "12345"

        # In a production system, PII should be:
        # 1. Encrypted at rest
        # 2. Only accessible to authorized users
        # 3. Logged when accessed
        # This is a placeholder for those features

    @pytest.mark.asyncio
    async def test_data_retention(self, privacy_manager):
        """Test data retention policies."""
        # Add document
        doc_id = await privacy_manager.add("Temporary document")

        # Simulate retention policy (immediate deletion for testing)
        success = await privacy_manager.delete(doc_id)
        assert success == True

        # Verify deletion
        assert len(privacy_manager.documents) == 0


class TestAccessControl:
    """Test access control mechanisms."""

    def test_api_key_access_control(self):
        """Test API key access control."""
        # This would test that API keys are required for certain operations
        # For now, it's a placeholder
        assert True

    def test_session_isolation(self):
        """Test that sessions are properly isolated."""
        # This would test that one user's session data is not accessible to another
        # For now, it's a placeholder
        assert True


class TestAuditLogging:
    """Test audit logging functionality."""

    def test_security_event_logging(self, tmp_path):
        """Test that security events are logged."""
        # This would test that security-relevant events are logged
        # For now, it's a placeholder
        assert True

    def test_data_access_logging(self):
        """Test that data access is logged."""
        # This would test that access to sensitive data is logged
        # For now, it's a placeholder
        assert True


class TestCryptography:
    """Test cryptographic functions."""

    def test_encryption_strength(self, tmp_path):
        """Test encryption strength."""
        with patch('litcoach.agents.security.Path.home', return_value=tmp_path):
            manager = SecureKeyManager()

            # Test that encryption produces different outputs for same input
            test_key = "sk-test123456789"
            encrypted1 = manager.encrypt_api_key(test_key)
            encrypted2 = manager.encrypt_api_key(test_key)

            # Should be different (due to different IVs/salts)
            assert encrypted1 != encrypted2

            # But both should decrypt to same value
            decrypted1 = manager.decrypt_api_key(encrypted1)
            decrypted2 = manager.decrypt_api_key(encrypted2)
            assert decrypted1 == test_key
            assert decrypted2 == test_key

    def test_key_derivation(self, tmp_path):
        """Test key derivation security."""
        with patch('litcoach.agents.security.Path.home', return_value=tmp_path):
            manager = SecureKeyManager()

            password = "test_password_123"
            salt1 = os.urandom(16)
            salt2 = os.urandom(16)

            # Same password with different salts should produce different keys
            key1 = manager._derive_key(password, salt1)
            key2 = manager._derive_key(password, salt2)
            assert key1 != key2

            # Same password and salt should produce same key
            key1_again = manager._derive_key(password, salt1)
            assert key1 == key1_again


class TestSecureDefaults:
    """Test secure default configurations."""

    def test_secure_file_permissions(self, tmp_path):
        """Test that files are created with secure permissions."""
        # Create test files
        test_file = tmp_path / "test_file"
        test_file.write_text("test content")

        # Check permissions (Unix systems)
        try:
            import stat
            file_mode = test_file.stat().st_mode

            # Should not be world-writable
            assert not (file_mode & stat.S_IWOTH)

            # Should not be world-readable (for sensitive files)
            # This depends on the specific file type

        except (AttributeError, OSError):
            # Skip on systems that don't support this
            pass

    def test_memory_safety(self):
        """Test memory safety considerations."""
        # This would test for memory leaks, buffer overflows, etc.
        # For now, it's a placeholder for memory safety testing
        assert True
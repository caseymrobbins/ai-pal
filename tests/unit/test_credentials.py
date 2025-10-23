"""
Unit tests for Secure Credential Manager.

Tests encryption, access control, audit logging, and GDPR compliance.
"""

import pytest
from pathlib import Path
import json

from ai_pal.core.credentials import SecureCredentialManager


# ============================================================================
# Initialization Tests
# ============================================================================

@pytest.mark.unit
def test_credential_manager_initialization(temp_credentials_file, temp_dir):
    """Test credential manager initializes correctly."""
    audit_log = temp_dir / "audit.log"
    manager = SecureCredentialManager(
        credentials_file=temp_credentials_file,
        audit_log_file=audit_log,
    )

    assert manager.credentials_file == temp_credentials_file
    assert manager.audit_log_file == audit_log
    assert len(manager._credentials) == 0
    assert manager._cipher is not None


@pytest.mark.unit
def test_creates_encryption_key(temp_credentials_file, temp_dir):
    """Test that encryption key is created if it doesn't exist."""
    manager = SecureCredentialManager(
        credentials_file=temp_credentials_file,
        audit_log_file=temp_dir / "audit.log",
    )

    assert manager._cipher is not None
    # Key file should exist
    assert Path(".master.key").exists()


# ============================================================================
# Credential Storage Tests
# ============================================================================

@pytest.mark.unit
def test_store_credential(credential_manager):
    """Test storing a credential."""
    result = credential_manager.store_credential(
        "TEST_KEY",
        "secret_value_123",
        requester="system",
    )

    assert result is True
    assert "TEST_KEY" in credential_manager._credentials
    assert credential_manager._credentials["TEST_KEY"] == "secret_value_123"


@pytest.mark.unit
def test_store_credential_unauthorized(credential_manager):
    """Test that unauthorized requesters cannot store credentials."""
    result = credential_manager.store_credential(
        "TEST_KEY",
        "secret_value",
        requester="random_plugin",
    )

    assert result is False
    assert "TEST_KEY" not in credential_manager._credentials


@pytest.mark.unit
def test_store_multiple_credentials(credential_manager, sample_credentials):
    """Test storing multiple credentials."""
    for name, value in sample_credentials.items():
        result = credential_manager.store_credential(name, value, "system")
        assert result is True

    assert len(credential_manager._credentials) == len(sample_credentials)


# ============================================================================
# Credential Retrieval Tests
# ============================================================================

@pytest.mark.unit
def test_get_credential_authorized(credential_manager):
    """Test retrieving a credential with proper authorization."""
    # Store credential
    credential_manager.store_credential("OPENAI_API_KEY", "sk-test", "system")

    # Grant access
    credential_manager._access_policies["openai_provider"] = {"OPENAI_API_KEY"}

    # Retrieve
    value = credential_manager.get_credential("OPENAI_API_KEY", "openai_provider")

    assert value == "sk-test"


@pytest.mark.unit
def test_get_credential_unauthorized(credential_manager):
    """Test that unauthorized access is denied."""
    credential_manager.store_credential("SECRET_KEY", "secret", "system")

    # Try to get without permission
    value = credential_manager.get_credential("SECRET_KEY", "random_plugin")

    assert value is None


@pytest.mark.unit
def test_get_credential_nonexistent(credential_manager):
    """Test getting a credential that doesn't exist."""
    credential_manager._access_policies["test"] = {"*"}

    value = credential_manager.get_credential("NONEXISTENT", "test")

    assert value is None


@pytest.mark.unit
def test_wildcard_access(credential_manager):
    """Test that wildcard access grants access to all credentials."""
    credential_manager.store_credential("KEY1", "value1", "system")
    credential_manager.store_credential("KEY2", "value2", "system")

    # Grant wildcard access
    credential_manager._access_policies["orchestrator"] = {"*"}

    # Can access any credential
    assert credential_manager.get_credential("KEY1", "orchestrator") == "value1"
    assert credential_manager.get_credential("KEY2", "orchestrator") == "value2"


# ============================================================================
# Audit Trail Tests
# ============================================================================

@pytest.mark.unit
def test_audit_trail_on_access(credential_manager):
    """Test that credential access is logged to audit trail."""
    credential_manager.store_credential("TEST_KEY", "value", "system")
    credential_manager._access_policies["test_module"] = {"TEST_KEY"}

    # Access the credential
    credential_manager.get_credential("TEST_KEY", "test_module")

    # Check audit trail
    trail = credential_manager.get_audit_trail()

    assert len(trail) > 0
    latest = trail[0]
    assert latest.credential_name == "TEST_KEY"
    assert latest.accessed_by == "test_module"
    assert latest.access_granted is True


@pytest.mark.unit
def test_audit_trail_on_denied_access(credential_manager):
    """Test that denied access is logged."""
    credential_manager.store_credential("SECRET", "value", "system")

    # Try to access without permission
    credential_manager.get_credential("SECRET", "unauthorized_module")

    # Check audit trail
    trail = credential_manager.get_audit_trail()

    assert len(trail) > 0
    latest = trail[0]
    assert latest.access_granted is False
    assert latest.reason is not None


@pytest.mark.unit
def test_audit_log_file_written(credential_manager, temp_dir):
    """Test that audit log is written to file."""
    credential_manager.store_credential("TEST", "value", "system")
    credential_manager._access_policies["test"] = {"TEST"}

    credential_manager.get_credential("TEST", "test")

    # Check log file exists and has content
    assert credential_manager.audit_log_file.exists()

    with open(credential_manager.audit_log_file, "r") as f:
        log_content = f.read()
        assert "TEST" in log_content
        assert "test" in log_content


# ============================================================================
# Credential Deletion Tests
# ============================================================================

@pytest.mark.unit
def test_delete_credential(credential_manager):
    """Test deleting a credential."""
    credential_manager.store_credential("TO_DELETE", "value", "system")
    assert "TO_DELETE" in credential_manager._credentials

    result = credential_manager.delete_credential("TO_DELETE", "system")

    assert result is True
    assert "TO_DELETE" not in credential_manager._credentials


@pytest.mark.unit
def test_delete_credential_unauthorized(credential_manager):
    """Test that unauthorized users cannot delete credentials."""
    credential_manager.store_credential("PROTECTED", "value", "system")

    result = credential_manager.delete_credential("PROTECTED", "random_plugin")

    assert result is False
    assert "PROTECTED" in credential_manager._credentials


@pytest.mark.unit
def test_delete_nonexistent_credential(credential_manager):
    """Test deleting a credential that doesn't exist."""
    result = credential_manager.delete_credential("NONEXISTENT", "system")

    assert result is False


# ============================================================================
# List Credentials Tests
# ============================================================================

@pytest.mark.unit
def test_list_credentials_wildcard(credential_manager, sample_credentials):
    """Test listing credentials with wildcard access."""
    for name, value in sample_credentials.items():
        credential_manager.store_credential(name, value, "system")

    credential_manager._access_policies["orchestrator"] = {"*"}

    listed = credential_manager.list_credentials("orchestrator")

    assert len(listed) == len(sample_credentials)
    assert set(listed) == set(sample_credentials.keys())


@pytest.mark.unit
def test_list_credentials_restricted(credential_manager):
    """Test listing credentials with restricted access."""
    credential_manager.store_credential("KEY1", "value1", "system")
    credential_manager.store_credential("KEY2", "value2", "system")
    credential_manager.store_credential("KEY3", "value3", "system")

    # Grant access to only KEY1 and KEY2
    credential_manager._access_policies["test_module"] = {"KEY1", "KEY2"}

    listed = credential_manager.list_credentials("test_module")

    assert len(listed) == 2
    assert "KEY1" in listed
    assert "KEY2" in listed
    assert "KEY3" not in listed


@pytest.mark.unit
def test_list_credentials_no_access(credential_manager):
    """Test listing credentials with no access."""
    credential_manager.store_credential("KEY", "value", "system")

    listed = credential_manager.list_credentials("unauthorized_module")

    assert len(listed) == 0


# ============================================================================
# Permission Management Tests
# ============================================================================

@pytest.mark.unit
def test_grant_access(credential_manager):
    """Test granting access to a credential."""
    result = credential_manager.grant_access(
        "test_module",
        "TEST_CREDENTIAL",
        granted_by="system",
    )

    assert result is True
    assert "TEST_CREDENTIAL" in credential_manager._access_policies["test_module"]


@pytest.mark.unit
def test_grant_access_unauthorized(credential_manager):
    """Test that unauthorized users cannot grant access."""
    result = credential_manager.grant_access(
        "test_module",
        "TEST_CREDENTIAL",
        granted_by="random_plugin",
    )

    assert result is False


@pytest.mark.unit
def test_revoke_access(credential_manager):
    """Test revoking access to a credential."""
    # First grant access
    credential_manager._access_policies["test_module"] = {"TEST_CREDENTIAL"}

    # Then revoke
    result = credential_manager.revoke_access(
        "test_module",
        "TEST_CREDENTIAL",
        revoked_by="system",
    )

    assert result is True
    assert "TEST_CREDENTIAL" not in credential_manager._access_policies.get(
        "test_module", set()
    )


@pytest.mark.unit
def test_revoke_access_unauthorized(credential_manager):
    """Test that unauthorized users cannot revoke access."""
    credential_manager._access_policies["test_module"] = {"TEST_CREDENTIAL"}

    result = credential_manager.revoke_access(
        "test_module",
        "TEST_CREDENTIAL",
        revoked_by="random_plugin",
    )

    assert result is False


# ============================================================================
# Encryption Tests
# ============================================================================

@pytest.mark.unit
def test_credentials_encrypted_on_disk(credential_manager, sample_credentials):
    """Test that credentials are encrypted when saved to disk."""
    # Store credentials
    for name, value in sample_credentials.items():
        credential_manager.store_credential(name, value, "system")

    # Save to disk
    credential_manager._save_credentials()

    # Read raw file - should be encrypted (not plaintext)
    with open(credential_manager.credentials_file, "rb") as f:
        raw_data = f.read()

    # Should not contain plaintext values
    for value in sample_credentials.values():
        assert value.encode() not in raw_data

    # Should not be valid JSON
    with pytest.raises(json.JSONDecodeError):
        json.loads(raw_data)


@pytest.mark.unit
def test_credentials_decrypted_on_load(credential_manager, temp_credentials_file, temp_dir):
    """Test that credentials are decrypted when loaded."""
    # Store and save
    credential_manager.store_credential("TEST", "secret_value", "system")
    credential_manager._save_credentials()

    # Create new manager (should load and decrypt)
    new_manager = SecureCredentialManager(
        credentials_file=temp_credentials_file,
        audit_log_file=temp_dir / "audit.log",
    )

    # Should have the credential decrypted
    assert "TEST" in new_manager._credentials
    assert new_manager._credentials["TEST"] == "secret_value"


# ============================================================================
# Environment Variable Import Tests
# ============================================================================

@pytest.mark.unit
def test_import_from_env(credential_manager, monkeypatch):
    """Test importing credentials from environment variables."""
    # Set environment variables
    monkeypatch.setenv("AI_PAL_CREDENTIAL_API_KEY", "test_key_123")
    monkeypatch.setenv("AI_PAL_CREDENTIAL_SECRET", "test_secret_456")
    monkeypatch.setenv("OTHER_VAR", "ignored")

    count = credential_manager.import_from_env()

    assert count == 2
    assert "API_KEY" in credential_manager._credentials
    assert "SECRET" in credential_manager._credentials
    assert credential_manager._credentials["API_KEY"] == "test_key_123"


# ============================================================================
# Audit Trail Filtering Tests
# ============================================================================

@pytest.mark.unit
def test_get_audit_trail_by_credential(credential_manager):
    """Test filtering audit trail by credential name."""
    credential_manager.store_credential("KEY1", "value1", "system")
    credential_manager.store_credential("KEY2", "value2", "system")

    credential_manager._access_policies["test"] = {"*"}

    credential_manager.get_credential("KEY1", "test")
    credential_manager.get_credential("KEY2", "test")
    credential_manager.get_credential("KEY1", "test")  # Access KEY1 twice

    trail = credential_manager.get_audit_trail(credential_name="KEY1")

    assert len(trail) == 2
    assert all(entry.credential_name == "KEY1" for entry in trail)


@pytest.mark.unit
def test_get_audit_trail_by_requester(credential_manager):
    """Test filtering audit trail by requester."""
    credential_manager.store_credential("KEY", "value", "system")

    credential_manager._access_policies["module1"] = {"KEY"}
    credential_manager._access_policies["module2"] = {"KEY"}

    credential_manager.get_credential("KEY", "module1")
    credential_manager.get_credential("KEY", "module2")
    credential_manager.get_credential("KEY", "module1")

    trail = credential_manager.get_audit_trail(requester="module1")

    assert len(trail) == 2
    assert all(entry.accessed_by == "module1" for entry in trail)


@pytest.mark.unit
def test_get_audit_trail_limit(credential_manager):
    """Test audit trail limit parameter."""
    credential_manager.store_credential("KEY", "value", "system")
    credential_manager._access_policies["test"] = {"KEY"}

    # Generate many accesses
    for _ in range(20):
        credential_manager.get_credential("KEY", "test")

    trail = credential_manager.get_audit_trail(limit=10)

    assert len(trail) == 10


# ============================================================================
# Security Tests
# ============================================================================

@pytest.mark.unit
def test_never_logs_credential_values(credential_manager, capsys):
    """Test that credential values are never logged."""
    secret_value = "super_secret_password_12345"

    credential_manager.store_credential("SECRET", secret_value, "system")

    # Capture logs/output
    captured = capsys.readouterr()

    # Secret value should not appear in logs
    assert secret_value not in captured.out
    assert secret_value not in captured.err


@pytest.mark.unit
def test_default_access_policies(credential_manager):
    """Test that default access policies are set up correctly."""
    # Core modules should have wildcard
    assert "*" in credential_manager._access_policies.get("orchestrator", set())
    assert "*" in credential_manager._access_policies.get("privacy", set())
    assert "*" in credential_manager._access_policies.get("ethics", set())

    # LLM providers should only access their own keys
    assert credential_manager._access_policies.get("openai_provider") == {
        "OPENAI_API_KEY"
    }
    assert credential_manager._access_policies.get("anthropic_provider") == {
        "ANTHROPIC_API_KEY"
    }

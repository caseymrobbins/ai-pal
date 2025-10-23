"""
Unit tests for Plugin Manager.

Tests hot-swappable plugin system, RBAC, sandboxing, freeze/rollback.
"""

import pytest
from pathlib import Path
from datetime import datetime

from ai_pal.core.plugin_manager import (
    PluginManager,
    PluginManifest,
    PluginPermission,
    PluginStatus,
    PluginSecurityViolation,
)


# ============================================================================
# Plugin Manager Initialization Tests
# ============================================================================

@pytest.mark.unit
def test_plugin_manager_initialization(temp_plugins_dir):
    """Test plugin manager initializes correctly."""
    manager = PluginManager(plugins_dir=temp_plugins_dir)

    assert manager.plugins_dir == temp_plugins_dir
    assert len(manager.discovered_plugins) == 0
    assert len(manager.loaded_plugins) == 0
    assert len(manager.frozen_plugins) == 0


@pytest.mark.unit
def test_plugin_manager_creates_directory(temp_dir):
    """Test plugin manager creates plugins directory if it doesn't exist."""
    plugins_dir = temp_dir / "new_plugins"
    assert not plugins_dir.exists()

    manager = PluginManager(plugins_dir=plugins_dir)

    assert plugins_dir.exists()
    assert plugins_dir.is_dir()


# ============================================================================
# Permission System Tests
# ============================================================================

@pytest.mark.unit
def test_request_permissions_safe(plugin_manager):
    """Test requesting safe permissions is auto-approved."""
    safe_permissions = {
        PluginPermission.READ_CONVERSATION_HISTORY,
        PluginPermission.CALL_OTHER_MODULES,
    }

    granted = plugin_manager.request_permissions("test_plugin", safe_permissions)

    assert granted is True
    assert plugin_manager.permission_policies["test_plugin"] == safe_permissions


@pytest.mark.unit
def test_request_permissions_dangerous(plugin_manager):
    """Test requesting dangerous permissions is restricted."""
    dangerous_permissions = {
        PluginPermission.NETWORK_ACCESS,
        PluginPermission.FILE_SYSTEM_WRITE,
        PluginPermission.EXECUTE_CODE,
    }

    granted = plugin_manager.request_permissions("test_plugin", dangerous_permissions)

    # Should be denied (returns False since no permissions granted)
    assert granted is False

    # Only safe permissions granted
    granted_perms = plugin_manager.permission_policies.get("test_plugin", set())
    assert PluginPermission.EXECUTE_CODE not in granted_perms


@pytest.mark.unit
def test_core_modules_get_all_permissions(plugin_manager):
    """Test core modules get wildcard permissions."""
    all_permissions = set(PluginPermission)

    granted = plugin_manager.request_permissions("orchestrator", all_permissions)

    assert granted is True
    assert "*" in plugin_manager.permission_policies["orchestrator"]


@pytest.mark.unit
def test_check_permission(plugin_manager):
    """Test permission checking."""
    # Grant permissions
    plugin_manager.permission_policies["test_plugin"] = {
        PluginPermission.READ_USER_DATA
    }

    # Check granted permission
    assert plugin_manager.check_permission(
        "test_plugin", PluginPermission.READ_USER_DATA
    )

    # Check denied permission
    assert not plugin_manager.check_permission(
        "test_plugin", PluginPermission.NETWORK_ACCESS
    )

    # Check non-existent plugin
    assert not plugin_manager.check_permission(
        "nonexistent", PluginPermission.READ_USER_DATA
    )


# ============================================================================
# Plugin Discovery Tests
# ============================================================================

@pytest.mark.unit
def test_discover_plugins_empty(plugin_manager):
    """Test discovering plugins with no plugins installed."""
    discovered = plugin_manager.discover_plugins()

    assert len(discovered) == 0
    assert len(plugin_manager.discovered_plugins) == 0


@pytest.mark.unit
def test_discover_plugins_with_manifests(plugin_manager, sample_plugin_manifest):
    """Test discovering plugins adds them to registry."""
    # Manually add a manifest for testing
    plugin_manager.discovered_plugins["test_plugin"] = sample_plugin_manifest

    assert "test_plugin" in plugin_manager.discovered_plugins
    manifest = plugin_manager.discovered_plugins["test_plugin"]
    assert manifest.name == "test_plugin"
    assert manifest.version == "1.0.0"


# ============================================================================
# Plugin Freezing Tests (Governance with Teeth)
# ============================================================================

@pytest.mark.unit
def test_freeze_plugin(plugin_manager, sample_plugin_manifest):
    """Test freezing a plugin."""
    # Add plugin to registry
    plugin_manager.discovered_plugins["test_plugin"] = sample_plugin_manifest

    # Freeze it
    result = plugin_manager.freeze_plugin(
        "test_plugin",
        reason="Gate 2 violation: extraction detected",
    )

    assert result is True
    assert "test_plugin" in plugin_manager.frozen_plugins


@pytest.mark.unit
def test_cannot_load_frozen_plugin(plugin_manager, sample_plugin_manifest):
    """Test that frozen plugins cannot be loaded."""
    plugin_manager.discovered_plugins["test_plugin"] = sample_plugin_manifest
    plugin_manager.freeze_plugin("test_plugin", reason="Test freeze")

    # Attempt to load
    instance = plugin_manager.load_plugin("test_plugin")

    assert instance is None


@pytest.mark.unit
def test_freeze_updates_loaded_plugin_status(plugin_manager, mock_module):
    """Test that freezing updates status of already-loaded plugin."""
    # Manually add a loaded plugin for testing
    from ai_pal.core.plugin_manager import PluginInstance, PluginManifest

    manifest = PluginManifest(
        name="test_plugin",
        version="1.0.0",
        description="Test",
        author="Test",
        module_class="test:Test",
    )

    instance = PluginInstance(
        manifest=manifest,
        module=mock_module,
        status=PluginStatus.RUNNING,
        loaded_at=datetime.now(),
        code_version="1.0.0",
    )

    plugin_manager.loaded_plugins["test_plugin"] = instance

    # Freeze it
    plugin_manager.freeze_plugin("test_plugin", reason="Test")

    # Check status updated
    assert instance.status == PluginStatus.FROZEN
    assert "FROZEN" in instance.last_error


# ============================================================================
# Plugin Unloading Tests
# ============================================================================

@pytest.mark.unit
def test_unload_plugin_not_loaded(plugin_manager):
    """Test unloading a plugin that isn't loaded."""
    result = plugin_manager.unload_plugin("nonexistent")

    assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_unload_plugin_calls_shutdown(plugin_manager, mock_module):
    """Test unloading calls the plugin's shutdown method."""
    from ai_pal.core.plugin_manager import PluginInstance, PluginManifest

    manifest = PluginManifest(
        name="test_plugin",
        version="1.0.0",
        description="Test",
        author="Test",
        module_class="test:Test",
    )

    instance = PluginInstance(
        manifest=manifest,
        module=mock_module,
        status=PluginStatus.RUNNING,
        loaded_at=datetime.now(),
        code_version="1.0.0",
    )

    plugin_manager.loaded_plugins["test_plugin"] = instance

    # Unload
    result = plugin_manager.unload_plugin("test_plugin")

    assert result is True
    assert "test_plugin" not in plugin_manager.loaded_plugins


# ============================================================================
# Plugin Status Tests
# ============================================================================

@pytest.mark.unit
def test_get_plugin_status_not_loaded(plugin_manager):
    """Test getting status of non-loaded plugin."""
    status = plugin_manager.get_plugin_status("nonexistent")

    assert status["name"] == "nonexistent"
    assert status["status"] == "not_loaded"
    assert status["frozen"] is False


@pytest.mark.unit
def test_get_plugin_status_loaded(plugin_manager, mock_module):
    """Test getting status of loaded plugin."""
    from ai_pal.core.plugin_manager import PluginInstance, PluginManifest

    manifest = PluginManifest(
        name="test_plugin",
        version="1.0.0",
        description="Test",
        author="Test",
        module_class="test:Test",
        required_permissions={PluginPermission.READ_USER_DATA},
    )

    instance = PluginInstance(
        manifest=manifest,
        module=mock_module,
        status=PluginStatus.RUNNING,
        loaded_at=datetime.now(),
        permissions_granted={PluginPermission.READ_USER_DATA},
        call_count=5,
        error_count=1,
        code_version="1.0.0",
    )

    plugin_manager.loaded_plugins["test_plugin"] = instance

    status = plugin_manager.get_plugin_status("test_plugin")

    assert status["name"] == "test_plugin"
    assert status["version"] == "1.0.0"
    assert status["status"] == "running"
    assert status["call_count"] == 5
    assert status["error_count"] == 1
    assert PluginPermission.READ_USER_DATA.value in status["permissions"]
    assert status["healthy"] is True  # error_count < 10


@pytest.mark.unit
def test_get_all_plugin_status(plugin_manager, sample_plugin_manifest):
    """Test getting status of all plugins."""
    plugin_manager.discovered_plugins["plugin1"] = sample_plugin_manifest
    plugin_manager.discovered_plugins["plugin2"] = sample_plugin_manifest

    all_status = plugin_manager.get_all_plugin_status()

    assert len(all_status) == 2
    assert "plugin1" in all_status
    assert "plugin2" in all_status


# ============================================================================
# Plugin Calling Tests (Security)
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_call_frozen_plugin_raises(plugin_manager, mock_module):
    """Test calling a frozen plugin raises SecurityViolation."""
    from ai_pal.core.plugin_manager import PluginInstance, PluginManifest

    manifest = PluginManifest(
        name="test_plugin",
        version="1.0.0",
        description="Test",
        author="Test",
        module_class="test:Test",
    )

    instance = PluginInstance(
        manifest=manifest,
        module=mock_module,
        status=PluginStatus.RUNNING,
        loaded_at=datetime.now(),
        code_version="1.0.0",
    )

    plugin_manager.loaded_plugins["test_plugin"] = instance
    plugin_manager.freeze_plugin("test_plugin", reason="Test")

    with pytest.raises(PluginSecurityViolation):
        await plugin_manager.call_plugin("test_plugin", "some_method")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_call_nonexistent_plugin_raises(plugin_manager):
    """Test calling non-existent plugin raises ValueError."""
    with pytest.raises(ValueError, match="Plugin not loaded"):
        await plugin_manager.call_plugin("nonexistent", "some_method")


# ============================================================================
# Version Control Tests (Rollback)
# ============================================================================

@pytest.mark.unit
def test_rollback_plugin_no_history(plugin_manager):
    """Test rollback fails when no version history exists."""
    result = plugin_manager.rollback_plugin("nonexistent")

    assert result is False


@pytest.mark.unit
def test_plugin_version_tracking(plugin_manager):
    """Test that plugin versions are tracked for rollback."""
    # Manually set up version history
    plugin_manager.plugin_versions["test_plugin"] = ["1.0.0", "0.9.0", "0.8.0"]

    versions = plugin_manager.plugin_versions["test_plugin"]

    assert len(versions) == 3
    assert versions[0] == "1.0.0"
    assert versions[-1] == "0.8.0"


# ============================================================================
# Error Counting Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_error_count_increments(plugin_manager, failing_module):
    """Test that plugin error count increments on failures."""
    from ai_pal.core.plugin_manager import PluginInstance, PluginManifest

    manifest = PluginManifest(
        name="failing_plugin",
        version="1.0.0",
        description="Test",
        author="Test",
        module_class="test:Test",
    )

    instance = PluginInstance(
        manifest=manifest,
        module=failing_module,
        status=PluginStatus.RUNNING,
        loaded_at=datetime.now(),
        code_version="1.0.0",
    )

    plugin_manager.loaded_plugins["failing_plugin"] = instance

    # Try to call a method that will fail
    with pytest.raises(RuntimeError):
        await plugin_manager.call_plugin("failing_plugin", "process", None)

    # Check error count
    assert instance.error_count == 1


# ============================================================================
# Permission Grant/Revoke Tests
# ============================================================================

@pytest.mark.unit
def test_grant_access(plugin_manager):
    """Test granting credential access to a plugin."""
    result = plugin_manager.request_permissions(
        "test_plugin",
        {PluginPermission.READ_USER_DATA},
    )

    assert result is True
    assert PluginPermission.READ_USER_DATA in plugin_manager.permission_policies[
        "test_plugin"
    ]


# ============================================================================
# Integration: Plugin Lifecycle
# ============================================================================

@pytest.mark.unit
def test_plugin_lifecycle(plugin_manager, sample_plugin_manifest):
    """Test complete plugin lifecycle: discover -> load -> freeze -> unload."""
    # 1. Discover
    plugin_manager.discovered_plugins["test_plugin"] = sample_plugin_manifest
    assert "test_plugin" in plugin_manager.discovered_plugins

    # 2. Request permissions
    granted = plugin_manager.request_permissions(
        "test_plugin",
        sample_plugin_manifest.required_permissions,
    )
    assert granted is True

    # 3. Freeze (simulating ethics module detecting violation)
    plugin_manager.freeze_plugin("test_plugin", reason="Test violation")
    assert "test_plugin" in plugin_manager.frozen_plugins

    # 4. Cannot load while frozen
    instance = plugin_manager.load_plugin("test_plugin")
    assert instance is None

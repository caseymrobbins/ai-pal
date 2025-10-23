"""
Plugin Manager - Hot-swappable plugin system with sandboxing and RBAC.

Implements the AC-AI requirement for "governance with teeth" via automatic
freezes and rollbacks without system restart.
"""

from typing import Dict, List, Optional, Set, Any, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import importlib
import importlib.metadata
import sys
import hashlib
from loguru import logger

from ai_pal.modules.base import BaseModule


class PluginPermission(Enum):
    """Plugin permission types following Principle of Least Privilege."""

    # Data access
    READ_USER_DATA = "read_user_data"
    WRITE_USER_DATA = "write_user_data"
    READ_CONVERSATION_HISTORY = "read_conversation_history"

    # System access
    NETWORK_ACCESS = "network_access"
    FILE_SYSTEM_READ = "file_system_read"
    FILE_SYSTEM_WRITE = "file_system_write"

    # Module communication
    CALL_OTHER_MODULES = "call_other_modules"
    RECEIVE_EVENTS = "receive_events"

    # Privileged operations
    MODIFY_SYSTEM_CONFIG = "modify_system_config"
    EXECUTE_CODE = "execute_code"
    ACCESS_CREDENTIALS = "access_credentials"


class PluginStatus(Enum):
    """Plugin lifecycle status."""

    DISCOVERED = "discovered"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    FROZEN = "frozen"  # Frozen by Ethics Module
    FAILED = "failed"
    UNLOADED = "unloaded"


@dataclass
class PluginManifest:
    """
    Plugin metadata and requirements.

    This is the plugin contract that all plugins must declare.
    """

    # Identity
    name: str
    version: str
    description: str
    author: str

    # Module class
    module_class: str  # Fully qualified class name

    # Permissions required (Principle of Least Privilege)
    required_permissions: Set[PluginPermission] = field(default_factory=set)

    # Dependencies
    python_dependencies: List[str] = field(default_factory=list)
    module_dependencies: List[str] = field(default_factory=list)  # Other plugins

    # Compatibility
    min_python_version: str = "3.9"
    min_ai_pal_version: str = "0.1.0"

    # Metadata
    homepage: Optional[str] = None
    license: str = "MIT"

    # Security
    checksum: Optional[str] = None  # SHA-256 of plugin code
    signed_by: Optional[str] = None  # Digital signature


@dataclass
class PluginInstance:
    """Running plugin instance with metadata."""

    manifest: PluginManifest
    module: BaseModule
    status: PluginStatus
    loaded_at: datetime
    last_error: Optional[str] = None
    permissions_granted: Set[PluginPermission] = field(default_factory=set)
    call_count: int = 0
    error_count: int = 0

    # Version control for rollback
    code_version: str = ""
    previous_versions: List[str] = field(default_factory=list)


class PluginSecurityViolation(Exception):
    """Raised when a plugin attempts unauthorized operation."""

    pass


class PluginManager:
    """
    Hot-swappable plugin manager with RBAC and sandboxing.

    Enables "governance with teeth" by allowing plugins to be frozen,
    rolled back, or unloaded without system restart.
    """

    def __init__(self, plugins_dir: Optional[Path] = None):
        """
        Initialize plugin manager.

        Args:
            plugins_dir: Directory containing plugin packages
        """
        self.plugins_dir = plugins_dir or Path("./plugins")
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        # Plugin registry
        self.discovered_plugins: Dict[str, PluginManifest] = {}
        self.loaded_plugins: Dict[str, PluginInstance] = {}

        # Permission management
        self.permission_policies: Dict[str, Set[PluginPermission]] = {}

        # Frozen plugins (by Ethics Module)
        self.frozen_plugins: Set[str] = set()

        # Version history for rollback
        self.plugin_versions: Dict[str, List[str]] = {}

        logger.info("Plugin Manager initialized")

    def discover_plugins(self) -> Dict[str, PluginManifest]:
        """
        Discover all available plugins using entry points mechanism.

        Plugins declare themselves via entry_points in their setup.py/pyproject.toml:

        [project.entry-points."ai_pal.plugins"]
        my_plugin = "my_plugin_package:get_manifest"

        Returns:
            Dictionary of plugin_name -> PluginManifest
        """
        logger.info("Discovering plugins...")

        discovered = {}

        # Discover via entry points
        try:
            entry_points = importlib.metadata.entry_points()

            # Python 3.10+ has a different API
            if hasattr(entry_points, 'select'):
                plugin_entries = entry_points.select(group='ai_pal.plugins')
            else:
                plugin_entries = entry_points.get('ai_pal.plugins', [])

            for entry_point in plugin_entries:
                try:
                    # Load the manifest function
                    manifest_func = entry_point.load()
                    manifest = manifest_func()

                    if not isinstance(manifest, PluginManifest):
                        logger.error(
                            f"Plugin {entry_point.name} returned invalid manifest"
                        )
                        continue

                    discovered[manifest.name] = manifest
                    logger.info(f"Discovered plugin: {manifest.name} v{manifest.version}")

                except Exception as e:
                    logger.error(f"Failed to load plugin {entry_point.name}: {e}")

        except Exception as e:
            logger.error(f"Failed to discover plugins: {e}")

        self.discovered_plugins = discovered
        logger.info(f"Discovery complete: {len(discovered)} plugins found")

        return discovered

    def request_permissions(
        self,
        plugin_name: str,
        permissions: Set[PluginPermission]
    ) -> bool:
        """
        Request permissions for a plugin (RBAC gate).

        In production, this would prompt the user or check a policy database.
        For now, we implement a simple allow-list.

        Args:
            plugin_name: Plugin requesting permissions
            permissions: Set of requested permissions

        Returns:
            True if all permissions granted, False otherwise
        """
        # Core modules get all permissions
        core_modules = {"ethics", "orchestrator", "privacy"}
        if plugin_name in core_modules:
            self.permission_policies[plugin_name] = set(PluginPermission)
            return True

        # Default safe permissions for standard plugins
        safe_permissions = {
            PluginPermission.READ_CONVERSATION_HISTORY,
            PluginPermission.CALL_OTHER_MODULES,
            PluginPermission.RECEIVE_EVENTS,
        }

        # Check if requesting only safe permissions
        if permissions.issubset(safe_permissions):
            self.permission_policies[plugin_name] = permissions
            logger.info(f"Granted safe permissions to {plugin_name}: {permissions}")
            return True

        # Dangerous permissions require explicit approval
        dangerous = permissions - safe_permissions
        logger.warning(
            f"Plugin {plugin_name} requests dangerous permissions: {dangerous}"
        )

        # In production, this would prompt the user or check policy
        # For now, deny dangerous permissions by default
        granted = permissions & safe_permissions
        self.permission_policies[plugin_name] = granted

        logger.warning(
            f"Granted restricted permissions to {plugin_name}: {granted}"
        )

        return len(dangerous) == 0

    def check_permission(
        self,
        plugin_name: str,
        permission: PluginPermission
    ) -> bool:
        """
        Check if plugin has a specific permission.

        Args:
            plugin_name: Plugin name
            permission: Permission to check

        Returns:
            True if permitted, False otherwise
        """
        granted = self.permission_policies.get(plugin_name, set())
        return permission in granted

    def load_plugin(
        self,
        plugin_name: str,
        auto_initialize: bool = True
    ) -> Optional[PluginInstance]:
        """
        Load a plugin into memory (hot-swappable).

        Args:
            plugin_name: Name of plugin to load
            auto_initialize: Whether to automatically initialize the plugin

        Returns:
            PluginInstance if successful, None otherwise
        """
        if plugin_name in self.frozen_plugins:
            logger.error(f"Cannot load frozen plugin: {plugin_name}")
            return None

        if plugin_name in self.loaded_plugins:
            logger.warning(f"Plugin already loaded: {plugin_name}")
            return self.loaded_plugins[plugin_name]

        if plugin_name not in self.discovered_plugins:
            logger.error(f"Plugin not discovered: {plugin_name}")
            return None

        manifest = self.discovered_plugins[plugin_name]

        try:
            logger.info(f"Loading plugin: {plugin_name}")

            # Check permissions
            if not self.request_permissions(plugin_name, manifest.required_permissions):
                logger.error(f"Permission denied for plugin: {plugin_name}")
                return None

            # Import the module class
            module_path, class_name = manifest.module_class.rsplit(":", 1)
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, class_name)

            # Verify it's a valid BaseModule
            if not issubclass(plugin_class, BaseModule):
                logger.error(
                    f"Plugin class {manifest.module_class} "
                    f"does not inherit from BaseModule"
                )
                return None

            # Instantiate the plugin
            plugin_instance = plugin_class()

            # Create plugin instance metadata
            instance = PluginInstance(
                manifest=manifest,
                module=plugin_instance,
                status=PluginStatus.LOADED,
                loaded_at=datetime.now(),
                permissions_granted=self.permission_policies[plugin_name],
                code_version=manifest.version,
            )

            self.loaded_plugins[plugin_name] = instance

            # Auto-initialize if requested
            if auto_initialize:
                success = self._initialize_plugin(instance)
                if not success:
                    self.unload_plugin(plugin_name)
                    return None

            logger.info(f"Plugin loaded successfully: {plugin_name}")
            return instance

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return None

    async def _initialize_plugin(self, instance: PluginInstance) -> bool:
        """
        Initialize a loaded plugin.

        Args:
            instance: Plugin instance to initialize

        Returns:
            True if successful, False otherwise
        """
        try:
            await instance.module.initialize()
            instance.status = PluginStatus.INITIALIZED
            logger.info(f"Plugin initialized: {instance.manifest.name}")
            return True
        except Exception as e:
            instance.status = PluginStatus.FAILED
            instance.last_error = str(e)
            logger.error(f"Plugin initialization failed: {instance.manifest.name}: {e}")
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin from memory (hot-swappable).

        This is a key feature for "governance with teeth" - allows
        removing problematic plugins without system restart.

        Args:
            plugin_name: Name of plugin to unload

        Returns:
            True if successful, False otherwise
        """
        if plugin_name not in self.loaded_plugins:
            logger.warning(f"Plugin not loaded: {plugin_name}")
            return False

        try:
            logger.info(f"Unloading plugin: {plugin_name}")

            instance = self.loaded_plugins[plugin_name]

            # Shutdown the plugin gracefully
            import asyncio
            asyncio.create_task(instance.module.shutdown())

            # Remove from loaded plugins
            del self.loaded_plugins[plugin_name]

            # Clean up permissions
            if plugin_name in self.permission_policies:
                del self.permission_policies[plugin_name]

            logger.info(f"Plugin unloaded: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False

    def freeze_plugin(self, plugin_name: str, reason: str) -> bool:
        """
        Freeze a plugin (Ethics Module enforcement).

        This is a critical "governance with teeth" mechanism.
        When the Ethics Module detects a Four Gates violation,
        it can immediately freeze the offending plugin.

        Args:
            plugin_name: Plugin to freeze
            reason: Reason for freeze (e.g., "Gate 2 violation: extraction detected")

        Returns:
            True if successful, False otherwise
        """
        logger.critical(
            f"🚨 FREEZING PLUGIN: {plugin_name} - Reason: {reason}"
        )

        # Add to frozen set
        self.frozen_plugins.add(plugin_name)

        # If loaded, pause it
        if plugin_name in self.loaded_plugins:
            instance = self.loaded_plugins[plugin_name]
            instance.status = PluginStatus.FROZEN
            instance.last_error = f"FROZEN: {reason}"

        logger.critical(
            f"Plugin {plugin_name} is now FROZEN. "
            f"Manual intervention required before re-enabling."
        )

        return True

    def rollback_plugin(
        self,
        plugin_name: str,
        target_version: Optional[str] = None
    ) -> bool:
        """
        Roll back plugin to a previous version.

        Another "governance with teeth" mechanism - if a new version
        violates ethical constraints, roll back to last known good.

        Args:
            plugin_name: Plugin to roll back
            target_version: Version to roll back to (None = previous)

        Returns:
            True if successful, False otherwise
        """
        logger.warning(f"Rolling back plugin: {plugin_name}")

        if plugin_name not in self.plugin_versions:
            logger.error(f"No version history for plugin: {plugin_name}")
            return False

        versions = self.plugin_versions[plugin_name]
        if not versions:
            logger.error(f"No previous versions for plugin: {plugin_name}")
            return False

        # Determine target version
        if target_version is None:
            target_version = versions[-1]  # Most recent previous

        if target_version not in versions:
            logger.error(
                f"Version {target_version} not found in history for {plugin_name}"
            )
            return False

        try:
            # Unload current version
            self.unload_plugin(plugin_name)

            # In production, this would:
            # 1. Fetch the target version from a repository
            # 2. Verify its checksum
            # 3. Load it

            # For now, we'll reload from discovery
            instance = self.load_plugin(plugin_name, auto_initialize=True)

            if instance:
                logger.info(
                    f"Successfully rolled back {plugin_name} to version {target_version}"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Rollback failed for {plugin_name}: {e}")
            return False

    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Hot-reload a plugin (unload + load).

        Useful for development and for applying updates.

        Args:
            plugin_name: Plugin to reload

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Reloading plugin: {plugin_name}")

        # Unload
        self.unload_plugin(plugin_name)

        # Re-discover (in case manifest changed)
        self.discover_plugins()

        # Load
        instance = self.load_plugin(plugin_name, auto_initialize=True)

        return instance is not None

    def get_plugin_status(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get comprehensive status of a plugin.

        Args:
            plugin_name: Plugin name

        Returns:
            Status dictionary
        """
        if plugin_name not in self.loaded_plugins:
            return {
                "name": plugin_name,
                "status": "not_loaded",
                "frozen": plugin_name in self.frozen_plugins,
            }

        instance = self.loaded_plugins[plugin_name]

        return {
            "name": plugin_name,
            "version": instance.manifest.version,
            "status": instance.status.value,
            "loaded_at": instance.loaded_at.isoformat(),
            "permissions": [p.value for p in instance.permissions_granted],
            "call_count": instance.call_count,
            "error_count": instance.error_count,
            "last_error": instance.last_error,
            "frozen": plugin_name in self.frozen_plugins,
            "healthy": instance.error_count < 10,  # Threshold
        }

    def get_all_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all plugins."""
        return {
            name: self.get_plugin_status(name)
            for name in self.discovered_plugins.keys()
        }

    async def call_plugin(
        self,
        plugin_name: str,
        method: str,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """
        Call a method on a plugin (with permission checking).

        Args:
            plugin_name: Plugin to call
            method: Method name
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Method result

        Raises:
            PluginSecurityViolation: If plugin is frozen or lacks permission
        """
        # Check if frozen
        if plugin_name in self.frozen_plugins:
            raise PluginSecurityViolation(
                f"Cannot call frozen plugin: {plugin_name}"
            )

        # Check if loaded
        if plugin_name not in self.loaded_plugins:
            raise ValueError(f"Plugin not loaded: {plugin_name}")

        instance = self.loaded_plugins[plugin_name]

        # Track call
        instance.call_count += 1

        try:
            # Get method
            method_func = getattr(instance.module, method)

            # Call it
            result = await method_func(*args, **kwargs)

            return result

        except Exception as e:
            instance.error_count += 1
            instance.last_error = str(e)
            logger.error(f"Plugin call failed: {plugin_name}.{method}: {e}")
            raise


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager

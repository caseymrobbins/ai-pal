"""
Plugin Registry

Manages loaded plugins and provides access to them.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePlugin, PluginType, PluginState
from .discovery import PluginManifest, PluginDiscovery
from .loader import PluginLoader, PluginLoadError

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central registry for managing plugins.

    Coordinates plugin discovery, loading, initialization, and lifecycle management.
    """

    def __init__(self):
        self.discovery = PluginDiscovery()
        self.loader = PluginLoader()
        self._plugins: Dict[str, BasePlugin] = {}
        self._manifests: Dict[str, PluginManifest] = {}
        self._plugin_configs: Dict[str, Dict[str, Any]] = {}

    async def discover_and_load_all(self, auto_initialize: bool = False) -> Dict[str, bool]:
        """
        Discover and load all available plugins.

        Args:
            auto_initialize: If True, automatically initialize plugins after loading

        Returns:
            Dictionary mapping plugin names to success status
        """
        logger.info("Discovering plugins...")
        manifests = self.discovery.discover()

        results = {}
        for name, manifest in manifests.items():
            try:
                await self.load_plugin(name, auto_initialize=auto_initialize)
                results[name] = True
            except Exception as e:
                logger.error(f"Failed to load plugin '{name}': {e}")
                results[name] = False

        logger.info(
            f"Loaded {sum(results.values())}/{len(results)} plugins successfully"
        )
        return results

    async def load_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None,
        auto_initialize: bool = False
    ) -> BasePlugin:
        """
        Load a specific plugin by name.

        Args:
            plugin_name: Name of the plugin to load
            config: Optional configuration for the plugin
            auto_initialize: If True, automatically initialize after loading

        Returns:
            Loaded plugin instance

        Raises:
            PluginLoadError: If loading fails
        """
        # Check if already loaded
        if plugin_name in self._plugins:
            logger.warning(f"Plugin '{plugin_name}' is already loaded")
            return self._plugins[plugin_name]

        # Get manifest
        manifest = self.discovery.get_plugin_by_name(plugin_name)
        if not manifest:
            raise PluginLoadError(f"Plugin '{plugin_name}' not found")

        # Load plugin
        plugin = self.loader.load_plugin(manifest)

        # Store plugin and manifest
        self._plugins[plugin_name] = plugin
        self._manifests[plugin_name] = manifest

        if config:
            self._plugin_configs[plugin_name] = config

        # Auto-initialize if requested
        if auto_initialize:
            await self.initialize_plugin(plugin_name, config or {})

        return plugin

    async def initialize_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize a loaded plugin.

        Args:
            plugin_name: Name of the plugin to initialize
            config: Configuration for the plugin

        Raises:
            ValueError: If plugin not loaded
            Exception: If initialization fails
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_name}' not loaded")

        if plugin.state not in [PluginState.LOADED, PluginState.STOPPED]:
            logger.warning(
                f"Plugin '{plugin_name}' is in state {plugin.state.value}, "
                f"skipping initialization"
            )
            return

        try:
            logger.info(f"Initializing plugin: {plugin_name}")
            plugin._set_state(PluginState.LOADING)

            # Use provided config or stored config
            plugin_config = config or self._plugin_configs.get(plugin_name, {})

            # Validate config
            if not plugin.validate_config(plugin_config):
                raise ValueError(f"Invalid configuration for plugin '{plugin_name}'")

            # Initialize plugin
            await plugin.initialize(plugin_config)
            plugin._set_state(PluginState.INITIALIZED)

            logger.info(f"Successfully initialized plugin: {plugin_name}")

        except Exception as e:
            logger.error(f"Failed to initialize plugin '{plugin_name}': {e}")
            plugin._set_state(PluginState.ERROR, e)
            raise

    async def start_plugin(self, plugin_name: str) -> None:
        """
        Start an initialized plugin.

        Args:
            plugin_name: Name of the plugin to start

        Raises:
            ValueError: If plugin not initialized
            Exception: If start fails
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_name}' not loaded")

        if plugin.state != PluginState.INITIALIZED:
            raise ValueError(
                f"Plugin '{plugin_name}' must be initialized before starting "
                f"(current state: {plugin.state.value})"
            )

        try:
            logger.info(f"Starting plugin: {plugin_name}")
            await plugin.start()
            plugin._set_state(PluginState.RUNNING)
            logger.info(f"Successfully started plugin: {plugin_name}")

        except Exception as e:
            logger.error(f"Failed to start plugin '{plugin_name}': {e}")
            plugin._set_state(PluginState.ERROR, e)
            raise

    async def stop_plugin(self, plugin_name: str) -> None:
        """
        Stop a running plugin.

        Args:
            plugin_name: Name of the plugin to stop

        Raises:
            ValueError: If plugin not loaded
            Exception: If stop fails
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_name}' not loaded")

        if plugin.state != PluginState.RUNNING:
            logger.warning(
                f"Plugin '{plugin_name}' is not running (state: {plugin.state.value})"
            )
            return

        try:
            logger.info(f"Stopping plugin: {plugin_name}")
            await plugin.stop()
            plugin._set_state(PluginState.STOPPED)
            logger.info(f"Successfully stopped plugin: {plugin_name}")

        except Exception as e:
            logger.error(f"Failed to stop plugin '{plugin_name}': {e}")
            plugin._set_state(PluginState.ERROR, e)
            raise

    async def unload_plugin(self, plugin_name: str) -> None:
        """
        Unload a plugin.

        Args:
            plugin_name: Name of the plugin to unload

        Raises:
            ValueError: If plugin not loaded
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise ValueError(f"Plugin '{plugin_name}' not loaded")

        # Stop if running
        if plugin.state == PluginState.RUNNING:
            await self.stop_plugin(plugin_name)

        # Unload
        self.loader.unload_plugin(plugin)

        # Remove from registry
        del self._plugins[plugin_name]
        if plugin_name in self._manifests:
            del self._manifests[plugin_name]
        if plugin_name in self._plugin_configs:
            del self._plugin_configs[plugin_name]

        logger.info(f"Unloaded plugin: {plugin_name}")

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get a loaded plugin by name"""
        return self._plugins.get(plugin_name)

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """Get all loaded plugins of a specific type"""
        return [
            plugin
            for name, plugin in self._plugins.items()
            if self._manifests[name].metadata.plugin_type == plugin_type
        ]

    def list_loaded_plugins(self) -> List[str]:
        """Get list of all loaded plugin names"""
        return list(self._plugins.keys())

    def list_available_plugins(self) -> List[str]:
        """Get list of all available (discovered but not necessarily loaded) plugin names"""
        return list(self.discovery._discovered_plugins.keys())

    async def health_check_all(self) -> Dict[str, bool]:
        """
        Perform health check on all running plugins.

        Returns:
            Dictionary mapping plugin names to health status
        """
        results = {}

        for name, plugin in self._plugins.items():
            if plugin.state == PluginState.RUNNING:
                try:
                    is_healthy = await plugin.health_check()
                    results[name] = is_healthy

                    if not is_healthy:
                        logger.warning(f"Plugin '{name}' failed health check")

                except Exception as e:
                    logger.error(f"Health check failed for plugin '{name}': {e}")
                    results[name] = False
                    plugin._set_state(PluginState.ERROR, e)

        return results

    def get_registry_status(self) -> Dict[str, Any]:
        """Get overall registry status"""
        return {
            "total_discovered": len(self.discovery._discovered_plugins),
            "total_loaded": len(self._plugins),
            "plugins_by_state": self._get_plugins_by_state(),
            "plugins_by_type": self._get_plugins_by_type_count(),
        }

    def _get_plugins_by_state(self) -> Dict[str, int]:
        """Get count of plugins by state"""
        counts: Dict[str, int] = {}
        for plugin in self._plugins.values():
            state = plugin.state.value
            counts[state] = counts.get(state, 0) + 1
        return counts

    def _get_plugins_by_type_count(self) -> Dict[str, int]:
        """Get count of plugins by type"""
        counts: Dict[str, int] = {}
        for name in self._plugins:
            manifest = self._manifests[name]
            plugin_type = manifest.metadata.plugin_type.value
            counts[plugin_type] = counts.get(plugin_type, 0) + 1
        return counts

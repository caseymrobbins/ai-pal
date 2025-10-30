"""
Plugin Loader

Loads plugins from manifests by importing Python modules and instantiating plugin classes.
"""

import sys
import importlib.util
import logging
from pathlib import Path
from typing import Optional, Type, Dict, Any

from .base import BasePlugin, PluginState
from .discovery import PluginManifest

logger = logging.getLogger(__name__)


class PluginLoadError(Exception):
    """Raised when plugin loading fails"""
    pass


class PluginLoader:
    """
    Loads plugins from manifests.

    Handles dynamic import of plugin modules and instantiation of plugin classes.
    """

    def __init__(self):
        self._loaded_modules: Dict[str, Any] = {}

    def load_plugin(self, manifest: PluginManifest) -> BasePlugin:
        """
        Load a plugin from its manifest.

        Args:
            manifest: Plugin manifest containing metadata and entry point

        Returns:
            Instantiated plugin object

        Raises:
            PluginLoadError: If loading fails
        """
        plugin_name = manifest.metadata.name

        try:
            logger.info(f"Loading plugin: {plugin_name}")

            # Validate manifest
            if not manifest.is_valid:
                raise PluginLoadError(
                    f"Invalid manifest for plugin '{plugin_name}': {manifest.errors}"
                )

            # Import plugin module
            plugin_class = self._import_plugin_class(manifest)

            # Validate plugin class
            if not issubclass(plugin_class, BasePlugin):
                raise PluginLoadError(
                    f"Plugin class {plugin_class.__name__} must inherit from BasePlugin"
                )

            # Instantiate plugin
            plugin = plugin_class()
            plugin._set_state(PluginState.LOADED)

            # Validate metadata
            if plugin.metadata.name != manifest.metadata.name:
                logger.warning(
                    f"Plugin metadata name '{plugin.metadata.name}' doesn't match "
                    f"manifest name '{manifest.metadata.name}'"
                )

            logger.info(f"Successfully loaded plugin: {plugin_name}")
            return plugin

        except Exception as e:
            logger.error(f"Failed to load plugin '{plugin_name}': {e}")
            raise PluginLoadError(f"Failed to load plugin '{plugin_name}': {e}") from e

    def _import_plugin_class(self, manifest: PluginManifest) -> Type[BasePlugin]:
        """
        Import and return the plugin class from the manifest.

        Args:
            manifest: Plugin manifest

        Returns:
            Plugin class

        Raises:
            PluginLoadError: If import fails
        """
        entry_point = manifest.entry_point
        plugin_path = manifest.path

        try:
            # Parse entry point (e.g., "my_plugin.MyPlugin")
            if '.' not in entry_point:
                raise PluginLoadError(
                    f"Invalid entry point '{entry_point}'. "
                    f"Expected format: 'module.ClassName'"
                )

            module_name, class_name = entry_point.rsplit('.', 1)

            # Add plugin directory to Python path
            if str(plugin_path) not in sys.path:
                sys.path.insert(0, str(plugin_path))

            # Check if module is already loaded
            if module_name in self._loaded_modules:
                module = self._loaded_modules[module_name]
            else:
                # Import the module
                module = self._import_module(module_name, plugin_path)
                self._loaded_modules[module_name] = module

            # Get the plugin class
            if not hasattr(module, class_name):
                raise PluginLoadError(
                    f"Module '{module_name}' has no class '{class_name}'"
                )

            plugin_class = getattr(module, class_name)
            return plugin_class

        except PluginLoadError:
            raise
        except Exception as e:
            raise PluginLoadError(f"Failed to import plugin class: {e}") from e

    def _import_module(self, module_name: str, plugin_path: Path) -> Any:
        """
        Import a Python module from the plugin path.

        Args:
            module_name: Name of the module to import
            plugin_path: Path to the plugin directory

        Returns:
            Imported module

        Raises:
            PluginLoadError: If import fails
        """
        try:
            # Try standard import first
            module = importlib.import_module(module_name)
            return module

        except ImportError:
            # If standard import fails, try loading from file
            module_file = plugin_path / f"{module_name.replace('.', '/')}.py"

            if not module_file.exists():
                # Try __init__.py for package
                module_file = plugin_path / module_name.replace('.', '/') / "__init__.py"

            if not module_file.exists():
                raise PluginLoadError(
                    f"Module file not found: {module_file}"
                )

            # Load module from file
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            if spec is None or spec.loader is None:
                raise PluginLoadError(
                    f"Failed to create module spec for {module_file}"
                )

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            return module

    def unload_plugin(self, plugin: BasePlugin) -> None:
        """
        Unload a plugin and clean up resources.

        Args:
            plugin: Plugin to unload
        """
        try:
            logger.info(f"Unloading plugin: {plugin.metadata.name}")

            # Stop the plugin if running
            if plugin.state in [PluginState.RUNNING, PluginState.INITIALIZED]:
                import asyncio
                try:
                    asyncio.run(plugin.stop())
                except Exception as e:
                    logger.error(f"Error stopping plugin during unload: {e}")

            plugin._set_state(PluginState.UNLOADED)
            logger.info(f"Successfully unloaded plugin: {plugin.metadata.name}")

        except Exception as e:
            logger.error(f"Error unloading plugin: {e}")
            plugin._set_state(PluginState.ERROR, e)

    def reload_plugin(self, manifest: PluginManifest, old_plugin: BasePlugin) -> BasePlugin:
        """
        Reload a plugin (unload and load again).

        Args:
            manifest: Plugin manifest
            old_plugin: Previously loaded plugin

        Returns:
            Newly loaded plugin instance

        Raises:
            PluginLoadError: If reload fails
        """
        logger.info(f"Reloading plugin: {manifest.metadata.name}")

        # Unload old plugin
        self.unload_plugin(old_plugin)

        # Remove cached module to force reload
        entry_point = manifest.entry_point
        if '.' in entry_point:
            module_name = entry_point.rsplit('.', 1)[0]
            if module_name in self._loaded_modules:
                del self._loaded_modules[module_name]
            if module_name in sys.modules:
                del sys.modules[module_name]

        # Load new plugin
        return self.load_plugin(manifest)

"""
Plugin Discovery System

Discovers plugins in specified directories by scanning for plugin manifests.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .base import PluginType, PluginMetadata

logger = logging.getLogger(__name__)


@dataclass
class PluginManifest:
    """Plugin manifest information"""
    path: Path
    metadata: PluginMetadata
    entry_point: str  # Python path to plugin class (e.g., "my_plugin.MyPlugin")
    is_valid: bool = True
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class PluginDiscovery:
    """
    Discovers plugins by scanning directories for plugin manifests.

    Plugin manifests are JSON files named 'plugin.json' with the following structure:
    {
        "name": "my-plugin",
        "version": "1.0.0",
        "plugin_type": "model_provider",
        "author": "Author Name",
        "description": "Plugin description",
        "entry_point": "my_plugin.MyPlugin",
        "dependencies": ["dep1", "dep2"],
        "min_system_version": "0.1.0",
        "max_system_version": "1.0.0",
        "homepage": "https://example.com",
        "license": "MIT"
    }
    """

    def __init__(self, plugin_dirs: Optional[List[Path]] = None):
        """
        Initialize plugin discovery.

        Args:
            plugin_dirs: List of directories to search for plugins.
                        If None, uses default plugin directories.
        """
        self.plugin_dirs = plugin_dirs or self._get_default_plugin_dirs()
        self._discovered_plugins: Dict[str, PluginManifest] = {}

    def _get_default_plugin_dirs(self) -> List[Path]:
        """Get default plugin directories"""
        default_dirs = [
            Path.cwd() / "plugins",  # Current directory
            Path.home() / ".ai_pal" / "plugins",  # User plugins
            Path(__file__).parent.parent / "plugins_builtin",  # Built-in plugins
        ]
        return [d for d in default_dirs if d.exists() or d == default_dirs[0]]

    def discover(self) -> Dict[str, PluginManifest]:
        """
        Discover all plugins in plugin directories.

        Returns:
            Dictionary mapping plugin names to their manifests
        """
        self._discovered_plugins.clear()

        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                logger.warning(f"Plugin directory does not exist: {plugin_dir}")
                continue

            logger.info(f"Scanning for plugins in: {plugin_dir}")
            self._scan_directory(plugin_dir)

        logger.info(f"Discovered {len(self._discovered_plugins)} plugins")
        return self._discovered_plugins

    def _scan_directory(self, directory: Path) -> None:
        """Scan a directory for plugin manifests"""
        # Look for plugin.json files
        manifest_files = list(directory.rglob("plugin.json"))

        for manifest_file in manifest_files:
            try:
                manifest = self._load_manifest(manifest_file)
                if manifest:
                    if manifest.metadata.name in self._discovered_plugins:
                        logger.warning(
                            f"Duplicate plugin name '{manifest.metadata.name}' found at "
                            f"{manifest_file}, skipping. First found at "
                            f"{self._discovered_plugins[manifest.metadata.name].path}"
                        )
                        continue

                    self._discovered_plugins[manifest.metadata.name] = manifest
                    logger.info(
                        f"Discovered plugin: {manifest.metadata.name} v{manifest.metadata.version} "
                        f"({manifest.metadata.plugin_type.value})"
                    )
            except Exception as e:
                logger.error(f"Error loading manifest from {manifest_file}: {e}")

    def _load_manifest(self, manifest_file: Path) -> Optional[PluginManifest]:
        """Load and parse a plugin manifest file"""
        try:
            with open(manifest_file, 'r') as f:
                data = json.load(f)

            # Validate required fields
            required_fields = ["name", "version", "plugin_type", "author", "description", "entry_point"]
            errors = []

            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")

            if errors:
                logger.error(f"Invalid manifest {manifest_file}: {errors}")
                return None

            # Parse plugin type
            try:
                plugin_type = PluginType(data["plugin_type"])
            except ValueError:
                errors.append(f"Invalid plugin_type: {data['plugin_type']}")
                logger.error(f"Invalid plugin_type in {manifest_file}: {data['plugin_type']}")
                return None

            # Create metadata
            metadata = PluginMetadata(
                name=data["name"],
                version=data["version"],
                plugin_type=plugin_type,
                author=data["author"],
                description=data["description"],
                dependencies=data.get("dependencies", []),
                min_system_version=data.get("min_system_version", "0.1.0"),
                max_system_version=data.get("max_system_version"),
                homepage=data.get("homepage"),
                license=data.get("license", "MIT"),
            )

            # Create manifest
            manifest = PluginManifest(
                path=manifest_file.parent,  # Plugin directory
                metadata=metadata,
                entry_point=data["entry_point"],
                is_valid=len(errors) == 0,
                errors=errors,
            )

            return manifest

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in manifest {manifest_file}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading manifest {manifest_file}: {e}")
            return None

    def get_plugin_by_name(self, name: str) -> Optional[PluginManifest]:
        """Get discovered plugin by name"""
        return self._discovered_plugins.get(name)

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginManifest]:
        """Get all discovered plugins of a specific type"""
        return [
            manifest
            for manifest in self._discovered_plugins.values()
            if manifest.metadata.plugin_type == plugin_type
        ]

    def list_all_plugins(self) -> List[PluginManifest]:
        """Get list of all discovered plugins"""
        return list(self._discovered_plugins.values())

    def add_plugin_dir(self, directory: Path) -> None:
        """Add a new plugin directory to search"""
        if directory not in self.plugin_dirs:
            self.plugin_dirs.append(directory)
            logger.info(f"Added plugin directory: {directory}")

    def remove_plugin_dir(self, directory: Path) -> None:
        """Remove a plugin directory from search"""
        if directory in self.plugin_dirs:
            self.plugin_dirs.remove(directory)
            logger.info(f"Removed plugin directory: {directory}")

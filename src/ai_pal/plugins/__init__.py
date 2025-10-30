"""
Plugin System for AI-PAL

Provides extensible plugin architecture for adding new capabilities to the system.
"""

from .base import (
    BasePlugin,
    PluginMetadata,
    PluginType,
    PluginState,
    ModelProviderPlugin,
    MonitoringPlugin,
    GatePlugin,
    IntegrationPlugin,
)
from .loader import PluginLoader, PluginLoadError
from .registry import PluginRegistry
from .discovery import PluginDiscovery, PluginManifest
from .sandbox import PluginSandbox, SandboxLimits, SandboxManager
from .dependencies import DependencyManager, VersionChecker, DependencyResolver

__all__ = [
    # Base classes
    "BasePlugin",
    "PluginMetadata",
    "PluginType",
    "PluginState",
    "ModelProviderPlugin",
    "MonitoringPlugin",
    "GatePlugin",
    "IntegrationPlugin",

    # Discovery and loading
    "PluginDiscovery",
    "PluginManifest",
    "PluginLoader",
    "PluginLoadError",
    "PluginRegistry",

    # Sandbox
    "PluginSandbox",
    "SandboxLimits",
    "SandboxManager",

    # Dependencies
    "DependencyManager",
    "VersionChecker",
    "DependencyResolver",
]

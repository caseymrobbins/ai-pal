"""
Base Plugin Classes and Interfaces

Defines the core plugin interface and metadata structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime


class PluginType(Enum):
    """Types of plugins supported by the system"""
    MODEL_PROVIDER = "model_provider"  # New LLM providers
    MONITORING = "monitoring"  # Custom monitoring systems
    GATE = "gate"  # Custom validation gates
    FFE_COMPONENT = "ffe_component"  # FFE extensions
    INTERFACE = "interface"  # User interface extensions
    INTEGRATION = "integration"  # Third-party integrations
    UTILITY = "utility"  # General utilities


@dataclass
class PluginMetadata:
    """Metadata describing a plugin"""
    name: str
    version: str
    plugin_type: PluginType
    author: str
    description: str
    dependencies: List[str] = None
    min_system_version: str = "0.1.0"
    max_system_version: Optional[str] = None
    homepage: Optional[str] = None
    license: str = "MIT"

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "version": self.version,
            "plugin_type": self.plugin_type.value,
            "author": self.author,
            "description": self.description,
            "dependencies": self.dependencies,
            "min_system_version": self.min_system_version,
            "max_system_version": self.max_system_version,
            "homepage": self.homepage,
            "license": self.license,
        }


class PluginState(Enum):
    """Plugin lifecycle states"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    DISABLED = "disabled"


class BasePlugin(ABC):
    """
    Base class for all plugins.

    All plugins must inherit from this class and implement the required methods.
    """

    def __init__(self):
        self._state = PluginState.UNLOADED
        self._error: Optional[Exception] = None
        self._loaded_at: Optional[datetime] = None
        self._initialized_at: Optional[datetime] = None

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata"""
        pass

    @property
    def state(self) -> PluginState:
        """Get current plugin state"""
        return self._state

    @property
    def error(self) -> Optional[Exception]:
        """Get error if plugin is in error state"""
        return self._error

    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the plugin with configuration.

        Args:
            config: Plugin-specific configuration dictionary

        Raises:
            Exception: If initialization fails
        """
        pass

    @abstractmethod
    async def start(self) -> None:
        """
        Start the plugin.

        Called after initialization to activate the plugin.

        Raises:
            Exception: If start fails
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the plugin.

        Should perform cleanup and release resources.

        Raises:
            Exception: If stop fails
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if plugin is healthy and functioning.

        Returns:
            True if healthy, False otherwise
        """
        pass

    def get_capabilities(self) -> List[str]:
        """
        Return list of capabilities provided by this plugin.

        Override to declare specific capabilities.

        Returns:
            List of capability names
        """
        return []

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate plugin configuration.

        Override to implement custom validation.

        Args:
            config: Configuration to validate

        Returns:
            True if valid, False otherwise
        """
        return True

    def _set_state(self, state: PluginState, error: Optional[Exception] = None):
        """Internal method to update plugin state"""
        self._state = state
        self._error = error

        if state == PluginState.LOADED:
            self._loaded_at = datetime.now()
        elif state == PluginState.INITIALIZED:
            self._initialized_at = datetime.now()

    def get_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        return {
            "metadata": self.metadata.to_dict(),
            "state": self._state.value,
            "error": str(self._error) if self._error else None,
            "loaded_at": self._loaded_at.isoformat() if self._loaded_at else None,
            "initialized_at": self._initialized_at.isoformat() if self._initialized_at else None,
            "capabilities": self.get_capabilities(),
        }


class ModelProviderPlugin(BasePlugin):
    """Base class for model provider plugins"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response from model.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Provider-specific parameters

        Returns:
            Response dictionary with generated text and metadata
        """
        pass

    @abstractmethod
    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost in USD"""
        pass


class MonitoringPlugin(BasePlugin):
    """Base class for monitoring plugins"""

    @abstractmethod
    async def record_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record a monitoring event"""
        pass

    @abstractmethod
    async def get_metrics(self, metric_type: str, **filters) -> List[Dict[str, Any]]:
        """Retrieve metrics"""
        pass


class GatePlugin(BasePlugin):
    """Base class for gate validation plugins"""

    @abstractmethod
    async def validate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate request through gate.

        Args:
            context: Request context to validate

        Returns:
            Validation result with pass/fail and details
        """
        pass


class IntegrationPlugin(BasePlugin):
    """Base class for third-party integration plugins"""

    @abstractmethod
    async def connect(self, credentials: Dict[str, str]) -> bool:
        """Establish connection to external service"""
        pass

    @abstractmethod
    async def sync_data(self, direction: str, data: Any) -> Any:
        """Sync data with external service"""
        pass

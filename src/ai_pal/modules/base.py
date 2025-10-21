"""Base module interface for AI Pal modules."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger


@dataclass
class ModuleRequest:
    """Request to a module."""

    task: str
    context: Dict[str, Any]
    user_id: str
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class ModuleResponse:
    """Response from a module."""

    result: Any
    confidence: float
    metadata: Dict[str, Any]
    timestamp: datetime
    processing_time_ms: float


class BaseModule(ABC):
    """Base class for all AI Pal modules."""

    def __init__(self, name: str, description: str, version: str = "0.1.0"):
        """
        Initialize module.

        Args:
            name: Module name
            description: Module description
            version: Module version
        """
        self.name = name
        self.description = description
        self.version = version
        self.enabled = True
        self.initialized = False

        logger.info(f"Module '{name}' created (v{version})")

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the module. Called once on startup."""
        pass

    @abstractmethod
    async def process(self, request: ModuleRequest) -> ModuleResponse:
        """
        Process a request.

        Args:
            request: Module request

        Returns:
            Module response
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup resources. Called on system shutdown."""
        pass

    async def health_check(self) -> bool:
        """
        Check module health.

        Returns:
            True if healthy, False otherwise
        """
        return self.enabled and self.initialized

    def enable(self) -> None:
        """Enable the module."""
        self.enabled = True
        logger.info(f"Module '{self.name}' enabled")

    def disable(self) -> None:
        """Disable the module."""
        self.enabled = False
        logger.info(f"Module '{self.name}' disabled")

    def get_info(self) -> Dict[str, Any]:
        """
        Get module information.

        Returns:
            Module metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "initialized": self.initialized,
        }

    def __repr__(self) -> str:
        """String representation."""
        status = "enabled" if self.enabled else "disabled"
        return f"<{self.__class__.__name__} '{self.name}' ({status})>"

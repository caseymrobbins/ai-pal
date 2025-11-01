"""
Structured Logging System

Provides structured JSON logging with contextual data for production observability.
Built on top of loguru for ease of use.
"""

import sys
import json
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger as loguru_logger


class StructuredLogger:
    """
    Structured logger for production observability

    Uses loguru under the hood with JSON formatting and contextual data.
    """

    def __init__(self, name: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize structured logger

        Args:
            name: Logger name (usually module name)
            context: Default context to include in all logs
        """
        self.name = name
        self.context = context or {}
        self._logger = loguru_logger.bind(logger_name=name, **self.context)

    def _add_context(self, **kwargs) -> Dict[str, Any]:
        """Merge default context with additional context"""
        return {**self.context, **kwargs}

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._logger.bind(**kwargs).debug(message)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._logger.bind(**kwargs).info(message)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._logger.bind(**kwargs).warning(message)

    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message"""
        if exc_info:
            self._logger.bind(**kwargs).exception(message)
        else:
            self._logger.bind(**kwargs).error(message)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._logger.bind(**kwargs).critical(message)

    def with_context(self, **kwargs) -> "StructuredLogger":
        """Create new logger with additional context"""
        new_context = {**self.context, **kwargs}
        return StructuredLogger(self.name, new_context)


# Global logger registry
_loggers: Dict[str, StructuredLogger] = {}
_initialized = False


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = False
):
    """
    Setup logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logs
        json_format: Use JSON format for logs
    """
    global _initialized

    # Remove default handler
    loguru_logger.remove()

    # Format
    if json_format:
        # JSON format for production
        format_string = (
            '{"time": "{time:YYYY-MM-DD HH:mm:ss}", '
            '"level": "{level}", '
            '"logger": "{extra[logger_name]}", '
            '"message": "{message}", '
            '"extra": {extra}}'
        )
    else:
        # Human-readable format for development
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{extra[logger_name]: <20}</cyan> | "
            "<level>{message}</level>"
        )

    # Console handler
    loguru_logger.add(
        sys.stderr,
        format=format_string,
        level=log_level,
        colorize=not json_format,
        backtrace=True,
        diagnose=True,
    )

    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        loguru_logger.add(
            str(log_file),
            format=format_string,
            level=log_level,
            rotation="500 MB",
            retention="10 days",
            compression="zip",
            backtrace=True,
            diagnose=True,
        )

    _initialized = True
    loguru_logger.info(f"Logging initialized at {log_level} level")


def get_logger(name: str, **context) -> StructuredLogger:
    """
    Get or create a structured logger

    Args:
        name: Logger name (usually module name)
        **context: Default context for this logger

    Returns:
        StructuredLogger instance
    """
    global _initialized

    # Auto-initialize if not done
    if not _initialized:
        setup_logging()

    # Return existing or create new
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, context)

    return _loggers[name]


# Convenience function for backward compatibility
def get_logger_simple(name: str):
    """Get logger (backward compatible API)"""
    return get_logger(name)

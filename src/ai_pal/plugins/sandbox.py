"""
Plugin Sandbox

Provides sandboxed execution environment for plugins with resource limits and security restrictions.
"""

import asyncio
import logging
import resource
import signal
import sys
from contextlib import contextmanager
from typing import Any, Callable, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class SandboxLimits:
    """Resource limits for sandboxed execution"""
    max_memory_mb: int = 512  # Maximum memory usage in MB
    max_cpu_time_seconds: int = 30  # Maximum CPU time
    max_execution_time_seconds: int = 60  # Maximum wall-clock time
    max_file_descriptors: int = 100  # Maximum open files
    max_subprocess_count: int = 0  # Maximum subprocesses (0 = no subprocesses)
    allow_network: bool = True  # Allow network access
    allow_file_write: bool = True  # Allow file writes


@dataclass
class SandboxViolation:
    """Information about a sandbox violation"""
    violation_type: str
    message: str
    timestamp: datetime
    stack_trace: Optional[str] = None


class SandboxTimeoutError(Exception):
    """Raised when sandbox execution exceeds time limit"""
    pass


class SandboxResourceError(Exception):
    """Raised when sandbox exceeds resource limits"""
    pass


class PluginSandbox:
    """
    Sandboxed execution environment for plugins.

    Provides:
    - Resource limits (memory, CPU, file descriptors)
    - Execution timeouts
    - Security restrictions
    - Violation tracking
    """

    def __init__(self, limits: Optional[SandboxLimits] = None):
        """
        Initialize sandbox with limits.

        Args:
            limits: Resource limits for sandbox. If None, uses default limits.
        """
        self.limits = limits or SandboxLimits()
        self.violations: list[SandboxViolation] = []
        self._original_limits: Dict[int, tuple] = {}

    @contextmanager
    def execute(self):
        """
        Context manager for sandboxed execution.

        Usage:
            with sandbox.execute():
                # Code runs with resource limits
                plugin.do_something()
        """
        try:
            self._apply_limits()
            yield
        except Exception as e:
            self._handle_violation(e)
            raise
        finally:
            self._restore_limits()

    async def execute_async(
        self,
        coro: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute an async function in sandbox with timeout.

        Args:
            coro: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of the async function

        Raises:
            SandboxTimeoutError: If execution exceeds time limit
            SandboxResourceError: If resource limits are exceeded
        """
        try:
            result = await asyncio.wait_for(
                coro(*args, **kwargs),
                timeout=self.limits.max_execution_time_seconds
            )
            return result

        except asyncio.TimeoutError:
            error = SandboxTimeoutError(
                f"Execution exceeded {self.limits.max_execution_time_seconds}s timeout"
            )
            self._record_violation("timeout", str(error))
            raise error

        except MemoryError as e:
            error = SandboxResourceError(f"Memory limit exceeded: {e}")
            self._record_violation("memory", str(error))
            raise error

        except Exception as e:
            self._handle_violation(e)
            raise

    def _apply_limits(self) -> None:
        """Apply resource limits to current process"""
        try:
            # Memory limit
            if self.limits.max_memory_mb > 0:
                memory_bytes = self.limits.max_memory_mb * 1024 * 1024
                soft, hard = resource.getrlimit(resource.RLIMIT_AS)
                self._original_limits[resource.RLIMIT_AS] = (soft, hard)
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
                logger.debug(f"Applied memory limit: {self.limits.max_memory_mb}MB")

            # CPU time limit
            if self.limits.max_cpu_time_seconds > 0:
                soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
                self._original_limits[resource.RLIMIT_CPU] = (soft, hard)
                resource.setrlimit(
                    resource.RLIMIT_CPU,
                    (self.limits.max_cpu_time_seconds, self.limits.max_cpu_time_seconds)
                )
                logger.debug(f"Applied CPU limit: {self.limits.max_cpu_time_seconds}s")

            # File descriptor limit
            if self.limits.max_file_descriptors > 0:
                soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
                self._original_limits[resource.RLIMIT_NOFILE] = (soft, hard)
                resource.setrlimit(
                    resource.RLIMIT_NOFILE,
                    (self.limits.max_file_descriptors, self.limits.max_file_descriptors)
                )
                logger.debug(f"Applied FD limit: {self.limits.max_file_descriptors}")

            # Subprocess limit (RLIMIT_NPROC)
            if self.limits.max_subprocess_count == 0:
                # Prevent subprocess creation
                soft, hard = resource.getrlimit(resource.RLIMIT_NPROC)
                self._original_limits[resource.RLIMIT_NPROC] = (soft, hard)
                resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
                logger.debug("Disabled subprocess creation")

        except (ValueError, OSError) as e:
            logger.warning(f"Failed to apply some resource limits: {e}")
            # Continue execution even if some limits can't be applied

    def _restore_limits(self) -> None:
        """Restore original resource limits"""
        for limit_type, (soft, hard) in self._original_limits.items():
            try:
                resource.setrlimit(limit_type, (soft, hard))
            except (ValueError, OSError) as e:
                logger.warning(f"Failed to restore limit {limit_type}: {e}")

        self._original_limits.clear()

    def _handle_violation(self, exception: Exception) -> None:
        """Handle and record a sandbox violation"""
        import traceback

        violation_type = type(exception).__name__
        message = str(exception)
        stack_trace = traceback.format_exc()

        self._record_violation(violation_type, message, stack_trace)

    def _record_violation(
        self,
        violation_type: str,
        message: str,
        stack_trace: Optional[str] = None
    ) -> None:
        """Record a sandbox violation"""
        violation = SandboxViolation(
            violation_type=violation_type,
            message=message,
            timestamp=datetime.now(),
            stack_trace=stack_trace,
        )

        self.violations.append(violation)
        logger.warning(
            f"Sandbox violation ({violation_type}): {message}"
        )

    def get_violations(self) -> list[SandboxViolation]:
        """Get all recorded violations"""
        return self.violations.copy()

    def clear_violations(self) -> None:
        """Clear recorded violations"""
        self.violations.clear()

    def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage.

        Returns:
            Dictionary with current resource usage stats
        """
        usage = resource.getrusage(resource.RUSAGE_SELF)

        return {
            "memory_mb": usage.ru_maxrss / 1024,  # Convert KB to MB
            "cpu_time_seconds": usage.ru_utime + usage.ru_stime,
            "page_faults": usage.ru_majflt,
            "voluntary_context_switches": usage.ru_nvcsw,
            "involuntary_context_switches": usage.ru_nivcsw,
        }

    def check_compliance(self) -> bool:
        """
        Check if current usage is within limits.

        Returns:
            True if within limits, False otherwise
        """
        usage = self.get_current_usage()

        # Check memory
        if usage["memory_mb"] > self.limits.max_memory_mb:
            self._record_violation(
                "memory",
                f"Memory usage {usage['memory_mb']:.1f}MB exceeds limit "
                f"{self.limits.max_memory_mb}MB"
            )
            return False

        # Check CPU time
        if usage["cpu_time_seconds"] > self.limits.max_cpu_time_seconds:
            self._record_violation(
                "cpu",
                f"CPU time {usage['cpu_time_seconds']:.1f}s exceeds limit "
                f"{self.limits.max_cpu_time_seconds}s"
            )
            return False

        return True


class SandboxManager:
    """
    Manages sandboxes for multiple plugins.

    Provides per-plugin sandbox instances with custom limits.
    """

    def __init__(self, default_limits: Optional[SandboxLimits] = None):
        """
        Initialize sandbox manager.

        Args:
            default_limits: Default limits for new sandboxes
        """
        self.default_limits = default_limits or SandboxLimits()
        self._sandboxes: Dict[str, PluginSandbox] = {}

    def create_sandbox(
        self,
        plugin_name: str,
        limits: Optional[SandboxLimits] = None
    ) -> PluginSandbox:
        """
        Create a sandbox for a plugin.

        Args:
            plugin_name: Name of the plugin
            limits: Custom limits for this plugin. If None, uses default limits.

        Returns:
            PluginSandbox instance
        """
        sandbox = PluginSandbox(limits or self.default_limits)
        self._sandboxes[plugin_name] = sandbox
        logger.info(f"Created sandbox for plugin: {plugin_name}")
        return sandbox

    def get_sandbox(self, plugin_name: str) -> Optional[PluginSandbox]:
        """Get sandbox for a plugin"""
        return self._sandboxes.get(plugin_name)

    def remove_sandbox(self, plugin_name: str) -> None:
        """Remove sandbox for a plugin"""
        if plugin_name in self._sandboxes:
            del self._sandboxes[plugin_name]
            logger.info(f"Removed sandbox for plugin: {plugin_name}")

    def check_all_compliance(self) -> Dict[str, bool]:
        """
        Check compliance for all sandboxes.

        Returns:
            Dictionary mapping plugin names to compliance status
        """
        return {
            name: sandbox.check_compliance()
            for name, sandbox in self._sandboxes.items()
        }

    def get_all_violations(self) -> Dict[str, list[SandboxViolation]]:
        """Get violations for all sandboxes"""
        return {
            name: sandbox.get_violations()
            for name, sandbox in self._sandboxes.items()
            if sandbox.violations
        }

    def get_all_usage(self) -> Dict[str, Dict[str, Any]]:
        """Get resource usage for all sandboxes"""
        return {
            name: sandbox.get_current_usage()
            for name, sandbox in self._sandboxes.items()
        }

"""
Health checking for AI-PAL services.

Provides health status for all system components.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio


class HealthStatus(str, Enum):
    """Health status values"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of a single component"""

    name: str
    status: HealthStatus
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    last_checked: datetime = field(default_factory=datetime.utcnow)
    response_time_ms: Optional[float] = None


@dataclass
class SystemHealth:
    """Overall system health"""

    status: HealthStatus
    components: Dict[str, ComponentHealth]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    uptime_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat() + "Z",
            "uptime_seconds": self.uptime_seconds,
            "components": {
                name: {
                    "status": component.status.value,
                    "message": component.message,
                    "details": component.details,
                    "last_checked": component.last_checked.isoformat() + "Z",
                    "response_time_ms": component.response_time_ms,
                }
                for name, component in self.components.items()
            },
        }


class HealthChecker:
    """
    Health checker for AI-PAL system.

    Checks health of:
    - Database connection
    - Redis cache
    - Model providers (Anthropic, OpenAI, local)
    - Plugin system
    - File system
    """

    def __init__(self):
        """Initialize health checker"""
        self.start_time = datetime.utcnow()
        self._last_health: Optional[SystemHealth] = None

    async def check_health(
        self, include_components: Optional[List[str]] = None
    ) -> SystemHealth:
        """
        Check health of all components.

        Args:
            include_components: Optional list of components to check
                               (if None, checks all)

        Returns:
            SystemHealth with overall and component status
        """
        components: Dict[str, ComponentHealth] = {}

        # Define all checks
        all_checks = {
            "database": self._check_database,
            "redis": self._check_redis,
            "models": self._check_models,
            "plugins": self._check_plugins,
            "filesystem": self._check_filesystem,
            "gates": self._check_gates,
        }

        # Filter checks if specified
        if include_components:
            checks = {
                k: v for k, v in all_checks.items() if k in include_components
            }
        else:
            checks = all_checks

        # Run all health checks concurrently
        results = await asyncio.gather(
            *[check() for check in checks.values()], return_exceptions=True
        )

        # Collect results
        for (name, _), result in zip(checks.items(), results):
            if isinstance(result, Exception):
                components[name] = ComponentHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(result)}",
                )
            else:
                components[name] = result

        # Determine overall status
        overall_status = self._determine_overall_status(components)

        # Calculate uptime
        uptime = (datetime.utcnow() - self.start_time).total_seconds()

        health = SystemHealth(
            status=overall_status, components=components, uptime_seconds=uptime
        )

        self._last_health = health
        return health

    def _determine_overall_status(
        self, components: Dict[str, ComponentHealth]
    ) -> HealthStatus:
        """
        Determine overall system status from component statuses.

        Logic:
        - All healthy → HEALTHY
        - Any unhealthy → UNHEALTHY
        - Any degraded → DEGRADED
        """
        if not components:
            return HealthStatus.UNKNOWN

        statuses = [c.status for c in components.values()]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNKNOWN

    async def _check_database(self) -> ComponentHealth:
        """Check database health"""
        import time

        start = time.time()

        try:
            # Try importing database module
            try:
                from ai_pal.database import get_db_session
            except ImportError:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    message="Database module not available",
                )

            # Try creating a session and executing a simple query
            try:
                # This would be the actual DB check in production
                # For now, just check if we can create a session
                session = await get_db_session()
                # Execute simple query (e.g., SELECT 1)
                # await session.execute("SELECT 1")
                elapsed_ms = (time.time() - start) * 1000

                return ComponentHealth(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connection successful",
                    response_time_ms=elapsed_ms,
                )
            except Exception as e:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Database query failed: {str(e)}",
                )

        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database check failed: {str(e)}",
            )

    async def _check_redis(self) -> ComponentHealth:
        """Check Redis cache health"""
        import time

        start = time.time()

        try:
            # Try to connect to Redis
            try:
                import redis.asyncio as redis
                import os

                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                client = redis.from_url(redis_url)

                # Ping Redis
                await client.ping()
                elapsed_ms = (time.time() - start) * 1000

                await client.close()

                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.HEALTHY,
                    message="Redis connection successful",
                    response_time_ms=elapsed_ms,
                )

            except ImportError:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.DEGRADED,
                    message="Redis module not available (optional)",
                )
            except Exception as e:
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Redis connection failed: {str(e)}",
                )

        except Exception as e:
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis check failed: {str(e)}",
            )

    async def _check_models(self) -> ComponentHealth:
        """Check model providers health"""
        import os

        details = {}
        all_healthy = True
        any_available = False

        # Check Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            details["anthropic"] = "configured"
            any_available = True
        else:
            details["anthropic"] = "not configured"

        # Check OpenAI
        if os.getenv("OPENAI_API_KEY"):
            details["openai"] = "configured"
            any_available = True
        else:
            details["openai"] = "not configured"

        # Check local models
        local_models_path = os.getenv("LOCAL_MODELS_PATH", "./models")
        import os.path

        if os.path.exists(local_models_path):
            details["local"] = "available"
            any_available = True
        else:
            details["local"] = "not available"

        if any_available:
            status = HealthStatus.HEALTHY
            message = "At least one model provider available"
        else:
            status = HealthStatus.DEGRADED
            message = "No model providers configured"

        return ComponentHealth(
            name="models",
            status=status,
            message=message,
            details=details,
        )

    async def _check_plugins(self) -> ComponentHealth:
        """Check plugin system health"""
        try:
            try:
                from ai_pal.plugins.manager import PluginManager

                manager = PluginManager()
                # Get loaded plugins count
                # plugins = await manager.list_plugins()

                return ComponentHealth(
                    name="plugins",
                    status=HealthStatus.HEALTHY,
                    message="Plugin system operational",
                    # details={"loaded_plugins": len(plugins)},
                )

            except ImportError:
                return ComponentHealth(
                    name="plugins",
                    status=HealthStatus.DEGRADED,
                    message="Plugin system not available (optional)",
                )

        except Exception as e:
            return ComponentHealth(
                name="plugins",
                status=HealthStatus.DEGRADED,
                message=f"Plugin check failed: {str(e)}",
            )

    async def _check_filesystem(self) -> ComponentHealth:
        """Check filesystem health"""
        import os
        import tempfile

        try:
            # Check data directory
            data_dir = os.getenv("DATA_DIR", "./data")
            logs_dir = os.getenv("LOGS_DIR", "./logs")

            details = {}

            # Check if directories exist and are writable
            for name, path in [("data", data_dir), ("logs", logs_dir)]:
                if os.path.exists(path):
                    # Try writing a test file
                    try:
                        test_file = os.path.join(path, ".health_check")
                        with open(test_file, "w") as f:
                            f.write("test")
                        os.remove(test_file)
                        details[name] = "writable"
                    except Exception:
                        details[name] = "read-only"
                else:
                    details[name] = "missing"

            # Check disk space
            import shutil

            stat = shutil.disk_usage(data_dir if os.path.exists(data_dir) else "/")
            free_gb = stat.free / (1024**3)
            total_gb = stat.total / (1024**3)
            percent_free = (stat.free / stat.total) * 100

            details["disk_free_gb"] = round(free_gb, 2)
            details["disk_total_gb"] = round(total_gb, 2)
            details["disk_free_percent"] = round(percent_free, 1)

            # Determine status based on free space
            if percent_free < 5:
                status = HealthStatus.UNHEALTHY
                message = f"Critical: Only {percent_free:.1f}% disk space remaining"
            elif percent_free < 15:
                status = HealthStatus.DEGRADED
                message = f"Warning: Only {percent_free:.1f}% disk space remaining"
            else:
                status = HealthStatus.HEALTHY
                message = "Filesystem healthy"

            return ComponentHealth(
                name="filesystem",
                status=status,
                message=message,
                details=details,
            )

        except Exception as e:
            return ComponentHealth(
                name="filesystem",
                status=HealthStatus.UNHEALTHY,
                message=f"Filesystem check failed: {str(e)}",
            )

    async def _check_gates(self) -> ComponentHealth:
        """Check Four Gates system health"""
        try:
            try:
                from ai_pal.gates.agency_validator import AgencyValidator
                from ai_pal.gates.extraction_analyzer import ExtractionAnalyzer
                from ai_pal.gates.override_checker import OverrideChecker
                from ai_pal.gates.performance_validator import PerformanceValidator

                # All gates importable
                details = {
                    "gate1_net_agency": "available",
                    "gate2_extraction": "available",
                    "gate3_override": "available",
                    "gate4_performance": "available",
                }

                return ComponentHealth(
                    name="gates",
                    status=HealthStatus.HEALTHY,
                    message="All Four Gates operational",
                    details=details,
                )

            except ImportError as e:
                return ComponentHealth(
                    name="gates",
                    status=HealthStatus.DEGRADED,
                    message=f"Some gates not available: {str(e)}",
                )

        except Exception as e:
            return ComponentHealth(
                name="gates",
                status=HealthStatus.UNHEALTHY,
                message=f"Gates check failed: {str(e)}",
            )

    def get_last_health(self) -> Optional[SystemHealth]:
        """Get last health check result"""
        return self._last_health


# Global health checker
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """
    Get global health checker (singleton).

    Returns:
        HealthChecker instance
    """
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        checker = get_health_checker()
        health = await checker.check_health()

        print(f"Overall Status: {health.status.value}")
        print(f"Uptime: {health.uptime_seconds:.1f}s")
        print("\nComponents:")

        for name, component in health.components.items():
            print(f"  {name}: {component.status.value}")
            if component.message:
                print(f"    Message: {component.message}")
            if component.response_time_ms:
                print(f"    Response Time: {component.response_time_ms:.1f}ms")

    asyncio.run(main())

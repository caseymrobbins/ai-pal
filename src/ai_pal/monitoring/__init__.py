"""
Monitoring Module - Phase 2 & Production Observability

Advanced monitoring systems for AC-AI compliance:
- ARI (Agency Retention Index) Monitoring
- EDM (Epistemic Debt Monitoring) with fact-checking

Production Observability:
- Structured JSON logging with contextual data
- Prometheus metrics collection
- Health checking for all components
- OpenTelemetry distributed tracing
"""

from .ari_monitor import ARIMonitor, AgencySnapshot, ARIReport, AgencyTrend
from .edm_monitor import EDMMonitor, EpistemicDebtSnapshot, EDMReport
from .logger import StructuredLogger, setup_logging, get_logger
from .metrics import MetricsCollector, get_metrics, Timer
from .health import HealthChecker, HealthStatus, SystemHealth, ComponentHealth, get_health_checker
from .tracer import Tracer, TracerProvider, Span, get_tracer, get_tracer_provider, trace

__all__ = [
    # ARI Monitoring
    "ARIMonitor",
    "AgencySnapshot",
    "ARIReport",
    "AgencyTrend",
    # EDM Monitoring
    "EDMMonitor",
    "EpistemicDebtSnapshot",
    "EDMReport",
    # Logging
    "StructuredLogger",
    "setup_logging",
    "get_logger",
    # Metrics
    "MetricsCollector",
    "get_metrics",
    "Timer",
    # Health
    "HealthChecker",
    "HealthStatus",
    "SystemHealth",
    "ComponentHealth",
    "get_health_checker",
    # Tracing
    "Tracer",
    "TracerProvider",
    "Span",
    "get_tracer",
    "get_tracer_provider",
    "trace",
]

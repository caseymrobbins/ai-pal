"""
Monitoring Module - Phase 2 & Production Observability

Advanced monitoring systems for AC-AI compliance:
- ARI (Agency Retention Index) Monitoring
- EDM (Epistemic Debt Monitoring) with fact-checking
- ARI Engine (Multi-layered skill atrophy detection)
- RDI Monitor (Privacy-first reality drift detection)

Production Observability:
- Structured JSON logging with contextual data
- Prometheus metrics collection
- Health checking for all components
- OpenTelemetry distributed tracing
"""

from .ari_monitor import ARIMonitor, AgencySnapshot, ARIReport, AgencyTrend
from .edm_monitor import EDMMonitor, EpistemicDebtSnapshot, EDMReport
from .ari_engine import (
    ARIEngine,
    PassiveLexicalAnalyzer,
    SocraticCopilot,
    DeepDiveMode,
    ARISignalLevel,
    UCCResponseType,
    LexicalMetrics,
    UnassistedCapabilityCheckpoint,
    ARIBaseline,
    ARIScore,
)
from .rdi_monitor import (
    RDIMonitor,
    RDILevel,
    DriftType,
    RDIScore as RDIScoreType,
    SemanticBaseline,
    ConsensusModel,
    DriftSignal,
    AnonymizedRDIStats,
)
from .logger import StructuredLogger, setup_logging, get_logger
from .metrics import MetricsCollector, get_metrics, Timer
from .health import HealthChecker, HealthStatus, SystemHealth, ComponentHealth, get_health_checker
from .tracer import Tracer, TracerProvider, Span, get_tracer, get_tracer_provider, trace

__all__ = [
    # ARI Monitoring (Original)
    "ARIMonitor",
    "AgencySnapshot",
    "ARIReport",
    "AgencyTrend",
    # ARI Engine (New)
    "ARIEngine",
    "PassiveLexicalAnalyzer",
    "SocraticCopilot",
    "DeepDiveMode",
    "ARISignalLevel",
    "UCCResponseType",
    "LexicalMetrics",
    "UnassistedCapabilityCheckpoint",
    "ARIBaseline",
    "ARIScore",
    # RDI Monitor (New)
    "RDIMonitor",
    "RDILevel",
    "DriftType",
    "RDIScoreType",
    "SemanticBaseline",
    "ConsensusModel",
    "DriftSignal",
    "AnonymizedRDIStats",
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

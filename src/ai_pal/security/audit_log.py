"""
Comprehensive Audit Logging System

Records all security-relevant events, decisions, and actions for compliance and forensics.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from queue import Queue


class AuditEventType(Enum):
    """Types of auditable events"""
    # Authentication & Authorization
    LOGIN = "login"
    LOGOUT = "logout"
    AUTH_FAILURE = "auth_failure"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"

    # Gate Events
    GATE_EVALUATION = "gate_evaluation"
    GATE_PASSED = "gate_passed"
    GATE_FAILED = "gate_failed"
    GATE_OVERRIDE = "gate_override"

    # Plugin Events
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"
    PLUGIN_ERROR = "plugin_error"
    PLUGIN_SANDBOX_VIOLATION = "plugin_sandbox_violation"

    # Security Events
    SECRET_DETECTED = "secret_detected"
    SANITIZATION_APPLIED = "sanitization_applied"
    VALIDATION_FAILED = "validation_failed"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # Data Events
    DATA_ACCESS = "data_access"
    DATA_MODIFIED = "data_modified"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"

    # Model Events
    MODEL_REQUEST = "model_request"
    MODEL_RESPONSE = "model_response"
    MODEL_ERROR = "model_error"
    HIGH_COST_REQUEST = "high_cost_request"

    # ARI/EDM Events
    ARI_SNAPSHOT = "ari_snapshot"
    EDM_DEBT_DETECTED = "edm_debt_detected"
    DESKILLING_DETECTED = "deskilling_detected"

    # System Events
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CONFIG_CHANGED = "config_changed"
    ERROR = "error"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Represents a single audit event"""
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    component: str
    action: str
    details: Dict[str, Any]
    result: str  # "success", "failure", "denied"
    ip_address: Optional[str] = None
    resource: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "component": self.component,
            "action": self.action,
            "details": self.details,
            "result": self.result,
            "ip_address": self.ip_address,
            "resource": self.resource,
        }

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    Main audit logging system.

    Features:
    - Structured event logging
    - Multiple output formats (JSON, text)
    - Async logging to prevent blocking
    - Log rotation and retention
    - Query and search capabilities
    """

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        log_to_file: bool = True,
        log_to_console: bool = False,
        retention_days: int = 90,
    ):
        """
        Initialize audit logger.

        Args:
            log_dir: Directory for audit log files
            log_to_file: Enable file logging
            log_to_console: Enable console logging
            retention_days: Number of days to retain audit logs
        """
        self.log_dir = log_dir or Path.home() / ".ai_pal" / "audit_logs"
        self.log_to_file = log_to_file
        self.log_to_console = log_to_console
        self.retention_days = retention_days

        # Create log directory
        if self.log_to_file:
            self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False

        # File handler for audit logs
        if self.log_to_file:
            self._setup_file_handler()

        # Console handler
        if self.log_to_console:
            self._setup_console_handler()

        # Async logging queue
        self._event_queue: Queue = Queue()
        self._worker_thread = threading.Thread(target=self._process_events, daemon=True)
        self._worker_thread.start()

        # Statistics
        self._event_count = 0
        self._event_counts_by_type: Dict[str, int] = {}

    def _setup_file_handler(self) -> None:
        """Setup rotating file handler"""
        from logging.handlers import RotatingFileHandler

        log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"

        handler = RotatingFileHandler(
            log_file,
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=10,
        )

        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def _setup_console_handler(self) -> None:
        """Setup console handler"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(asctime)s] AUDIT %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_event(self, event: AuditEvent) -> None:
        """
        Log an audit event.

        Args:
            event: Audit event to log
        """
        # Add to async queue
        self._event_queue.put(event)

    def _process_events(self) -> None:
        """Process events from queue (runs in background thread)"""
        while True:
            try:
                event = self._event_queue.get()
                self._write_event(event)
                self._event_queue.task_done()
            except Exception as e:
                logging.error(f"Error processing audit event: {e}")

    def _write_event(self, event: AuditEvent) -> None:
        """Write event to log"""
        # Update statistics
        self._event_count += 1
        event_type = event.event_type.value
        self._event_counts_by_type[event_type] = \
            self._event_counts_by_type.get(event_type, 0) + 1

        # Map severity to log level
        level_map = {
            AuditSeverity.DEBUG: logging.DEBUG,
            AuditSeverity.INFO: logging.INFO,
            AuditSeverity.WARNING: logging.WARNING,
            AuditSeverity.ERROR: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL,
        }

        log_level = level_map[event.severity]

        # Log as JSON
        self.logger.log(log_level, event.to_json())

    def log_gate_evaluation(
        self,
        gate_name: str,
        user_id: str,
        session_id: str,
        passed: bool,
        details: Dict[str, Any],
    ) -> None:
        """Log a gate evaluation event"""
        event = AuditEvent(
            event_type=AuditEventType.GATE_PASSED if passed else AuditEventType.GATE_FAILED,
            severity=AuditSeverity.INFO if passed else AuditSeverity.WARNING,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            component="gate_system",
            action=f"evaluate_{gate_name}",
            details=details,
            result="success" if passed else "failure",
            resource=gate_name,
        )
        self.log_event(event)

    def log_plugin_event(
        self,
        plugin_name: str,
        event_type: AuditEventType,
        details: Dict[str, Any],
        severity: AuditSeverity = AuditSeverity.INFO,
    ) -> None:
        """Log a plugin-related event"""
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now(),
            user_id=None,
            session_id=None,
            component="plugin_system",
            action=event_type.value,
            details=details,
            result="success",
            resource=plugin_name,
        )
        self.log_event(event)

    def log_security_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str],
        session_id: Optional[str],
        details: Dict[str, Any],
        severity: AuditSeverity = AuditSeverity.WARNING,
    ) -> None:
        """Log a security-related event"""
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            component="security",
            action=event_type.value,
            details=details,
            result="detected",
        )
        self.log_event(event)

    def log_model_request(
        self,
        user_id: str,
        session_id: str,
        model_name: str,
        cost_usd: float,
        details: Dict[str, Any],
    ) -> None:
        """Log a model request"""
        # Determine severity based on cost
        severity = AuditSeverity.WARNING if cost_usd > 0.10 else AuditSeverity.INFO
        event_type = AuditEventType.HIGH_COST_REQUEST if cost_usd > 0.10 else AuditEventType.MODEL_REQUEST

        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            component="model_orchestrator",
            action="execute_model",
            details={**details, "cost_usd": cost_usd},
            result="success",
            resource=model_name,
        )
        self.log_event(event)

    def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        granted: bool,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a data access event"""
        event = AuditEvent(
            event_type=AuditEventType.ACCESS_GRANTED if granted else AuditEventType.ACCESS_DENIED,
            severity=AuditSeverity.INFO if granted else AuditSeverity.WARNING,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=None,
            component="data_access",
            action=action,
            details=details or {},
            result="granted" if granted else "denied",
            resource=resource,
        )
        self.log_event(event)

    def query_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Query audit events.

        Args:
            start_time: Filter events after this time
            end_time: Filter events before this time
            event_type: Filter by event type
            user_id: Filter by user ID
            severity: Filter by severity
            limit: Maximum number of events to return

        Returns:
            List of matching events
        """
        events = []

        # Read from log files
        if not self.log_dir.exists():
            return events

        log_files = sorted(self.log_dir.glob("audit_*.jsonl"))

        for log_file in reversed(log_files):  # Start with most recent
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if len(events) >= limit:
                            break

                        try:
                            event_dict = json.loads(line)

                            # Apply filters
                            if start_time and datetime.fromisoformat(event_dict['timestamp']) < start_time:
                                continue
                            if end_time and datetime.fromisoformat(event_dict['timestamp']) > end_time:
                                continue
                            if event_type and event_dict['event_type'] != event_type.value:
                                continue
                            if user_id and event_dict.get('user_id') != user_id:
                                continue
                            if severity and event_dict['severity'] != severity.value:
                                continue

                            events.append(event_dict)

                        except json.JSONDecodeError:
                            continue

                if len(events) >= limit:
                    break

            except Exception as e:
                logging.error(f"Error reading audit log {log_file}: {e}")

        return events[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit log statistics"""
        return {
            "total_events": self._event_count,
            "events_by_type": self._event_counts_by_type,
            "queue_size": self._event_queue.qsize(),
            "log_directory": str(self.log_dir),
            "retention_days": self.retention_days,
        }

    def cleanup_old_logs(self) -> int:
        """
        Remove audit logs older than retention period.

        Returns:
            Number of files deleted
        """
        if not self.log_dir.exists():
            return 0

        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0

        for log_file in self.log_dir.glob("audit_*.jsonl*"):
            try:
                # Extract date from filename
                date_str = log_file.stem.replace("audit_", "").split(".")[0]
                file_date = datetime.strptime(date_str, "%Y%m%d")

                if file_date < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
                    logging.info(f"Deleted old audit log: {log_file}")

            except Exception as e:
                logging.error(f"Error cleaning up audit log {log_file}: {e}")

        return deleted_count


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_audit_event(event: AuditEvent) -> None:
    """Convenience function to log audit event"""
    get_audit_logger().log_event(event)


# Convenience functions for common audit events
def audit_gate_evaluation(gate_name: str, user_id: str, session_id: str, passed: bool, details: Dict[str, Any]) -> None:
    """Audit a gate evaluation"""
    get_audit_logger().log_gate_evaluation(gate_name, user_id, session_id, passed, details)


def audit_plugin_loaded(plugin_name: str, version: str) -> None:
    """Audit a plugin load event"""
    get_audit_logger().log_plugin_event(
        plugin_name,
        AuditEventType.PLUGIN_LOADED,
        {"version": version},
    )


def audit_secret_detected(secret_type: str, location: str, severity: str) -> None:
    """Audit a secret detection"""
    get_audit_logger().log_security_event(
        AuditEventType.SECRET_DETECTED,
        None,
        None,
        {"secret_type": secret_type, "location": location},
        AuditSeverity[severity.upper()] if severity.upper() in AuditSeverity.__members__ else AuditSeverity.WARNING,
    )


def audit_model_request(user_id: str, session_id: str, model_name: str, cost_usd: float, tokens: int) -> None:
    """Audit a model request"""
    get_audit_logger().log_model_request(
        user_id,
        session_id,
        model_name,
        cost_usd,
        {"total_tokens": tokens},
    )

"""
Audit Logs API endpoints

Provides access to audit trail data for user dashboard and compliance.
"""

from fastapi import APIRouter, Query, Path, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ai_pal.monitoring import get_logger
from ai_pal.security.audit_log import AuditLogger, AuditEventType, AuditSeverity

logger = get_logger("ai_pal.api.audit")
router = APIRouter(prefix="/api/users", tags=["Audit Logs"])

# Initialize audit logger
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or initialize audit logger"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(
            log_to_file=True,
            log_to_console=False,
            retention_days=90
        )
    return _audit_logger


# ===== RESPONSE MODELS =====

class AuditLogEntry(BaseModel):
    """Single audit log entry"""
    event_type: str = Field(..., description="Event type")
    severity: str = Field(..., description="Severity level: debug, info, warning, error, critical")
    timestamp: str = Field(..., description="Event timestamp")
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    component: str = Field(..., description="Component that generated the event")
    action: str = Field(..., description="Action that was performed")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional event details")
    result: str = Field(..., description="Result: success, failure, denied")
    ip_address: Optional[str] = Field(None, description="IP address")
    resource: Optional[str] = Field(None, description="Resource affected")


class AuditLogsResponse(BaseModel):
    """List of audit logs response"""
    user_id: str = Field(..., description="User ID")
    logs: List[AuditLogEntry] = Field(..., description="Audit log entries")
    total_count: int = Field(..., description="Total number of logs")
    start_date: Optional[str] = Field(None, description="Query start date")
    end_date: Optional[str] = Field(None, description="Query end date")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters used in query")


class AuditStatisticsResponse(BaseModel):
    """Audit log statistics"""
    total_events: int = Field(..., description="Total number of events logged")
    events_by_type: Dict[str, int] = Field(..., description="Event counts by type")
    queue_size: int = Field(..., description="Current event queue size")
    log_directory: str = Field(..., description="Log directory path")
    retention_days: int = Field(..., description="Log retention period in days")


class EventTypesResponse(BaseModel):
    """Available event types"""
    event_types: List[str] = Field(..., description="Available event types for filtering")
    severity_levels: List[str] = Field(..., description="Available severity levels")


# ===== ENDPOINTS =====

@router.get("/{user_id}/audit-logs", response_model=AuditLogsResponse)
async def get_user_audit_logs(
    user_id: str = Path(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days of audit logs to fetch"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
) -> AuditLogsResponse:
    """
    Get audit logs for a user.

    Returns audit trail with optional filtering by date range, event type, and severity.

    Args:
        user_id: User ID to fetch audit logs for
        days: Number of days of history to retrieve (default: 30, max: 365)
        event_type: Optional filter by event type
        severity: Optional filter by severity level
        limit: Maximum number of logs to return (default: 100, max: 1000)

    Returns:
        AuditLogsResponse with audit log entries
    """
    try:
        audit_logger = get_audit_logger()

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Convert event_type and severity to enums if provided
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = AuditEventType[event_type.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid event_type: {event_type}"
                )

        severity_enum = None
        if severity:
            try:
                severity_enum = AuditSeverity[severity.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid severity: {severity}"
                )

        # Query audit logs
        logs_data = audit_logger.query_events(
            start_time=start_date,
            end_time=end_date,
            event_type=event_type_enum,
            user_id=user_id,
            severity=severity_enum,
            limit=limit
        )

        # Filter logs to only include events for this user
        user_logs = [log for log in logs_data if log.get('user_id') == user_id or not log.get('user_id')]

        # Convert to AuditLogEntry objects
        log_entries = [
            AuditLogEntry(
                event_type=log.get('event_type', 'unknown'),
                severity=log.get('severity', 'info'),
                timestamp=log.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
                user_id=log.get('user_id'),
                session_id=log.get('session_id'),
                component=log.get('component', 'unknown'),
                action=log.get('action', 'unknown'),
                details=log.get('details', {}),
                result=log.get('result', 'unknown'),
                ip_address=log.get('ip_address'),
                resource=log.get('resource')
            )
            for log in user_logs
        ]

        # Build filters applied info
        filters_applied = {
            "days": days,
            "user_id": user_id,
        }
        if event_type:
            filters_applied["event_type"] = event_type
        if severity:
            filters_applied["severity"] = severity

        return AuditLogsResponse(
            user_id=user_id,
            logs=log_entries,
            total_count=len(log_entries),
            start_date=start_date.isoformat() + "Z",
            end_date=end_date.isoformat() + "Z",
            filters_applied=filters_applied
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching audit logs for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch audit logs: {str(e)}"
        )


@router.get("/system/audit-stats", response_model=AuditStatisticsResponse)
async def get_audit_statistics() -> AuditStatisticsResponse:
    """
    Get audit log statistics.

    Returns overall audit log statistics including event counts and configuration.

    Returns:
        AuditStatisticsResponse with statistics
    """
    try:
        audit_logger = get_audit_logger()
        stats = audit_logger.get_statistics()

        return AuditStatisticsResponse(
            total_events=stats.get('total_events', 0),
            events_by_type=stats.get('events_by_type', {}),
            queue_size=stats.get('queue_size', 0),
            log_directory=stats.get('log_directory', ''),
            retention_days=stats.get('retention_days', 90)
        )

    except Exception as e:
        logger.error(f"Error fetching audit statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch audit statistics: {str(e)}"
        )


@router.get("/system/audit-event-types", response_model=EventTypesResponse)
async def get_audit_event_types() -> EventTypesResponse:
    """
    Get available audit event types and severity levels.

    Useful for populating filter dropdowns in the UI.

    Returns:
        EventTypesResponse with available event types and severity levels
    """
    try:
        # Get all event types and severity levels from enums
        event_types = [e.value for e in AuditEventType]
        severity_levels = [s.value for s in AuditSeverity]

        return EventTypesResponse(
            event_types=sorted(event_types),
            severity_levels=sorted(severity_levels)
        )

    except Exception as e:
        logger.error(f"Error fetching event types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch event types: {str(e)}"
        )


@router.get(
    "/{user_id}/audit-logs/export",
    response_model=List[AuditLogEntry],
    description="Export audit logs for user (all entries, no limit)"
)
async def export_user_audit_logs(
    user_id: str = Path(..., description="User ID"),
    days: int = Query(90, ge=1, le=365, description="Number of days to export"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
) -> List[AuditLogEntry]:
    """
    Export audit logs for a user.

    Returns all audit log entries matching the filters (useful for compliance exports).

    Args:
        user_id: User ID
        days: Number of days to export (default: 90)
        event_type: Optional event type filter

    Returns:
        List of AuditLogEntry objects
    """
    try:
        audit_logger = get_audit_logger()

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Convert event_type to enum if provided
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = AuditEventType[event_type.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid event_type: {event_type}"
                )

        # Query logs with no limit for export
        logs_data = audit_logger.query_events(
            start_time=start_date,
            end_time=end_date,
            event_type=event_type_enum,
            user_id=user_id,
            limit=10000  # High limit for export
        )

        # Filter to user's logs
        user_logs = [log for log in logs_data if log.get('user_id') == user_id or not log.get('user_id')]

        # Convert to AuditLogEntry objects
        return [
            AuditLogEntry(
                event_type=log.get('event_type', 'unknown'),
                severity=log.get('severity', 'info'),
                timestamp=log.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
                user_id=log.get('user_id'),
                session_id=log.get('session_id'),
                component=log.get('component', 'unknown'),
                action=log.get('action', 'unknown'),
                details=log.get('details', {}),
                result=log.get('result', 'unknown'),
                ip_address=log.get('ip_address'),
                resource=log.get('resource')
            )
            for log in user_logs
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting audit logs for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export audit logs: {str(e)}"
        )

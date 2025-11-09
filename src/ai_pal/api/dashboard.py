"""
Dashboard Summary API endpoint

Provides aggregated metrics for the main dashboard overview.
"""

from fastapi import APIRouter, Path, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from ai_pal.monitoring import get_logger
from ai_pal.storage.database import DatabaseManager, ARIRepository, GoalRepository, BackgroundTaskRepository
from ai_pal.security.audit_log import AuditLogger

logger = get_logger("ai_pal.api.dashboard")
router = APIRouter(prefix="/api/users", tags=["Dashboard"])

# Store db_manager reference (set during app startup)
_db_manager: Optional[DatabaseManager] = None


def set_db_manager(db_manager: DatabaseManager):
    """Set database manager instance"""
    global _db_manager
    _db_manager = db_manager


# ===== RESPONSE MODELS =====

class RecentActivity(BaseModel):
    """Recent activity entry"""
    timestamp: str = Field(..., description="Activity timestamp")
    type: str = Field(..., description="Activity type")
    description: str = Field(..., description="Activity description")
    status: str = Field(..., description="Activity status")


class DashboardSummary(BaseModel):
    """Complete dashboard summary"""
    user_id: str = Field(..., description="User ID")

    # ARI Metrics
    current_ari_score: float = Field(..., description="Current ARI autonomy retention score")
    ari_trend: str = Field(..., description="ARI trend: improving, stable, declining")
    ari_status: str = Field(..., description="ARI status: healthy, warning, critical")

    # Goals
    active_goals: int = Field(..., description="Number of active goals")
    completed_goals: int = Field(..., description="Number of completed goals")
    total_goals: int = Field(..., description="Total number of goals")
    goal_completion_rate: float = Field(..., description="Goal completion percentage")

    # Background Tasks
    pending_tasks: int = Field(..., description="Number of pending background tasks")
    completed_tasks_today: int = Field(..., description="Tasks completed today")
    failed_tasks: int = Field(..., description="Number of failed tasks")

    # Audit
    recent_events_count: int = Field(..., description="Number of recent audit events (last 7 days)")
    critical_events: int = Field(..., description="Number of critical audit events")

    # Summary
    last_updated: str = Field(..., description="Dashboard last updated timestamp")
    update_timestamp: str = Field(..., description="ISO format timestamp of when data was gathered")

    # Recent Activity
    recent_activities: List[RecentActivity] = Field(..., description="Recent user activities")

    # Quick Stats
    quick_stats: Dict[str, Any] = Field(default_factory=dict, description="Additional quick stats")


# ===== ENDPOINTS =====

@router.get("/{user_id}/dashboard-summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    user_id: str = Path(..., description="User ID")
) -> DashboardSummary:
    """
    Get complete dashboard summary for a user.

    Aggregates data from ARI, Goals, Tasks, and Audit endpoints to provide
    a quick overview for the main dashboard.

    Args:
        user_id: User ID to fetch dashboard summary for

    Returns:
        DashboardSummary with aggregated metrics
    """
    try:
        if not _db_manager:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database not initialized"
            )

        # Get repositories
        ari_repo = ARIRepository(_db_manager)
        goal_repo = GoalRepository(_db_manager)
        task_repo = BackgroundTaskRepository(_db_manager)
        audit_logger = AuditLogger(log_to_file=True, log_to_console=False)

        # ===== Gather ARI Metrics =====
        ari_snapshots = await ari_repo.get_snapshots_by_user(user_id, limit=2)
        current_ari_score = 50.0
        ari_trend = "stable"
        ari_status = "stable"

        if ari_snapshots:
            current = ari_snapshots[0]
            current_ari_score = current.get("autonomy_retention", 50.0)

            # Determine trend
            if len(ari_snapshots) > 1:
                previous = ari_snapshots[1]
                prev_score = previous.get("autonomy_retention", 50.0)
                change = current_ari_score - prev_score

                if change > 5:
                    ari_trend = "improving"
                elif change < -5:
                    ari_trend = "declining"
                else:
                    ari_trend = "stable"

            # Determine status
            if current_ari_score >= 80:
                ari_status = "healthy"
            elif current_ari_score >= 50:
                ari_status = "stable"
            elif current_ari_score >= 30:
                ari_status = "warning"
            else:
                ari_status = "critical"

        # ===== Gather Goal Metrics =====
        goals = await goal_repo.get_active_goals(user_id)
        active_goals = len([g for g in goals if g.get("status") == "active"])
        completed_goals = len([g for g in goals if g.get("status") == "completed"])
        total_goals = len(goals)
        goal_completion_rate = (completed_goals / total_goals * 100) if total_goals > 0 else 0

        # ===== Gather Task Metrics =====
        pending_tasks = await task_repo.get_tasks_by_status(user_id, "pending", limit=1000)
        completed_tasks = await task_repo.get_tasks_by_status(user_id, "completed", limit=1000)
        failed_tasks = await task_repo.get_tasks_by_status(user_id, "failed", limit=1000)

        # Count tasks completed today
        from datetime import datetime, timedelta
        today = datetime.utcnow().date()
        completed_today = sum(
            1 for task in completed_tasks
            if isinstance(task.get("completed_at"), datetime) and
            task.get("completed_at").date() == today
        )

        # ===== Gather Audit Metrics =====
        from datetime import timedelta as td
        recent_events = audit_logger.query_events(
            start_time=datetime.utcnow() - td(days=7),
            user_id=user_id,
            limit=1000
        )
        critical_events = sum(
            1 for event in recent_events
            if event.get("severity") == "critical"
        )

        # ===== Build Recent Activities =====
        recent_activities = []

        # Add recent goals
        for goal in goals[:3]:
            recent_activities.append(RecentActivity(
                timestamp=goal.get("created_at", datetime.utcnow().isoformat()),
                type="goal",
                description=f"Goal: {goal.get('description', 'Untitled')[:50]}",
                status=goal.get("status", "unknown")
            ))

        # Add recent tasks
        for task in completed_tasks[:2]:
            recent_activities.append(RecentActivity(
                timestamp=task.get("completed_at", datetime.utcnow().isoformat()),
                type="task",
                description=f"Task {task.get('task_type', 'unknown')} completed",
                status="completed"
            ))

        # Add recent critical events
        for event in recent_events[:1]:
            if event.get("severity") == "critical":
                recent_activities.append(RecentActivity(
                    timestamp=event.get("timestamp", datetime.utcnow().isoformat()),
                    type="audit",
                    description=f"Event: {event.get('action', 'unknown')}",
                    status="critical"
                ))

        # Sort by timestamp (newest first)
        recent_activities.sort(
            key=lambda x: x.timestamp,
            reverse=True
        )

        # ===== Build Response =====
        return DashboardSummary(
            user_id=user_id,
            current_ari_score=current_ari_score,
            ari_trend=ari_trend,
            ari_status=ari_status,
            active_goals=active_goals,
            completed_goals=completed_goals,
            total_goals=total_goals,
            goal_completion_rate=goal_completion_rate,
            pending_tasks=len(pending_tasks),
            completed_tasks_today=completed_today,
            failed_tasks=len(failed_tasks),
            recent_events_count=len(recent_events),
            critical_events=critical_events,
            last_updated=datetime.utcnow().isoformat() + "Z",
            update_timestamp=datetime.utcnow().isoformat() + "Z",
            recent_activities=recent_activities[:5],  # Top 5 activities
            quick_stats={
                "total_active_tasks": len(pending_tasks),
                "total_completed_tasks": len(completed_tasks),
                "audit_event_types": list(set(e.get("event_type") for e in recent_events))[:5],
                "system_health": {
                    "ari_healthy": ari_status == "healthy",
                    "goals_on_track": goal_completion_rate >= 50,
                    "no_critical_errors": critical_events == 0,
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dashboard summary for user {user_id}: {e}")

        # Return default summary on error
        return DashboardSummary(
            user_id=user_id,
            current_ari_score=50.0,
            ari_trend="stable",
            ari_status="stable",
            active_goals=0,
            completed_goals=0,
            total_goals=0,
            goal_completion_rate=0,
            pending_tasks=0,
            completed_tasks_today=0,
            failed_tasks=0,
            recent_events_count=0,
            critical_events=0,
            last_updated=datetime.utcnow().isoformat() + "Z",
            update_timestamp=datetime.utcnow().isoformat() + "Z",
            recent_activities=[],
            quick_stats={"error": str(e)}
        )

"""
Background Task Management API Endpoints

Provides REST API for:
- Triggering background tasks
- Monitoring task progress
- Retrieving task results
- Task history and analytics
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

from loguru import logger

# Import Celery tasks
from ai_pal.tasks.celery_app import app as celery_app
from ai_pal.storage.database import DatabaseManager, BackgroundTaskRepository

# Create router
router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Initialize database (will be set by main.py)
_db_manager: Optional[DatabaseManager] = None
_task_repo: Optional[BackgroundTaskRepository] = None


def get_task_repo() -> BackgroundTaskRepository:
    """Get task repository instance"""
    global _db_manager, _task_repo

    if _task_repo is None:
        if _db_manager is None:
            raise HTTPException(
                status_code=500,
                detail="Database manager not initialized"
            )
        _task_repo = BackgroundTaskRepository(_db_manager)

    return _task_repo


def set_db_manager(db_manager: DatabaseManager):
    """Set database manager (called by main.py)"""
    global _db_manager
    _db_manager = db_manager


# ===== REQUEST/RESPONSE MODELS =====

class TaskSubmitRequest(BaseModel):
    """Request to submit a background task"""
    task_type: str = Field(..., description="Task type (ari_snapshot, ffe_planning, etc.)")
    user_id: Optional[str] = Field(None, description="User ID")
    priority: int = Field(5, ge=1, le=10, description="Task priority (1-10)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Task parameters")


class TaskSubmitResponse(BaseModel):
    """Response from task submission"""
    task_id: str
    celery_task_id: str
    status: str
    created_at: datetime
    message: str


class TaskStatusResponse(BaseModel):
    """Task status response"""
    task_id: str
    task_name: str
    task_type: str
    status: str
    user_id: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    attempts: int
    duration_seconds: Optional[float]


class TaskListResponse(BaseModel):
    """List of tasks"""
    tasks: List[TaskStatusResponse]
    total_count: int
    limit: int
    offset: int


# ===== TASK SUBMISSION ENDPOINTS =====

@router.post("/ari/aggregate-snapshots", response_model=TaskSubmitResponse)
async def submit_ari_snapshot_task(
    request: TaskSubmitRequest,
    task_repo: BackgroundTaskRepository = Depends(get_task_repo)
) -> TaskSubmitResponse:
    """
    Submit ARI snapshot aggregation task

    Task Parameters:
    - user_id: (optional) User to aggregate
    - time_window_hours: (optional, default 24) Time window for aggregation
    """
    try:
        task_id = str(uuid4())

        # Extract parameters
        user_id = request.parameters.get("user_id", request.user_id)
        time_window_hours = request.parameters.get("time_window_hours", 24)

        # Submit to Celery
        celery_task = celery_app.send_task(
            "ai_pal.tasks.ari_tasks.aggregate_ari_snapshots",
            args=(user_id, time_window_hours),
            priority=request.priority,
            queue="ari_analysis"
        )

        # Create database record
        await task_repo.create_task(
            task_id=task_id,
            task_name="aggregate_ari_snapshots",
            task_type="ari_snapshot",
            priority=request.priority,
            user_id=user_id,
            kwargs={"user_id": user_id, "time_window_hours": time_window_hours}
        )

        logger.info(f"Submitted ARI snapshot task: {task_id} (Celery: {celery_task.id})")

        return TaskSubmitResponse(
            task_id=task_id,
            celery_task_id=celery_task.id,
            status="pending",
            created_at=datetime.now(),
            message=f"ARI snapshot aggregation task submitted"
        )

    except Exception as exc:
        logger.error(f"Error submitting ARI task: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ffe/plan-goal", response_model=TaskSubmitResponse)
async def submit_ffe_planning_task(
    request: TaskSubmitRequest,
    task_repo: BackgroundTaskRepository = Depends(get_task_repo)
) -> TaskSubmitResponse:
    """
    Submit FFE goal planning task

    Task Parameters:
    - goal_id: (required) Goal ID
    - goal_description: (required) Goal description
    - complexity_level: (optional, default 'medium') simple|medium|complex
    """
    try:
        task_id = str(uuid4())

        # Validate required parameters
        goal_id = request.parameters.get("goal_id")
        goal_description = request.parameters.get("goal_description")

        if not goal_id or not goal_description:
            raise HTTPException(
                status_code=400,
                detail="goal_id and goal_description are required"
            )

        user_id = request.user_id
        complexity_level = request.parameters.get("complexity_level", "medium")

        # Submit to Celery
        celery_task = celery_app.send_task(
            "ai_pal.tasks.ffe_tasks.plan_ffe_goal",
            args=(goal_id, user_id, goal_description, complexity_level),
            priority=request.priority,
            queue="ffe_planning"
        )

        # Create database record
        await task_repo.create_task(
            task_id=task_id,
            task_name="plan_ffe_goal",
            task_type="ffe_planning",
            priority=request.priority,
            user_id=user_id,
            kwargs={
                "goal_id": goal_id,
                "goal_description": goal_description,
                "complexity_level": complexity_level
            }
        )

        logger.info(f"Submitted FFE planning task: {task_id} (Celery: {celery_task.id})")

        return TaskSubmitResponse(
            task_id=task_id,
            celery_task_id=celery_task.id,
            status="pending",
            created_at=datetime.now(),
            message="FFE goal planning task submitted"
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error submitting FFE task: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/edm/batch-analysis", response_model=TaskSubmitResponse)
async def submit_edm_analysis_task(
    request: TaskSubmitRequest,
    task_repo: BackgroundTaskRepository = Depends(get_task_repo)
) -> TaskSubmitResponse:
    """
    Submit EDM batch analysis task

    Task Parameters:
    - user_id: (optional) User to analyze
    - time_window_days: (optional, default 7) Days to analyze
    - min_severity: (optional, default 'low') low|medium|high|critical
    """
    try:
        task_id = str(uuid4())

        user_id = request.parameters.get("user_id", request.user_id)
        time_window_days = request.parameters.get("time_window_days", 7)
        min_severity = request.parameters.get("min_severity", "low")

        # Submit to Celery
        celery_task = celery_app.send_task(
            "ai_pal.tasks.edm_tasks.edm_batch_analysis",
            args=(user_id, time_window_days, min_severity),
            priority=request.priority,
            queue="edm_analysis"
        )

        # Create database record
        await task_repo.create_task(
            task_id=task_id,
            task_name="edm_batch_analysis",
            task_type="edm_analysis",
            priority=request.priority,
            user_id=user_id,
            kwargs={
                "user_id": user_id,
                "time_window_days": time_window_days,
                "min_severity": min_severity
            }
        )

        logger.info(f"Submitted EDM analysis task: {task_id} (Celery: {celery_task.id})")

        return TaskSubmitResponse(
            task_id=task_id,
            celery_task_id=celery_task.id,
            status="pending",
            created_at=datetime.now(),
            message="EDM batch analysis task submitted"
        )

    except Exception as exc:
        logger.error(f"Error submitting EDM task: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ===== TASK MONITORING ENDPOINTS =====

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    task_repo: BackgroundTaskRepository = Depends(get_task_repo)
) -> TaskStatusResponse:
    """Get status of a specific task"""
    try:
        task = await task_repo.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return TaskStatusResponse(**task)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error getting task status: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/list", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[str] = Query(None, description="Filter by status"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    task_repo: BackgroundTaskRepository = Depends(get_task_repo)
) -> TaskListResponse:
    """List background tasks with optional filtering"""
    try:
        tasks: List[Dict[str, Any]] = []

        if user_id:
            tasks = await task_repo.get_user_tasks(user_id, limit=limit, offset=offset)
        elif status:
            tasks = await task_repo.get_tasks_by_status(status, limit=limit, offset=offset)
        else:
            # Get recent tasks (not implemented in repo yet, using pending as default)
            tasks = await task_repo.get_pending_tasks(limit=limit)

        return TaskListResponse(
            tasks=[TaskStatusResponse(**t) for t in tasks],
            total_count=len(tasks),
            limit=limit,
            offset=offset
        )

    except Exception as exc:
        logger.error(f"Error listing tasks: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/pending", response_model=TaskListResponse)
async def get_pending_tasks(
    limit: int = Query(10, ge=1, le=100),
    task_repo: BackgroundTaskRepository = Depends(get_task_repo)
) -> TaskListResponse:
    """Get pending tasks"""
    try:
        tasks = await task_repo.get_pending_tasks(limit=limit)

        return TaskListResponse(
            tasks=[TaskStatusResponse(**t) for t in tasks],
            total_count=len(tasks),
            limit=limit,
            offset=0
        )

    except Exception as exc:
        logger.error(f"Error getting pending tasks: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/failed", response_model=TaskListResponse)
async def get_failed_tasks(
    limit: int = Query(10, ge=1, le=100),
    task_repo: BackgroundTaskRepository = Depends(get_task_repo)
) -> TaskListResponse:
    """Get failed tasks"""
    try:
        tasks = await task_repo.get_failed_tasks(limit=limit)

        return TaskListResponse(
            tasks=[TaskStatusResponse(**t) for t in tasks],
            total_count=len(tasks),
            limit=limit,
            offset=0
        )

    except Exception as exc:
        logger.error(f"Error getting failed tasks: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ===== TASK MANAGEMENT ENDPOINTS =====

@router.delete("/{task_id}")
async def cancel_task(
    task_id: str,
    task_repo: BackgroundTaskRepository = Depends(get_task_repo)
) -> Dict[str, Any]:
    """Cancel a pending task"""
    try:
        task = await task_repo.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task["status"] not in ["pending", "running"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel task with status {task['status']}"
            )

        # Revoke Celery task if it exists
        if task.get("celery_task_id"):
            celery_app.control.revoke(task["celery_task_id"], terminate=True)

        # Update database
        await task_repo.update_task_status(task_id, "cancelled")

        logger.info(f"Cancelled task {task_id}")

        return {"message": "Task cancelled successfully", "task_id": task_id}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error cancelling task: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: str,
    task_repo: BackgroundTaskRepository = Depends(get_task_repo)
) -> TaskSubmitResponse:
    """Retry a failed task"""
    try:
        task = await task_repo.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task["status"] != "failed":
            raise HTTPException(
                status_code=400,
                detail=f"Cannot retry task with status {task['status']}"
            )

        # Resubmit task
        new_task_id = str(uuid4())

        celery_task = celery_app.send_task(
            task["task_name"],
            args=task.get("args", ()),
            kwargs=task.get("kwargs", {}),
            priority=task.get("priority", 5)
        )

        # Create new database record
        await task_repo.create_task(
            task_id=new_task_id,
            task_name=task["task_name"],
            task_type=task["task_type"],
            priority=task.get("priority", 5),
            user_id=task.get("user_id"),
            args=task.get("args"),
            kwargs=task.get("kwargs")
        )

        logger.info(f"Retried task {task_id} as {new_task_id}")

        return TaskSubmitResponse(
            task_id=new_task_id,
            celery_task_id=celery_task.id,
            status="pending",
            created_at=datetime.now(),
            message=f"Task retried successfully (new task ID: {new_task_id})"
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error retrying task: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ===== HEALTH CHECK =====

@router.get("/health")
async def check_task_system_health() -> Dict[str, Any]:
    """Check health of task system"""
    try:
        # Check Celery connection
        celery_ok = False
        try:
            stats = celery_app.control.inspect().active()
            celery_ok = stats is not None
        except Exception as e:
            logger.warning(f"Celery health check failed: {e}")

        return {
            "status": "healthy" if celery_ok else "degraded",
            "celery_connected": celery_ok,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as exc:
        logger.error(f"Error checking task system health: {exc}")
        return {
            "status": "unhealthy",
            "error": str(exc),
            "timestamp": datetime.now().isoformat()
        }

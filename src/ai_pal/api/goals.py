"""
FFE (Fractal Flow Engine) Goals API endpoints

Provides goal management and progress tracking for users.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from ai_pal.monitoring import get_logger
from ai_pal.storage.database import DatabaseManager, GoalRepository
from ai_pal.cache.redis_cache import RedisCache
from ai_pal.storage.cached_repositories import CachedGoalRepository, create_cached_goal_repo

logger = get_logger("ai_pal.api.goals")
router = APIRouter(prefix="/api/users", tags=["FFE Goals"])

# Store db_manager and cache references (set during app startup)
_db_manager: Optional[DatabaseManager] = None
_cache: Optional[RedisCache] = None


def set_db_manager(db_manager: DatabaseManager):
    """Set database manager instance"""
    global _db_manager
    _db_manager = db_manager


def set_cache(cache: RedisCache):
    """Set Redis cache instance"""
    global _cache
    _cache = cache


def get_goal_repository() -> Union[CachedGoalRepository, GoalRepository]:
    """Get goal repository with caching if available"""
    if not _db_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized"
        )

    # Use cached repository if cache is available and enabled
    if _cache and _cache.enabled:
        return create_cached_goal_repo(_db_manager, _cache)

    # Fall back to regular repository
    return GoalRepository(_db_manager)


# ===== RESPONSE MODELS =====

class GoalResponse(BaseModel):
    """FFE goal response"""
    goal_id: str = Field(..., description="Unique goal ID")
    description: str = Field(..., description="Goal description")
    status: str = Field(..., description="Goal status: active, paused, completed")
    importance: int = Field(..., description="Importance level (1-10)")
    complexity: str = Field(..., description="Complexity: simple, medium, complex")
    progress: float = Field(..., description="Progress percentage (0-100)")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    estimated_value: Optional[float] = Field(None, description="Estimated value")
    atomic_blocks: List[Dict[str, Any]] = Field(default_factory=list, description="Atomic blocks")


class GoalsListResponse(BaseModel):
    """List of goals response"""
    user_id: str = Field(..., description="User ID")
    goals: List[GoalResponse] = Field(..., description="List of goals")
    total_count: int = Field(..., description="Total number of goals")
    active_count: int = Field(..., description="Number of active goals")
    completed_count: int = Field(..., description="Number of completed goals")


class GoalCreateRequest(BaseModel):
    """Request to create a goal"""
    description: str = Field(..., description="Goal description", min_length=1, max_length=1000)
    importance: int = Field(default=5, description="Importance level (1-10)", ge=1, le=10)
    complexity: Optional[str] = Field("medium", description="Complexity: simple, medium, complex")
    estimated_value: Optional[float] = Field(None, description="Estimated value")


class GoalUpdateRequest(BaseModel):
    """Request to update a goal"""
    description: Optional[str] = Field(None, description="Goal description")
    importance: Optional[int] = Field(None, description="Importance level (1-10)", ge=1, le=10)
    status: Optional[str] = Field(None, description="Goal status: active, paused, completed")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)", ge=0, le=100)
    estimated_value: Optional[float] = Field(None, description="Estimated value")


# ===== HELPER FUNCTIONS =====

async def _format_goal(db_row: Dict[str, Any]) -> GoalResponse:
    """Format database goal to response model"""
    created_at = db_row.get("created_at")
    updated_at = db_row.get("updated_at")

    if isinstance(created_at, datetime):
        created_at_str = created_at.isoformat() + "Z"
    else:
        created_at_str = str(created_at) if created_at else None

    if isinstance(updated_at, datetime):
        updated_at_str = updated_at.isoformat() + "Z"
    else:
        updated_at_str = str(updated_at) if updated_at else None

    return GoalResponse(
        goal_id=db_row.get("goal_id", ""),
        description=db_row.get("description", ""),
        status=db_row.get("status", "active"),
        importance=db_row.get("importance", 5),
        complexity=db_row.get("complexity_level", "medium"),
        progress=db_row.get("progress_percentage", 0),
        created_at=created_at_str or datetime.utcnow().isoformat() + "Z",
        updated_at=updated_at_str,
        estimated_value=db_row.get("estimated_value"),
        atomic_blocks=db_row.get("atomic_blocks", [])
    )


# ===== ENDPOINTS =====

@router.get("/{user_id}/goals", response_model=GoalsListResponse)
async def get_user_goals(
    user_id: str = Path(..., description="User ID"),
    status: Optional[str] = Query(None, description="Filter by status: active, completed, paused"),
    repo: GoalRepository = Depends(get_goal_repository)
) -> GoalsListResponse:
    """
    Get all goals for a user.

    Returns list of goals with optional status filtering.

    Args:
        user_id: User ID to fetch goals for
        status: Optional status filter (active, completed, paused)

    Returns:
        GoalsListResponse with list of goals and counts
    """
    try:
        # Get active goals
        active_goals_data = await repo.get_active_goals(user_id)

        # Format goals
        formatted_goals = []
        for goal in active_goals_data:
            formatted_goals.append(await _format_goal(goal))

        # Apply status filter
        if status:
            formatted_goals = [g for g in formatted_goals if g.status.lower() == status.lower()]

        # Calculate counts
        total_count = len(formatted_goals)
        active_count = sum(1 for g in formatted_goals if g.status == "active")
        completed_count = sum(1 for g in formatted_goals if g.status == "completed")

        return GoalsListResponse(
            user_id=user_id,
            goals=formatted_goals,
            total_count=total_count,
            active_count=active_count,
            completed_count=completed_count
        )

    except Exception as e:
        logger.error(f"Error fetching goals for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch goals: {str(e)}"
        )


@router.get("/{user_id}/goals/{goal_id}", response_model=GoalResponse)
async def get_user_goal(
    user_id: str = Path(..., description="User ID"),
    goal_id: str = Path(..., description="Goal ID"),
    repo: GoalRepository = Depends(get_goal_repository)
) -> GoalResponse:
    """
    Get a specific goal for a user.

    Args:
        user_id: User ID
        goal_id: Goal ID to fetch

    Returns:
        GoalResponse with goal details
    """
    try:
        goal = await repo.get_goal(goal_id)

        if not goal or goal.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )

        return await _format_goal(goal)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching goal {goal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch goal: {str(e)}"
        )


@router.post("/{user_id}/goals", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_user_goal(
    user_id: str = Path(..., description="User ID"),
    goal_data: GoalCreateRequest = None,
    repo: GoalRepository = Depends(get_goal_repository)
) -> GoalResponse:
    """
    Create a new goal for a user.

    Args:
        user_id: User ID
        goal_data: Goal creation data

    Returns:
        GoalResponse with created goal details
    """
    try:
        from uuid import uuid4

        goal_id = str(uuid4())

        goal_dict = {
            "goal_id": goal_id,
            "user_id": user_id,
            "description": goal_data.description,
            "importance": goal_data.importance,
            "complexity_level": goal_data.complexity or "medium",
            "estimated_value": goal_data.estimated_value,
            "status": "active",
            "progress_percentage": 0,
            "created_at": datetime.utcnow(),
        }

        saved_id = await repo.save_goal(goal_dict)

        return GoalResponse(
            goal_id=goal_id,
            description=goal_data.description,
            status="active",
            importance=goal_data.importance,
            complexity=goal_data.complexity or "medium",
            progress=0,
            created_at=datetime.utcnow().isoformat() + "Z",
            estimated_value=goal_data.estimated_value,
            atomic_blocks=[]
        )

    except Exception as e:
        logger.error(f"Error creating goal for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create goal: {str(e)}"
        )


@router.put("/{user_id}/goals/{goal_id}", response_model=GoalResponse)
async def update_user_goal(
    user_id: str = Path(..., description="User ID"),
    goal_id: str = Path(..., description="Goal ID"),
    goal_data: GoalUpdateRequest = None,
    repo: GoalRepository = Depends(get_goal_repository)
) -> GoalResponse:
    """
    Update a goal for a user.

    Args:
        user_id: User ID
        goal_id: Goal ID to update
        goal_data: Updated goal data

    Returns:
        GoalResponse with updated goal details
    """
    try:
        # Verify goal exists and belongs to user
        goal = await repo.get_goal(goal_id)
        if not goal or goal.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )

        # Prepare update dict
        update_dict = {}
        if goal_data.description is not None:
            update_dict["description"] = goal_data.description
        if goal_data.importance is not None:
            update_dict["importance"] = goal_data.importance
        if goal_data.status is not None:
            update_dict["status"] = goal_data.status
        if goal_data.progress is not None:
            update_dict["progress_percentage"] = goal_data.progress
        if goal_data.estimated_value is not None:
            update_dict["estimated_value"] = goal_data.estimated_value

        update_dict["updated_at"] = datetime.utcnow()

        # Update goal
        if update_dict:
            await repo.update_goal(goal_id, update_dict)

        # Fetch and return updated goal
        updated_goal = await repo.get_goal(goal_id)
        return await _format_goal(updated_goal)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating goal {goal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update goal: {str(e)}"
        )


@router.delete("/{user_id}/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_goal(
    user_id: str = Path(..., description="User ID"),
    goal_id: str = Path(..., description="Goal ID"),
    repo: GoalRepository = Depends(get_goal_repository)
):
    """
    Delete a goal for a user.

    Args:
        user_id: User ID
        goal_id: Goal ID to delete
    """
    try:
        # Verify goal exists and belongs to user
        goal = await repo.get_goal(goal_id)
        if not goal or goal.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )

        # Delete goal
        await repo.delete_goal(goal_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting goal {goal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete goal: {str(e)}"
        )


@router.post("/{user_id}/goals/{goal_id}/complete", response_model=GoalResponse)
async def complete_user_goal(
    user_id: str = Path(..., description="User ID"),
    goal_id: str = Path(..., description="Goal ID"),
    repo: GoalRepository = Depends(get_goal_repository)
) -> GoalResponse:
    """
    Mark a goal as completed.

    Args:
        user_id: User ID
        goal_id: Goal ID to mark as completed

    Returns:
        GoalResponse with updated goal
    """
    try:
        # Verify goal exists and belongs to user
        goal = await repo.get_goal(goal_id)
        if not goal or goal.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )

        # Update goal status
        await repo.update_goal(goal_id, {
            "status": "completed",
            "progress_percentage": 100,
            "updated_at": datetime.utcnow()
        })

        # Fetch and return updated goal
        updated_goal = await repo.get_goal(goal_id)
        return await _format_goal(updated_goal)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing goal {goal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete goal: {str(e)}"
        )

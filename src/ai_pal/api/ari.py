"""
ARI (Agency Retention Index) API endpoints

Provides access to ARI metrics and snapshots for user dashboard.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from ai_pal.monitoring import get_logger
from ai_pal.storage.database import DatabaseManager, ARIRepository
from ai_pal.cache.redis_cache import RedisCache
from ai_pal.storage.cached_repositories import CachedARIRepository, create_cached_ari_repo

logger = get_logger("ai_pal.api.ari")
router = APIRouter(prefix="/api/users", tags=["ARI Metrics"])

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


def get_ari_repository() -> Union[CachedARIRepository, ARIRepository]:
    """Get ARI repository with caching if available"""
    if not _db_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized"
        )

    # Use cached repository if cache is available and enabled
    if _cache and _cache.enabled:
        return create_cached_ari_repo(_db_manager, _cache)

    # Fall back to regular repository
    return ARIRepository(_db_manager)


# ===== RESPONSE MODELS =====

class ARIDimension(BaseModel):
    """Single ARI dimension"""
    name: str = Field(..., description="Dimension name")
    value: float = Field(..., description="Dimension value (0-100)")
    trend: Optional[str] = Field(None, description="Trend: up, down, stable")


class ARISnapshot(BaseModel):
    """ARI snapshot response"""
    snapshot_id: str = Field(..., description="Unique snapshot ID")
    timestamp: str = Field(..., description="Snapshot timestamp")
    autonomy_retention: float = Field(..., description="Overall autonomy retention score")
    delta_agency: float = Field(..., description="Change in agency")
    trend: str = Field(..., description="Overall trend: improving, stable, declining")
    dimensions: List[ARIDimension] = Field(..., description="Individual ARI dimensions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ARIHistory(BaseModel):
    """ARI history response"""
    user_id: str = Field(..., description="User ID")
    latest_snapshot: ARISnapshot = Field(..., description="Most recent snapshot")
    historical_data: List[ARISnapshot] = Field(..., description="Historical snapshots (last 30 days)")
    trend_analysis: Dict[str, Any] = Field(..., description="Trend analysis and insights")


class ARIMetricsResponse(BaseModel):
    """Current ARI metrics response"""
    user_id: str = Field(..., description="User ID")
    current_score: float = Field(..., description="Current autonomy retention score")
    previous_score: Optional[float] = Field(None, description="Previous score")
    score_change: Optional[float] = Field(None, description="Score change since last snapshot")
    status: str = Field(..., description="Status: improving, stable, declining, critical")
    dimensions: List[ARIDimension] = Field(..., description="All ARI dimensions with current values")
    update_timestamp: str = Field(..., description="Timestamp of this update")


# ===== HELPER FUNCTIONS =====

def _calculate_trend(current: float, previous: Optional[float]) -> str:
    """Calculate trend based on score change"""
    if previous is None:
        return "stable"

    change = current - previous
    if change > 5:
        return "up"
    elif change < -5:
        return "down"
    else:
        return "stable"


def _get_status_from_score(score: float) -> str:
    """Determine status from ARI score"""
    if score >= 85:
        return "improving"
    elif score >= 70:
        return "stable"
    elif score >= 50:
        return "declining"
    else:
        return "critical"


async def _format_snapshot(db_row: Dict[str, Any]) -> ARISnapshot:
    """Format database snapshot to response model"""
    timestamp = db_row.get("timestamp")
    if isinstance(timestamp, datetime):
        timestamp_str = timestamp.isoformat() + "Z"
    else:
        timestamp_str = str(timestamp)

    # Extract dimensions
    dimensions = [
        ARIDimension(
            name="Decision Quality",
            value=db_row.get("decision_quality", 0),
            trend="up"
        ),
        ARIDimension(
            name="Skill Development",
            value=db_row.get("skill_development", 0),
            trend="up"
        ),
        ARIDimension(
            name="AI Reliance",
            value=db_row.get("ai_reliance", 0),
            trend="stable"
        ),
        ARIDimension(
            name="Bottleneck Resolution",
            value=db_row.get("bottleneck_resolution", 0),
            trend="up"
        ),
        ARIDimension(
            name="User Confidence",
            value=db_row.get("user_confidence", 0),
            trend="up"
        ),
        ARIDimension(
            name="Engagement",
            value=db_row.get("engagement", 0),
            trend="stable"
        ),
        ARIDimension(
            name="Autonomy Perception",
            value=db_row.get("autonomy_perception", 0),
            trend="up"
        ),
    ]

    return ARISnapshot(
        snapshot_id=db_row.get("snapshot_id", ""),
        timestamp=timestamp_str,
        autonomy_retention=db_row.get("autonomy_retention", 0),
        delta_agency=db_row.get("delta_agency", 0),
        trend=_calculate_trend(db_row.get("autonomy_retention", 0), None),
        dimensions=dimensions,
        metadata={
            "total_interactions": db_row.get("total_interactions", 0),
            "decision_count": db_row.get("decision_count", 0),
        }
    )


# ===== ENDPOINTS =====

@router.get("/{user_id}/ari", response_model=ARIMetricsResponse)
async def get_user_ari_metrics(
    user_id: str = Path(..., description="User ID"),
    repo: ARIRepository = Depends(get_ari_repository)
) -> ARIMetricsResponse:
    """
    Get current ARI metrics for a user.

    Returns the latest ARI snapshot with all dimensions and trend analysis.

    Args:
        user_id: User ID to fetch metrics for

    Returns:
        ARIMetricsResponse with current ARI metrics
    """
    try:
        # Get latest snapshot
        snapshots = await repo.get_snapshots_by_user(user_id, limit=2)

        if not snapshots:
            # Return default metrics if no snapshots exist
            return ARIMetricsResponse(
                user_id=user_id,
                current_score=50.0,
                previous_score=None,
                score_change=None,
                status="stable",
                dimensions=[
                    ARIDimension(name="Decision Quality", value=50.0),
                    ARIDimension(name="Skill Development", value=50.0),
                    ARIDimension(name="AI Reliance", value=50.0),
                    ARIDimension(name="Bottleneck Resolution", value=50.0),
                    ARIDimension(name="User Confidence", value=50.0),
                    ARIDimension(name="Engagement", value=50.0),
                    ARIDimension(name="Autonomy Perception", value=50.0),
                ],
                update_timestamp=datetime.utcnow().isoformat() + "Z"
            )

        current = snapshots[0]
        previous = snapshots[1] if len(snapshots) > 1 else None

        current_score = current.get("autonomy_retention", 50.0)
        previous_score = previous.get("autonomy_retention") if previous else None
        score_change = (current_score - previous_score) if previous_score else None

        # Build dimensions
        dimensions = [
            ARIDimension(
                name="Decision Quality",
                value=current.get("decision_quality", 0),
                trend=_calculate_trend(current.get("decision_quality", 0),
                                      previous.get("decision_quality") if previous else None)
            ),
            ARIDimension(
                name="Skill Development",
                value=current.get("skill_development", 0),
                trend=_calculate_trend(current.get("skill_development", 0),
                                      previous.get("skill_development") if previous else None)
            ),
            ARIDimension(
                name="AI Reliance",
                value=current.get("ai_reliance", 0),
                trend="stable"
            ),
            ARIDimension(
                name="Bottleneck Resolution",
                value=current.get("bottleneck_resolution", 0),
                trend=_calculate_trend(current.get("bottleneck_resolution", 0),
                                      previous.get("bottleneck_resolution") if previous else None)
            ),
            ARIDimension(
                name="User Confidence",
                value=current.get("user_confidence", 0),
                trend=_calculate_trend(current.get("user_confidence", 0),
                                      previous.get("user_confidence") if previous else None)
            ),
            ARIDimension(
                name="Engagement",
                value=current.get("engagement", 0),
                trend=_calculate_trend(current.get("engagement", 0),
                                      previous.get("engagement") if previous else None)
            ),
            ARIDimension(
                name="Autonomy Perception",
                value=current.get("autonomy_perception", 0),
                trend=_calculate_trend(current.get("autonomy_perception", 0),
                                      previous.get("autonomy_perception") if previous else None)
            ),
        ]

        return ARIMetricsResponse(
            user_id=user_id,
            current_score=current_score,
            previous_score=previous_score,
            score_change=score_change,
            status=_get_status_from_score(current_score),
            dimensions=dimensions,
            update_timestamp=datetime.utcnow().isoformat() + "Z"
        )

    except Exception as e:
        logger.error(f"Error fetching ARI metrics for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch ARI metrics: {str(e)}"
        )


@router.get("/{user_id}/ari/history", response_model=ARIHistory)
async def get_user_ari_history(
    user_id: str = Path(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days of history to fetch"),
    repo: ARIRepository = Depends(get_ari_repository)
) -> ARIHistory:
    """
    Get ARI history for a user over a time period.

    Returns historical snapshots and trend analysis.

    Args:
        user_id: User ID to fetch history for
        days: Number of days of history to return (default: 30, max: 365)

    Returns:
        ARIHistory with historical snapshots and trend analysis
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get snapshots
        snapshots = await repo.get_snapshots_by_user(
            user_id,
            start_date=start_date,
            end_date=end_date,
            limit=None
        )

        if not snapshots:
            return ARIHistory(
                user_id=user_id,
                latest_snapshot=ARISnapshot(
                    snapshot_id="",
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    autonomy_retention=50.0,
                    delta_agency=0.0,
                    trend="stable",
                    dimensions=[
                        ARIDimension(name="Decision Quality", value=50.0),
                        ARIDimension(name="Skill Development", value=50.0),
                        ARIDimension(name="AI Reliance", value=50.0),
                        ARIDimension(name="Bottleneck Resolution", value=50.0),
                        ARIDimension(name="User Confidence", value=50.0),
                        ARIDimension(name="Engagement", value=50.0),
                        ARIDimension(name="Autonomy Perception", value=50.0),
                    ]
                ),
                historical_data=[],
                trend_analysis={}
            )

        # Format snapshots
        formatted_snapshots = [await _format_snapshot(s) for s in snapshots]
        latest = formatted_snapshots[0] if formatted_snapshots else None

        # Calculate trend analysis
        if len(formatted_snapshots) > 1:
            scores = [s.autonomy_retention for s in formatted_snapshots]
            avg_score = sum(scores) / len(scores)
            trend_direction = "improving" if scores[0] > scores[-1] else "declining"
        else:
            avg_score = latest.autonomy_retention if latest else 50.0
            trend_direction = "stable"

        trend_analysis = {
            "average_score": avg_score,
            "trend_direction": trend_direction,
            "period_days": days,
            "snapshot_count": len(formatted_snapshots),
        }

        return ARIHistory(
            user_id=user_id,
            latest_snapshot=latest or ARISnapshot(
                snapshot_id="",
                timestamp=datetime.utcnow().isoformat() + "Z",
                autonomy_retention=50.0,
                delta_agency=0.0,
                trend="stable",
                dimensions=[]
            ),
            historical_data=formatted_snapshots[1:] if len(formatted_snapshots) > 1 else [],
            trend_analysis=trend_analysis
        )

    except Exception as e:
        logger.error(f"Error fetching ARI history for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch ARI history: {str(e)}"
        )

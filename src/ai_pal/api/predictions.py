"""
Predictions and Analytics API Endpoints

Provides endpoints for ARI trend forecasting, goal completion predictions,
and system health predictions.
"""

from fastapi import APIRouter, Path, Query, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from ai_pal.monitoring import get_logger
from ai_pal.storage.database import DatabaseManager, ARIRepository, GoalRepository
from ai_pal.cache.redis_cache import RedisCache
from ai_pal.analytics.forecasting import ARIForecaster
from ai_pal.analytics.goal_prediction import GoalPredictor

logger = get_logger("ai_pal.api.predictions")
router = APIRouter(prefix="/api/users", tags=["Predictions"])

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


# ===== RESPONSE MODELS =====


class ARIPrediction(BaseModel):
    """ARI trend prediction"""

    can_forecast: bool = Field(..., description="Whether forecast is possible")
    predicted_score: Optional[float] = Field(None, description="Predicted ARI score")
    lower_bound: Optional[float] = Field(None, description="Confidence interval lower bound")
    upper_bound: Optional[float] = Field(None, description="Confidence interval upper bound")
    confidence: float = Field(..., description="Confidence level (0-1)")
    trend: str = Field(..., description="Trend: improving, stable, declining, unknown")
    slope: Optional[float] = Field(None, description="Regression slope")
    days_ahead: int = Field(..., description="Number of days forecast")
    data_points_used: int = Field(..., description="Number of historical data points")
    message: Optional[str] = Field(None, description="Message if forecast not possible")


class GoalPrediction(BaseModel):
    """Goal completion prediction"""

    prediction: str = Field(..., description="will_complete, at_risk, unlikely")
    completion_probability: float = Field(..., description="Probability of completion (0-1)")
    estimated_completion_date: Optional[str] = Field(None, description="ISO format date")
    days_to_completion: Optional[float] = Field(None, description="Estimated days to complete")
    risk_level: str = Field(..., description="low, medium, high, critical")
    recommendation: str = Field(..., description="Action recommendation")
    deadline_days_remaining: Optional[float] = Field(None, description="Days until deadline")


class SystemHealthPrediction(BaseModel):
    """System health prediction"""

    service: str = Field(..., description="Service name")
    prediction: str = Field(..., description="healthy, warning, critical")
    confidence: float = Field(..., description="Prediction confidence (0-1)")
    recommendation: str = Field(..., description="Action recommendation")
    metric_trend: str = Field(..., description="Trend of key metrics")
    estimated_failure_days: Optional[int] = Field(None, description="Days until potential failure")


# ===== DEPENDENCIES =====


def get_ari_repository() -> ARIRepository:
    """Get ARI repository"""
    if not _db_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized",
        )
    return ARIRepository(_db_manager)


def get_goal_repository() -> GoalRepository:
    """Get goal repository"""
    if not _db_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database not initialized",
        )
    return GoalRepository(_db_manager)


# ===== ENDPOINTS =====


@router.get("/{user_id}/ari/forecast", response_model=ARIPrediction)
async def forecast_ari_trend(
    user_id: str = Path(..., description="User ID"),
    days_ahead: int = Query(7, ge=1, le=90, description="Days to forecast"),
    repo: ARIRepository = Depends(get_ari_repository),
) -> ARIPrediction:
    """
    Forecast ARI trend for a user.

    Uses linear regression on historical ARI snapshots to predict future scores
    with confidence intervals.

    Args:
        user_id: User ID
        days_ahead: Number of days to forecast (1-90)

    Returns:
        ARIPrediction with forecast score and confidence
    """
    try:
        # Get historical ARI snapshots
        snapshots = await repo.get_snapshots_by_user(user_id, limit=30)

        if not snapshots:
            return ARIPrediction(
                can_forecast=False,
                confidence=0.0,
                trend="unknown",
                days_ahead=days_ahead,
                data_points_used=0,
                message="No historical ARI data available",
            )

        # Convert to forecast format
        ari_history = [
            {
                "timestamp": snap.get("created_at", snap.get("timestamp", "")),
                "autonomy_retention": snap.get("autonomy_retention", 50),
            }
            for snap in snapshots
        ]

        # Run forecast
        forecast_result = ARIForecaster.forecast_ari_trend(
            ari_history, days_ahead=days_ahead
        )

        logger.info(f"Forecasted ARI trend for user {user_id}: {forecast_result}")

        return ARIPrediction(**forecast_result)

    except Exception as e:
        logger.error(f"Error forecasting ARI for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecast failed: {str(e)}",
        )


@router.get("/{user_id}/goals/{goal_id}/completion-estimate", response_model=GoalPrediction)
async def predict_goal_completion(
    user_id: str = Path(..., description="User ID"),
    goal_id: str = Path(..., description="Goal ID"),
    repo: GoalRepository = Depends(get_goal_repository),
) -> GoalPrediction:
    """
    Predict goal completion probability and timeline.

    Based on current progress, time elapsed, and deadline to estimate
    completion probability and likely completion date.

    Args:
        user_id: User ID
        goal_id: Goal ID

    Returns:
        GoalPrediction with completion probability and estimate
    """
    try:
        # Get goal
        goal = await repo.get_goal_by_id(goal_id)

        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goal {goal_id} not found",
            )

        # Get historical completion rate for similar goals
        all_goals = await repo.get_active_goals(user_id, limit=100)
        completed = len([g for g in all_goals if g.get("status") == "completed"])
        total = len(all_goals)
        historical_rate = (completed / total) if total > 0 else 0.7

        # Predict
        prediction = GoalPredictor.predict_goal_outcome(goal, historical_rate)

        logger.info(
            f"Predicted completion for goal {goal_id} (user {user_id}): {prediction}"
        )

        return GoalPrediction(**prediction)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting goal completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )


@router.get("/{user_id}/system/predictions")
async def predict_system_health(
    user_id: str = Path(..., description="User ID"),
) -> Dict[str, Any]:
    """
    Predict system health and potential issues.

    Analyzes current metrics trends to predict service health and recommend
    preventive actions.

    Args:
        user_id: User ID

    Returns:
        Dict with health predictions for each service
    """
    try:
        # Get current system health
        from ai_pal.monitoring import get_health_checker

        checker = get_health_checker()
        health = await checker.check_health()

        predictions = []

        for service_status in health.services:
            service_name = service_status.name
            status_value = service_status.status.value

            # Simple prediction logic
            if status_value == "healthy":
                prediction = "healthy"
                confidence = 0.95
                recommendation = "System is operating normally"
                metric_trend = "stable"
                estimated_failure_days = None
            elif status_value == "warning":
                prediction = "warning"
                confidence = 0.7
                recommendation = "Monitor metrics closely. Consider optimizing resources."
                metric_trend = "declining"
                estimated_failure_days = 7
            else:
                prediction = "critical"
                confidence = 0.9
                recommendation = "Immediate action required. Review system logs and resource usage."
                metric_trend = "critical"
                estimated_failure_days = 1

            predictions.append(
                {
                    "service": service_name,
                    "prediction": prediction,
                    "confidence": confidence,
                    "recommendation": recommendation,
                    "metric_trend": metric_trend,
                    "estimated_failure_days": estimated_failure_days,
                }
            )

        logger.info(f"Generated system health predictions for user {user_id}")

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "user_id": user_id,
            "predictions": predictions,
        }

    except Exception as e:
        logger.error(f"Error predicting system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )

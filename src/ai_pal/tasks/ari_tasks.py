"""
ARI (Autonomy Retention Index) Background Tasks

Tasks for:
- Periodic ARI snapshot aggregation and analysis
- Trend calculation
- Alert generation for agency decline
"""

import asyncio
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import json

from celery import shared_task
from loguru import logger

from ai_pal.tasks.base_task import AIpalTask


class ARIAggregateSnapshotsTask(AIpalTask):
    """Aggregate ARI snapshots for analytics and trend calculation"""

    name = "ai_pal.tasks.ari_tasks.aggregate_snapshots"
    bind = True
    max_retries = 3
    default_retry_delay = 60

    def run(
        self,
        user_id: Optional[str] = None,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Aggregate ARI snapshots

        Args:
            user_id: User ID to aggregate (None for all users)
            time_window_hours: Time window for aggregation

        Returns:
            Aggregation result
        """
        try:
            logger.info(
                f"Starting ARI aggregation for user={user_id}, "
                f"window={time_window_hours}h"
            )

            # Run async database operations using asyncio.run()
            return asyncio.run(self._aggregate_snapshots_async(user_id, time_window_hours))

        except Exception as exc:
            logger.error(f"Error aggregating ARI snapshots: {exc}")
            raise

    async def _aggregate_snapshots_async(
        self,
        user_id: Optional[str],
        time_window_hours: int
    ) -> Dict[str, Any]:
        """
        Async implementation of snapshot aggregation

        Args:
            user_id: User ID to aggregate
            time_window_hours: Time window for aggregation

        Returns:
            Aggregation result
        """
        # Import here to avoid circular imports
        from ai_pal.storage.database import ARIRepository

        if not self.db_manager:
            raise RuntimeError("Database manager not configured")

        ari_repo = ARIRepository(self.db_manager)

        # Get snapshots from the time window
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_window_hours)

        snapshots = await ari_repo.get_snapshots_by_user(
            user_id=user_id or "all_users",
            start_date=start_time,
            end_date=end_time
        )

        if not snapshots:
            logger.info(f"No snapshots found for user {user_id}")
            return {
                "aggregated_count": 0,
                "time_window_hours": time_window_hours,
                "user_id": user_id
            }

        # Calculate aggregate statistics
        metrics = {
            "decision_quality": [],
            "skill_development": [],
            "ai_reliance": [],
            "bottleneck_resolution": [],
            "user_confidence": [],
            "engagement": [],
            "autonomy_perception": [],
            "autonomy_retention": [],
            "delta_agency": []
        }

        for snapshot in snapshots:
            for metric_name in metrics:
                if metric_name in snapshot:
                    metrics[metric_name].append(snapshot[metric_name])

        # Calculate statistics
        result = {
            "user_id": user_id,
            "time_window_hours": time_window_hours,
            "aggregated_count": len(snapshots),
            "snapshot_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "metrics_summary": {}
        }

        for metric_name, values in metrics.items():
            if values:
                result["metrics_summary"][metric_name] = {
                    "count": len(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1]
                }

        logger.info(
            f"ARI aggregation complete: {len(snapshots)} snapshots aggregated"
        )

        return result


class ARITrendAnalysisTask(AIpalTask):
    """Analyze ARI trends to detect agency decline patterns"""

    name = "ai_pal.tasks.ari_tasks.analyze_trends"
    bind = True
    max_retries = 3
    default_retry_delay = 60

    def run(
        self,
        user_id: str,
        lookback_days: int = 30,
        threshold_percent: float = 10.0
    ) -> Dict[str, Any]:
        """
        Analyze ARI trends for agency decline

        Args:
            user_id: User ID to analyze
            lookback_days: Days to look back for trend analysis
            threshold_percent: Decline threshold in percentage

        Returns:
            Trend analysis result
        """
        try:
            logger.info(
                f"Starting ARI trend analysis for user={user_id}, "
                f"lookback={lookback_days}d"
            )

            # Run async database operations using asyncio.run()
            return asyncio.run(self._analyze_trends_async(user_id, lookback_days, threshold_percent))

        except Exception as exc:
            logger.error(f"Error analyzing ARI trends: {exc}")
            raise

    async def _analyze_trends_async(
        self,
        user_id: str,
        lookback_days: int,
        threshold_percent: float
    ) -> Dict[str, Any]:
        """
        Async implementation of trend analysis

        Args:
            user_id: User ID to analyze
            lookback_days: Days to look back
            threshold_percent: Decline threshold

        Returns:
            Trend analysis result
        """
        from ai_pal.storage.database import ARIRepository

        if not self.db_manager:
            raise RuntimeError("Database manager not configured")

        ari_repo = ARIRepository(self.db_manager)

        # Get recent snapshots
        end_time = datetime.now()
        start_time = end_time - timedelta(days=lookback_days)

        snapshots = await ari_repo.get_snapshots_by_user(
            user_id=user_id,
            start_date=start_time,
            end_date=end_time
        )

        if len(snapshots) < 2:
            return {
                "user_id": user_id,
                "status": "insufficient_data",
                "message": "Not enough snapshots for trend analysis"
            }

        # Sort by timestamp
        snapshots.sort(key=lambda s: s["timestamp"])

        # Calculate trends
        trends = {}
        alerts = []

        metrics = [
            "autonomy_retention",
            "decision_quality",
            "skill_development",
            "engagement"
        ]

        for metric in metrics:
            values = [s[metric] for s in snapshots if metric in s]
            if len(values) >= 2:
                first_value = values[0]
                last_value = values[-1]
                change_percent = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0

                trends[metric] = {
                    "first_value": first_value,
                    "last_value": last_value,
                    "change_percent": change_percent,
                    "data_points": len(values)
                }

                # Alert if decline exceeds threshold
                if change_percent < -threshold_percent:
                    alerts.append({
                        "metric": metric,
                        "severity": "warning" if change_percent > -20 else "critical",
                        "decline_percent": abs(change_percent),
                        "message": f"{metric} declined {abs(change_percent):.1f}%"
                    })

        result = {
            "user_id": user_id,
            "lookback_days": lookback_days,
            "data_points": len(snapshots),
            "trends": trends,
            "alerts": alerts,
            "analysis_timestamp": datetime.now().isoformat()
        }

        if alerts:
            logger.warning(f"ARI trend analysis found {len(alerts)} alerts for user {user_id}")

        return result


# Celery task instances
@shared_task(bind=True, base=ARIAggregateSnapshotsTask)
def aggregate_ari_snapshots(self, user_id: Optional[str] = None, time_window_hours: int = 24):
    """Aggregate ARI snapshots - Celery task wrapper"""
    return self.run(user_id=user_id, time_window_hours=time_window_hours)


@shared_task(bind=True, base=ARITrendAnalysisTask)
def analyze_ari_trends(self, user_id: str, lookback_days: int = 30, threshold_percent: float = 10.0):
    """Analyze ARI trends - Celery task wrapper"""
    return self.run(user_id=user_id, lookback_days=lookback_days, threshold_percent=threshold_percent)

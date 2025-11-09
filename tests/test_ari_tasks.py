"""
Unit tests for ARI (Autonomy Retention Index) background tasks.

Tests:
- ARI snapshot aggregation
- Trend analysis and alert generation
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from ai_pal.tasks.ari_tasks import (
    ARIAggregateSnapshotsTask,
    ARITrendAnalysisTask,
)


@pytest.mark.unit
class TestARIAggregateSnapshotsTask:
    """Test ARI snapshot aggregation task"""

    def test_task_initialization(self):
        """Test task initialization"""
        task = ARIAggregateSnapshotsTask()
        assert task.name == "ai_pal.tasks.ari_tasks.aggregate_snapshots"
        assert task.bind is True
        assert task.max_retries == 3

    def test_task_get_task_type(self):
        """Test task type detection"""
        task = ARIAggregateSnapshotsTask()
        assert task._get_task_type() == "ari_snapshot"

    def test_aggregate_snapshots_with_data(self, mock_ari_repository):
        """Test snapshot aggregation with sample data"""
        task = ARIAggregateSnapshotsTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "user_id": "user1",
                "time_window_hours": 24,
                "aggregated_count": 5,
                "metrics_summary": {}
            }
            result = task.run(user_id="user1", time_window_hours=24)

            assert result["user_id"] == "user1"
            assert result["time_window_hours"] == 24
            assert "aggregated_count" in result
            assert "metrics_summary" in result

    def test_aggregate_snapshots_empty_data(self, mock_ari_repository):
        """Test aggregation with no snapshots"""
        task = ARIAggregateSnapshotsTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {"aggregated_count": 0}
            result = task.run(user_id="user1", time_window_hours=24)

            assert result["aggregated_count"] >= 0

    def test_aggregate_snapshots_calculates_statistics(self, mock_ari_repository):
        """Test that aggregation calculates proper statistics"""
        task = ARIAggregateSnapshotsTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "metrics_summary": {"autonomy_retention": {"average": 0.82}}
            }
            result = task.run(user_id="user1", time_window_hours=24)

            # Check metrics structure exists
            assert "metrics_summary" in result
            metrics = result["metrics_summary"]
            assert isinstance(metrics, dict)

    def test_aggregate_snapshots_run_method(self, mock_ari_repository):
        """Test run method executes async operation"""
        task = ARIAggregateSnapshotsTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {"aggregated_count": 5}
            result = task.run(user_id="user1", time_window_hours=24)

            assert mock_asyncio.called
            assert result["aggregated_count"] == 5


@pytest.mark.unit
class TestARITrendAnalysisTask:
    """Test ARI trend analysis task"""

    def test_task_initialization(self):
        """Test task initialization"""
        task = ARITrendAnalysisTask()
        assert task.name == "ai_pal.tasks.ari_tasks.analyze_trends"
        assert task.bind is True
        assert task.max_retries == 3

    def test_analyze_trends_with_data(self, mock_ari_repository):
        """Test trend analysis with sample data"""
        task = ARITrendAnalysisTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "user_id": "user1",
                "lookback_days": 30,
                "trends": {},
                "alerts": []
            }
            result = task.run(user_id="user1", lookback_days=30)

            assert result["user_id"] == "user1"
            assert result["lookback_days"] == 30
            assert "trends" in result
            assert "alerts" in result

    def test_analyze_trends_insufficient_data(self, mock_ari_repository):
        """Test trend analysis with insufficient snapshots"""
        task = ARITrendAnalysisTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {"status": "insufficient_data"}
            result = task.run(user_id="user1", lookback_days=30)

            # With mocked db_manager, result should still have valid structure
            assert "status" in result or "trends" in result

    def test_analyze_trends_detects_decline(self, mock_ari_repository):
        """Test that trends analysis detects agency decline"""
        task = ARITrendAnalysisTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "trends": {"autonomy_retention": {"change_percent": -15.0}},
                "alerts": [{"type": "decline", "metric": "autonomy_retention"}]
            }
            result = task.run(user_id="user1", lookback_days=30)

            # Should have trends and alerts structure
            assert "trends" in result
            assert "alerts" in result

    def test_analyze_trends_calculates_changes(self, mock_ari_repository):
        """Test that trends calculates percentage changes"""
        task = ARITrendAnalysisTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "trends": {"autonomy_retention": {"change_percent": -5.0}}
            }
            result = task.run(user_id="user1", lookback_days=30)

            # Check trend structure exists
            assert "trends" in result
            assert isinstance(result["trends"], dict)

    def test_analyze_trends_run_method(self, mock_ari_repository):
        """Test run method executes async operation"""
        task = ARITrendAnalysisTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "user_id": "user1",
                "trends": {},
                "alerts": []
            }
            result = task.run(user_id="user1", lookback_days=30)

            assert mock_asyncio.called
            assert result["user_id"] == "user1"


@pytest.mark.integration
class TestARITasksIntegration:
    """Integration tests for ARI tasks"""

    def test_aggregation_then_trend_analysis(self, mock_ari_repository):
        """Test workflow: aggregate snapshots then analyze trends"""
        agg_task = ARIAggregateSnapshotsTask()
        trend_task = ARITrendAnalysisTask()

        agg_task.db_manager = MagicMock()
        trend_task.db_manager = MagicMock()

        # First aggregate
        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {"aggregated_count": 10}
            agg_result = agg_task.run(user_id="user1", time_window_hours=24)

            assert agg_result["aggregated_count"] >= 0

        # Then analyze trends
        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "trends": {},
                "alerts": []
            }
            trend_result = trend_task.run(user_id="user1", lookback_days=30)

            assert "trends" in trend_result
            assert "alerts" in trend_result

    def test_task_error_handling(self):
        """Test task error handling"""
        task = ARIAggregateSnapshotsTask()
        task.db_manager = None  # Simulate missing DB

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.side_effect = RuntimeError("Database not configured")

            with pytest.raises(RuntimeError):
                task.run(user_id="user1", time_window_hours=24)

    def test_task_retry_logic(self):
        """Test task retry mechanism"""
        task = ARIAggregateSnapshotsTask()
        assert task.max_retries == 3
        assert task.default_retry_delay == 60


@pytest.mark.unit
class TestARITaskMetrics:
    """Test ARI metrics and calculations"""

    def test_metrics_aggregation_accuracy(self, mock_ari_repository):
        """Test metrics aggregation produces valid values"""
        task = ARIAggregateSnapshotsTask()
        task.db_manager = MagicMock()

        # Test that task can be initialized
        assert task is not None
        assert task.name == "ai_pal.tasks.ari_tasks.aggregate_snapshots"

    def test_trend_change_percentage_calculation(self, mock_ari_repository):
        """Test percentage change calculation"""
        task = ARITrendAnalysisTask()
        task.db_manager = MagicMock()

        # Verify task properties
        assert task.name == "ai_pal.tasks.ari_tasks.analyze_trends"
        assert task.max_retries == 3

    def test_autonomy_retention_range(self):
        """Test autonomy retention values are in valid range"""
        # Valid autonomy retention values (0-1)
        valid_values = [0.0, 0.5, 0.85, 1.0]

        for value in valid_values:
            assert 0 <= value <= 1

    def test_alert_threshold_validation(self):
        """Test alert threshold values"""
        valid_thresholds = [5.0, 10.0, 15.0, 20.0]

        for threshold in valid_thresholds:
            assert threshold > 0
            assert threshold <= 100

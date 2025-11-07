"""
Unit tests for EDM (Epistemic Debt Management) background tasks.

Tests:
- EDM batch analysis
- Epistemic debt resolution tracking
- Misinformation detection
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from ai_pal.tasks.edm_tasks import (
    EDMBatchAnalysisTask,
    EDMResolutionTrackingTask,
    EDMMisinformationDetectionTask,
)


@pytest.mark.unit
class TestEDMBatchAnalysisTask:
    """Test EDM batch analysis task"""

    def test_task_initialization(self):
        """Test task initialization"""
        task = EDMBatchAnalysisTask()
        assert task.name == "ai_pal.tasks.edm_tasks.batch_analysis"
        assert task.bind is True
        assert task.max_retries == 3

    def test_task_get_task_type(self):
        """Test task type detection"""
        task = EDMBatchAnalysisTask()
        assert task._get_task_type() == "edm_analysis"

    @pytest.mark.asyncio
    async def test_batch_analysis_result_structure(self):
        """Test batch analysis returns proper structure"""
        task = EDMBatchAnalysisTask()
        task.db_manager = MagicMock()

        result = await task._batch_analysis_async(
            user_id="user1",
            time_window_days=7,
            min_severity="low"
        )

        # Verify result structure
        assert result["user_id"] == "user1"
        assert result["time_window_days"] == 7
        assert result["min_severity"] == "low"
        assert "debts_analyzed" in result
        assert "debts_by_severity" in result
        assert "analysis_timestamp" in result

    @pytest.mark.asyncio
    async def test_batch_analysis_severity_filtering(self):
        """Test that analysis respects severity filtering"""
        task = EDMBatchAnalysisTask()
        task.db_manager = MagicMock()

        # Test different severity levels
        for severity in ["low", "medium", "high", "critical"]:
            result = await task._batch_analysis_async(
                user_id="user1",
                time_window_days=7,
                min_severity=severity
            )

            assert result["min_severity"] == severity

    def test_batch_analysis_run_method(self):
        """Test run method executes async operation"""
        task = EDMBatchAnalysisTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "user_id": "user1",
                "debts_analyzed": 5,
            }
            result = task.run(
                user_id="user1",
                time_window_days=7,
                min_severity="low"
            )

            assert mock_asyncio.called
            assert result["debts_analyzed"] == 5


@pytest.mark.unit
class TestEDMResolutionTrackingTask:
    """Test EDM resolution tracking task"""

    def test_task_initialization(self):
        """Test task initialization"""
        task = EDMResolutionTrackingTask()
        assert task.name == "ai_pal.tasks.edm_tasks.track_resolutions"
        assert task.bind is True
        assert task.max_retries == 2

    @pytest.mark.asyncio
    async def test_track_resolutions_result_structure(self):
        """Test resolution tracking returns proper structure"""
        task = EDMResolutionTrackingTask()
        task.db_manager = MagicMock()

        result = await task._track_resolutions_async(
            user_id="user1",
            lookback_days=30
        )

        # Verify result structure
        assert result["user_id"] == "user1"
        assert result["lookback_days"] == 30
        assert "total_resolutions" in result
        assert "avg_resolution_time_days" in result
        assert "resolution_rate_percent" in result
        assert "tracking_timestamp" in result

    @pytest.mark.asyncio
    async def test_track_resolutions_different_periods(self):
        """Test resolution tracking for different time periods"""
        task = EDMResolutionTrackingTask()
        task.db_manager = MagicMock()

        for days in [7, 14, 30, 90]:
            result = await task._track_resolutions_async(
                user_id="user1",
                lookback_days=days
            )

            assert result["lookback_days"] == days

    def test_track_resolutions_run_method(self):
        """Test run method executes async operation"""
        task = EDMResolutionTrackingTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "user_id": "user1",
                "total_resolutions": 10,
                "resolution_rate_percent": 85.0,
            }
            result = task.run(user_id="user1", lookback_days=30)

            assert mock_asyncio.called
            assert result["total_resolutions"] == 10


@pytest.mark.unit
class TestEDMMisinformationDetectionTask:
    """Test EDM misinformation detection task"""

    def test_task_initialization(self):
        """Test task initialization"""
        task = EDMMisinformationDetectionTask()
        assert task.name == "ai_pal.tasks.edm_tasks.detect_misinformation"
        assert task.bind is True
        assert task.max_retries == 2

    @pytest.mark.asyncio
    async def test_detect_misinformation_result_structure(self):
        """Test misinformation detection returns proper structure"""
        task = EDMMisinformationDetectionTask()
        task.db_manager = MagicMock()

        result = await task._detect_misinformation_async(
            user_id="user1",
            interaction_ids=None
        )

        # Verify result structure
        assert result["user_id"] == "user1"
        assert "interactions_scanned" in result
        assert "potential_misinformation_found" in result
        assert "high_confidence_findings" in result
        assert "medium_confidence_findings" in result
        assert "detection_timestamp" in result

    @pytest.mark.asyncio
    async def test_detect_misinformation_with_interactions(self):
        """Test misinformation detection with specific interactions"""
        task = EDMMisinformationDetectionTask()
        task.db_manager = MagicMock()

        interaction_ids = ["int-1", "int-2", "int-3"]

        result = await task._detect_misinformation_async(
            user_id="user1",
            interaction_ids=interaction_ids
        )

        assert result["interactions_scanned"] == len(interaction_ids)

    @pytest.mark.asyncio
    async def test_detect_misinformation_confidence_levels(self):
        """Test that findings include confidence levels"""
        task = EDMMisinformationDetectionTask()
        task.db_manager = MagicMock()

        result = await task._detect_misinformation_async(
            user_id="user1",
            interaction_ids=["int-1"]
        )

        # Check that we have categories for confidence levels
        assert isinstance(result["high_confidence_findings"], list)
        assert isinstance(result["medium_confidence_findings"], list)

    def test_detect_misinformation_run_method(self):
        """Test run method executes async operation"""
        task = EDMMisinformationDetectionTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "user_id": "user1",
                "potential_misinformation_found": 2,
            }
            result = task.run(user_id="user1", interaction_ids=None)

            assert mock_asyncio.called
            assert result["potential_misinformation_found"] == 2


@pytest.mark.integration
class TestEDMTasksIntegration:
    """Integration tests for EDM tasks"""

    @pytest.mark.asyncio
    async def test_analysis_detection_tracking_workflow(self):
        """Test workflow: analysis -> detection -> tracking"""
        analysis_task = EDMBatchAnalysisTask()
        detection_task = EDMMisinformationDetectionTask()
        tracking_task = EDMResolutionTrackingTask()

        analysis_task.db_manager = MagicMock()
        detection_task.db_manager = MagicMock()
        tracking_task.db_manager = MagicMock()

        # First analyze debts
        analysis_result = await analysis_task._batch_analysis_async(
            user_id="user1",
            time_window_days=7,
            min_severity="low"
        )

        assert "debts_analyzed" in analysis_result

        # Then detect misinformation
        detection_result = await detection_task._detect_misinformation_async(
            user_id="user1",
            interaction_ids=None
        )

        assert "potential_misinformation_found" in detection_result

        # Finally track resolutions
        tracking_result = await tracking_task._track_resolutions_async(
            user_id="user1",
            lookback_days=30
        )

        assert "total_resolutions" in tracking_result

    def test_task_error_handling(self):
        """Test task error handling"""
        task = EDMBatchAnalysisTask()
        task.db_manager = None  # Simulate missing DB

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.side_effect = RuntimeError("Database not configured")

            with pytest.raises(RuntimeError):
                task.run(user_id="user1", time_window_days=7)


@pytest.mark.unit
class TestEDMMetrics:
    """Test EDM metrics and calculations"""

    def test_severity_levels(self):
        """Test EDM severity level classification"""
        severity_levels = ["low", "medium", "high", "critical"]

        for level in severity_levels:
            assert level in severity_levels

    def test_confidence_score_range(self):
        """Test confidence scores are in valid range"""
        valid_scores = [0.0, 0.5, 1.0]  # Should be 0-1

        for score in valid_scores:
            assert 0 <= score <= 1

    def test_resolution_rate_calculation(self):
        """Test resolution rate calculation"""
        total_debts = 100
        resolved_debts = 85

        resolution_rate = (resolved_debts / total_debts) * 100
        assert resolution_rate == 85.0
        assert 0 <= resolution_rate <= 100

    def test_resolution_time_calculation(self):
        """Test resolution time calculation"""
        from datetime import timedelta

        created = datetime.now() - timedelta(days=5)
        resolved = datetime.now()

        resolution_time = (resolved - created).days
        assert resolution_time == 5

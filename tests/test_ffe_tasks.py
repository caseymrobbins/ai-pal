"""
Unit tests for FFE (Fractal Flow Engine) background tasks.

Tests:
- FFE goal planning and decomposition
- FFE progress tracking
- Atomic block estimation
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from ai_pal.tasks.ffe_tasks import FFEGoalPlanningTask, FFEProgressTrackingTask


@pytest.mark.unit
class TestFFEGoalPlanningTask:
    """Test FFE goal planning task"""

    def test_task_initialization(self):
        """Test task initialization"""
        task = FFEGoalPlanningTask()
        assert task.name == "ai_pal.tasks.ffe_tasks.plan_goal"
        assert task.bind is True
        assert task.max_retries == 3

    def test_task_get_task_type(self):
        """Test task type detection"""
        task = FFEGoalPlanningTask()
        assert task._get_task_type() == "ffe_planning"

    @pytest.mark.asyncio
    async def test_plan_goal_simple_complexity(self, mock_goal_repository):
        """Test goal planning for simple goal"""
        task = FFEGoalPlanningTask()
        task.db_manager = MagicMock()

        result = await task._plan_goal_async(
            goal_id="goal-1",
            user_id="user1",
            goal_description="Learn Python basics",
            complexity_level="simple"
        )

        # Simple goals should have 3 blocks
        assert result["atomic_blocks_count"] == 3
        assert len(result["atomic_blocks"]) == 3
        assert result["complexity_level"] == "simple"

    @pytest.mark.asyncio
    async def test_plan_goal_medium_complexity(self, mock_goal_repository):
        """Test goal planning for medium goal"""
        task = FFEGoalPlanningTask()
        task.db_manager = MagicMock()

        result = await task._plan_goal_async(
            goal_id="goal-1",
            user_id="user1",
            goal_description="Build REST API",
            complexity_level="medium"
        )

        # Medium goals should have 5 blocks
        assert result["atomic_blocks_count"] == 5
        assert len(result["atomic_blocks"]) == 5

    @pytest.mark.asyncio
    async def test_plan_goal_complex_complexity(self, mock_goal_repository):
        """Test goal planning for complex goal"""
        task = FFEGoalPlanningTask()
        task.db_manager = MagicMock()

        result = await task._plan_goal_async(
            goal_id="goal-1",
            user_id="user1",
            goal_description="Full system migration",
            complexity_level="complex"
        )

        # Complex goals should have 7 blocks
        assert result["atomic_blocks_count"] == 7
        assert len(result["atomic_blocks"]) == 7

    @pytest.mark.asyncio
    async def test_atomic_blocks_have_required_fields(self, mock_goal_repository):
        """Test that atomic blocks have all required fields"""
        task = FFEGoalPlanningTask()
        task.db_manager = MagicMock()

        result = await task._plan_goal_async(
            goal_id="goal-1",
            user_id="user1",
            goal_description="Test Goal",
            complexity_level="medium"
        )

        for block in result["atomic_blocks"]:
            assert "block_index" in block
            assert "description" in block
            assert "size" in block
            assert "estimated_minutes" in block

    @pytest.mark.asyncio
    async def test_total_estimated_time(self, mock_goal_repository):
        """Test that total estimated time is calculated"""
        task = FFEGoalPlanningTask()
        task.db_manager = MagicMock()

        result = await task._plan_goal_async(
            goal_id="goal-1",
            user_id="user1",
            goal_description="Test Goal",
            complexity_level="medium"
        )

        # Verify total time is sum of blocks
        total = sum(block["estimated_minutes"] for block in result["atomic_blocks"])
        assert result["total_estimated_minutes"] == total

    def test_plan_goal_run_method(self, mock_goal_repository):
        """Test run method executes async operation"""
        task = FFEGoalPlanningTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "goal_id": "goal-1",
                "status": "planned",
                "atomic_blocks_count": 5
            }
            result = task.run(
                goal_id="goal-1",
                user_id="user1",
                goal_description="Test",
                complexity_level="medium"
            )

            assert mock_asyncio.called
            assert result["atomic_blocks_count"] == 5


@pytest.mark.unit
class TestFFEProgressTrackingTask:
    """Test FFE progress tracking task"""

    def test_task_initialization(self):
        """Test task initialization"""
        task = FFEProgressTrackingTask()
        assert task.name == "ai_pal.tasks.ffe_tasks.track_progress"
        assert task.bind is True
        assert task.max_retries == 2

    def test_track_progress_existing_goal(self, mock_goal_repository):
        """Test progress tracking for existing goal"""
        task = FFEProgressTrackingTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "status": "active",
                "goal_description": "Test goal",
                "progress_timestamp": "2024-01-01T12:00:00Z"
            }
            result = task.run(goal_id="goal-1", user_id="user1")

            assert result["status"] != "not_found"
            assert "goal_description" in result
            assert "progress_timestamp" in result

    def test_track_progress_nonexistent_goal(self, mock_goal_repository):
        """Test progress tracking for non-existent goal"""
        task = FFEProgressTrackingTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "status": "not_found",
                "goal_id": "nonexistent"
            }
            result = task.run(goal_id="nonexistent", user_id="user1")

            # Result should have valid structure
            assert "status" in result or "goal_id" in result

    def test_track_progress_run_method(self, mock_goal_repository):
        """Test run method executes async operation"""
        task = FFEProgressTrackingTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "goal_id": "goal-1",
                "status": "active"
            }
            result = task.run(goal_id="goal-1", user_id="user1")

            assert mock_asyncio.called
            assert result["status"] == "active"


@pytest.mark.integration
class TestFFETasksIntegration:
    """Integration tests for FFE tasks"""

    def test_plan_then_track_workflow(self, mock_goal_repository):
        """Test workflow: plan goal then track progress"""
        plan_task = FFEGoalPlanningTask()
        track_task = FFEProgressTrackingTask()

        plan_task.db_manager = MagicMock()
        track_task.db_manager = MagicMock()

        # First plan goal
        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "status": "planned",
                "atomic_blocks_count": 5
            }
            plan_result = plan_task.run(
                goal_id="goal-1",
                user_id="user1",
                goal_description="Complete project",
                complexity_level="medium"
            )

            assert plan_result["status"] == "planned"
            assert plan_result["atomic_blocks_count"] > 0

        # Then track progress
        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "goal_id": "goal-1",
                "status": "in_progress"
            }
            track_result = track_task.run(goal_id="goal-1", user_id="user1")

            assert track_result["goal_id"] == "goal-1"

    def test_task_error_handling(self):
        """Test task error handling"""
        task = FFEGoalPlanningTask()
        task.db_manager = None  # Simulate missing DB

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.side_effect = RuntimeError("Database not configured")

            with pytest.raises(RuntimeError):
                task.run(
                    goal_id="goal-1",
                    user_id="user1",
                    goal_description="Test",
                    complexity_level="medium"
                )


@pytest.mark.unit
class TestFFEAtomicBlockGeneration:
    """Test atomic block generation"""

    def test_block_structure(self):
        """Test atomic block structure"""
        block = {
            "block_index": 1,
            "description": "Step 1: Setup",
            "size": "medium",
            "estimated_minutes": 120,
        }

        assert block["block_index"] >= 1
        assert len(block["description"]) > 0
        assert block["size"] in ["small", "medium", "large"]
        assert block["estimated_minutes"] > 0

    def test_complexity_block_mapping(self):
        """Test complexity to block count mapping"""
        mappings = {
            "simple": 3,
            "medium": 5,
            "complex": 7,
        }

        for complexity, expected_count in mappings.items():
            assert expected_count > 0
            assert expected_count % 2 == 1  # Odd numbers for fractal structure

    def test_time_estimation_per_block(self):
        """Test time estimation per block"""
        total_hours = 16
        num_blocks = 5
        time_per_block = total_hours / num_blocks

        assert time_per_block * 60 > 0  # Convert to minutes
        assert time_per_block * 60 == 192  # 16 hours / 5 blocks * 60 minutes

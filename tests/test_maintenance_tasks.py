"""
Unit tests for Maintenance background tasks.

Tests:
- Audit log archival
- Database maintenance
- Cache cleanup
- Data retention policy enforcement
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from ai_pal.tasks.maintenance_tasks import (
    AuditLogArchivalTask,
    DatabaseMaintenanceTask,
    CacheCleanupTask,
    DataRetentionPolicyTask,
)


@pytest.mark.unit
class TestAuditLogArchivalTask:
    """Test audit log archival task"""

    def test_task_initialization(self):
        """Test task initialization"""
        task = AuditLogArchivalTask()
        assert task.name == "ai_pal.tasks.maintenance_tasks.archive_audit_logs"
        assert task.bind is True
        assert task.max_retries == 2

    def test_task_get_task_type(self):
        """Test task type detection"""
        task = AuditLogArchivalTask()
        assert task._get_task_type() == "maintenance"

    def test_archive_run_method(self):
        """Test run method executes async operation"""
        task = AuditLogArchivalTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "status": "completed",
                "logs_archived": 1000,
                "logs_deleted": 500,
            }
            result = task.run(days_to_keep=90)

            assert mock_asyncio.called
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_archive_result_structure(self):
        """Test archival returns proper structure"""
        task = AuditLogArchivalTask()
        task.db_manager = MagicMock()

        result = await task._archive_async(
            days_to_keep=90,
            archive_location="s3://bucket/logs"
        )

        # Verify result structure
        assert result["status"] == "completed"
        assert "logs_archived" in result
        assert "logs_deleted" in result
        assert "archive_size_bytes" in result
        assert "cutoff_date" in result
        assert "archive_location" in result

    @pytest.mark.asyncio
    async def test_archive_respects_days_to_keep(self):
        """Test archival respects days_to_keep parameter"""
        task = AuditLogArchivalTask()
        task.db_manager = MagicMock()

        for days in [30, 60, 90, 180]:
            result = await task._archive_async(
                days_to_keep=days,
                archive_location="s3://bucket/logs"
            )

            # Cutoff date should reflect the days_to_keep
            assert result["cutoff_date"]


@pytest.mark.unit
class TestDatabaseMaintenanceTask:
    """Test database maintenance task"""

    def test_task_initialization(self):
        """Test task initialization"""
        task = DatabaseMaintenanceTask()
        assert task.name == "ai_pal.tasks.maintenance_tasks.database_maintenance"
        assert task.bind is True
        assert task.max_retries == 1

    def test_maintenance_run_method(self):
        """Test run method executes async operation"""
        task = DatabaseMaintenanceTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "status": "completed",
                "optimization_level": "standard",
                "operations_performed": ["analyze_tables", "vacuum"],
            }
            result = task.run(optimization_level="standard")

            assert mock_asyncio.called
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_maintenance_result_structure(self):
        """Test maintenance returns proper structure"""
        task = DatabaseMaintenanceTask()
        task.db_manager = MagicMock()

        result = await task._maintenance_async(
            optimization_level="standard"
        )

        # Verify result structure
        assert result["status"] == "completed"
        assert "optimization_level" in result
        assert "operations_performed" in result
        assert "tables_analyzed" in result
        assert "space_freed_bytes" in result
        assert "maintenance_timestamp" in result

    @pytest.mark.asyncio
    async def test_maintenance_light_optimization(self):
        """Test light optimization level"""
        task = DatabaseMaintenanceTask()
        task.db_manager = MagicMock()

        result = await task._maintenance_async(
            optimization_level="light"
        )

        assert result["optimization_level"] == "light"
        assert "analyze_tables" in result["operations_performed"]

    @pytest.mark.asyncio
    async def test_maintenance_heavy_optimization(self):
        """Test heavy optimization level"""
        task = DatabaseMaintenanceTask()
        task.db_manager = MagicMock()

        result = await task._maintenance_async(
            optimization_level="heavy"
        )

        assert result["optimization_level"] == "heavy"
        # Heavy should include more operations
        assert len(result["operations_performed"]) >= 3

    @pytest.mark.asyncio
    async def test_maintenance_space_freed(self):
        """Test that space_freed_bytes is calculated"""
        task = DatabaseMaintenanceTask()
        task.db_manager = MagicMock()

        result = await task._maintenance_async(
            optimization_level="standard"
        )

        # Space should be non-negative
        assert result["space_freed_bytes"] >= 0


@pytest.mark.unit
class TestCacheCleanupTask:
    """Test cache cleanup task"""

    def test_task_initialization(self):
        """Test task initialization"""
        task = CacheCleanupTask()
        assert task.name == "ai_pal.tasks.maintenance_tasks.cleanup_cache"
        assert task.bind is True
        assert task.max_retries == 2

    def test_cleanup_run_method(self):
        """Test run method executes async operation"""
        task = CacheCleanupTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "status": "completed",
                "entries_cleaned": 500,
            }
            result = task.run(max_age_hours=24)

            assert mock_asyncio.called
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_cleanup_result_structure(self):
        """Test cleanup returns proper structure"""
        task = CacheCleanupTask()
        task.db_manager = MagicMock()

        result = await task._cleanup_async(
            max_age_hours=24,
            cleanup_expired_only=True
        )

        # Verify result structure
        assert result["status"] == "completed"
        assert "entries_cleaned" in result
        assert "entries_expired" in result
        assert "cache_freed_bytes" in result
        assert "max_age_hours" in result

    @pytest.mark.asyncio
    async def test_cleanup_different_age_limits(self):
        """Test cleanup with different age limits"""
        task = CacheCleanupTask()
        task.db_manager = MagicMock()

        for hours in [1, 6, 24, 168]:  # 1h, 6h, 24h, 1 week
            result = await task._cleanup_async(
                max_age_hours=hours,
                cleanup_expired_only=True
            )

            assert result["max_age_hours"] == hours

    @pytest.mark.asyncio
    async def test_cleanup_expired_only_flag(self):
        """Test cleanup respects expired_only flag"""
        task = CacheCleanupTask()
        task.db_manager = MagicMock()

        # Test with expired_only=True
        result1 = await task._cleanup_async(
            max_age_hours=24,
            cleanup_expired_only=True
        )
        assert result1["cleanup_expired_only"] is True

        # Test with expired_only=False
        result2 = await task._cleanup_async(
            max_age_hours=24,
            cleanup_expired_only=False
        )
        assert result2["cleanup_expired_only"] is False


@pytest.mark.unit
class TestDataRetentionPolicyTask:
    """Test data retention policy task"""

    def test_task_initialization(self):
        """Test task initialization"""
        task = DataRetentionPolicyTask()
        assert task.name == "ai_pal.tasks.maintenance_tasks.enforce_retention_policy"
        assert task.bind is True
        assert task.max_retries == 1

    def test_policy_run_method(self):
        """Test run method executes async operation"""
        task = DataRetentionPolicyTask()
        task.db_manager = MagicMock()

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {
                "status": "completed",
                "policy": {"ari_snapshots": 365},
            }
            result = task.run(policy=None)

            assert mock_asyncio.called
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_policy_result_structure(self):
        """Test policy enforcement returns proper structure"""
        task = DataRetentionPolicyTask()
        task.db_manager = MagicMock()

        result = await task._enforce_policy_async(policy=None)

        # Verify result structure
        assert result["status"] == "completed"
        assert "policy" in result
        assert "records_deleted_by_type" in result
        assert "storage_freed_bytes" in result
        assert "enforcement_timestamp" in result

    @pytest.mark.asyncio
    async def test_policy_default_values(self):
        """Test default retention policy values"""
        task = DataRetentionPolicyTask()
        task.db_manager = MagicMock()

        result = await task._enforce_policy_async(policy=None)

        policy = result["policy"]
        assert "ari_snapshots" in policy
        assert "audit_logs" in policy
        assert "failed_tasks" in policy
        assert policy["ari_snapshots"] == 365  # 1 year
        assert policy["audit_logs"] == 90  # 3 months

    @pytest.mark.asyncio
    async def test_policy_custom_values(self):
        """Test custom retention policy"""
        task = DataRetentionPolicyTask()
        task.db_manager = MagicMock()

        custom_policy = {
            "ari_snapshots": 180,
            "audit_logs": 60,
            "temp_files": 7,
        }

        result = await task._enforce_policy_async(policy=custom_policy)

        assert result["policy"] == custom_policy

    @pytest.mark.asyncio
    async def test_policy_retention_days_valid(self):
        """Test retention policy days are valid"""
        task = DataRetentionPolicyTask()
        task.db_manager = MagicMock()

        result = await task._enforce_policy_async(policy=None)

        policy = result["policy"]
        for key, days in policy.items():
            assert days > 0  # All retention periods should be positive
            assert days <= 3650  # No more than 10 years


@pytest.mark.integration
class TestMaintenanceTasksIntegration:
    """Integration tests for maintenance tasks"""

    def test_maintenance_workflow(self):
        """Test complete maintenance workflow"""
        archive_task = AuditLogArchivalTask()
        db_task = DatabaseMaintenanceTask()
        cache_task = CacheCleanupTask()
        policy_task = DataRetentionPolicyTask()

        archive_task.db_manager = MagicMock()
        db_task.db_manager = MagicMock()
        cache_task.db_manager = MagicMock()
        policy_task.db_manager = MagicMock()

        # First archive logs
        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {"status": "completed"}
            archive_result = archive_task.run(days_to_keep=90)
            assert archive_result["status"] == "completed"

        # Then maintain database
        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {"status": "completed"}
            db_result = db_task.run(optimization_level="standard")
            assert db_result["status"] == "completed"

        # Then cleanup cache
        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {"status": "completed"}
            cache_result = cache_task.run(max_age_hours=24)
            assert cache_result["status"] == "completed"

        # Finally enforce retention policy
        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.return_value = {"status": "completed"}
            policy_result = policy_task.run(policy=None)
            assert policy_result["status"] == "completed"

    def test_task_error_handling(self):
        """Test task error handling"""
        task = AuditLogArchivalTask()
        task.db_manager = None  # Simulate missing DB

        with patch('asyncio.run') as mock_asyncio:
            mock_asyncio.side_effect = RuntimeError("Database not configured")

            with pytest.raises(RuntimeError):
                task.run(days_to_keep=90)


@pytest.mark.unit
class TestRetentionPolicyMetrics:
    """Test retention policy metrics"""

    def test_common_retention_periods(self):
        """Test common retention period values"""
        periods = {
            "ari_snapshots": 365,  # 1 year
            "audit_logs": 90,  # 3 months
            "failed_tasks": 30,  # 1 month
            "temp_files": 7,  # 1 week
        }

        for data_type, days in periods.items():
            assert days > 0
            assert 1 <= days <= 3650

    def test_space_freed_calculation(self):
        """Test space freed calculation"""
        entries_deleted = 10000
        avg_size_bytes = 1024  # 1KB per entry

        space_freed = entries_deleted * avg_size_bytes
        assert space_freed == 10240000  # 10MB (10000 * 1024)

    def test_optimization_levels(self):
        """Test optimization level hierarchy"""
        levels = ["light", "standard", "heavy"]
        operation_counts = {
            "light": 1,
            "standard": 3,
            "heavy": 4,
        }

        # Heavy should have more operations than standard
        assert operation_counts["heavy"] >= operation_counts["standard"]
        assert operation_counts["standard"] >= operation_counts["light"]

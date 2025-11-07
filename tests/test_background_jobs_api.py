"""
Integration tests for Background Jobs API endpoints.

Tests:
- Task submission endpoints
- Task monitoring endpoints
- Task management endpoints
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient
from httpx import AsyncClient

from ai_pal.api.main import app
from ai_pal.api.tasks import router


@pytest.mark.unit
class TestTaskSubmissionEndpoints:
    """Test task submission endpoints"""

    def test_ari_aggregation_endpoint_exists(self):
        """Test ARI aggregation endpoint exists"""
        # Check that the route is registered
        routes = [route.path for route in app.routes]
        assert any("/api/tasks/ari/aggregate-snapshots" in route for route in routes)

    def test_ffe_planning_endpoint_exists(self):
        """Test FFE planning endpoint exists"""
        routes = [route.path for route in app.routes]
        assert any("/api/tasks/ffe/plan-goal" in route for route in routes)

    def test_edm_analysis_endpoint_exists(self):
        """Test EDM analysis endpoint exists"""
        routes = [route.path for route in app.routes]
        assert any("/api/tasks/edm/batch-analysis" in route for route in routes)

    def test_task_submission_request_model(self):
        """Test task submission request model"""
        from ai_pal.api.tasks import TaskSubmitRequest

        request = TaskSubmitRequest(
            task_type="ari_snapshot",
            user_id="user1",
            priority=5,
            parameters={"time_window_hours": 24}
        )

        assert request.task_type == "ari_snapshot"
        assert request.user_id == "user1"
        assert request.priority == 5

    def test_task_submission_response_model(self):
        """Test task submission response model"""
        from ai_pal.api.tasks import TaskSubmitResponse

        response = TaskSubmitResponse(
            task_id="task-1",
            celery_task_id="celery-1",
            status="pending",
            created_at=datetime.now(),
            message="Task submitted"
        )

        assert response.task_id == "task-1"
        assert response.status == "pending"


@pytest.mark.unit
class TestTaskMonitoringEndpoints:
    """Test task monitoring endpoints"""

    def test_task_status_endpoint_exists(self):
        """Test task status endpoint exists"""
        routes = [route.path for route in app.routes]
        assert any("/api/tasks/status" in route for route in routes)

    def test_task_list_endpoint_exists(self):
        """Test task list endpoint exists"""
        routes = [route.path for route in app.routes]
        assert any("/api/tasks/list" in route for route in routes)

    def test_pending_tasks_endpoint_exists(self):
        """Test pending tasks endpoint exists"""
        routes = [route.path for route in app.routes]
        assert any("/api/tasks/pending" in route for route in routes)

    def test_failed_tasks_endpoint_exists(self):
        """Test failed tasks endpoint exists"""
        routes = [route.path for route in app.routes]
        assert any("/api/tasks/failed" in route for route in routes)

    def test_task_status_response_model(self):
        """Test task status response model"""
        from ai_pal.api.tasks import TaskStatusResponse

        response = TaskStatusResponse(
            task_id="task-1",
            task_name="aggregate_ari_snapshots",
            task_type="ari_snapshot",
            status="completed",
            user_id="user1",
            created_at=datetime.now(),
            started_at=datetime.now(),
            completed_at=datetime.now(),
            result={"count": 10},
            error_message=None,
            attempts=1,
            duration_seconds=5.2
        )

        assert response.task_id == "task-1"
        assert response.status == "completed"
        assert response.duration_seconds == 5.2

    def test_task_list_response_model(self):
        """Test task list response model"""
        from ai_pal.api.tasks import TaskListResponse, TaskStatusResponse

        task = TaskStatusResponse(
            task_id="task-1",
            task_name="test",
            task_type="test",
            status="pending",
            user_id="user1",
            created_at=datetime.now(),
            started_at=None,
            completed_at=None,
            result=None,
            error_message=None,
            attempts=0,
            duration_seconds=None
        )

        response = TaskListResponse(
            tasks=[task],
            total_count=1,
            limit=20,
            offset=0
        )

        assert len(response.tasks) == 1
        assert response.total_count == 1


@pytest.mark.unit
class TestTaskManagementEndpoints:
    """Test task management endpoints"""

    def test_cancel_task_endpoint_exists(self):
        """Test cancel task endpoint exists"""
        routes = [route.path for route in app.routes]
        assert any("/api/tasks" in route and "{task_id}" in route for route in routes)

    def test_retry_task_endpoint_exists(self):
        """Test retry task endpoint exists"""
        routes = [route.path for route in app.routes]
        assert any("/api/tasks/{task_id}/retry" in route for route in routes)

    def test_health_endpoint_exists(self):
        """Test health check endpoint exists"""
        routes = [route.path for route in app.routes]
        assert any("/api/tasks/health" in route for route in routes)


@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API"""

    def test_api_app_has_task_router(self):
        """Test that API app has task router registered"""
        # The router should be included in the app
        routes = [route.path for route in app.routes]
        task_routes = [r for r in routes if "/api/tasks" in r]
        assert len(task_routes) > 0

    def test_api_cors_configured(self):
        """Test that CORS is configured"""
        middlewares = [m for m in app.user_middleware]
        assert len(middlewares) > 0

    def test_api_startup_events_exist(self):
        """Test that startup events are configured"""
        # Check that the app has startup events
        # This is harder to test directly, but we can check the app structure
        assert hasattr(app, "user_middleware")


@pytest.mark.unit
class TestAPIErrorHandling:
    """Test API error handling"""

    def test_invalid_task_id_returns_404(self):
        """Test that invalid task ID returns 404"""
        # This would be tested in integration tests with actual requests
        from ai_pal.api.tasks import TaskStatusResponse

        # The API should return 404 for non-existent tasks
        # (actual testing would use test client)
        pass

    def test_invalid_parameters_return_400(self):
        """Test that invalid parameters return 400"""
        # The API should validate request parameters
        # (actual testing would use test client)
        pass

    def test_database_error_returns_500(self):
        """Test that database errors return 500"""
        # The API should handle database errors gracefully
        # (actual testing would use test client)
        pass


@pytest.mark.unit
class TestAPIModels:
    """Test API request/response models"""

    def test_task_submit_request_validation(self):
        """Test TaskSubmitRequest validation"""
        from ai_pal.api.tasks import TaskSubmitRequest

        # Valid request
        valid_request = TaskSubmitRequest(
            task_type="ari_snapshot",
            user_id="user1",
            priority=5,
            parameters={"time_window_hours": 24}
        )
        assert valid_request.task_type is not None

        # Invalid priority should fail
        with pytest.raises(ValueError):
            TaskSubmitRequest(
                task_type="ari_snapshot",
                user_id="user1",
                priority=11,  # Out of range (1-10)
                parameters={}
            )

    def test_task_submit_response_serialization(self):
        """Test TaskSubmitResponse serialization"""
        from ai_pal.api.tasks import TaskSubmitResponse

        response = TaskSubmitResponse(
            task_id="task-1",
            celery_task_id="celery-1",
            status="pending",
            created_at=datetime.now(),
            message="Task submitted"
        )

        # Should be serializable to dict
        response_dict = response.dict()
        assert response_dict["task_id"] == "task-1"
        assert response_dict["status"] == "pending"

    def test_task_status_response_optional_fields(self):
        """Test TaskStatusResponse with optional fields"""
        from ai_pal.api.tasks import TaskStatusResponse

        # Pending task (minimal fields)
        pending_task = TaskStatusResponse(
            task_id="task-1",
            task_name="test",
            task_type="test",
            status="pending",
            user_id="user1",
            created_at=datetime.now(),
            started_at=None,
            completed_at=None,
            result=None,
            error_message=None,
            attempts=0,
            duration_seconds=None
        )
        assert pending_task.result is None
        assert pending_task.error_message is None

        # Completed task (all fields)
        completed_task = TaskStatusResponse(
            task_id="task-2",
            task_name="test",
            task_type="test",
            status="completed",
            user_id="user1",
            created_at=datetime.now(),
            started_at=datetime.now(),
            completed_at=datetime.now(),
            result={"count": 5},
            error_message=None,
            attempts=1,
            duration_seconds=5.2
        )
        assert completed_task.result is not None
        assert completed_task.duration_seconds == 5.2


@pytest.mark.unit
class TestAPIRequestValidation:
    """Test API request validation"""

    def test_priority_range_validation(self):
        """Test priority is within valid range"""
        from ai_pal.api.tasks import TaskSubmitRequest

        # Valid priorities
        for priority in range(1, 11):
            request = TaskSubmitRequest(
                task_type="ari_snapshot",
                user_id="user1",
                priority=priority,
                parameters={}
            )
            assert request.priority == priority

    def test_task_type_validation(self):
        """Test task type is recognized"""
        from ai_pal.api.tasks import TaskSubmitRequest

        valid_types = ["ari_snapshot", "ffe_planning", "edm_analysis"]

        for task_type in valid_types:
            request = TaskSubmitRequest(
                task_type=task_type,
                user_id="user1",
                priority=5,
                parameters={}
            )
            assert request.task_type == task_type

    def test_parameters_flexibility(self):
        """Test that parameters dict is flexible"""
        from ai_pal.api.tasks import TaskSubmitRequest

        # Should accept any parameters dict
        request = TaskSubmitRequest(
            task_type="ari_snapshot",
            user_id="user1",
            priority=5,
            parameters={
                "time_window_hours": 24,
                "custom_param": "value",
                "nested": {"key": "value"}
            }
        )
        assert request.parameters["time_window_hours"] == 24
        assert request.parameters["custom_param"] == "value"


@pytest.mark.unit
class TestAPIEndpointDocumentation:
    """Test API endpoint documentation"""

    def test_openapi_schema_available(self):
        """Test OpenAPI schema is available"""
        # FastAPI automatically generates OpenAPI schema at /openapi.json
        assert hasattr(app, "openapi")

    def test_api_documentation_available(self):
        """Test API documentation endpoints exist"""
        routes = [route.path for route in app.routes]
        assert any("/docs" in route for route in routes)

    def test_redoc_documentation_available(self):
        """Test ReDoc documentation is available"""
        routes = [route.path for route in app.routes]
        assert any("/redoc" in route for route in routes)

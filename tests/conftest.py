"""
Pytest fixtures and configuration for AI Pal tests.

Provides reusable test fixtures, mock objects, and utilities.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from ai_pal.core.plugin_manager import (
    PluginManager,
    PluginManifest,
    PluginPermission,
)
from ai_pal.core.credentials import SecureCredentialManager
from ai_pal.modules.base import BaseModule, ModuleRequest, ModuleResponse
from ai_pal.modules.ethics import EthicsModule


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest."""
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Temporary Directory Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_plugins_dir(temp_dir):
    """Create a temporary plugins directory."""
    plugins_dir = temp_dir / "plugins"
    plugins_dir.mkdir()
    return plugins_dir


@pytest.fixture
def temp_credentials_file(temp_dir):
    """Create a temporary credentials file path."""
    return temp_dir / ".secrets"


@pytest.fixture
def temp_reports_dir(temp_dir):
    """Create a temporary reports directory."""
    reports_dir = temp_dir / "reports"
    reports_dir.mkdir()
    return reports_dir


# ============================================================================
# Mock Module Fixtures
# ============================================================================

class MockModule(BaseModule):
    """Mock module for testing."""

    def __init__(self, name: str = "mock_module"):
        super().__init__(
            name=name,
            description="Mock module for testing",
            version="1.0.0",
        )
        self.initialize_called = False
        self.shutdown_called = False
        self.process_called = False
        self.last_request = None

    async def initialize(self) -> None:
        """Initialize mock module."""
        self.initialize_called = True
        self.initialized = True

    async def process(self, request: ModuleRequest) -> ModuleResponse:
        """Process mock request."""
        self.process_called = True
        self.last_request = request

        return ModuleResponse(
            result={"mock": "response"},
            confidence=0.95,
            metadata={"processed": True},
            timestamp=datetime.now(),
            processing_time_ms=10.0,
        )

    async def shutdown(self) -> None:
        """Shutdown mock module."""
        self.shutdown_called = True
        self.initialized = False


class FailingModule(BaseModule):
    """Mock module that fails for testing error handling."""

    def __init__(self):
        super().__init__(
            name="failing_module",
            description="Module that fails",
            version="1.0.0",
        )

    async def initialize(self) -> None:
        """Initialize - fails."""
        raise RuntimeError("Initialization failed")

    async def process(self, request: ModuleRequest) -> ModuleResponse:
        """Process - fails."""
        raise RuntimeError("Processing failed")

    async def shutdown(self) -> None:
        """Shutdown."""
        pass


@pytest.fixture
def mock_module():
    """Create a mock module."""
    return MockModule()


@pytest.fixture
def failing_module():
    """Create a failing module."""
    return FailingModule()


# ============================================================================
# Plugin Manager Fixtures
# ============================================================================

@pytest.fixture
def plugin_manager(temp_plugins_dir):
    """Create a plugin manager with temporary directory."""
    manager = PluginManager(plugins_dir=temp_plugins_dir)
    return manager


@pytest.fixture
def sample_plugin_manifest():
    """Create a sample plugin manifest."""
    return PluginManifest(
        name="test_plugin",
        version="1.0.0",
        description="Test plugin",
        author="Test Author",
        module_class="test_module:TestModule",
        required_permissions={
            PluginPermission.READ_USER_DATA,
            PluginPermission.CALL_OTHER_MODULES,
        },
        python_dependencies=["requests>=2.28.0"],
        module_dependencies=["ethics"],
    )


@pytest.fixture
def dangerous_plugin_manifest():
    """Create a plugin manifest with dangerous permissions."""
    return PluginManifest(
        name="dangerous_plugin",
        version="1.0.0",
        description="Plugin requesting dangerous permissions",
        author="Test Author",
        module_class="dangerous_module:DangerousModule",
        required_permissions={
            PluginPermission.NETWORK_ACCESS,
            PluginPermission.FILE_SYSTEM_WRITE,
            PluginPermission.EXECUTE_CODE,
        },
    )


# ============================================================================
# Credential Manager Fixtures
# ============================================================================

@pytest.fixture
def credential_manager(temp_credentials_file, temp_dir):
    """Create a credential manager with temporary storage."""
    audit_log = temp_dir / "credential_access.log"
    manager = SecureCredentialManager(
        credentials_file=temp_credentials_file,
        audit_log_file=audit_log,
    )
    return manager


@pytest.fixture
def sample_credentials():
    """Sample credentials for testing."""
    return {
        "OPENAI_API_KEY": "sk-test-key-123",
        "ANTHROPIC_API_KEY": "claude-test-key-456",
        "TEST_SECRET": "super-secret-value",
    }


# ============================================================================
# Ethics Module Fixtures
# ============================================================================

@pytest.fixture
async def ethics_module():
    """Create and initialize an ethics module."""
    module = EthicsModule()
    await module.initialize()
    return module


@pytest.fixture
def sample_action_context():
    """Sample context for ethics testing."""
    return {
        "user_id": "test_user_123",
        "action": "test_action",
        "task_efficacy": 0.75,
        "opportunity_expansion": 0.65,
        "autonomy_retention": 0.85,
        "skill_development": 0.60,
        "epistemic_debt": 0.10,
        "hallucination_rate": 0.05,
        "bhir": 1.3,
        "reversible": True,
    }


# ============================================================================
# AHO Tribunal Fixtures
# ============================================================================

@pytest.fixture
def sample_appeal():
    """Create a sample appeal for testing."""
    from ai_pal.api.aho_tribunal import Appeal, AppealStatus, AppealPriority

    return Appeal(
        appeal_id="APPEAL-TEST-001",
        user_id="test_user_123",
        action_id="ACTION-001",
        timestamp=datetime.now(),
        status=AppealStatus.PENDING,
        priority=AppealPriority.HIGH,
        ai_decision="Content flagged as inappropriate",
        user_complaint="This was a false positive - my content was legitimate",
        decision_context={
            "content_type": "text",
            "confidence": 0.85,
            "model": "content_moderator_v2",
        },
    )


# ============================================================================
# Gate Testing Fixtures
# ============================================================================

@pytest.fixture
def vulnerable_user_profiles():
    """Create diverse user profiles for gate testing."""
    return [
        {
            "user_id": "general_001",
            "demographic_group": "general",
            "baseline_skill": 0.75,
            "baseline_autonomy": 0.80,
            "is_vulnerable": False,
        },
        {
            "user_id": "elderly_001",
            "demographic_group": "elderly",
            "baseline_skill": 0.45,
            "baseline_autonomy": 0.60,
            "is_vulnerable": True,
        },
        {
            "user_id": "low_income_001",
            "demographic_group": "low_income",
            "baseline_skill": 0.55,
            "baseline_autonomy": 0.55,
            "is_vulnerable": True,
        },
        {
            "user_id": "disabled_001",
            "demographic_group": "disabled",
            "baseline_skill": 0.60,
            "baseline_autonomy": 0.65,
            "is_vulnerable": True,
        },
    ]


# ============================================================================
# Mock HTTP Client Fixtures
# ============================================================================

@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client for API testing."""
    from unittest.mock import MagicMock

    client = MagicMock()
    client.get.return_value.status_code = 200
    client.post.return_value.status_code = 200
    client.get.return_value.json.return_value = {"status": "ok"}
    client.post.return_value.json.return_value = {"status": "ok"}

    return client


# ============================================================================
# Test Data Generators
# ============================================================================

@pytest.fixture
def generate_test_users():
    """Factory fixture for generating test users."""

    def _generate(count: int = 10, vulnerable_ratio: float = 0.3):
        """Generate test users with specified characteristics."""
        import random

        users = []
        vulnerable_count = int(count * vulnerable_ratio)

        for i in range(count):
            is_vulnerable = i < vulnerable_count

            if is_vulnerable:
                group = random.choice(["elderly", "low_income", "disabled"])
                skill_range = (0.3, 0.6)
                autonomy_range = (0.4, 0.7)
            else:
                group = "general"
                skill_range = (0.6, 0.9)
                autonomy_range = (0.7, 0.9)

            users.append({
                "user_id": f"{group}_{i:03d}",
                "demographic_group": group,
                "baseline_skill": random.uniform(*skill_range),
                "baseline_autonomy": random.uniform(*autonomy_range),
                "is_vulnerable": is_vulnerable,
            })

        return users

    return _generate


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_artifacts(temp_dir):
    """Automatically cleanup test artifacts after each test."""
    yield
    # Cleanup happens automatically via temp_dir fixture


# ============================================================================
# Assertion Helpers
# ============================================================================

@pytest.fixture
def assert_agency_delta():
    """Helper to assert agency delta meets thresholds."""

    def _assert(delta: float, min_threshold: float = 0.0):
        assert delta >= min_threshold, (
            f"Agency delta {delta:.3f} below minimum threshold {min_threshold}"
        )

    return _assert


@pytest.fixture
def assert_disparity_ratio():
    """Helper to assert disparity ratios are within acceptable bounds."""

    def _assert(ratio: float, max_ratio: float = 1.2):
        assert ratio <= max_ratio, (
            f"Disparity ratio {ratio:.2f} exceeds maximum {max_ratio}"
        )

    return _assert


# ============================================================================
# Performance Timing Fixtures
# ============================================================================

@pytest.fixture
def timer():
    """Simple timer fixture for performance testing."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed_ms(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time) * 1000
            return 0

    return Timer()

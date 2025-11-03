"""
Test Agency Dashboard integration with ARI Engine and RDI Monitor
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import tempfile
import shutil

from src.ai_pal.ui.agency_dashboard import (
    AgencyDashboard,
    DashboardSection,
    ARIEngineStatus,
    RDIMonitorStatus
)
from src.ai_pal.monitoring import ARIEngine, RDIMonitor, ARIMonitor, EDMMonitor
from src.ai_pal.improvement.self_improvement import SelfImprovementLoop
from src.ai_pal.privacy.advanced_privacy import AdvancedPrivacyManager
from src.ai_pal.orchestration.multi_model import MultiModelOrchestrator
from src.ai_pal.context.enhanced_context import EnhancedContextManager


@pytest.fixture
def temp_storage():
    """Create temporary storage directory"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def ari_engine(temp_storage):
    """Create ARI Engine instance"""
    return ARIEngine(storage_dir=temp_storage / "ari")


@pytest.fixture
def rdi_monitor(temp_storage):
    """Create RDI Monitor instance"""
    return RDIMonitor(
        storage_dir=temp_storage / "rdi",
        enable_privacy_mode=True
    )


@pytest.mark.asyncio
async def test_dashboard_with_ari_engine(ari_engine, temp_storage):
    """Test dashboard generation with ARI Engine"""
    # Create minimal dependencies
    ari_monitor = ARIMonitor()
    edm_monitor = EDMMonitor()
    improvement_loop = SelfImprovementLoop(ari_monitor, edm_monitor)
    privacy_manager = AdvancedPrivacyManager(storage_dir=temp_storage / "privacy")
    orchestrator = MultiModelOrchestrator()
    context_manager = EnhancedContextManager(storage_dir=temp_storage / "context")

    # Create dashboard with ARI Engine
    dashboard = AgencyDashboard(
        ari_monitor=ari_monitor,
        edm_monitor=edm_monitor,
        improvement_loop=improvement_loop,
        privacy_manager=privacy_manager,
        orchestrator=orchestrator,
        context_manager=context_manager,
        ari_engine=ari_engine
    )

    # Add some ARI data
    user_id = "test_user"
    await ari_engine.analyze_user_text(
        user_id,
        "This is a complex technical implementation with sophisticated algorithms.",
        "document"
    )

    # Generate dashboard with ARI_ENGINE section
    dashboard_data = await dashboard.generate_dashboard(
        user_id,
        sections=[DashboardSection.ARI_ENGINE]
    )

    # Verify ARI Engine data is present
    assert dashboard_data.ari_engine_status is not None
    assert isinstance(dashboard_data.ari_engine_status, ARIEngineStatus)
    assert 0.0 <= dashboard_data.ari_engine_status.overall_ari <= 1.0
    assert dashboard_data.ari_engine_status.signal_level in ["high", "medium", "low", "critical"]


@pytest.mark.asyncio
async def test_dashboard_with_rdi_monitor(rdi_monitor, temp_storage):
    """Test dashboard generation with RDI Monitor"""
    # Create minimal dependencies
    ari_monitor = ARIMonitor()
    edm_monitor = EDMMonitor()
    improvement_loop = SelfImprovementLoop(ari_monitor, edm_monitor)
    privacy_manager = AdvancedPrivacyManager(storage_dir=temp_storage / "privacy")
    orchestrator = MultiModelOrchestrator()
    context_manager = EnhancedContextManager(storage_dir=temp_storage / "context")

    # Create dashboard with RDI Monitor
    dashboard = AgencyDashboard(
        ari_monitor=ari_monitor,
        edm_monitor=edm_monitor,
        improvement_loop=improvement_loop,
        privacy_manager=privacy_manager,
        orchestrator=orchestrator,
        context_manager=context_manager,
        rdi_monitor=rdi_monitor
    )

    # Add some RDI data
    user_id = "test_user"
    await rdi_monitor.analyze_input(
        user_id,
        "The earth orbits the sun as part of our solar system.",
        "science"
    )
    rdi_monitor.calculate_rdi_score(user_id)

    # Generate dashboard with RDI_MONITOR section
    dashboard_data = await dashboard.generate_dashboard(
        user_id,
        sections=[DashboardSection.RDI_MONITOR]
    )

    # Verify RDI Monitor data is present
    assert dashboard_data.rdi_monitor_status is not None
    assert isinstance(dashboard_data.rdi_monitor_status, RDIMonitorStatus)
    assert 0.0 <= dashboard_data.rdi_monitor_status.overall_rdi <= 1.0
    assert dashboard_data.rdi_monitor_status.rdi_level in [
        "aligned", "minor_drift", "moderate_drift", "significant_drift", "critical_drift"
    ]
    assert "private" in dashboard_data.rdi_monitor_status.privacy_notice.lower()


@pytest.mark.asyncio
async def test_dashboard_with_both_ari_and_rdi(ari_engine, rdi_monitor, temp_storage):
    """Test dashboard generation with both ARI Engine and RDI Monitor"""
    # Create minimal dependencies
    ari_monitor = ARIMonitor()
    edm_monitor = EDMMonitor()
    improvement_loop = SelfImprovementLoop(ari_monitor, edm_monitor)
    privacy_manager = AdvancedPrivacyManager(storage_dir=temp_storage / "privacy")
    orchestrator = MultiModelOrchestrator()
    context_manager = EnhancedContextManager(storage_dir=temp_storage / "context")

    # Create dashboard with both
    dashboard = AgencyDashboard(
        ari_monitor=ari_monitor,
        edm_monitor=edm_monitor,
        improvement_loop=improvement_loop,
        privacy_manager=privacy_manager,
        orchestrator=orchestrator,
        context_manager=context_manager,
        ari_engine=ari_engine,
        rdi_monitor=rdi_monitor
    )

    # Add data for both
    user_id = "test_user"

    # ARI data
    await ari_engine.analyze_user_text(
        user_id,
        "Complex technical implementation",
        "document"
    )

    # RDI data
    await rdi_monitor.analyze_input(user_id, "Scientific statement", "science")
    rdi_monitor.calculate_rdi_score(user_id)

    # Generate dashboard with both sections
    dashboard_data = await dashboard.generate_dashboard(
        user_id,
        sections=[DashboardSection.ARI_ENGINE, DashboardSection.RDI_MONITOR]
    )

    # Verify both are present
    assert dashboard_data.ari_engine_status is not None
    assert dashboard_data.rdi_monitor_status is not None


@pytest.mark.asyncio
async def test_dashboard_alerts_from_ari(ari_engine, temp_storage):
    """Test that ARI alerts appear in system alerts"""
    # Create dashboard
    ari_monitor = ARIMonitor()
    edm_monitor = EDMMonitor()
    improvement_loop = SelfImprovementLoop(ari_monitor, edm_monitor)
    privacy_manager = AdvancedPrivacyManager(storage_dir=temp_storage / "privacy")
    orchestrator = MultiModelOrchestrator()
    context_manager = EnhancedContextManager(storage_dir=temp_storage / "context")

    dashboard = AgencyDashboard(
        ari_monitor=ari_monitor,
        edm_monitor=edm_monitor,
        improvement_loop=improvement_loop,
        privacy_manager=privacy_manager,
        orchestrator=orchestrator,
        context_manager=context_manager,
        ari_engine=ari_engine
    )

    user_id = "test_user"

    # Add minimal ARI data to trigger calculation
    await ari_engine.analyze_user_text(user_id, "test", "document")

    # Generate dashboard
    dashboard_data = await dashboard.generate_dashboard(
        user_id,
        sections=[DashboardSection.ARI_ENGINE]
    )

    # System alerts should be a list
    assert isinstance(dashboard_data.system_alerts, list)


def test_ari_engine_status_dataclass():
    """Test ARIEngineStatus dataclass"""
    status = ARIEngineStatus(
        overall_ari=0.75,
        signal_level="high",
        lexical_ari=0.70,
        interaction_ari=0.80,
        baseline_deviation=0.05,
        trend_direction="improving",
        days_in_trend=7
    )

    assert status.overall_ari == 0.75
    assert status.signal_level == "high"
    assert status.trend_direction == "improving"


def test_rdi_monitor_status_dataclass():
    """Test RDIMonitorStatus dataclass"""
    status = RDIMonitorStatus(
        overall_rdi=0.15,
        rdi_level="minor_drift",
        semantic_drift=0.10,
        factual_drift=0.05,
        logical_drift=0.20,
        trend_direction="stable"
    )

    assert status.overall_rdi == 0.15
    assert status.rdi_level == "minor_drift"
    assert "private" in status.privacy_notice.lower()
    assert status.opted_into_aggregates is False

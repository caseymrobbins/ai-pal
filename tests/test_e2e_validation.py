"""
End-to-End Validation Test for Phase 1-3 Integration

This test validates that all Phase 1-3 components work together
in a realistic workflow scenario.
"""

import asyncio
import pytest
from pathlib import Path
import tempfile
from datetime import datetime

from ai_pal.core.integrated_system import IntegratedACSystem, create_default_system
from ai_pal.gates.gate_system import GateType
from ai_pal.context.enhanced_context import MemoryType


@pytest.fixture
def temp_storage():
    """Create temporary storage directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def e2e_system(temp_storage):
    """Create a fully configured system for E2E testing"""
    system = create_default_system(
        data_dir=temp_storage,
        credentials_path=temp_storage / "credentials.json"
    )
    return system


class TestEndToEndIntegration:
    """End-to-end integration tests"""

    def test_system_initialization(self, e2e_system):
        """Test: System initializes with all components"""
        system = e2e_system

        print("\n=== System Initialization ===")

        # Verify Phase 1 components
        assert system.credential_manager is not None, "Credential manager should be initialized"
        assert system.gate_system is not None, "Gate system should be initialized"
        assert system.tribunal is not None, "AHO tribunal should be initialized"
        print("✓ Phase 1 components initialized")

        # Verify Phase 2 components
        assert system.ari_monitor is not None, "ARI monitor should be initialized"
        assert system.edm_monitor is not None, "EDM monitor should be initialized"
        assert system.improvement_loop is not None, "Improvement loop should be initialized"
        print("✓ Phase 2 components initialized")

        # Verify Phase 3 components
        assert system.context_manager is not None, "Context manager should be initialized"
        assert system.privacy_manager is not None, "Privacy manager should be initialized"
        assert system.orchestrator is not None, "Orchestrator should be initialized"
        assert system.dashboard is not None, "Dashboard should be initialized"
        print("✓ Phase 3 components initialized")

        print("\n✓ All components successfully initialized!")

    @pytest.mark.asyncio
    async def test_gate_system_validation(self, e2e_system):
        """Test: Four Gates validate actions"""
        system = e2e_system

        print("\n=== Gate System Validation ===")

        # Create a test action
        test_action = {
            "action_id": "test_001",
            "user_id": "test_user",
            "action_type": "suggestion",
            "description": "Suggest using a more efficient algorithm",
            "teaches_skill": True,
            "replaces_user_decision": False
        }

        # Test Gate 1: Autonomy
        result = await system.gate_system.validate(test_action, GateType.AUTONOMY)
        print(f"Gate 1 (Autonomy): {'PASS' if result.passed else 'FAIL'} - {result.reason}")

        # Test Gate 2: Humanity
        result = await system.gate_system.validate(test_action, GateType.HUMANITY)
        print(f"Gate 2 (Humanity): {'PASS' if result.passed else 'FAIL'} - {result.reason}")

        # Test Gate 3: Oversight
        result = await system.gate_system.validate(test_action, GateType.OVERSIGHT)
        print(f"Gate 3 (Oversight): {'PASS' if result.passed else 'FAIL'} - {result.reason}")

        # Test Gate 4: Alignment
        result = await system.gate_system.validate(test_action, GateType.ALIGNMENT)
        print(f"Gate 4 (Alignment): {'PASS' if result.passed else 'FAIL'} - {result.reason}")

        # Validate all gates
        all_results = await system.gate_system.validate_all(test_action, {"user_skill": 0.5})
        passed_count = sum(1 for r in all_results.values() if r.passed)
        print(f"\n✓ All gates validated: {passed_count}/4 passed")

    @pytest.mark.asyncio
    async def test_context_memory_workflow(self, e2e_system):
        """Test: Context memory storage and retrieval"""
        system = e2e_system

        print("\n=== Context Memory Workflow ===")

        user_id = "test_user"
        session_id = "test_session_001"

        # Add a memory
        memory = await system.context_manager.store_memory(
            user_id=user_id,
            session_id=session_id,
            content="User prefers concise explanations over verbose ones",
            memory_type=MemoryType.PREFERENCE,
            tags={"communication", "style"}
        )

        print(f"✓ Memory added: {memory.memory_id}")

        # Retrieve memories
        memories = system.context_manager.memories.get(user_id, [])
        assert len(memories) > 0, "Should have at least one memory"
        print(f"✓ Retrieved {len(memories)} memories for user")

        # Search memories
        results = await system.context_manager.search_memories(
            user_id=user_id,
            query="communication preferences",
            top_k=5
        )
        print(f"✓ Search returned {len(results)} relevant memories")

    @pytest.mark.asyncio
    async def test_privacy_filtering(self, e2e_system):
        """Test: PII detection and filtering"""
        system = e2e_system

        print("\n=== Privacy Filtering ===")

        # Text with PII
        text_with_pii = "My email is john.doe@example.com and phone is 555-123-4567"

        # Detect PII
        detections = await system.privacy_manager.detect_pii(text_with_pii)
        print(f"✓ Detected {len(detections)} PII instances")

        for detection in detections:
            print(f"  - {detection.pii_type.value}: '{detection.detected_value}' (confidence: {detection.confidence:.2f})")

        assert len(detections) > 0, "Should detect email and phone number"

    @pytest.mark.asyncio
    async def test_ari_monitoring(self, e2e_system):
        """Test: Agency Retention Index monitoring"""
        system = e2e_system

        print("\n=== ARI Monitoring ===")

        user_id = "test_user"

        # Record a snapshot
        from ai_pal.monitoring.ari_monitor import AgencySnapshot, AgencyLevel
        snapshot = AgencySnapshot(
            user_id=user_id,
            timestamp=datetime.now(),
            delta_agency=0.7,
            agency_level=AgencyLevel.GROWING,
            decision_agency=0.7,
            learning_agency=0.6,
            momentum_agency=0.8,
            engagement_score=0.75,
            skill_growth=0.05,
            ai_dependency=0.3
        )

        await system.ari_monitor.record_snapshot(snapshot)

        print("✓ Snapshot recorded")

        # Generate report
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        report = system.ari_monitor.generate_report(user_id, start_date, end_date)
        print(f"✓ ARI Report generated:")
        print(f"  - User ID: {report.user_id}")
        print(f"  - Period: {report.period_start} to {report.period_end}")

    @pytest.mark.asyncio
    async def test_aho_tribunal_workflow(self, e2e_system):
        """Test: AHO Tribunal appeal workflow"""
        system = e2e_system

        print("\n=== AHO Tribunal Workflow ===")

        # Submit an appeal
        appeal = await system.tribunal.submit_appeal(
            user_id="test_user",
            action_id="action_001",
            ai_decision="AI decided to automate this task",
            user_complaint="I wanted to learn how to do this myself",
            impact_on_agency=-0.3
        )

        print(f"✓ Appeal submitted: {appeal.appeal_id}")
        print(f"  Status: {appeal.status.value}")

        # Review the appeal
        reviewed = await system.tribunal.review_appeal(
            appeal.appeal_id,
            reviewer_notes="User concern is valid - task should teach, not replace"
        )

        print(f"✓ Appeal reviewed")
        print(f"  Verdict: {reviewed.verdict.value if hasattr(reviewed, 'verdict') else 'pending'}")

    @pytest.mark.asyncio
    async def test_dashboard_generation(self, e2e_system):
        """Test: Agency dashboard generation"""
        system = e2e_system

        print("\n=== Dashboard Generation ===")

        user_id = "test_user"

        # Generate dashboard
        dashboard = await system.dashboard.generate_dashboard(
            user_id=user_id,
            period_days=7
        )

        print(f"✓ Dashboard generated")
        print(f"  Overall health score: {dashboard.overall_health_score:.1f}/100")
        print(f"  System alerts: {len(dashboard.system_alerts)}")

        if dashboard.agency_metrics:
            print(f"  Agency ΔA: {dashboard.agency_metrics.current_delta_agency:+.3f}")

        if dashboard.privacy_status:
            print(f"  Privacy budget used: {dashboard.privacy_status.epsilon_percentage:.1f}%")

    @pytest.mark.asyncio
    async def test_full_request_workflow(self, e2e_system):
        """Test: Complete request processing workflow"""
        system = e2e_system

        print("\n=== Full Request Workflow ===")

        user_id = "test_user"
        session_id = "session_001"

        # 1. User makes a request with PII
        user_request = "Can you help me organize my calendar? My email is user@example.com"
        print(f"\n1. User request received: '{user_request[:50]}...'")

        # 2. Privacy filtering
        pii_detections = await system.privacy_manager.detect_pii(user_request)
        print(f"2. Privacy scan: {len(pii_detections)} PII detected")

        # 3. Store in context
        memory = await system.context_manager.store_memory(
            user_id=user_id,
            session_id=session_id,
            content="User requested calendar organization help",
            memory_type=MemoryType.CONVERSATION,
            tags={"request", "calendar"}
        )
        print(f"3. Context stored: {memory.memory_id}")

        # 4. Check gates for proposed action
        proposed_action = {
            "action_id": "organize_calendar",
            "user_id": user_id,
            "action_type": "assistance",
            "description": "Help organize calendar",
            "teaches_skill": True,
            "replaces_user_decision": False
        }

        gate_results = await system.gate_system.validate_all(proposed_action, {"user_skill": 0.5})
        passed_gates = sum(1 for r in gate_results.values() if r.passed)
        print(f"4. Gate validation: {passed_gates}/4 gates passed")

        # 5. Record snapshot for ARI
        from ai_pal.monitoring.ari_monitor import AgencySnapshot, AgencyLevel
        snapshot = AgencySnapshot(
            user_id=user_id,
            timestamp=datetime.now(),
            delta_agency=0.8,
            agency_level=AgencyLevel.GROWING,
            decision_agency=0.8,
            learning_agency=0.7,
            momentum_agency=0.9,
            engagement_score=0.8,
            skill_growth=0.02,
            ai_dependency=0.2
        )
        await system.ari_monitor.record_snapshot(snapshot)
        print(f"5. ARI monitoring: snapshot recorded")

        # 6. Generate dashboard
        dashboard = await system.dashboard.generate_dashboard(user_id, period_days=1)
        print(f"6. Dashboard: health score {dashboard.overall_health_score:.1f}/100")

        print("\n✓ Complete workflow executed successfully!")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])

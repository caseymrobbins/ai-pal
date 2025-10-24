"""
Quick smoke test for Phase 4 - Core Integration

This is a lightweight test to verify basic imports and structure
without requiring full dependencies.
"""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that all Phase 3 modules can be imported"""
    print("Testing imports...")

    try:
        # Phase 3 - Context
        from ai_pal.context import enhanced_context
        print("✓ Context module imports")

        # Phase 3 - Privacy
        from ai_pal.privacy import advanced_privacy
        print("✓ Privacy module imports")

        # Phase 3 - Orchestration
        from ai_pal.orchestration import multi_model
        print("✓ Orchestration module imports")

        # Phase 3 - UI
        from ai_pal.ui import agency_dashboard
        print("✓ UI module imports")

        # Phase 3 - Integrated System
        from ai_pal.core import integrated_system
        print("✓ Integrated system imports")

        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_enums():
    """Test that enums are defined correctly"""
    print("\nTesting enums...")

    try:
        from ai_pal.context.enhanced_context import MemoryType, MemoryPriority
        from ai_pal.privacy.advanced_privacy import PIIType, PrivacyAction, ConsentLevel
        from ai_pal.orchestration.multi_model import ModelProvider, OptimizationGoal
        from ai_pal.core.integrated_system import RequestStage

        # Test enum values
        assert MemoryType.CONVERSATION.value == "conversation"
        assert PIIType.EMAIL.value == "email"
        assert ModelProvider.LOCAL.value == "local"
        assert RequestStage.INTAKE.value == "intake"

        print("✓ All enums defined correctly")
        return True
    except Exception as e:
        print(f"✗ Enum test failed: {e}")
        return False


def test_dataclass_structure():
    """Test that dataclasses are defined correctly"""
    print("\nTesting dataclass structures...")

    try:
        from ai_pal.context.enhanced_context import MemoryEntry, MemoryType, MemoryPriority
        from ai_pal.privacy.advanced_privacy import PIIDetection, PIIType, PrivacyAction
        from ai_pal.orchestration.multi_model import ModelCapabilities, TaskRequirements, TaskComplexity
        from datetime import datetime

        # Test MemoryEntry creation (without embedding)
        memory = MemoryEntry(
            memory_id="test_1",
            user_id="user_1",
            session_id="session_1",
            content="Test memory",
            memory_type=MemoryType.FACT,
            priority=MemoryPriority.HIGH,
            timestamp=datetime.now(),
            tags={"test"},
            embedding=None,
            relevance_score=1.0,
            access_count=0,
            last_accessed=datetime.now(),
            consolidated=False
        )
        assert memory.content == "Test memory"
        print("✓ MemoryEntry dataclass works")

        # Test PIIDetection creation
        detection = PIIDetection(
            pii_type=PIIType.EMAIL,
            text="test@example.com",
            start_pos=0,
            end_pos=16,
            confidence=0.95,
            sensitivity_level="high"
        )
        assert detection.text == "test@example.com"
        print("✓ PIIDetection dataclass works")

        # Test TaskRequirements creation
        requirements = TaskRequirements(
            task_type="summarization",
            complexity=TaskComplexity.SIMPLE,
            max_cost=0.01,
            max_latency_ms=1000,
            min_quality=0.7,
            requires_local=False
        )
        assert requirements.max_cost == 0.01
        print("✓ TaskRequirements dataclass works")

        return True
    except Exception as e:
        print(f"✗ Dataclass test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("Phase 4: Quick Smoke Test")
    print("=" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Enums", test_enums()))
    results.append(("Dataclasses", test_dataclass_structure()))

    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print("\n" + f"{passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All smoke tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""
Comprehensive tests for AI-Powered FFE Components

Tests that Scoping Agent, Strength Amplifier, and Reward Emitter
properly use MultiModelOrchestrator when available, and fall back
to templates when not.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from pathlib import Path

from ai_pal.ffe.components import (
    ScopingAgent,
    StrengthAmplifier,
    RewardEmitter,
)
from ai_pal.ffe.engine import FractalFlowEngine
from ai_pal.ffe.models import (
    GoalPacket,
    TaskComplexityLevel,
    GoalStatus,
    PersonalityProfile,
    SignatureStrength,
    StrengthType,
    AtomicBlock,
)
from ai_pal.orchestration.multi_model import (
    MultiModelOrchestrator,
    LLMResponse,
)


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator"""
    orchestrator = Mock(spec=MultiModelOrchestrator)
    return orchestrator


@pytest.fixture
def mock_llm_response():
    """Create a mock LLM response"""
    return LLMResponse(
        generated_text="Mock AI response",
        model_name="test-model",
        provider="test",
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        finish_reason="stop",
        cost_usd=0.001,
        latency_ms=100.0,
        timestamp=datetime.now(),
    )


@pytest.fixture
def sample_goal():
    """Create a sample goal for testing"""
    return GoalPacket(
        goal_id="test-goal-1",
        user_id="test-user",
        description="Build a complete web application with authentication",
        complexity_level=TaskComplexityLevel.LARGE,
        status=GoalStatus.IN_PROGRESS,
        created_at=datetime.now(),
    )


@pytest.fixture
def sample_personality():
    """Create a sample personality profile"""
    return PersonalityProfile(
        user_id="test-user",
        core_values=["learning", "creativity", "helping others"],
        signature_strengths=[
            SignatureStrength(
                strength_id="str-1",
                strength_type=StrengthType.ANALYTICAL,
                identity_label="Systematic Thinker",
                confidence_score=0.9,
            ),
            SignatureStrength(
                strength_id="str-2",
                strength_type=StrengthType.CREATIVE,
                identity_label="Creative Problem Solver",
                confidence_score=0.85,
            ),
        ],
        learning_style="visual",
        work_preferences={"prefers_structure": True, "likes_variety": True},
    )


@pytest.fixture
def sample_atomic_block():
    """Create a sample atomic block"""
    return AtomicBlock(
        block_id="block-1",
        user_id="test-user",
        description="Write authentication logic",
        estimated_minutes=25,
        parent_goal_id="goal-1",
        applied_strength=SignatureStrength(
            strength_id="str-1",
            strength_type=StrengthType.ANALYTICAL,
            identity_label="Systematic Thinker",
            confidence_score=0.9,
        ),
        reframed_description="Use your systematic thinking to structure the auth logic",
    )


# ============================================================================
# Scoping Agent Tests
# ============================================================================


@pytest.mark.asyncio
async def test_scoping_agent_with_orchestrator(mock_orchestrator, sample_goal, mock_llm_response):
    """Test Scoping Agent uses AI when orchestrator is provided"""
    # Configure mock to return AI response
    mock_llm_response.generated_text = """CRITICAL_PATH: Implement user registration and login flow
VALUE_SCORE: 0.85
EFFORT_SCORE: 0.25
REASONING: Auth is the foundation that unlocks 80% of the app's value"""

    mock_orchestrator.select_model = AsyncMock(return_value=Mock(provider="local", model_name="phi-2"))
    mock_orchestrator.execute_model = AsyncMock(return_value=mock_llm_response)

    agent = ScopingAgent(orchestrator=mock_orchestrator)

    # Verify agent is in AI mode
    assert agent.orchestrator is not None

    # Perform scoping
    session = await agent.scope_goal(sample_goal)

    # Verify AI was called
    mock_orchestrator.select_model.assert_called_once()
    mock_orchestrator.execute_model.assert_called_once()

    # Verify scoping results
    assert session is not None
    assert session.identified_80_win is not None
    assert "registration" in session.identified_80_win.lower() or "login" in session.identified_80_win.lower()
    assert session.value_effort_analysis['value_score'] > 0
    assert session.output_goal is not None


@pytest.mark.asyncio
async def test_scoping_agent_without_orchestrator(sample_goal):
    """Test Scoping Agent falls back to templates when orchestrator is None"""
    agent = ScopingAgent(orchestrator=None)

    # Verify agent is in template mode
    assert agent.orchestrator is None

    # Perform scoping
    session = await agent.scope_goal(sample_goal)

    # Verify scoping still works with templates
    assert session is not None
    assert session.identified_80_win is not None
    assert session.output_goal is not None


@pytest.mark.asyncio
async def test_scoping_agent_ai_fallback_on_error(mock_orchestrator, sample_goal):
    """Test Scoping Agent falls back to templates if AI fails"""
    # Configure mock to raise error
    mock_orchestrator.select_model = AsyncMock(side_effect=Exception("API error"))

    agent = ScopingAgent(orchestrator=mock_orchestrator)

    # Perform scoping
    session = await agent.scope_goal(sample_goal)

    # Verify it still works (fell back to templates)
    assert session is not None
    assert session.identified_80_win is not None


# ============================================================================
# Strength Amplifier Tests
# ============================================================================


@pytest.mark.asyncio
async def test_strength_amplifier_with_orchestrator(
    mock_orchestrator, sample_personality, sample_atomic_block, mock_llm_response
):
    """Test Strength Amplifier uses AI when orchestrator is provided"""
    # Configure mock to return AI response
    mock_llm_response.generated_text = """REFRAMED_TASK: Use your analytical mind to architect a secure, logical authentication system
STRENGTH_CONNECTION: Your systematic thinking will help you structure the flow perfectly
IDENTITY_AFFIRMATION: This is where your Systematic Thinker strength truly shines"""

    mock_orchestrator.select_model = AsyncMock(return_value=Mock(provider="local", model_name="phi-2"))
    mock_orchestrator.execute_model = AsyncMock(return_value=mock_llm_response)

    amplifier = StrengthAmplifier(orchestrator=mock_orchestrator)

    # Verify amplifier is in AI mode
    assert amplifier.orchestrator is not None

    # Apply strength
    reframed = await amplifier.apply_strength_to_task(sample_atomic_block, sample_personality)

    # Verify AI was called
    mock_orchestrator.execute_model.assert_called_once()

    # Verify reframing
    assert reframed is not None
    assert len(reframed) > 0
    assert "analytical" in reframed.lower() or "systematic" in reframed.lower()


@pytest.mark.asyncio
async def test_strength_amplifier_without_orchestrator(sample_personality, sample_atomic_block):
    """Test Strength Amplifier falls back to templates when orchestrator is None"""
    amplifier = StrengthAmplifier(orchestrator=None)

    # Verify amplifier is in template mode
    assert amplifier.orchestrator is None

    # Apply strength
    reframed = await amplifier.apply_strength_to_task(sample_atomic_block, sample_personality)

    # Verify reframing still works with templates
    assert reframed is not None
    assert len(reframed) > 0


@pytest.mark.asyncio
async def test_strength_amplifier_ai_fallback_on_error(
    mock_orchestrator, sample_personality, sample_atomic_block
):
    """Test Strength Amplifier falls back to templates if AI fails"""
    # Configure mock to raise error
    mock_orchestrator.select_model = AsyncMock(side_effect=Exception("API error"))

    amplifier = StrengthAmplifier(orchestrator=mock_orchestrator)

    # Apply strength
    reframed = await amplifier.apply_strength_to_task(sample_atomic_block, sample_personality)

    # Verify it still works (fell back to templates)
    assert reframed is not None
    assert len(reframed) > 0


# ============================================================================
# Reward Emitter Tests
# ============================================================================


@pytest.mark.asyncio
async def test_reward_emitter_with_orchestrator(
    mock_orchestrator, sample_atomic_block, mock_llm_response
):
    """Test Reward Emitter uses AI when orchestrator is provided"""
    # Configure mock to return AI response
    mock_llm_response.generated_text = """✓ Excellent work! You used your systematic thinking to architect that authentication flow like the true Systematic Thinker you are. Your logical approach made complex security requirements crystal clear. This is your analytical strength in action!"""

    mock_orchestrator.select_model = AsyncMock(return_value=Mock(provider="local", model_name="phi-2"))
    mock_orchestrator.execute_model = AsyncMock(return_value=mock_llm_response)

    emitter = RewardEmitter(orchestrator=mock_orchestrator)

    # Verify emitter is in AI mode
    assert emitter.orchestrator is not None

    # Emit reward
    reward = await emitter.emit_reward(sample_atomic_block)

    # Verify AI was called
    mock_orchestrator.execute_model.assert_called_once()

    # Verify reward
    assert reward is not None
    assert reward.message is not None
    assert len(reward.message) > 0
    assert "✓" in reward.message


@pytest.mark.asyncio
async def test_reward_emitter_without_orchestrator(sample_atomic_block):
    """Test Reward Emitter falls back to templates when orchestrator is None"""
    emitter = RewardEmitter(orchestrator=None)

    # Verify emitter is in template mode
    assert emitter.orchestrator is None

    # Emit reward
    reward = await emitter.emit_reward(sample_atomic_block)

    # Verify reward still works with templates
    assert reward is not None
    assert reward.message is not None
    assert "✓" in reward.message


@pytest.mark.asyncio
async def test_reward_emitter_ai_fallback_on_error(mock_orchestrator, sample_atomic_block):
    """Test Reward Emitter falls back to templates if AI fails"""
    # Configure mock to raise error
    mock_orchestrator.execute_model = AsyncMock(side_effect=Exception("API error"))

    emitter = RewardEmitter(orchestrator=mock_orchestrator)

    # Emit reward
    reward = await emitter.emit_reward(sample_atomic_block)

    # Verify it still works (fell back to templates)
    assert reward is not None
    assert reward.message is not None


# ============================================================================
# FFE Engine Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ffe_engine_with_orchestrator(mock_orchestrator, tmp_path):
    """Test FFE Engine properly passes orchestrator to components"""
    engine = FractalFlowEngine(
        storage_dir=tmp_path,
        orchestrator=mock_orchestrator,
    )

    # Verify orchestrator was passed to components
    assert engine.orchestrator is mock_orchestrator
    assert engine.scoping_agent.orchestrator is mock_orchestrator
    assert engine.strength_amplifier.orchestrator is mock_orchestrator
    assert engine.reward_emitter.orchestrator is mock_orchestrator


@pytest.mark.asyncio
async def test_ffe_engine_without_orchestrator(tmp_path):
    """Test FFE Engine works without orchestrator (template mode)"""
    engine = FractalFlowEngine(storage_dir=tmp_path)

    # Verify components are in template mode
    assert engine.orchestrator is None
    assert engine.scoping_agent.orchestrator is None
    assert engine.strength_amplifier.orchestrator is None
    assert engine.reward_emitter.orchestrator is None


# ============================================================================
# Performance and Quality Tests
# ============================================================================


@pytest.mark.asyncio
async def test_ai_scoping_produces_different_results_than_templates(
    mock_orchestrator, sample_goal, mock_llm_response
):
    """Test that AI produces different (presumably better) results than templates"""
    # Configure AI response
    mock_llm_response.generated_text = """CRITICAL_PATH: Focus on core user authentication flow first
VALUE_SCORE: 0.9
EFFORT_SCORE: 0.2
REASONING: Auth unlocks the rest of the app"""

    mock_orchestrator.select_model = AsyncMock(return_value=Mock(provider="local", model_name="phi-2"))
    mock_orchestrator.execute_model = AsyncMock(return_value=mock_llm_response)

    # Get AI result
    ai_agent = ScopingAgent(orchestrator=mock_orchestrator)
    ai_session = await ai_agent.scope_goal(sample_goal)

    # Get template result
    template_agent = ScopingAgent(orchestrator=None)
    template_session = await template_agent.scope_goal(sample_goal)

    # Results should be different (AI should be more specific)
    # Template will use generic patterns, AI should be more context-aware
    assert ai_session.identified_80_win != template_session.identified_80_win


@pytest.mark.asyncio
async def test_ai_components_handle_complex_scenarios(mock_orchestrator, mock_llm_response):
    """Test AI components handle complex, real-world scenarios"""
    # Create a complex, ambiguous goal
    complex_goal = GoalPacket(
        goal_id="complex-1",
        user_id="test-user",
        description="Improve team productivity and morale while reducing technical debt",
        complexity_level=TaskComplexityLevel.EPIC,
        status=GoalStatus.IN_PROGRESS,
        created_at=datetime.now(),
    )

    # Configure AI response
    mock_llm_response.generated_text = """CRITICAL_PATH: Implement automated testing to reduce bugs and build confidence
VALUE_SCORE: 0.85
EFFORT_SCORE: 0.3
REASONING: Testing reduces technical debt while improving team confidence"""

    mock_orchestrator.select_model = AsyncMock(return_value=Mock(provider="local", model_name="phi-2"))
    mock_orchestrator.execute_model = AsyncMock(return_value=mock_llm_response)

    agent = ScopingAgent(orchestrator=mock_orchestrator)
    session = await agent.scope_goal(complex_goal)

    # AI should be able to find a specific 80/20 win even in complex scenarios
    assert session is not None
    assert session.identified_80_win is not None
    assert len(session.identified_80_win) > 20  # Should be reasonably detailed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

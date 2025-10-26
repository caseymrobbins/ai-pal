"""
Unit tests for ARI Measurement System.

Tests unassisted capability checkpoint identification, response evaluation,
and ARI scoring.
"""

import pytest
from pathlib import Path
from datetime import datetime

from ai_pal.ari.measurement import (
    ARIMeasurementSystem,
    ARIDimension,
    ARILevel,
    ARIScore,
    UnassistedCapabilityCheckpoint,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def ari_system(temp_dir):
    """Create ARI measurement system."""
    storage_dir = temp_dir / "ari"
    storage_dir.mkdir()
    return ARIMeasurementSystem(storage_dir=storage_dir)


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return "test_user_123"


# ============================================================================
# Initialization Tests
# ============================================================================

@pytest.mark.unit
def test_ari_system_initialization(ari_system):
    """Test ARI system initializes correctly."""
    assert ari_system.storage_dir is not None
    assert isinstance(ari_system.user_profiles, dict)
    assert isinstance(ari_system.active_checkpoints, dict)
    assert isinstance(ari_system.measurement_history, list)


# ============================================================================
# Checkpoint Identification Tests
# ============================================================================

@pytest.mark.unit
def test_identify_code_checkpoints(ari_system):
    """Test checkpoint identification for code generation."""
    checkpoints = ari_system.identify_checkpoints(
        user_request="Write a Python function to parse JSON files",
        task_type="code_generation"
    )

    assert len(checkpoints) > 0
    # Should have function naming checkpoint
    assert any("name" in cp.question.lower() for cp in checkpoints)
    # Should have logic checkpoint
    assert any("logic" in cp.question.lower() or "algorithm" in cp.question.lower() for cp in checkpoints)


@pytest.mark.unit
def test_identify_writing_checkpoints(ari_system):
    """Test checkpoint identification for writing tasks."""
    checkpoints = ari_system.identify_checkpoints(
        user_request="Draft an email to my team about the new project",
        task_type="writing"
    )

    assert len(checkpoints) > 0
    # Should have key points checkpoint
    assert any("key points" in cp.question.lower() or "points" in cp.question.lower() for cp in checkpoints)
    # Should have audience/tone checkpoint
    assert any("audience" in cp.question.lower() or "tone" in cp.question.lower() for cp in checkpoints)


@pytest.mark.unit
def test_checkpoints_stored(ari_system):
    """Test checkpoints are stored in active_checkpoints."""
    checkpoints = ari_system.identify_checkpoints(
        user_request="Write code",
        task_type="code_generation"
    )

    for checkpoint in checkpoints:
        assert checkpoint.checkpoint_id in ari_system.active_checkpoints


# ============================================================================
# Response Evaluation Tests
# ============================================================================

@pytest.mark.unit
def test_evaluate_high_ari_response(ari_system, sample_user_id):
    """Test evaluation of high ARI response."""
    checkpoints = ari_system.identify_checkpoints(
        user_request="Write a parser",
        task_type="code_generation"
    )

    checkpoint = checkpoints[0]

    # Detailed, specific response
    ari_level = ari_system.record_checkpoint_response(
        checkpoint_id=checkpoint.checkpoint_id,
        user_response="I want to name it parse_json_file, and it should use the json module with error handling for invalid JSON",
        user_id=sample_user_id
    )

    assert ari_level == ARILevel.HIGH


@pytest.mark.unit
def test_evaluate_low_ari_response(ari_system, sample_user_id):
    """Test evaluation of low ARI response (explicit deferral)."""
    checkpoints = ari_system.identify_checkpoints(
        user_request="Write a parser",
        task_type="code_generation"
    )

    checkpoint = checkpoints[0]

    # Explicit deferral
    ari_level = ari_system.record_checkpoint_response(
        checkpoint_id=checkpoint.checkpoint_id,
        user_response="I don't know, just guess",
        user_id=sample_user_id
    )

    assert ari_level == ARILevel.LOW


@pytest.mark.unit
def test_evaluate_medium_ari_response(ari_system, sample_user_id):
    """Test evaluation of medium ARI response."""
    checkpoints = ari_system.identify_checkpoints(
        user_request="Write a parser",
        task_type="code_generation"
    )

    checkpoint = checkpoints[0]

    # Short but specific
    ari_level = ari_system.record_checkpoint_response(
        checkpoint_id=checkpoint.checkpoint_id,
        user_response="parse_json would work",
        user_id=sample_user_id
    )

    assert ari_level == ARILevel.MEDIUM


@pytest.mark.unit
def test_various_deferral_phrases(ari_system, sample_user_id):
    """Test various deferral phrases are recognized as LOW ARI."""
    checkpoints = ari_system.identify_checkpoints(
        user_request="Write code",
        task_type="code_generation"
    )

    deferral_phrases = [
        "I don't know",
        "not sure",
        "just guess",
        "you decide",
        "whatever",
        "up to you",
        "idk"
    ]

    for i, phrase in enumerate(deferral_phrases):
        if i >= len(checkpoints):
            break

        checkpoint = checkpoints[i]
        ari_level = ari_system.record_checkpoint_response(
            checkpoint_id=checkpoint.checkpoint_id,
            user_response=phrase,
            user_id=sample_user_id
        )

        assert ari_level == ARILevel.LOW, f"'{phrase}' should result in LOW ARI"


# ============================================================================
# Synthesis Scoring Tests
# ============================================================================

@pytest.mark.unit
def test_score_synthesis_response(ari_system, sample_user_id):
    """Test synthesis response scoring."""
    response = "A decorator in Python is a function that modifies the behavior of another function. It uses the @ syntax and is useful for adding functionality like logging, authentication, or caching without modifying the original function."

    criteria = {
        "keywords": ["function", "decorator", "modify", "behavior"],
        "required_components": ["definition", "use_case"]
    }

    score = ari_system.score_synthesis_response(
        user_response=response,
        expected_criteria=criteria,
        domain="python_programming",
        user_id=sample_user_id
    )

    assert score is not None
    assert score.dimension == ARIDimension.SYNTHESIS
    assert score.accuracy is not None
    assert score.logic is not None
    assert score.completeness is not None


@pytest.mark.unit
def test_synthesis_score_accuracy(ari_system, sample_user_id):
    """Test accuracy scoring in synthesis responses."""
    criteria = {
        "keywords": ["list", "mutable", "tuple", "immutable"]
    }

    # Response with all keywords
    high_accuracy_response = "A list is mutable while a tuple is immutable"
    score_high = ari_system.score_synthesis_response(
        user_response=high_accuracy_response,
        expected_criteria=criteria,
        domain="python",
        user_id=sample_user_id
    )

    # Response with few keywords
    low_accuracy_response = "They're different data structures"
    score_low = ari_system.score_synthesis_response(
        user_response=low_accuracy_response,
        expected_criteria=criteria,
        domain="python",
        user_id=sample_user_id
    )

    assert score_high.accuracy > score_low.accuracy


@pytest.mark.unit
def test_synthesis_score_logic(ari_system, sample_user_id):
    """Test logic scoring in synthesis responses."""
    criteria = {"keywords": []}

    # Response with logical connectors
    logical_response = "If you use a list, then you can modify it because lists are mutable. However, tuples are immutable, therefore they cannot be changed after creation."

    # Response without logical structure
    non_logical_response = "Lists and tuples are different"

    score_logical = ari_system.score_synthesis_response(
        user_response=logical_response,
        expected_criteria=criteria,
        domain="python",
        user_id=sample_user_id
    )

    score_non_logical = ari_system.score_synthesis_response(
        user_response=non_logical_response,
        expected_criteria=criteria,
        domain="python",
        user_id=sample_user_id
    )

    assert score_logical.logic > score_non_logical.logic


@pytest.mark.unit
def test_synthesis_overall_level(ari_system, sample_user_id):
    """Test overall ARI level determination from rubric scores."""
    # High accuracy response
    high_response = "Decorators in Python are functions that modify other functions using the @ syntax. They're useful because they allow you to add functionality like logging, authentication, or caching. Therefore, you can enhance functions without modifying their code, which follows the open-closed principle."

    criteria = {
        "keywords": ["decorator", "function", "modify", "syntax"],
        "required_components": ["definition", "use_case", "example"]
    }

    score = ari_system.score_synthesis_response(
        user_response=high_response,
        expected_criteria=criteria,
        domain="python",
        user_id=sample_user_id
    )

    # Should be HIGH due to good coverage of all aspects
    assert score.level in [ARILevel.HIGH, ARILevel.MEDIUM]


# ============================================================================
# User Profile Tests
# ============================================================================

@pytest.mark.unit
def test_user_profile_creation(ari_system, sample_user_id):
    """Test user profile is created on first measurement."""
    checkpoints = ari_system.identify_checkpoints(
        user_request="Write code",
        task_type="code_generation"
    )

    ari_system.record_checkpoint_response(
        checkpoint_id=checkpoints[0].checkpoint_id,
        user_response="Detailed response here",
        user_id=sample_user_id
    )

    profile = ari_system.get_user_ari_profile(sample_user_id)
    assert sample_user_id in ari_system.user_profiles
    assert len(profile) > 0


@pytest.mark.unit
def test_user_profile_update(ari_system, sample_user_id):
    """Test user profile updates with multiple measurements."""
    domain = "programming"

    # First measurement
    checkpoints1 = ari_system.identify_checkpoints("Write code", "code_generation")
    ari_system.record_checkpoint_response(
        checkpoint_id=checkpoints1[0].checkpoint_id,
        user_response="Detailed response",
        user_id=sample_user_id
    )

    # Second measurement
    checkpoints2 = ari_system.identify_checkpoints("Write another script", "code_generation")
    ari_system.record_checkpoint_response(
        checkpoint_id=checkpoints2[0].checkpoint_id,
        user_response="Another detailed response",
        user_id=sample_user_id
    )

    # Check profile updated
    profile = ari_system.get_user_ari_profile(sample_user_id)
    dimension = checkpoints1[0].dimension

    if dimension in profile and domain in profile[dimension]:
        score = profile[dimension][domain]
        assert score.measurement_count >= 2


@pytest.mark.unit
def test_confidence_increases_with_measurements(ari_system, sample_user_id):
    """Test confidence increases with more measurements."""
    domain = "programming"
    dimension = ARIDimension.KNOWLEDGE

    # Record multiple measurements
    for i in range(5):
        checkpoints = ari_system.identify_checkpoints(f"Task {i}", "code_generation")
        # Find a knowledge checkpoint
        knowledge_cp = next((cp for cp in checkpoints if cp.dimension == dimension), checkpoints[0])

        ari_system.record_checkpoint_response(
            checkpoint_id=knowledge_cp.checkpoint_id,
            user_response=f"Detailed response {i}",
            user_id=sample_user_id
        )

    profile = ari_system.get_user_ari_profile(sample_user_id)

    if dimension in profile and domain in profile[dimension]:
        score = profile[dimension][domain]
        # Confidence should be higher than initial 0.5
        assert score.confidence > 0.5


@pytest.mark.unit
def test_get_user_ari_level(ari_system, sample_user_id):
    """Test retrieving user's ARI level for dimension/domain."""
    checkpoints = ari_system.identify_checkpoints("Write code", "code_generation")

    ari_system.record_checkpoint_response(
        checkpoint_id=checkpoints[0].checkpoint_id,
        user_response="Very detailed and specific response",
        user_id=sample_user_id
    )

    ari_level = ari_system.get_user_ari_level(
        user_id=sample_user_id,
        dimension=checkpoints[0].dimension,
        domain=checkpoints[0].domain
    )

    assert ari_level in [ARILevel.HIGH, ARILevel.MEDIUM, ARILevel.LOW]


@pytest.mark.unit
def test_unknown_ari_for_unmeasured(ari_system, sample_user_id):
    """Test UNKNOWN ARI level for unmeasured dimension/domain."""
    ari_level = ari_system.get_user_ari_level(
        user_id=sample_user_id,
        dimension=ARIDimension.SYNTHESIS,
        domain="unmeasured_domain"
    )

    assert ari_level == ARILevel.UNKNOWN


# ============================================================================
# Measurement History Tests
# ============================================================================

@pytest.mark.unit
def test_measurement_history_recorded(ari_system, sample_user_id):
    """Test measurements are added to history."""
    initial_history_len = len(ari_system.measurement_history)

    checkpoints = ari_system.identify_checkpoints("Write code", "code_generation")
    ari_system.record_checkpoint_response(
        checkpoint_id=checkpoints[0].checkpoint_id,
        user_response="Response",
        user_id=sample_user_id
    )

    assert len(ari_system.measurement_history) > initial_history_len


# ============================================================================
# Persistence Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_persist_and_load_profiles(ari_system, sample_user_id):
    """Test ARI profiles can be persisted and loaded."""
    # Record some measurements
    checkpoints = ari_system.identify_checkpoints("Write code", "code_generation")
    ari_system.record_checkpoint_response(
        checkpoint_id=checkpoints[0].checkpoint_id,
        user_response="Detailed response",
        user_id=sample_user_id
    )

    # Persist
    await ari_system.persist_profiles()

    # Create new system and load
    new_system = ARIMeasurementSystem(storage_dir=ari_system.storage_dir)
    await new_system.load_profiles()

    # Verify profile loaded
    assert sample_user_id in new_system.user_profiles


# ============================================================================
# Edge Cases Tests
# ============================================================================

@pytest.mark.unit
def test_empty_response(ari_system, sample_user_id):
    """Test handling of empty response."""
    checkpoints = ari_system.identify_checkpoints("Write code", "code_generation")

    ari_level = ari_system.record_checkpoint_response(
        checkpoint_id=checkpoints[0].checkpoint_id,
        user_response="",
        user_id=sample_user_id
    )

    assert ari_level == ARILevel.UNKNOWN


@pytest.mark.unit
def test_nonexistent_checkpoint(ari_system, sample_user_id):
    """Test error for nonexistent checkpoint."""
    with pytest.raises(ValueError):
        ari_system.record_checkpoint_response(
            checkpoint_id="nonexistent",
            user_response="Response",
            user_id=sample_user_id
        )

"""
Comprehensive tests for ARI Engine and RDI Monitor

Tests:
- PassiveLexicalAnalyzer
- SocraticCopilot
- DeepDiveMode
- ARIEngine
- RDIMonitor (with privacy enforcement)
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from src.ai_pal.monitoring.ari_engine import (
    ARIEngine,
    PassiveLexicalAnalyzer,
    SocraticCopilot,
    DeepDiveMode,
    ARISignalLevel,
    UCCResponseType,
    LexicalMetrics,
    UnassistedCapabilityCheckpoint,
    ARIBaseline,
    ARIScore
)

from src.ai_pal.monitoring.rdi_monitor import (
    RDIMonitor,
    RDILevel,
    DriftType,
    RDIScore as RDIScoreType,
    AnonymizedRDIStats
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_storage():
    """Create temporary storage directory"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def lexical_analyzer(temp_storage):
    """Create PassiveLexicalAnalyzer instance"""
    return PassiveLexicalAnalyzer(
        storage_dir=temp_storage / "lexical",
        lookback_window_days=30
    )


@pytest.fixture
def socratic_copilot(temp_storage):
    """Create SocraticCopilot instance"""
    return SocraticCopilot(storage_dir=temp_storage / "uccs")


@pytest.fixture
def deep_dive(temp_storage):
    """Create DeepDiveMode instance"""
    return DeepDiveMode(storage_dir=temp_storage / "baselines")


@pytest.fixture
def ari_engine(temp_storage):
    """Create ARIEngine instance"""
    return ARIEngine(storage_dir=temp_storage / "ari")


@pytest.fixture
def rdi_monitor(temp_storage):
    """Create RDIMonitor instance"""
    return RDIMonitor(
        storage_dir=temp_storage / "rdi",
        enable_privacy_mode=True
    )


# ============================================================================
# PASSIVE LEXICAL ANALYZER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_lexical_analyzer_basic_analysis(lexical_analyzer):
    """Test basic text analysis"""
    text = """
    The implementation of this complex algorithm requires careful consideration
    of performance tradeoffs and scalability constraints. We must analyze the
    computational complexity and memory utilization patterns to ensure optimal
    efficiency in production environments.
    """

    metrics = await lexical_analyzer.analyze_text(
        user_id="test_user",
        text=text,
        text_type="document"
    )

    assert metrics is not None
    assert metrics.lexical_diversity > 0
    assert metrics.vocabulary_richness > 0
    assert metrics.syntactic_complexity_score > 0
    assert metrics.total_words > 0
    assert metrics.unique_words > 0


@pytest.mark.asyncio
async def test_lexical_analyzer_simple_vs_complex(lexical_analyzer):
    """Test that complex text scores higher than simple text"""
    simple_text = "I like cats. Cats are nice. I have a cat."

    complex_text = """
    The utilization of sophisticated algorithmic approaches necessitates
    comprehensive evaluation of performance characteristics, particularly
    regarding computational complexity and resource allocation strategies.
    """

    simple_metrics = await lexical_analyzer.analyze_text(
        "user1", simple_text, "document"
    )
    complex_metrics = await lexical_analyzer.analyze_text(
        "user2", complex_text, "document"
    )

    # Complex text should have higher diversity and complexity
    assert complex_metrics.lexical_diversity > simple_metrics.lexical_diversity
    assert complex_metrics.syntactic_complexity_score > simple_metrics.syntactic_complexity_score


@pytest.mark.asyncio
async def test_lexical_analyzer_calculate_ari(lexical_analyzer):
    """Test ARI calculation from multiple samples"""
    user_id = "test_user"

    # Add multiple samples
    texts = [
        "This is a sophisticated technical implementation requiring careful analysis.",
        "The complex algorithm demonstrates intricate computational patterns and efficiency.",
        "Advanced methodologies facilitate comprehensive evaluation of system performance."
    ]

    for text in texts:
        await lexical_analyzer.analyze_text(user_id, text, "document")

    # Calculate ARI
    ari_score, trend = lexical_analyzer.calculate_lexical_ari(user_id)

    assert 0.0 <= ari_score <= 1.0
    assert trend in ["improving", "stable", "declining"]


@pytest.mark.asyncio
async def test_lexical_analyzer_detects_decline(lexical_analyzer):
    """Test detection of lexical decline"""
    user_id = "declining_user"

    # Start with complex text
    complex_texts = [
        "The sophisticated implementation necessitates comprehensive algorithmic evaluation.",
        "Advanced computational methodologies demonstrate intricate performance characteristics."
    ]

    for text in complex_texts:
        await lexical_analyzer.analyze_text(user_id, text, "document")

    # Then decline to simpler text
    simple_texts = [
        "I did the thing. It works now.",
        "Made it work. Is good.",
        "Fixed it. Works."
    ]

    for text in simple_texts:
        await lexical_analyzer.analyze_text(user_id, text, "document")

    # Add more samples for reliable trend detection
    for _ in range(7):
        await lexical_analyzer.analyze_text(user_id, "Simple stuff. Easy.", "document")

    ari_score, trend = lexical_analyzer.calculate_lexical_ari(user_id)

    # Should detect decline or have lower score
    assert trend == "declining" or ari_score < 0.5


# ============================================================================
# SOCRATIC CO-PILOT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_socratic_copilot_identify_uccs(socratic_copilot):
    """Test UCC identification for tasks"""
    questions = await socratic_copilot.identify_uccs(
        user_id="test_user",
        task_description="Improve the performance of the database queries",
        domain="programming"
    )

    assert len(questions) > 0
    assert isinstance(questions[0], str)
    # Should ask about subjective goals (improve/better)
    assert any("criteria" in q.lower() or "specific" in q.lower() for q in questions)


@pytest.mark.asyncio
async def test_socratic_copilot_log_accurate_response(socratic_copilot):
    """Test logging of accurate user response"""
    ucc = await socratic_copilot.log_response(
        user_id="test_user",
        task_description="Write a sorting function",
        question="What should the main logic be?",
        user_response="I want to use quicksort because it has O(n log n) average time complexity "
                     "and is efficient for most real-world data distributions.",
        domain="programming"
    )

    assert ucc is not None
    assert ucc.response_type == UCCResponseType.ACCURATE
    assert ucc.capability_demonstrated > 0.7
    assert ucc.ari_signal == ARISignalLevel.HIGH


@pytest.mark.asyncio
async def test_socratic_copilot_log_delegated_response(socratic_copilot):
    """Test logging of delegated response"""
    ucc = await socratic_copilot.log_response(
        user_id="test_user",
        task_description="Write a sorting function",
        question="What should the main logic be?",
        user_response="Just guess what's best",
        domain="programming"
    )

    assert ucc.response_type == UCCResponseType.DELEGATED
    assert ucc.capability_demonstrated == 0.0
    assert ucc.ari_signal == ARISignalLevel.CRITICAL


@pytest.mark.asyncio
async def test_socratic_copilot_log_uncertain_response(socratic_copilot):
    """Test logging of uncertain response"""
    ucc = await socratic_copilot.log_response(
        user_id="test_user",
        task_description="Optimize database query",
        question="What indexes should we use?",
        user_response="I don't know, not sure what would help",
        domain="programming"
    )

    assert ucc.response_type == UCCResponseType.UNCERTAIN
    assert ucc.capability_demonstrated < 0.5
    assert ucc.ari_signal == ARISignalLevel.LOW


@pytest.mark.asyncio
async def test_socratic_copilot_calculate_interaction_ari(socratic_copilot):
    """Test interaction ARI calculation"""
    user_id = "test_user"

    # Log multiple responses
    await socratic_copilot.log_response(
        user_id, "task1", "q1", "Detailed accurate response with reasoning", "programming"
    )
    await socratic_copilot.log_response(
        user_id, "task2", "q2", "Another good response explaining the approach", "programming"
    )

    ari_score, signal = socratic_copilot.calculate_interaction_ari(user_id)

    assert 0.0 <= ari_score <= 1.0
    assert signal in [ARISignalLevel.HIGH, ARISignalLevel.MEDIUM, ARISignalLevel.LOW, ARISignalLevel.CRITICAL]


# ============================================================================
# DEEP DIVE MODE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_deep_dive_start_session(deep_dive):
    """Test starting a deep dive session"""
    questions = await deep_dive.start_deep_dive(
        user_id="test_user",
        domain="programming"
    )

    assert len(questions) >= 5
    assert all(isinstance(q, str) for q in questions)
    assert any("approach" in q.lower() for q in questions)


@pytest.mark.asyncio
async def test_deep_dive_record_and_finalize(deep_dive, lexical_analyzer):
    """Test recording responses and finalizing baseline"""
    user_id = "test_user"
    domain = "programming"

    # Start session
    questions = await deep_dive.start_deep_dive(user_id, domain)

    # Record responses
    for question in questions:
        response = """
        I typically approach problems by first understanding the requirements,
        then breaking them down into smaller components. I consider the trade-offs
        between different approaches and evaluate performance characteristics.
        """
        await deep_dive.record_deep_dive_response(user_id, domain, question, response)

    # Finalize baseline
    baseline = await deep_dive.finalize_baseline(user_id, domain)

    assert baseline is not None
    assert baseline.user_id == deep_dive._hash_user_id(user_id) or baseline.user_id.startswith(user_id)
    assert baseline.domain == domain
    assert baseline.sample_count >= 5
    assert baseline.synthesis_quality_score > 0
    assert baseline.reasoning_depth_score > 0


def _hash_user_id_deepdive(deep_dive, user_id):
    """Helper to get hashed user ID from deep dive"""
    import hashlib
    return hashlib.sha256(f"{user_id}_deepdive".encode()).hexdigest()[:16]


# ============================================================================
# ARI ENGINE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_ari_engine_analyze_text(ari_engine):
    """Test ARI Engine text analysis"""
    metrics = await ari_engine.analyze_user_text(
        user_id="test_user",
        text="This is a sophisticated implementation of complex algorithms.",
        text_type="document"
    )

    assert metrics is not None
    assert metrics.lexical_diversity > 0


@pytest.mark.asyncio
async def test_ari_engine_intercept_task(ari_engine):
    """Test ARI Engine task interception"""
    questions = await ari_engine.intercept_task_delegation(
        user_id="test_user",
        task_description="Improve the database performance",
        domain="programming"
    )

    assert len(questions) > 0


@pytest.mark.asyncio
async def test_ari_engine_comprehensive_ari(ari_engine):
    """Test comprehensive ARI calculation"""
    user_id = "test_user"

    # Add some data
    await ari_engine.analyze_user_text(
        user_id,
        "Complex technical implementation with sophisticated algorithms.",
        "document"
    )

    questions = await ari_engine.intercept_task_delegation(
        user_id, "Write a function", "programming"
    )

    for q in questions[:2]:
        await ari_engine.record_ucc_response(
            user_id,
            "Write a function",
            q,
            "I think we should use this approach because it's efficient",
            "programming"
        )

    # Calculate comprehensive ARI
    ari_score = ari_engine.calculate_comprehensive_ari(user_id)

    assert ari_score is not None
    assert 0.0 <= ari_score.overall_ari <= 1.0
    assert ari_score.signal_level in [
        ARISignalLevel.HIGH,
        ARISignalLevel.MEDIUM,
        ARISignalLevel.LOW,
        ARISignalLevel.CRITICAL
    ]
    assert ari_score.trend_direction in ["improving", "stable", "declining"]


@pytest.mark.asyncio
async def test_ari_engine_deep_dive_integration(ari_engine):
    """Test deep dive integration with ARI engine"""
    user_id = "test_user"
    domain = "programming"

    # Start deep dive
    questions = await ari_engine.start_deep_dive_session(user_id, domain)
    assert len(questions) >= 5

    # Record responses
    for q in questions:
        await ari_engine.record_deep_dive_response(
            user_id, domain, q,
            "Detailed response demonstrating knowledge and reasoning"
        )

    # Finalize
    baseline = await ari_engine.finalize_deep_dive_baseline(user_id, domain)
    assert baseline is not None


# ============================================================================
# RDI MONITOR TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_rdi_monitor_privacy_mode_enabled(rdi_monitor):
    """Test that RDI monitor has privacy mode enabled"""
    assert rdi_monitor.privacy_mode is True


@pytest.mark.asyncio
async def test_rdi_monitor_analyze_input(rdi_monitor):
    """Test RDI analysis of user input"""
    drift_score, signals = await rdi_monitor.analyze_input(
        user_id="test_user",
        user_input="I believe the earth is round and orbits the sun.",
        domain="science"
    )

    assert 0.0 <= drift_score <= 1.0
    assert isinstance(signals, list)


@pytest.mark.asyncio
async def test_rdi_monitor_user_id_hashing(rdi_monitor):
    """Test that user IDs are hashed for privacy"""
    user_id = "test_user_123"
    hashed = rdi_monitor._hash_user_id(user_id)

    # Should be a hash, not the original ID
    assert hashed != user_id
    assert len(hashed) == 16  # Short hash


@pytest.mark.asyncio
async def test_rdi_monitor_no_raw_storage(rdi_monitor, temp_storage):
    """Test that raw user input is not stored"""
    user_input = "This is sensitive user input that should not be stored"

    await rdi_monitor.analyze_input(
        user_id="test_user",
        user_input=user_input
    )

    # Check that raw input is not in any stored files
    rdi_dir = temp_storage / "rdi"
    if rdi_dir.exists():
        for file in rdi_dir.glob("*.json"):
            with open(file, 'r') as f:
                content = f.read()
                assert user_input not in content


@pytest.mark.asyncio
async def test_rdi_monitor_calculate_score(rdi_monitor):
    """Test RDI score calculation"""
    user_id = "test_user"

    # Add some data
    for _ in range(5):
        await rdi_monitor.analyze_input(
            user_id,
            "Sample input for establishing baseline patterns",
            "general"
        )

    # Calculate score
    score = rdi_monitor.calculate_rdi_score(user_id)

    assert score is not None
    assert 0.0 <= score.overall_rdi <= 1.0
    assert score.rdi_level in [
        RDILevel.ALIGNED,
        RDILevel.MINOR_DRIFT,
        RDILevel.MODERATE_DRIFT,
        RDILevel.SIGNIFICANT_DRIFT,
        RDILevel.CRITICAL_DRIFT
    ]
    assert score._is_private is True


@pytest.mark.asyncio
async def test_rdi_monitor_dashboard_data(rdi_monitor):
    """Test getting RDI data for private dashboard"""
    user_id = "test_user"

    # Add some data
    await rdi_monitor.analyze_input(user_id, "Test input", "general")
    rdi_monitor.calculate_rdi_score(user_id)

    # Get dashboard data
    dashboard_data = rdi_monitor.get_user_rdi_for_dashboard(user_id)

    assert dashboard_data["rdi_available"] is True
    assert "current_rdi" in dashboard_data
    assert "rdi_level" in dashboard_data
    assert "history" in dashboard_data
    assert "_privacy_notice" in dashboard_data


def test_rdi_monitor_opt_in(rdi_monitor):
    """Test user opt-in to aggregate sharing"""
    user_id = "test_user"

    result = rdi_monitor.opt_in_to_aggregate_sharing(user_id)
    assert result is True

    # Check that user is in opt-ins
    hashed = rdi_monitor._hash_user_id(user_id)
    assert hashed in rdi_monitor._aggregate_opt_ins


def test_rdi_monitor_aggregate_privacy_threshold(rdi_monitor):
    """Test that aggregate requires minimum 100 users"""
    # Add only 50 users (below threshold)
    for i in range(50):
        user_id = f"user_{i}"
        rdi_monitor.opt_in_to_aggregate_sharing(user_id)
        rdi_monitor.calculate_rdi_score(user_id)

    # Try to generate aggregate
    aggregate = rdi_monitor.generate_anonymized_aggregate()

    # Should fail due to insufficient users
    assert aggregate is None


def test_rdi_monitor_aggregate_with_sufficient_users(rdi_monitor):
    """Test aggregate generation with sufficient users"""
    # Add 100+ users
    for i in range(110):
        user_id = f"user_{i}"
        rdi_monitor.opt_in_to_aggregate_sharing(user_id)

        # Generate a score
        score = RDIScoreType(
            user_id=rdi_monitor._hash_user_id(user_id),
            timestamp=datetime.now(),
            overall_rdi=0.3 + (i % 10) * 0.05,  # Vary the scores
            rdi_level=RDILevel.ALIGNED,
            semantic_drift=0.2,
            factual_drift=0.1,
            logical_drift=0.0,
            trend_direction="stable",
            days_in_trend=0
        )

        hashed = rdi_monitor._hash_user_id(user_id)
        if hashed not in rdi_monitor._local_rdi_scores:
            rdi_monitor._local_rdi_scores[hashed] = []
        rdi_monitor._local_rdi_scores[hashed].append(score)

    # Generate aggregate
    aggregate = rdi_monitor.generate_anonymized_aggregate()

    # Should succeed
    assert aggregate is not None
    assert aggregate.total_users >= 100
    assert aggregate.minimum_user_threshold_met is True
    assert aggregate.anonymization_applied is True
    assert aggregate.pii_scrubbed is True


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_ari_and_rdi_integration(ari_engine, rdi_monitor):
    """Test integration between ARI Engine and RDI Monitor"""
    user_id = "test_user"

    # Analyze text with both systems
    text = "Complex algorithmic implementation demonstrating sophisticated patterns."

    # ARI analysis
    ari_metrics = await ari_engine.analyze_user_text(user_id, text, "document")

    # RDI analysis
    rdi_drift, rdi_signals = await rdi_monitor.analyze_input(user_id, text, "programming")

    # Both should produce valid results
    assert ari_metrics is not None
    assert 0.0 <= rdi_drift <= 1.0


@pytest.mark.asyncio
async def test_full_ari_workflow(ari_engine):
    """Test complete ARI workflow"""
    user_id = "workflow_user"

    # 1. Passive lexical analysis
    for i in range(5):
        await ari_engine.analyze_user_text(
            user_id,
            f"Sample text number {i} with varying complexity and structure.",
            "document"
        )

    # 2. Socratic co-pilot interaction
    questions = await ari_engine.intercept_task_delegation(
        user_id, "Implement a new feature", "programming"
    )

    for q in questions[:3]:
        await ari_engine.record_ucc_response(
            user_id, "Implement a new feature", q,
            "I want to use this approach because it's efficient and maintainable",
            "programming"
        )

    # 3. Calculate comprehensive ARI
    ari_score = ari_engine.calculate_comprehensive_ari(user_id, "programming")

    assert ari_score is not None
    assert ari_score.overall_ari >= 0.0
    assert ari_score.lexical_ari >= 0.0
    assert ari_score.interaction_ari >= 0.0


@pytest.mark.asyncio
async def test_full_rdi_workflow(rdi_monitor):
    """Test complete RDI workflow"""
    user_id = "workflow_user"

    # 1. Analyze multiple inputs
    inputs = [
        "The earth orbits the sun as part of our solar system.",
        "Scientific evidence supports evolutionary theory.",
        "Mathematical proofs demonstrate the validity of theorems."
    ]

    for inp in inputs:
        await rdi_monitor.analyze_input(user_id, inp, "science")

    # 2. Calculate RDI score
    score = rdi_monitor.calculate_rdi_score(user_id)

    assert score is not None
    assert score._is_private is True

    # 3. Get dashboard data (private)
    dashboard = rdi_monitor.get_user_rdi_for_dashboard(user_id)

    assert dashboard["rdi_available"] is True
    assert "_privacy_notice" in dashboard
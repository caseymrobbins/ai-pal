"""
Unit Tests for EDM Monitor

Tests the Epistemic Debt Monitoring system including:
- Text analysis for debt patterns
- Debt classification and severity
- Fact-checking integration
- Debt resolution tracking
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from ai_pal.monitoring.edm_monitor import (
    EDMMonitor,
    EpistemicDebtSnapshot,
    DebtSeverity,
    FactCheckStatus,
    EDMReport,
)


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage directory"""
    return tmp_path / "edm_test"


@pytest.fixture
def edm_monitor(temp_storage):
    """Create EDM monitor instance"""
    return EDMMonitor(
        storage_dir=temp_storage,
        fact_check_enabled=False,  # Disable for testing
    )


# ============================================================================
# Text Analysis Tests - Unfalsifiable Claims
# ============================================================================


@pytest.mark.asyncio
async def test_detect_unfalsifiable_everyone_knows(edm_monitor):
    """Test detection of 'everyone knows' pattern"""
    text = "Everyone knows that AI will replace all jobs by 2030."

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    assert len(debts) > 0
    assert any(debt.debt_type == "unfalsifiable" for debt in debts)
    assert any("everyone knows" in debt.claim.lower() for debt in debts)


@pytest.mark.asyncio
async def test_detect_unfalsifiable_obviously(edm_monitor):
    """Test detection of 'it's obvious' pattern"""
    text = "It's obvious that this approach is the best solution."

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    assert len(debts) > 0
    assert any(debt.debt_type == "unfalsifiable" for debt in debts)


@pytest.mark.asyncio
async def test_detect_unfalsifiable_no_one_can_deny(edm_monitor):
    """Test detection of 'no one can deny' pattern"""
    text = "No one can deny that quantum computing will solve all problems."

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    assert len(debts) > 0
    assert any(debt.debt_type == "unfalsifiable" for debt in debts)


# ============================================================================
# Text Analysis Tests - Unverified Assertions
# ============================================================================


@pytest.mark.asyncio
async def test_detect_unverified_studies_show(edm_monitor):
    """Test detection of 'studies show' without citation"""
    text = "Studies show that AI improves productivity by 300%."

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    assert len(debts) > 0
    assert any(debt.debt_type == "missing_citation" for debt in debts)


@pytest.mark.asyncio
async def test_detect_unverified_research_indicates(edm_monitor):
    """Test detection of 'research indicates' without citation"""
    text = "Research indicates that meditation increases brain size."

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    assert len(debts) > 0
    assert any(debt.debt_type == "missing_citation" for debt in debts)


@pytest.mark.asyncio
async def test_no_debt_with_proper_citation(edm_monitor):
    """Test that proper citations don't trigger alerts"""
    text = """According to Smith et al. (2023), machine learning models show
    significant improvement when trained on larger datasets. The study,
    published in Nature, analyzed 100 different models."""

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    # Should not detect high-severity debt for properly cited claims
    high_severity = [d for d in debts if d.severity in [DebtSeverity.HIGH, DebtSeverity.CRITICAL]]
    assert len(high_severity) == 0


# ============================================================================
# Text Analysis Tests - Vague Claims
# ============================================================================


@pytest.mark.asyncio
async def test_detect_vague_many_people(edm_monitor):
    """Test detection of 'many people' vague claim"""
    text = "Many people believe that blockchain will revolutionize everything."

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    assert len(debts) > 0
    assert any(debt.debt_type == "vague_claim" for debt in debts)
    assert any(debt.severity == DebtSeverity.LOW for debt in debts)


@pytest.mark.asyncio
async def test_detect_vague_some_say(edm_monitor):
    """Test detection of 'some say' vague claim"""
    text = "Some say that renewable energy can't meet our needs."

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-user",
        user_id="test-user",
    )

    assert len(debts) > 0
    assert any(debt.debt_type == "vague_claim" for debt in debts)


# ============================================================================
# Severity Classification Tests
# ============================================================================


@pytest.mark.asyncio
async def test_severity_low_for_vague(edm_monitor):
    """Test that vague claims are classified as LOW severity"""
    text = "Generally speaking, people prefer simpler interfaces."

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    assert len(debts) > 0
    vague_debts = [d for d in debts if d.debt_type == "vague_claim"]
    assert all(d.severity == DebtSeverity.LOW for d in vague_debts)


@pytest.mark.asyncio
async def test_severity_medium_for_unfalsifiable(edm_monitor):
    """Test that unfalsifiable claims are classified as MEDIUM severity"""
    text = "Clearly, this is the only correct approach to the problem."

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    assert len(debts) > 0
    unfalsifiable_debts = [d for d in debts if d.debt_type == "unfalsifiable"]
    assert all(d.severity == DebtSeverity.MEDIUM for d in unfalsifiable_debts)


@pytest.mark.asyncio
async def test_severity_high_for_missing_citation(edm_monitor):
    """Test that missing citations are classified as HIGH severity"""
    text = "Statistics show that 87% of users prefer our product."

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    assert len(debts) > 0
    citation_debts = [d for d in debts if d.debt_type == "missing_citation"]
    assert all(d.severity == DebtSeverity.HIGH for d in citation_debts)


# ============================================================================
# Multiple Patterns Tests
# ============================================================================


@pytest.mark.asyncio
async def test_detect_multiple_patterns(edm_monitor):
    """Test detection of multiple debt patterns in same text"""
    text = """
    Everyone knows that AI is the future. Studies show that adoption rates
    are increasing exponentially. Many people are concerned about job
    displacement, but clearly the benefits outweigh the risks.
    """

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    # Should detect multiple types
    assert len(debts) >= 3
    debt_types = {d.debt_type for d in debts}
    assert "unfalsifiable" in debt_types
    assert "missing_citation" in debt_types or "vague_claim" in debt_types


# ============================================================================
# Debt Resolution Tests
# ============================================================================


@pytest.mark.asyncio
async def test_resolve_debt(edm_monitor):
    """Test resolving an epistemic debt"""
    text = "Studies show AI improves productivity."

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    assert len(debts) > 0
    debt = debts[0]

    # Resolve the debt
    await edm_monitor.resolve_debt(
        debt_id=debt.debt_id,
        resolution_method="citation_added",
    )

    # Verify debt is resolved - direct dict access
    resolved_debt = edm_monitor.debt_instances[debt.debt_id]
    assert resolved_debt.resolved is True
    assert resolved_debt.resolution_method == "citation_added"


# ============================================================================
# Reporting Tests
# ============================================================================


@pytest.mark.asyncio
async def test_generate_report(edm_monitor):
    """Test generating EDM report"""
    # Create some debts
    texts = [
        "Everyone knows this is true.",
        "Studies show remarkable results.",
        "Many people agree with this view.",
    ]

    for i, text in enumerate(texts):
        await edm_monitor.analyze_text(
            text=text,
            task_id=f"task-{i}",
            user_id="test-user",
        )

    # Generate report - correct parameter names
    report = edm_monitor.generate_report(
        user_id="test-user",
        start_date=datetime.now() - timedelta(days=1),
        end_date=datetime.now() + timedelta(hours=1),
    )

    assert report is not None
    assert report.total_debt_instances >= 3
    assert len(report.debt_by_severity) > 0


# ============================================================================
# Clean Text Tests
# ============================================================================


@pytest.mark.asyncio
async def test_no_false_positives_scientific_text(edm_monitor):
    """Test that clean scientific text doesn't trigger false alerts"""
    text = """
    According to the results published in Journal of AI Research (2023),
    the proposed algorithm achieved 95% accuracy on the benchmark dataset.
    The methodology involved training on 10,000 labeled examples, with
    cross-validation performed using 5 folds. Statistical significance
    was confirmed using t-tests (p < 0.05).
    """

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    # Should not detect HIGH or CRITICAL severity debts
    high_severity = [d for d in debts if d.severity in [DebtSeverity.HIGH, DebtSeverity.CRITICAL]]
    assert len(high_severity) == 0


@pytest.mark.asyncio
async def test_no_false_positives_technical_text(edm_monitor):
    """Test that technical documentation doesn't trigger false alerts"""
    text = """
    The function accepts two parameters: the input array and a threshold value.
    It returns the filtered results based on the specified criteria.
    Performance is O(n) where n is the array length.
    """

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    # Technical text should not trigger debt detection
    assert len(debts) == 0


# ============================================================================
# Persistence Tests
# ============================================================================


@pytest.mark.asyncio
async def test_debt_persistence(edm_monitor):
    """Test that debts persist across monitor instances"""
    text = "Everyone knows that this is the best approach."

    # Record debts
    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    assert len(debts) > 0
    debt_id = debts[0].debt_id

    # Create new monitor instance
    new_monitor = EDMMonitor(
        storage_dir=edm_monitor.storage_dir,
        fact_check_enabled=False,
    )

    # Should be able to retrieve debt - direct dict access
    retrieved_debt = new_monitor.debt_instances.get(debt_id)
    assert retrieved_debt is not None
    assert retrieved_debt.debt_id == debt_id


# ============================================================================
# Edge Cases
# ============================================================================


@pytest.mark.asyncio
async def test_empty_text(edm_monitor):
    """Test analysis of empty text"""
    debts = await edm_monitor.analyze_text(
        text="",
        task_id="test-task",
        user_id="test-user",
    )

    assert len(debts) == 0


@pytest.mark.asyncio
async def test_very_long_text(edm_monitor):
    """Test analysis of very long text"""
    # Create long text with patterns
    text = " ".join(["Everyone knows this is true."] * 100)

    debts = await edm_monitor.analyze_text(
        text=text,
        task_id="test-task",
        user_id="test-user",
    )

    # Should detect patterns even in long text
    assert len(debts) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

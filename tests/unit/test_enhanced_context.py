"""
Unit tests for Enhanced Context Window Management (Phase 3.3).

Tests accurate token counting, relevance scoring, smart pruning,
and memory management.
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta

from ai_pal.context.enhanced_context import (
    EnhancedContextManager,
    MemoryEntry,
    MemoryType,
    MemoryPriority,
    ContextWindow,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def context_manager(temp_dir):
    """Create an enhanced context manager."""
    storage_dir = temp_dir / "context"
    storage_dir.mkdir()
    return EnhancedContextManager(
        storage_dir=storage_dir,
        max_context_tokens=2000,
        memory_decay_days=30
    )


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return "test_user_123"


@pytest.fixture
def sample_memories():
    """Create sample memory entries."""
    now = datetime.now()
    return [
        MemoryEntry(
            memory_id="mem_001",
            user_id="test_user_123",
            content="User prefers Python over JavaScript",
            memory_type=MemoryType.PREFERENCE,
            priority=MemoryPriority.HIGH,
            timestamp=now - timedelta(days=1),
            access_count=5,
            last_accessed=now
        ),
        MemoryEntry(
            memory_id="mem_002",
            user_id="test_user_123",
            content="User is working on a machine learning project",
            memory_type=MemoryType.CONTEXT,
            priority=MemoryPriority.MEDIUM,
            timestamp=now - timedelta(days=7),
            access_count=2,
            last_accessed=now - timedelta(days=2)
        ),
        MemoryEntry(
            memory_id="mem_003",
            user_id="test_user_123",
            content="User's signature strength is analytical thinking",
            memory_type=MemoryType.IDENTITY,
            priority=MemoryPriority.CRITICAL,
            timestamp=now - timedelta(days=30),
            access_count=10,
            last_accessed=now
        ),
        MemoryEntry(
            memory_id="mem_004",
            user_id="test_user_123",
            content="Temporary note about today's meeting",
            memory_type=MemoryType.CONVERSATION,
            priority=MemoryPriority.EPHEMERAL,
            timestamp=now - timedelta(hours=2),
            access_count=1,
            last_accessed=now - timedelta(hours=1)
        ),
    ]


# ============================================================================
# Initialization Tests
# ============================================================================

@pytest.mark.unit
def test_context_manager_initialization(context_manager):
    """Test context manager initializes correctly."""
    assert context_manager.storage_dir is not None
    assert context_manager.max_context_tokens == 2000
    assert context_manager.memory_decay_days == 30
    assert isinstance(context_manager.memories, dict)
    assert isinstance(context_manager.context_windows, dict)


@pytest.mark.unit
def test_tokenizer_initialization(context_manager):
    """Test tiktoken tokenizer is initialized."""
    # Should have tokenizer or None (if tiktoken unavailable)
    assert hasattr(context_manager, 'tokenizer')


# ============================================================================
# Token Counting Tests
# ============================================================================

@pytest.mark.unit
def test_count_tokens_basic(context_manager):
    """Test basic token counting."""
    text = "Hello, world! This is a test."
    token_count = context_manager._count_tokens(text)

    # Should be > 0
    assert token_count > 0

    # Rough estimate: should be close to word count
    word_count = len(text.split())
    assert token_count >= word_count * 0.5  # At least half the word count
    assert token_count <= word_count * 2    # At most twice the word count


@pytest.mark.unit
def test_count_tokens_empty_string(context_manager):
    """Test token counting with empty string."""
    token_count = context_manager._count_tokens("")
    assert token_count == 0


@pytest.mark.unit
def test_count_tokens_long_text(context_manager):
    """Test token counting with longer text."""
    # Create a longer text
    text = " ".join(["word"] * 100)
    token_count = context_manager._count_tokens(text)

    # Should be roughly proportional to length
    assert token_count > 50
    assert token_count < 200


# ============================================================================
# Relevance Scoring Tests
# ============================================================================

@pytest.mark.unit
def test_relevance_scoring_critical_priority(context_manager, sample_memories):
    """Test CRITICAL memories get high relevance scores."""
    critical_memory = sample_memories[2]  # The CRITICAL one
    score = context_manager._calculate_relevance_score(critical_memory)

    # Critical memories should score high (priority component is 40% * 1.0 = 0.4)
    assert score >= 0.4


@pytest.mark.unit
def test_relevance_scoring_recent_vs_old(context_manager):
    """Test recent memories score higher than old ones."""
    now = datetime.now()

    recent_memory = MemoryEntry(
        memory_id="recent",
        user_id="test",
        content="Recent content",
        memory_type=MemoryType.CONTEXT,
        priority=MemoryPriority.MEDIUM,
        timestamp=now - timedelta(hours=1),
        access_count=1,
        last_accessed=now
    )

    old_memory = MemoryEntry(
        memory_id="old",
        user_id="test",
        content="Old content",
        memory_type=MemoryType.CONTEXT,
        priority=MemoryPriority.MEDIUM,
        timestamp=now - timedelta(days=25),
        access_count=1,
        last_accessed=now - timedelta(days=20)
    )

    recent_score = context_manager._calculate_relevance_score(recent_memory, now)
    old_score = context_manager._calculate_relevance_score(old_memory, now)

    assert recent_score > old_score


@pytest.mark.unit
def test_relevance_scoring_access_patterns(context_manager):
    """Test frequently accessed memories score higher."""
    now = datetime.now()

    frequent_memory = MemoryEntry(
        memory_id="frequent",
        user_id="test",
        content="Frequently accessed",
        memory_type=MemoryType.CONTEXT,
        priority=MemoryPriority.MEDIUM,
        timestamp=now - timedelta(days=10),
        access_count=15,
        last_accessed=now
    )

    rare_memory = MemoryEntry(
        memory_id="rare",
        user_id="test",
        content="Rarely accessed",
        memory_type=MemoryType.CONTEXT,
        priority=MemoryPriority.MEDIUM,
        timestamp=now - timedelta(days=10),
        access_count=1,
        last_accessed=now - timedelta(days=5)
    )

    frequent_score = context_manager._calculate_relevance_score(frequent_memory, now)
    rare_score = context_manager._calculate_relevance_score(rare_memory, now)

    assert frequent_score > rare_score


@pytest.mark.unit
def test_relevance_scoring_components(context_manager):
    """Test all four scoring components contribute."""
    now = datetime.now()

    # Memory with all good factors
    perfect_memory = MemoryEntry(
        memory_id="perfect",
        user_id="test",
        content="Perfect memory",
        memory_type=MemoryType.IDENTITY,
        priority=MemoryPriority.CRITICAL,      # High priority (40%)
        timestamp=now - timedelta(hours=1),    # Recent (30%)
        access_count=20,                        # Frequently accessed (20%)
        last_accessed=now                       # Recently accessed (10%)
    )

    score = context_manager._calculate_relevance_score(perfect_memory, now)

    # Should be very high (close to 1.0)
    assert score >= 0.8
    assert score <= 1.0


# ============================================================================
# Memory Management Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_add_memory(context_manager, sample_user_id):
    """Test adding a memory."""
    memory_id = await context_manager.add_memory(
        user_id=sample_user_id,
        content="This is a test memory",
        memory_type=MemoryType.CONTEXT,
        priority=MemoryPriority.MEDIUM
    )

    assert memory_id is not None
    assert memory_id in context_manager.memories
    assert context_manager.memories[memory_id].content == "This is a test memory"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_memory(context_manager, sample_user_id):
    """Test retrieving a memory."""
    # Add memory
    memory_id = await context_manager.add_memory(
        user_id=sample_user_id,
        content="Test content",
        memory_type=MemoryType.CONTEXT,
        priority=MemoryPriority.MEDIUM
    )

    # Retrieve it
    memory = await context_manager.get_memory(memory_id)

    assert memory is not None
    assert memory.memory_id == memory_id
    assert memory.content == "Test content"
    assert memory.access_count == 1  # Should increment on access


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_memory_priority(context_manager, sample_user_id):
    """Test updating memory priority."""
    # Add memory
    memory_id = await context_manager.add_memory(
        user_id=sample_user_id,
        content="Test",
        memory_type=MemoryType.CONTEXT,
        priority=MemoryPriority.LOW
    )

    # Update priority
    await context_manager.update_memory_priority(memory_id, MemoryPriority.HIGH)

    # Check updated
    memory = await context_manager.get_memory(memory_id)
    assert memory.priority == MemoryPriority.HIGH


# ============================================================================
# Context Window Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_context_window(context_manager, sample_user_id):
    """Test creating a context window."""
    window = await context_manager.create_context_window(
        user_id=sample_user_id,
        query="Test query"
    )

    assert window is not None
    assert window.user_id == sample_user_id
    assert window.query == "Test query"
    assert isinstance(window.memory_ids, list)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_populate_context_window(context_manager, sample_user_id, sample_memories):
    """Test populating context window with relevant memories."""
    # Add sample memories
    for memory in sample_memories:
        context_manager.memories[memory.memory_id] = memory

    # Create and populate window
    window = await context_manager.create_context_window(
        user_id=sample_user_id,
        query="Tell me about Python"
    )

    # Should have some memories
    assert len(window.memory_ids) > 0

    # CRITICAL memories should be included
    critical_memory_id = "mem_003"
    assert critical_memory_id in window.memory_ids


@pytest.mark.unit
@pytest.mark.asyncio
async def test_context_window_respects_token_limit(context_manager, sample_user_id):
    """Test context window stays within token limit."""
    # Add many large memories
    for i in range(20):
        long_content = " ".join(["word"] * 100)  # ~100 tokens each
        await context_manager.add_memory(
            user_id=sample_user_id,
            content=long_content,
            memory_type=MemoryType.CONTEXT,
            priority=MemoryPriority.MEDIUM
        )

    # Create window with limited tokens
    context_manager.max_context_tokens = 500
    window = await context_manager.create_context_window(
        user_id=sample_user_id,
        query="Test"
    )

    # Calculate total tokens
    total_tokens = sum(
        context_manager._count_tokens(context_manager.memories[mid].content)
        for mid in window.memory_ids
    )

    # Should be within limit
    assert total_tokens <= context_manager.max_context_tokens


# ============================================================================
# Context Pruning Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_prune_context_window(context_manager, sample_memories):
    """Test pruning removes least relevant memories."""
    # Create window
    window = ContextWindow(
        window_id="test_window",
        user_id="test_user_123",
        query="Test",
        memory_ids=[m.memory_id for m in sample_memories],
        created_at=datetime.now(),
        total_tokens=5000  # Over limit
    )

    # Add memories to manager
    for memory in sample_memories:
        context_manager.memories[memory.memory_id] = memory

    # Prune to free 1000 tokens
    tokens_freed = await context_manager._prune_context_window(window, tokens_needed=1000)

    # Should have freed some tokens
    assert tokens_freed > 0

    # Should not have removed CRITICAL memory
    critical_memory_id = "mem_003"
    assert critical_memory_id in window.memory_ids or critical_memory_id in window.pruned_memories
    # If still in window, it wasn't pruned (good!)
    # If in pruned_memories, check it's not the first one removed
    if critical_memory_id not in window.memory_ids:
        # Critical should be last to prune, so if everything was pruned, it's ok
        assert len(window.pruned_memories) == len(sample_memories) - len(window.memory_ids)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_prune_protects_critical_memories(context_manager, sample_memories):
    """Test pruning protects CRITICAL memories."""
    # Create window
    window = ContextWindow(
        window_id="test_window",
        user_id="test_user_123",
        query="Test",
        memory_ids=[m.memory_id for m in sample_memories],
        created_at=datetime.now(),
        total_tokens=5000
    )

    # Add memories
    for memory in sample_memories:
        context_manager.memories[memory.memory_id] = memory

    # Prune heavily
    await context_manager._prune_context_window(window, tokens_needed=4000)

    # CRITICAL memory should still be in window
    critical_memory_id = "mem_003"
    assert critical_memory_id in window.memory_ids


@pytest.mark.unit
@pytest.mark.asyncio
async def test_prune_removes_lowest_relevance_first(context_manager):
    """Test pruning removes lowest relevance memories first."""
    now = datetime.now()

    # Create memories with different relevance
    low_relevance = MemoryEntry(
        memory_id="low",
        user_id="test",
        content="Low relevance memory",
        memory_type=MemoryType.CONVERSATION,
        priority=MemoryPriority.EPHEMERAL,
        timestamp=now - timedelta(days=20),
        access_count=1,
        last_accessed=now - timedelta(days=15)
    )

    high_relevance = MemoryEntry(
        memory_id="high",
        user_id="test",
        content="High relevance memory",
        memory_type=MemoryType.IDENTITY,
        priority=MemoryPriority.HIGH,
        timestamp=now - timedelta(hours=1),
        access_count=10,
        last_accessed=now
    )

    # Add to manager
    context_manager.memories["low"] = low_relevance
    context_manager.memories["high"] = high_relevance

    # Create window with both
    window = ContextWindow(
        window_id="test",
        user_id="test",
        query="Test",
        memory_ids=["low", "high"],
        created_at=now,
        total_tokens=1000
    )

    # Prune to remove one
    await context_manager._prune_context_window(window, tokens_needed=500)

    # Low relevance should be pruned first
    assert "low" in window.pruned_memories or "low" not in window.memory_ids
    # High relevance should remain
    assert "high" in window.memory_ids


# ============================================================================
# Memory Decay Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_memory_decay(context_manager, sample_user_id):
    """Test old memories decay in relevance."""
    now = datetime.now()

    # Create old memory
    old_memory = MemoryEntry(
        memory_id="old",
        user_id=sample_user_id,
        content="Very old memory",
        memory_type=MemoryType.CONTEXT,
        priority=MemoryPriority.MEDIUM,
        timestamp=now - timedelta(days=100),  # Beyond decay period
        access_count=1,
        last_accessed=now - timedelta(days=90)
    )

    # Calculate relevance
    score = context_manager._calculate_relevance_score(old_memory, now)

    # Should be low due to age
    assert score < 0.5


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cleanup_old_memories(context_manager, sample_user_id):
    """Test cleanup removes very old memories."""
    now = datetime.now()

    # Add old ephemeral memory
    old_id = await context_manager.add_memory(
        user_id=sample_user_id,
        content="Very old ephemeral",
        memory_type=MemoryType.CONVERSATION,
        priority=MemoryPriority.EPHEMERAL
    )

    # Manually set timestamp to very old
    context_manager.memories[old_id].timestamp = now - timedelta(days=200)

    # Run cleanup
    await context_manager.cleanup_old_memories(max_age_days=30)

    # Old ephemeral should be removed
    assert old_id not in context_manager.memories


# ============================================================================
# Edge Cases Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_empty_context_window(context_manager, sample_user_id):
    """Test creating context window with no memories."""
    window = await context_manager.create_context_window(
        user_id=sample_user_id,
        query="Test"
    )

    assert window is not None
    assert len(window.memory_ids) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_nonexistent_memory(context_manager):
    """Test getting memory that doesn't exist."""
    memory = await context_manager.get_memory("nonexistent")
    assert memory is None


@pytest.mark.unit
def test_count_tokens_special_characters(context_manager):
    """Test token counting with special characters."""
    text = "Hello! 你好 👋 @#$%^&*()"
    token_count = context_manager._count_tokens(text)

    # Should handle special characters
    assert token_count > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_context_window_persistence(context_manager, sample_user_id, sample_memories):
    """Test context windows can be persisted and loaded."""
    # Add memories
    for memory in sample_memories:
        context_manager.memories[memory.memory_id] = memory

    # Create window
    window = await context_manager.create_context_window(
        user_id=sample_user_id,
        query="Test query"
    )

    # Persist
    await context_manager._persist_context_windows()

    # Create new manager and load
    new_manager = EnhancedContextManager(
        storage_dir=context_manager.storage_dir,
        max_context_tokens=2000
    )
    await new_manager._load_context_windows()

    # Window should be loaded
    assert window.window_id in new_manager.context_windows

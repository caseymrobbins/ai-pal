"""
Tests for Phase 3: Enhanced Context Management

Tests semantic search, memory consolidation, and context window optimization.
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile

from ai_pal.context.enhanced_context import (
    EnhancedContextManager,
    MemoryEntry,
    MemoryType,
    MemoryPriority,
    ConversationThread,
)


@pytest.fixture
def temp_storage():
    """Create temporary storage directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def context_manager(temp_storage):
    """Create context manager instance"""
    return EnhancedContextManager(
        storage_dir=temp_storage,
        max_context_tokens=4096,
        consolidation_threshold=5
    )


@pytest.mark.asyncio
async def test_add_memory(context_manager):
    """Test adding a memory"""
    memory = await context_manager.store_memory(
        user_id="test_user",
        session_id="session_1",
        content="Python is a programming language",
        memory_type=MemoryType.FACT,
        priority=MemoryPriority.HIGH,
        tags={"programming", "python"}
    )

    assert memory.user_id == "test_user"
    assert memory.content == "Python is a programming language"
    assert memory.memory_type == MemoryType.FACT
    assert memory.priority == MemoryPriority.HIGH
    assert "programming" in memory.tags


@pytest.mark.asyncio
async def test_search_memories(context_manager):
    """Test semantic search of memories"""
    # Add several memories
    await context_manager.store_memory(
        user_id="test_user",
        session_id="session_1",
        content="Python is a programming language used for data science",
        memory_type=MemoryType.FACT,
        priority=MemoryPriority.HIGH,
        tags={"programming", "python", "data"}
    )

    await context_manager.store_memory(
        user_id="test_user",
        session_id="session_1",
        content="JavaScript is used for web development",
        memory_type=MemoryType.FACT,
        priority=MemoryPriority.MEDIUM,
        tags={"programming", "javascript", "web"}
    )

    await context_manager.store_memory(
        user_id="test_user",
        session_id="session_1",
        content="I prefer dark mode in my editor",
        memory_type=MemoryType.PREFERENCE,
        priority=MemoryPriority.LOW,
        tags={"preferences", "editor"}
    )

    # Search for programming-related memories
    results = await context_manager.search_memories(
        user_id="test_user",
        query="programming languages",
        memory_types=[MemoryType.FACT],
        limit=10
    )

    assert len(results) >= 2
    # Should return Python and JavaScript memories


@pytest.mark.asyncio
async def test_memory_consolidation(context_manager):
    """Test memory consolidation"""
    # Add enough memories to trigger consolidation
    for i in range(6):
        await context_manager.store_memory(
            user_id="test_user",
            session_id="session_1",
            content=f"Memory number {i}",
            memory_type=MemoryType.CONVERSATION,
            priority=MemoryPriority.MEDIUM,
            tags={"test"}
        )

    # Trigger consolidation
    await context_manager.consolidate_memories("test_user")

    # Check that memories were consolidated
    user_memories = context_manager.memories.get("test_user", [])
    consolidated_count = sum(1 for m in user_memories if m.consolidated)

    assert consolidated_count > 0


@pytest.mark.asyncio
async def test_context_window_optimization(context_manager):
    """Test context window optimization"""
    # Add many memories
    for i in range(20):
        await context_manager.store_memory(
            user_id="test_user",
            session_id="session_1",
            content=f"This is memory number {i} with some content to use tokens",
            memory_type=MemoryType.CONVERSATION,
            priority=MemoryPriority.MEDIUM if i % 2 == 0 else MemoryPriority.LOW,
            tags={"test"}
        )

    # Get optimized context window
    window = await context_manager.create_context_window(
        user_id="test_user",
        session_id="session_1",
        max_tokens=1000
    )

    assert window is not None
    assert len(window.memory_ids) > 0
    assert window.total_tokens <= 1000


@pytest.mark.asyncio
async def test_memory_persistence(temp_storage):
    """Test that memories persist across manager instances"""
    # Create first manager and add memory
    manager1 = EnhancedContextManager(storage_dir=temp_storage)
    await manager1.store_memory(
        user_id="test_user",
        session_id="session_1",
        content="Persistent memory",
        memory_type=MemoryType.FACT,
        priority=MemoryPriority.HIGH,
        tags={"test"}
    )

    # Create second manager (should load existing memories)
    manager2 = EnhancedContextManager(storage_dir=temp_storage)

    user_memories = manager2.memories.get("test_user", [])
    assert len(user_memories) == 1
    assert user_memories[0].content == "Persistent memory"


@pytest.mark.asyncio
async def test_conversation_thread(context_manager):
    """Test conversation threading"""
    thread_id = "thread_1"

    # Add memories to thread
    await context_manager.store_memory(
        user_id="test_user",
        session_id="session_1",
        content="What is Python?",
        memory_type=MemoryType.CONVERSATION,
        priority=MemoryPriority.MEDIUM,
        tags={"thread:" + thread_id}
    )

    await context_manager.store_memory(
        user_id="test_user",
        session_id="session_1",
        content="Python is a programming language",
        memory_type=MemoryType.CONVERSATION,
        priority=MemoryPriority.MEDIUM,
        tags={"thread:" + thread_id}
    )

    # Search within thread
    results = await context_manager.search_memories(
        user_id="test_user",
        query="Python",
        tags={"thread:" + thread_id},
        limit=10
    )

    assert len(results) == 2


@pytest.mark.asyncio
async def test_memory_expiry(context_manager):
    """Test automatic memory expiry"""
    # Add old memory
    old_memory = MemoryEntry(
        memory_id="old_1",
        timestamp=datetime.now() - timedelta(days=100),
        user_id="test_user",
        session_id="session_1",
        content="Old memory",
        memory_type=MemoryType.CONVERSATION,
        priority=MemoryPriority.LOW,
        tags=set(),
        access_count=0,
        last_accessed=datetime.now() - timedelta(days=100),
        relevance_score=1.0,
        consolidated=False
    )

    context_manager.memories["test_user"] = [old_memory]

    # Prune expired memories
    await context_manager.prune_expired_memories("test_user")

    # Old memory should be removed (default retention is 90 days)
    user_memories = context_manager.memories.get("test_user", [])
    assert len(user_memories) == 0


@pytest.mark.asyncio
async def test_memory_update(context_manager):
    """Test updating existing memory"""
    # Add memory
    memory = await context_manager.store_memory(
        user_id="test_user",
        session_id="session_1",
        content="Original content",
        memory_type=MemoryType.FACT,
        priority=MemoryPriority.MEDIUM,
        tags={"test"}
    )

    memory_id = memory.memory_id

    # Update memory
    updated = await context_manager.update_memory(
        user_id="test_user",
        memory_id=memory_id,
        content="Updated content",
        priority=MemoryPriority.HIGH
    )

    assert updated is not None
    assert updated.content == "Updated content"
    assert updated.priority == MemoryPriority.HIGH


def test_memory_types():
    """Test memory type enum"""
    assert MemoryType.CONVERSATION.value == "conversation"
    assert MemoryType.FACT.value == "fact"
    assert MemoryType.PREFERENCE.value == "preference"
    assert MemoryType.SKILL.value == "skill"
    assert MemoryType.GOAL.value == "goal"
    assert MemoryType.CONTEXT.value == "context"


def test_memory_priorities():
    """Test memory priority enum"""
    assert MemoryPriority.CRITICAL.value == "critical"
    assert MemoryPriority.HIGH.value == "high"
    assert MemoryPriority.MEDIUM.value == "medium"
    assert MemoryPriority.LOW.value == "low"
    assert MemoryPriority.EPHEMERAL.value == "ephemeral"

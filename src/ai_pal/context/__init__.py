"""
Context Module - Phase 3

Enhanced context management for maintaining conversation coherence:
- Long-term memory with semantic search
- Context window optimization
- Memory consolidation
- Conversation threading
"""

from .enhanced_context import (
    EnhancedContextManager,
    MemoryEntry,
    MemoryType,
    MemoryPriority,
    ConversationThread,
    ContextWindow,
)

__all__ = [
    "EnhancedContextManager",
    "MemoryEntry",
    "MemoryType",
    "MemoryPriority",
    "ConversationThread",
    "ContextWindow",
]

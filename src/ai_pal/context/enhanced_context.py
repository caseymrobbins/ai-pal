"""
Enhanced Context Management System

Provides sophisticated context handling for maintaining conversation coherence
and user agency:

- Long-term memory with semantic search
- Context window management
- Conversation threading
- Memory consolidation
- Relevance scoring
- Privacy-preserving storage

Part of Phase 3: Enhanced Context, Privacy, Multi-Model Orchestration
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import hashlib
from collections import defaultdict
import tiktoken

from loguru import logger


class MemoryType(Enum):
    """Types of memory entries"""
    CONVERSATION = "conversation"  # Conversational exchange
    FACT = "fact"  # Factual information
    PREFERENCE = "preference"  # User preference
    SKILL = "skill"  # User skill/capability
    GOAL = "goal"  # User goal/objective
    CONTEXT = "context"  # General context


class MemoryPriority(Enum):
    """Memory priority levels"""
    CRITICAL = "critical"  # Must retain
    HIGH = "high"  # Important
    MEDIUM = "medium"  # Standard
    LOW = "low"  # Can be pruned
    EPHEMERAL = "ephemeral"  # Delete after session


@dataclass
class MemoryEntry:
    """Single memory entry"""
    memory_id: str
    timestamp: datetime
    user_id: str
    session_id: str

    # Content
    content: str
    memory_type: MemoryType
    priority: MemoryPriority

    # Metadata
    tags: Set[str] = field(default_factory=set)
    embedding: Optional[List[float]] = None  # Semantic embedding

    # Relationships
    related_memories: Set[str] = field(default_factory=set)
    parent_memory: Optional[str] = None

    # Relevance tracking
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    relevance_score: float = 1.0  # Decays over time

    # Privacy
    contains_pii: bool = False
    encrypted: bool = False

    # Lifecycle
    expires_at: Optional[datetime] = None
    consolidated: bool = False

    metadata: Dict = field(default_factory=dict)


@dataclass
class ConversationThread:
    """Thread of related conversation turns"""
    thread_id: str
    user_id: str
    started_at: datetime
    updated_at: datetime

    # Thread content
    title: Optional[str] = None
    summary: Optional[str] = None
    memory_ids: List[str] = field(default_factory=list)

    # Thread metadata
    tags: Set[str] = field(default_factory=set)
    goals_achieved: List[str] = field(default_factory=list)
    skills_developed: List[str] = field(default_factory=list)

    # Status
    active: bool = True
    archived: bool = False


@dataclass
class ContextWindow:
    """Active context window for current conversation"""
    window_id: str
    user_id: str
    session_id: str
    created_at: datetime

    # Window content
    memory_ids: List[str] = field(default_factory=list)
    total_tokens: int = 0
    max_tokens: int = 4096

    # Optimization
    pruned_memories: List[str] = field(default_factory=list)
    consolidated_summaries: List[str] = field(default_factory=list)


class EnhancedContextManager:
    """
    Enhanced Context Management System

    Manages conversation context with:
    - Long-term memory storage with semantic search
    - Context window optimization
    - Memory consolidation and pruning
    - Conversation threading
    - Privacy-preserving storage
    """

    def __init__(
        self,
        storage_dir: Path,
        max_context_tokens: int = 4096,
        memory_decay_days: int = 90,
        consolidation_threshold: int = 50,  # Consolidate after N memories
        enable_semantic_search: bool = True
    ):
        """
        Initialize Enhanced Context Manager

        Args:
            storage_dir: Directory for memory storage
            max_context_tokens: Maximum tokens in context window
            memory_decay_days: Days before memory relevance decays
            consolidation_threshold: Number of memories before consolidation
            enable_semantic_search: Enable semantic similarity search
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.max_context_tokens = max_context_tokens
        self.memory_decay_days = memory_decay_days
        self.consolidation_threshold = consolidation_threshold
        self.enable_semantic_search = enable_semantic_search

        # In-memory storage
        self.memories: Dict[str, MemoryEntry] = {}
        self.threads: Dict[str, ConversationThread] = {}
        self.context_windows: Dict[str, ContextWindow] = {}

        # Indexes
        self.user_memories: Dict[str, Set[str]] = defaultdict(set)
        self.session_memories: Dict[str, Set[str]] = defaultdict(set)
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        self.type_index: Dict[MemoryType, Set[str]] = defaultdict(set)

        # Token counting (Phase 3.3 enhancement)
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
            logger.info("Initialized tiktoken for accurate token counting")
        except Exception as e:
            logger.warning(f"Failed to initialize tiktoken: {e}, using fallback")
            self.tokenizer = None

        # Load existing data
        self._load_memories()
        self._load_threads()

        logger.info(
            f"Enhanced Context Manager initialized with storage at {storage_dir}, "
            f"max context: {max_context_tokens} tokens"
        )

    def _load_memories(self) -> None:
        """Load existing memories from storage"""
        memories_dir = self.storage_dir / "memories"
        if not memories_dir.exists():
            return

        for memory_file in memories_dir.glob("*.json"):
            try:
                with open(memory_file, 'r') as f:
                    data = json.load(f)
                    memory = MemoryEntry(
                        memory_id=data["memory_id"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        user_id=data["user_id"],
                        session_id=data["session_id"],
                        content=data["content"],
                        memory_type=MemoryType(data["memory_type"]),
                        priority=MemoryPriority(data["priority"]),
                        tags=set(data.get("tags", [])),
                        embedding=data.get("embedding"),
                        related_memories=set(data.get("related_memories", [])),
                        parent_memory=data.get("parent_memory"),
                        access_count=data.get("access_count", 0),
                        last_accessed=datetime.fromisoformat(data["last_accessed"])
                        if data.get("last_accessed") else None,
                        relevance_score=data.get("relevance_score", 1.0),
                        contains_pii=data.get("contains_pii", False),
                        encrypted=data.get("encrypted", False),
                        expires_at=datetime.fromisoformat(data["expires_at"])
                        if data.get("expires_at") else None,
                        consolidated=data.get("consolidated", False),
                        metadata=data.get("metadata", {})
                    )

                    self.memories[memory.memory_id] = memory
                    self._index_memory(memory)

            except Exception as e:
                logger.error(f"Failed to load memory {memory_file}: {e}")

    def _load_threads(self) -> None:
        """Load existing conversation threads"""
        threads_dir = self.storage_dir / "threads"
        if not threads_dir.exists():
            return

        for thread_file in threads_dir.glob("*.json"):
            try:
                with open(thread_file, 'r') as f:
                    data = json.load(f)
                    thread = ConversationThread(
                        thread_id=data["thread_id"],
                        user_id=data["user_id"],
                        started_at=datetime.fromisoformat(data["started_at"]),
                        updated_at=datetime.fromisoformat(data["updated_at"]),
                        title=data.get("title"),
                        summary=data.get("summary"),
                        memory_ids=data.get("memory_ids", []),
                        tags=set(data.get("tags", [])),
                        goals_achieved=data.get("goals_achieved", []),
                        skills_developed=data.get("skills_developed", []),
                        active=data.get("active", True),
                        archived=data.get("archived", False)
                    )

                    self.threads[thread.thread_id] = thread

            except Exception as e:
                logger.error(f"Failed to load thread {thread_file}: {e}")

    def _index_memory(self, memory: MemoryEntry) -> None:
        """Index memory for fast retrieval"""
        self.user_memories[memory.user_id].add(memory.memory_id)
        self.session_memories[memory.session_id].add(memory.memory_id)
        self.type_index[memory.memory_type].add(memory.memory_id)

        for tag in memory.tags:
            self.tag_index[tag].add(memory.memory_id)

    async def store_memory(
        self,
        user_id: str,
        session_id: str,
        content: str,
        memory_type: MemoryType,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        tags: Optional[Set[str]] = None,
        parent_memory: Optional[str] = None,
        expires_in_days: Optional[int] = None
    ) -> MemoryEntry:
        """
        Store a new memory entry

        Args:
            user_id: User ID
            session_id: Session ID
            content: Memory content
            memory_type: Type of memory
            priority: Priority level
            tags: Optional tags
            parent_memory: Optional parent memory ID
            expires_in_days: Optional expiration in days

        Returns:
            Created memory entry
        """
        memory_id = self._generate_memory_id(user_id, content)

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        elif priority == MemoryPriority.EPHEMERAL:
            expires_at = datetime.now() + timedelta(hours=24)

        # Create memory
        memory = MemoryEntry(
            memory_id=memory_id,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            content=content,
            memory_type=memory_type,
            priority=priority,
            tags=tags or set(),
            parent_memory=parent_memory,
            expires_at=expires_at
        )

        # Generate embedding if semantic search enabled
        if self.enable_semantic_search:
            memory.embedding = await self._generate_embedding(content)

        # Store in memory
        self.memories[memory_id] = memory
        self._index_memory(memory)

        # Persist to disk
        await self._persist_memory(memory)

        logger.debug(f"Stored {memory_type.value} memory for user {user_id}")

        # Check for consolidation
        await self._check_consolidation(user_id)

        return memory

    def _generate_memory_id(self, user_id: str, content: str) -> str:
        """Generate unique memory ID"""
        hash_input = f"{user_id}_{content}_{datetime.now().timestamp()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate semantic embedding for text

        In production, this would use a sentence transformer model
        For now, returns placeholder
        """
        # TODO: Integrate with actual embedding model
        # e.g., sentence-transformers, OpenAI embeddings, etc.

        # Placeholder: simple hash-based pseudo-embedding
        hash_val = hashlib.sha256(text.encode()).hexdigest()
        embedding = [int(hash_val[i:i+2], 16) / 255.0 for i in range(0, 32, 2)]
        return embedding

    async def _persist_memory(self, memory: MemoryEntry) -> None:
        """Persist memory to disk"""
        memories_dir = self.storage_dir / "memories"
        memories_dir.mkdir(exist_ok=True)

        filepath = memories_dir / f"{memory.memory_id}.json"

        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "memory_id": memory.memory_id,
                    "timestamp": memory.timestamp.isoformat(),
                    "user_id": memory.user_id,
                    "session_id": memory.session_id,
                    "content": memory.content,
                    "memory_type": memory.memory_type.value,
                    "priority": memory.priority.value,
                    "tags": list(memory.tags),
                    "embedding": memory.embedding,
                    "related_memories": list(memory.related_memories),
                    "parent_memory": memory.parent_memory,
                    "access_count": memory.access_count,
                    "last_accessed": memory.last_accessed.isoformat()
                    if memory.last_accessed else None,
                    "relevance_score": memory.relevance_score,
                    "contains_pii": memory.contains_pii,
                    "encrypted": memory.encrypted,
                    "expires_at": memory.expires_at.isoformat()
                    if memory.expires_at else None,
                    "consolidated": memory.consolidated,
                    "metadata": memory.metadata
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist memory: {e}")

    async def search_memories(
        self,
        user_id: str,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        tags: Optional[Set[str]] = None,
        limit: int = 10,
        min_relevance: float = 0.5
    ) -> List[MemoryEntry]:
        """
        Search memories using semantic similarity

        Args:
            user_id: User ID
            query: Search query
            memory_types: Filter by memory types
            tags: Filter by tags
            limit: Maximum results
            min_relevance: Minimum relevance score

        Returns:
            List of matching memories, sorted by relevance
        """
        # Get user's memories
        if user_id not in self.user_memories:
            return []

        candidate_memories = [
            self.memories[mid] for mid in self.user_memories[user_id]
            if mid in self.memories
        ]

        # Filter by type
        if memory_types:
            candidate_memories = [
                m for m in candidate_memories
                if m.memory_type in memory_types
            ]

        # Filter by tags
        if tags:
            candidate_memories = [
                m for m in candidate_memories
                if m.tags.intersection(tags)
            ]

        # Filter expired memories
        now = datetime.now()
        candidate_memories = [
            m for m in candidate_memories
            if m.expires_at is None or m.expires_at > now
        ]

        # Semantic search if enabled
        if self.enable_semantic_search:
            query_embedding = await self._generate_embedding(query)

            # Calculate similarities
            scored_memories = []
            for memory in candidate_memories:
                if memory.embedding:
                    similarity = self._cosine_similarity(
                        query_embedding,
                        memory.embedding
                    )

                    # Adjust for relevance decay
                    adjusted_score = similarity * memory.relevance_score

                    if adjusted_score >= min_relevance:
                        scored_memories.append((memory, adjusted_score))

            # Sort by score
            scored_memories.sort(key=lambda x: x[1], reverse=True)
            results = [m for m, _ in scored_memories[:limit]]
        else:
            # Fallback: simple text matching
            results = [
                m for m in candidate_memories
                if query.lower() in m.content.lower()
            ][:limit]

        # Update access statistics
        for memory in results:
            memory.access_count += 1
            memory.last_accessed = datetime.now()
            await self._persist_memory(memory)

        return results

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    async def create_context_window(
        self,
        user_id: str,
        session_id: str,
        relevant_memory_ids: Optional[List[str]] = None
    ) -> ContextWindow:
        """
        Create optimized context window for current conversation

        Args:
            user_id: User ID
            session_id: Session ID
            relevant_memory_ids: Optional pre-selected memory IDs

        Returns:
            Created context window
        """
        window_id = f"{session_id}_{datetime.now().timestamp()}"

        window = ContextWindow(
            window_id=window_id,
            user_id=user_id,
            session_id=session_id,
            created_at=datetime.now(),
            max_tokens=self.max_context_tokens
        )

        if relevant_memory_ids:
            # Add specified memories
            for memory_id in relevant_memory_ids:
                if memory_id in self.memories:
                    await self._add_to_context_window(window, memory_id)
        else:
            # Auto-select most relevant memories
            await self._populate_context_window(window)

        self.context_windows[window_id] = window

        logger.info(
            f"Created context window with {len(window.memory_ids)} memories, "
            f"{window.total_tokens} tokens"
        )

        return window

    def _count_tokens(self, text: str) -> int:
        """
        Accurately count tokens in text (Phase 3.3 enhancement)

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Token counting failed: {e}, using fallback")

        # Fallback: crude estimation
        return int(len(text.split()) * 1.3)

    def _calculate_relevance_score(
        self,
        memory: MemoryEntry,
        current_time: Optional[datetime] = None
    ) -> float:
        """
        Calculate comprehensive relevance score (Phase 3.3 enhancement)

        Factors:
        - Priority (40%): Critical memories always score high
        - Recency (30%): Recent memories more relevant
        - Access patterns (20%): Frequently accessed memories more relevant
        - Time decay (10%): Relevance decays over time

        Args:
            memory: Memory to score
            current_time: Current time (defaults to now)

        Returns:
            Relevance score (0-1)
        """
        if current_time is None:
            current_time = datetime.now()

        score = 0.0

        # Priority component (40%)
        priority_scores = {
            MemoryPriority.CRITICAL: 1.0,
            MemoryPriority.HIGH: 0.8,
            MemoryPriority.MEDIUM: 0.5,
            MemoryPriority.LOW: 0.3,
            MemoryPriority.EPHEMERAL: 0.1
        }
        score += priority_scores.get(memory.priority, 0.5) * 0.4

        # Recency component (30%)
        time_diff = (current_time - memory.timestamp).total_seconds()
        max_age = self.memory_decay_days * 86400  # days to seconds
        recency_score = max(0, 1 - (time_diff / max_age))
        score += recency_score * 0.3

        # Access patterns component (20%)
        # More accesses = more relevant, with diminishing returns
        access_score = min(1.0, memory.access_count / 10)
        score += access_score * 0.2

        # Time decay component (10%)
        if memory.last_accessed:
            time_since_access = (current_time - memory.last_accessed).total_seconds()
            decay_score = max(0, 1 - (time_since_access / max_age))
            score += decay_score * 0.1
        else:
            score += 0.05  # Half score if never accessed

        return min(1.0, score)

    async def _prune_context_window(
        self,
        window: ContextWindow,
        tokens_needed: int
    ) -> int:
        """
        Intelligently prune context window to make space (Phase 3.3 enhancement)

        Args:
            window: Context window to prune
            tokens_needed: Number of tokens needed

        Returns:
            Number of tokens freed
        """
        if not window.memory_ids:
            return 0

        # Calculate relevance scores for all memories in window
        memory_scores = []
        for memory_id in window.memory_ids:
            if memory_id not in self.memories:
                continue

            memory = self.memories[memory_id]
            relevance = self._calculate_relevance_score(memory)
            tokens = self._count_tokens(memory.content)

            memory_scores.append((memory_id, relevance, tokens))

        # Sort by relevance (lowest first)
        memory_scores.sort(key=lambda x: x[1])

        # Remove least relevant memories until enough space
        tokens_freed = 0
        removed_ids = []

        for memory_id, relevance, tokens in memory_scores:
            if tokens_freed >= tokens_needed:
                break

            # Don't remove CRITICAL memories
            memory = self.memories[memory_id]
            if memory.priority == MemoryPriority.CRITICAL:
                continue

            removed_ids.append(memory_id)
            tokens_freed += tokens

            # Track pruned memory
            window.pruned_memories.append(memory_id)

            logger.debug(
                f"Pruned memory {memory_id} (relevance: {relevance:.2f}, "
                f"tokens: {tokens}) from window"
            )

        # Remove from window
        for memory_id in removed_ids:
            window.memory_ids.remove(memory_id)
            window.total_tokens -= self._count_tokens(self.memories[memory_id].content)

        logger.info(f"Pruned {len(removed_ids)} memories, freed {tokens_freed} tokens")

        return tokens_freed

    async def _add_to_context_window(
        self,
        window: ContextWindow,
        memory_id: str
    ) -> bool:
        """Add memory to context window if space available"""
        if memory_id not in self.memories:
            return False

        memory = self.memories[memory_id]

        # Accurate token counting (Phase 3.3 enhancement)
        memory_tokens = self._count_tokens(memory.content)

        # Try to add if space available
        if window.total_tokens + memory_tokens <= window.max_tokens:
            window.memory_ids.append(memory_id)
            window.total_tokens += memory_tokens

            # Update access tracking
            memory.access_count += 1
            memory.last_accessed = datetime.now()

            return True

        # No space - try smart pruning (Phase 3.3 enhancement)
        tokens_needed = memory_tokens - (window.max_tokens - window.total_tokens)
        tokens_freed = await self._prune_context_window(window, tokens_needed)

        if tokens_freed >= tokens_needed:
            # Successfully made space, add memory
            window.memory_ids.append(memory_id)
            window.total_tokens += memory_tokens

            # Update access tracking
            memory.access_count += 1
            memory.last_accessed = datetime.now()

            logger.info(
                f"Added memory {memory_id} after pruning "
                f"({tokens_freed} tokens freed)"
            )
            return True

        return False

    async def _populate_context_window(self, window: ContextWindow) -> None:
        """
        Auto-populate context window with relevant memories (Phase 3.3 enhanced)

        Uses comprehensive relevance scoring instead of simple priority+recency
        """
        # Get session memories
        session_memory_ids = list(self.session_memories[window.session_id])

        # Calculate relevance score for each memory
        memory_scores = []
        for mid in session_memory_ids:
            if mid not in self.memories:
                continue

            memory = self.memories[mid]
            relevance = self._calculate_relevance_score(memory)
            memory_scores.append((memory, relevance))

        # Sort by relevance (highest first)
        sorted_memories = sorted(
            memory_scores,
            key=lambda x: x[1],
            reverse=True
        )

        # Add memories until window is full
        for memory, relevance in sorted_memories:
            success = await self._add_to_context_window(window, memory.memory_id)
            if not success:
                # Window full even after pruning
                logger.debug(f"Context window full, added {len(window.memory_ids)} memories")
                break

        logger.info(
            f"Populated context window with {len(window.memory_ids)} memories, "
            f"{window.total_tokens}/{window.max_tokens} tokens"
        )

    def _priority_score(self, priority: MemoryPriority) -> int:
        """Convert priority to numeric score"""
        scores = {
            MemoryPriority.CRITICAL: 4,
            MemoryPriority.HIGH: 3,
            MemoryPriority.MEDIUM: 2,
            MemoryPriority.LOW: 1,
            MemoryPriority.EPHEMERAL: 0
        }
        return scores.get(priority, 0)

    async def _check_consolidation(self, user_id: str) -> None:
        """Check if memory consolidation is needed"""
        if user_id not in self.user_memories:
            return

        unconsolidated = [
            mid for mid in self.user_memories[user_id]
            if mid in self.memories and not self.memories[mid].consolidated
        ]

        if len(unconsolidated) >= self.consolidation_threshold:
            logger.info(f"Triggering memory consolidation for user {user_id}")
            await self._consolidate_memories(user_id, unconsolidated)

    async def _consolidate_memories(
        self,
        user_id: str,
        memory_ids: List[str]
    ) -> None:
        """
        Consolidate multiple memories into summaries

        In production, this would use LLM to generate summaries
        """
        logger.info(f"Consolidating {len(memory_ids)} memories for user {user_id}")

        # Group by thread/topic
        # Generate summaries
        # Mark originals as consolidated
        # Store consolidated summaries

        # Placeholder implementation
        for memory_id in memory_ids:
            if memory_id in self.memories:
                self.memories[memory_id].consolidated = True
                await self._persist_memory(self.memories[memory_id])

    async def decay_relevance(self) -> int:
        """
        Decay relevance scores based on age and access patterns

        Returns:
            Number of memories decayed
        """
        now = datetime.now()
        decay_cutoff = now - timedelta(days=self.memory_decay_days)

        decayed_count = 0

        for memory in self.memories.values():
            # Skip critical memories
            if memory.priority == MemoryPriority.CRITICAL:
                continue

            # Decay based on age
            if memory.timestamp < decay_cutoff:
                days_old = (now - memory.timestamp).days
                decay_factor = max(0.1, 1.0 - (days_old / (self.memory_decay_days * 2)))

                # Adjust for access patterns
                if memory.access_count > 0:
                    access_boost = min(0.3, memory.access_count * 0.05)
                    decay_factor += access_boost

                if memory.relevance_score != decay_factor:
                    memory.relevance_score = decay_factor
                    await self._persist_memory(memory)
                    decayed_count += 1

        logger.info(f"Decayed relevance for {decayed_count} memories")
        return decayed_count

    async def prune_expired_memories(self) -> int:
        """
        Remove expired memories

        Returns:
            Number of memories pruned
        """
        now = datetime.now()
        to_prune = []

        for memory_id, memory in self.memories.items():
            if memory.expires_at and memory.expires_at <= now:
                to_prune.append(memory_id)

        # Remove from storage
        for memory_id in to_prune:
            memory = self.memories[memory_id]

            # Remove from indexes
            self.user_memories[memory.user_id].discard(memory_id)
            self.session_memories[memory.session_id].discard(memory_id)
            self.type_index[memory.memory_type].discard(memory_id)

            for tag in memory.tags:
                self.tag_index[tag].discard(memory_id)

            # Remove file
            filepath = self.storage_dir / "memories" / f"{memory_id}.json"
            if filepath.exists():
                filepath.unlink()

            # Remove from memory
            del self.memories[memory_id]

        logger.info(f"Pruned {len(to_prune)} expired memories")
        return len(to_prune)

    def get_user_stats(self, user_id: str) -> Dict:
        """Get memory statistics for user"""
        if user_id not in self.user_memories:
            return {
                "user_id": user_id,
                "total_memories": 0
            }

        user_memory_list = [
            self.memories[mid]
            for mid in self.user_memories[user_id]
            if mid in self.memories
        ]

        by_type = defaultdict(int)
        by_priority = defaultdict(int)

        for memory in user_memory_list:
            by_type[memory.memory_type.value] += 1
            by_priority[memory.priority.value] += 1

        return {
            "user_id": user_id,
            "total_memories": len(user_memory_list),
            "by_type": dict(by_type),
            "by_priority": dict(by_priority),
            "average_relevance": sum(m.relevance_score for m in user_memory_list) / len(user_memory_list)
            if user_memory_list else 0.0,
            "total_access_count": sum(m.access_count for m in user_memory_list)
        }

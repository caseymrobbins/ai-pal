"""
ARI (Autonomy Retention Index) Engine

Multi-layered, non-invasive measurement system for detecting AI-induced skill atrophy.

Implements three measurement methods:
1. Passive Lexical Analysis - Continuous background measurement
2. Socratic Co-pilot - Embedded interaction measurement
3. Deep Dive Mode - Opt-in baseline establishment

Part of the Agency-Centric AI framework's monitoring capabilities.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import re
from collections import Counter
import math

from loguru import logger


# ============================================================================
# ENUMS & DATA STRUCTURES
# ============================================================================

class ARISignalLevel(Enum):
    """ARI signal levels"""
    HIGH = "high"          # User demonstrating strong capability
    MEDIUM = "medium"      # User demonstrating moderate capability
    LOW = "low"           # User showing reduced capability
    CRITICAL = "critical"  # Severe capability loss detected


class UCCResponseType(Enum):
    """Types of responses to Unassisted Capability Checkpoints"""
    ACCURATE = "accurate"           # User provided accurate answer
    PARTIAL = "partial"             # User provided partial answer
    UNCERTAIN = "uncertain"         # User expressed uncertainty
    DELEGATED = "delegated"         # User delegated back to AI ("just guess", "you do it")
    NO_RESPONSE = "no_response"     # User didn't respond


@dataclass
class LexicalMetrics:
    """Metrics from passive lexical analysis"""
    timestamp: datetime

    # Lexical richness
    lexical_diversity: float        # Type-token ratio
    vocabulary_richness: float      # Unique word count / total words

    # Syntactic complexity
    average_sentence_length: float  # Words per sentence
    syntactic_complexity_score: float  # Based on parse tree depth

    # Domain expertise
    domain_term_density: float      # Percentage of domain-specific terms
    technical_vocabulary_count: int

    # Text characteristics
    total_words: int
    unique_words: int
    sentence_count: int

    # Context
    text_sample_id: str
    text_type: str  # "email", "code", "document", etc.


@dataclass
class UnassistedCapabilityCheckpoint:
    """A checkpoint where user capability is measured"""
    ucc_id: str
    task_description: str
    question: str  # The Socratic question asked

    # Expected capability
    expected_knowledge_level: str  # "basic", "intermediate", "advanced"
    domain: str  # e.g., "programming", "writing", "analysis"

    # User response
    response_type: UCCResponseType
    response_text: Optional[str] = None
    response_timestamp: Optional[datetime] = None

    # Assessment
    capability_demonstrated: float = 0.0  # 0-1 score
    ari_signal: ARISignalLevel = ARISignalLevel.MEDIUM

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ARIBaseline:
    """User's baseline capability profile from Deep Dive mode"""
    user_id: str
    domain: str

    # Knowledge baseline
    knowledge_topics: List[str] = field(default_factory=list)
    demonstrated_skills: Dict[str, float] = field(default_factory=dict)  # skill -> proficiency

    # Synthesis capabilities
    synthesis_quality_score: float = 0.0  # 0-1
    reasoning_depth_score: float = 0.0    # 0-1

    # Lexical baseline
    baseline_lexical_diversity: float = 0.0
    baseline_syntactic_complexity: float = 0.0

    # Metadata
    established_at: datetime = field(default_factory=datetime.now)
    sample_count: int = 0  # Number of interactions used to establish baseline


@dataclass
class ARIScore:
    """Comprehensive ARI score for a user"""
    user_id: str
    timestamp: datetime

    # Overall ARI (0-1, higher is better)
    overall_ari: float
    signal_level: ARISignalLevel

    # Component scores
    lexical_ari: float          # From passive lexical analysis
    interaction_ari: float      # From Socratic co-pilot
    baseline_deviation: float   # Deviation from deep dive baseline

    # Trend indicators
    trend_direction: str        # "improving", "stable", "declining"
    days_in_trend: int

    # Alerts
    alerts: List[str] = field(default_factory=list)

    # Confidence
    confidence: float = 0.0     # How confident in this score (0-1)


# ============================================================================
# PASSIVE LEXICAL ANALYZER
# ============================================================================

class PassiveLexicalAnalyzer:
    """
    Continuous background measurement of user's written output.

    Analyzes lexical richness, syntactic complexity, and domain expertise
    to detect skill atrophy through linguistic regression.

    **Privacy:** All analysis happens on-device. Raw text is not stored,
    only aggregate metrics.
    """

    def __init__(
        self,
        storage_dir: Path,
        lookback_window_days: int = 30,
        min_samples_for_baseline: int = 10
    ):
        """
        Initialize passive lexical analyzer

        Args:
            storage_dir: Directory for storing metric history
            lookback_window_days: How far back to analyze for trends
            min_samples_for_baseline: Minimum samples needed for baseline
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.lookback_window_days = lookback_window_days
        self.min_samples_for_baseline = min_samples_for_baseline

        # In-memory cache of metrics
        self.metrics_history: Dict[str, List[LexicalMetrics]] = {}

        # Load existing metrics
        self._load_metrics()

        logger.info(f"PassiveLexicalAnalyzer initialized with {lookback_window_days}-day window")

    def _load_metrics(self) -> None:
        """Load existing metrics from storage"""
        metric_files = list(self.storage_dir.glob("lexical_*.json"))
        logger.info(f"Loading {len(metric_files)} lexical metric files")

        for metric_file in metric_files:
            try:
                with open(metric_file, 'r') as f:
                    data = json.load(f)
                    user_id = data.get("user_id")
                    if user_id:
                        if user_id not in self.metrics_history:
                            self.metrics_history[user_id] = []

                        metric = LexicalMetrics(
                            timestamp=datetime.fromisoformat(data["timestamp"]),
                            lexical_diversity=data["lexical_diversity"],
                            vocabulary_richness=data["vocabulary_richness"],
                            average_sentence_length=data["average_sentence_length"],
                            syntactic_complexity_score=data["syntactic_complexity_score"],
                            domain_term_density=data["domain_term_density"],
                            technical_vocabulary_count=data["technical_vocabulary_count"],
                            total_words=data["total_words"],
                            unique_words=data["unique_words"],
                            sentence_count=data["sentence_count"],
                            text_sample_id=data["text_sample_id"],
                            text_type=data["text_type"]
                        )
                        self.metrics_history[user_id].append(metric)
            except Exception as e:
                logger.error(f"Failed to load metric {metric_file}: {e}")

    async def analyze_text(
        self,
        user_id: str,
        text: str,
        text_type: str = "document",
        text_sample_id: Optional[str] = None
    ) -> LexicalMetrics:
        """
        Analyze a text sample and extract lexical metrics.

        **Privacy:** Raw text is analyzed locally and not stored.
        Only aggregate metrics are retained.

        Args:
            user_id: User who wrote the text
            text: The text to analyze
            text_type: Type of text (email, code, document, etc.)
            text_sample_id: Optional identifier for the sample

        Returns:
            LexicalMetrics object with extracted metrics
        """
        logger.debug(f"Analyzing text for user {user_id}, type={text_type}, length={len(text)}")

        # Calculate metrics
        metrics = LexicalMetrics(
            timestamp=datetime.now(),
            lexical_diversity=self._calculate_lexical_diversity(text),
            vocabulary_richness=self._calculate_vocabulary_richness(text),
            average_sentence_length=self._calculate_avg_sentence_length(text),
            syntactic_complexity_score=self._calculate_syntactic_complexity(text),
            domain_term_density=self._calculate_domain_term_density(text),
            technical_vocabulary_count=self._count_technical_vocabulary(text),
            total_words=len(self._tokenize_words(text)),
            unique_words=len(set(self._tokenize_words(text))),
            sentence_count=len(self._split_sentences(text)),
            text_sample_id=text_sample_id or f"sample_{datetime.now().timestamp()}",
            text_type=text_type
        )

        # Store metrics
        if user_id not in self.metrics_history:
            self.metrics_history[user_id] = []
        self.metrics_history[user_id].append(metrics)

        # Persist to disk
        await self._persist_metric(user_id, metrics)

        logger.info(
            f"Analyzed text for {user_id}: "
            f"diversity={metrics.lexical_diversity:.3f}, "
            f"complexity={metrics.syntactic_complexity_score:.3f}"
        )

        return metrics

    def _tokenize_words(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Simple tokenization (lowercase, alphanumeric)
        words = re.findall(r'\b[a-z]+\b', text.lower())
        return words

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _calculate_lexical_diversity(self, text: str) -> float:
        """
        Calculate type-token ratio (TTR)

        TTR = unique words / total words
        Higher values indicate richer vocabulary
        """
        words = self._tokenize_words(text)
        if not words:
            return 0.0

        unique_words = len(set(words))
        total_words = len(words)

        # Apply correction for text length (longer texts naturally have lower TTR)
        # Use root TTR for better cross-text comparison
        ttr = unique_words / math.sqrt(total_words) if total_words > 1 else 0.0

        return min(1.0, ttr / 10.0)  # Normalize to 0-1

    def _calculate_vocabulary_richness(self, text: str) -> float:
        """
        Calculate vocabulary richness (simple ratio)

        Returns: unique_words / total_words
        """
        words = self._tokenize_words(text)
        if not words:
            return 0.0

        unique_words = len(set(words))
        total_words = len(words)

        return unique_words / total_words

    def _calculate_avg_sentence_length(self, text: str) -> float:
        """
        Calculate average sentence length in words

        Longer sentences often indicate more complex expression
        """
        sentences = self._split_sentences(text)
        if not sentences:
            return 0.0

        total_words = 0
        for sentence in sentences:
            total_words += len(self._tokenize_words(sentence))

        return total_words / len(sentences)

    def _calculate_syntactic_complexity(self, text: str) -> float:
        """
        Estimate syntactic complexity

        Heuristic based on:
        - Sentence length variation
        - Use of subordinate clauses (commas, conjunctions)
        - Passive voice indicators

        Returns: 0-1 score
        """
        sentences = self._split_sentences(text)
        if not sentences:
            return 0.0

        # Calculate sentence length variance
        lengths = [len(self._tokenize_words(s)) for s in sentences]
        if len(lengths) < 2:
            variance = 0
        else:
            mean_length = sum(lengths) / len(lengths)
            variance = sum((x - mean_length) ** 2 for x in lengths) / len(lengths)

        # Count complexity indicators
        complexity_markers = [
            ',',  # Subordinate clauses
            ';',  # Complex sentences
            'which', 'that', 'who', 'whom',  # Relative clauses
            'because', 'although', 'while', 'whereas',  # Subordinating conjunctions
        ]

        marker_count = sum(text.lower().count(marker) for marker in complexity_markers)
        marker_density = marker_count / len(sentences) if sentences else 0

        # Combine metrics
        complexity_score = (
            0.4 * min(1.0, variance / 50.0) +  # Sentence variety
            0.4 * min(1.0, marker_density / 3.0) +  # Complexity markers
            0.2 * min(1.0, mean_length / 25.0)  # Average length
        )

        return complexity_score

    def _calculate_domain_term_density(self, text: str) -> float:
        """
        Calculate density of domain-specific terminology

        Heuristic: words with length > 8 or containing technical patterns
        """
        words = self._tokenize_words(text)
        if not words:
            return 0.0

        # Technical patterns
        technical_patterns = [
            r'^[a-z]+[A-Z]',  # camelCase
            r'_',              # snake_case
            r'^[a-z]{8,}$',    # Long words (often technical)
        ]

        technical_count = 0
        for word in words:
            if len(word) > 8:
                technical_count += 1
            elif any(re.search(pattern, word) for pattern in technical_patterns):
                technical_count += 1

        return technical_count / len(words)

    def _count_technical_vocabulary(self, text: str) -> int:
        """Count unique technical/domain-specific terms"""
        words = self._tokenize_words(text)
        technical_words = set()

        for word in words:
            if len(word) > 8 or '_' in word:
                technical_words.add(word)

        return len(technical_words)

    async def _persist_metric(self, user_id: str, metric: LexicalMetrics) -> None:
        """Persist metric to disk"""
        filename = f"lexical_{user_id}_{metric.timestamp.isoformat()}.json"
        filepath = self.storage_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "user_id": user_id,
                    "timestamp": metric.timestamp.isoformat(),
                    "lexical_diversity": metric.lexical_diversity,
                    "vocabulary_richness": metric.vocabulary_richness,
                    "average_sentence_length": metric.average_sentence_length,
                    "syntactic_complexity_score": metric.syntactic_complexity_score,
                    "domain_term_density": metric.domain_term_density,
                    "technical_vocabulary_count": metric.technical_vocabulary_count,
                    "total_words": metric.total_words,
                    "unique_words": metric.unique_words,
                    "sentence_count": metric.sentence_count,
                    "text_sample_id": metric.text_sample_id,
                    "text_type": metric.text_type
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist lexical metric: {e}")

    def calculate_lexical_ari(self, user_id: str) -> Tuple[float, str]:
        """
        Calculate lexical ARI score from historical metrics

        Returns:
            Tuple of (ari_score, trend_direction)
            ari_score: 0-1, where 1 is best
            trend_direction: "improving", "stable", or "declining"
        """
        if user_id not in self.metrics_history or not self.metrics_history[user_id]:
            logger.warning(f"No lexical metrics for user {user_id}")
            return 0.5, "stable"

        metrics = self.metrics_history[user_id]

        # Filter to lookback window
        cutoff = datetime.now() - timedelta(days=self.lookback_window_days)
        recent_metrics = [m for m in metrics if m.timestamp >= cutoff]

        if len(recent_metrics) < self.min_samples_for_baseline:
            logger.warning(f"Insufficient samples for user {user_id}: {len(recent_metrics)}")
            return 0.5, "stable"

        # Calculate current average metrics
        current_diversity = sum(m.lexical_diversity for m in recent_metrics[-5:]) / min(5, len(recent_metrics))
        current_complexity = sum(m.syntactic_complexity_score for m in recent_metrics[-5:]) / min(5, len(recent_metrics))
        current_domain_density = sum(m.domain_term_density for m in recent_metrics[-5:]) / min(5, len(recent_metrics))

        # Calculate ARI score (0-1)
        ari_score = (
            0.4 * current_diversity +
            0.4 * current_complexity +
            0.2 * current_domain_density
        )

        # Detect trend
        if len(recent_metrics) >= 10:
            # Compare early vs late samples
            early = recent_metrics[:len(recent_metrics)//2]
            late = recent_metrics[len(recent_metrics)//2:]

            early_avg = sum(m.lexical_diversity + m.syntactic_complexity_score for m in early) / (2 * len(early))
            late_avg = sum(m.lexical_diversity + m.syntactic_complexity_score for m in late) / (2 * len(late))

            diff = late_avg - early_avg

            if diff > 0.05:
                trend = "improving"
            elif diff < -0.05:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        logger.info(
            f"Lexical ARI for {user_id}: {ari_score:.3f}, trend={trend}"
        )

        return ari_score, trend


# ============================================================================
# SOCRATIC CO-PILOT
# ============================================================================

class SocraticCopilot:
    """
    Embedded interaction measurement through Unassisted Capability Checkpoints (UCCs).

    When a user delegates a task, the co-pilot identifies key checkpoints
    where user knowledge is needed, asks clarifying questions, and logs
    the quality of responses to track capability retention.
    """

    def __init__(self, storage_dir: Path):
        """
        Initialize Socratic co-pilot

        Args:
            storage_dir: Directory for storing UCC history
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self.ucc_history: Dict[str, List[UnassistedCapabilityCheckpoint]] = {}

        # Load existing UCCs
        self._load_uccs()

        logger.info("SocraticCopilot initialized")

    def _load_uccs(self) -> None:
        """Load existing UCCs from storage"""
        ucc_files = list(self.storage_dir.glob("ucc_*.json"))
        logger.info(f"Loading {len(ucc_files)} UCC files")

        for ucc_file in ucc_files:
            try:
                with open(ucc_file, 'r') as f:
                    data = json.load(f)
                    user_id = data.get("user_id")
                    if user_id:
                        if user_id not in self.ucc_history:
                            self.ucc_history[user_id] = []

                        ucc = UnassistedCapabilityCheckpoint(
                            ucc_id=data["ucc_id"],
                            task_description=data["task_description"],
                            question=data["question"],
                            expected_knowledge_level=data["expected_knowledge_level"],
                            domain=data["domain"],
                            response_type=UCCResponseType(data["response_type"]),
                            response_text=data.get("response_text"),
                            response_timestamp=datetime.fromisoformat(data["response_timestamp"]) if data.get("response_timestamp") else None,
                            capability_demonstrated=data["capability_demonstrated"],
                            ari_signal=ARISignalLevel(data["ari_signal"]),
                            created_at=datetime.fromisoformat(data["created_at"])
                        )
                        self.ucc_history[user_id].append(ucc)
            except Exception as e:
                logger.error(f"Failed to load UCC {ucc_file}: {e}")

    async def identify_uccs(
        self,
        user_id: str,
        task_description: str,
        domain: str
    ) -> List[str]:
        """
        Identify Unassisted Capability Checkpoints for a task.

        Analyzes the task and identifies key points where user knowledge
        is needed rather than AI guessing.

        Args:
            user_id: User delegating the task
            task_description: Description of the task
            domain: Domain of the task (programming, writing, etc.)

        Returns:
            List of checkpoint questions to ask the user
        """
        logger.debug(f"Identifying UCCs for task: {task_description[:50]}...")

        # Task analysis heuristics
        questions = []

        # Check for ambiguous requirements
        ambiguous_terms = ['improve', 'enhance', 'better', 'good', 'nice']
        if any(term in task_description.lower() for term in ambiguous_terms):
            questions.append(
                "This task has some subjective goals. What specific criteria "
                "should I use to evaluate success?"
            )

        # Check for missing constraints
        if domain == "programming" and "function" in task_description.lower():
            questions.append(
                "For this function, what should the main logic be? "
                "(I want to ensure I implement what you have in mind)"
            )

        # Check for domain-specific gaps
        if domain == "writing":
            questions.append(
                "What tone and style are you aiming for with this piece? "
                "(formal, casual, technical, etc.)"
            )
        elif domain == "analysis":
            questions.append(
                "What insights or conclusions are you expecting to draw from this analysis?"
            )

        # Always ask for confirmation on assumptions
        questions.append(
            "Before I proceed, what assumptions should I be aware of, "
            "or what constraints should I keep in mind?"
        )

        logger.info(f"Identified {len(questions)} UCCs for task")
        return questions

    async def log_response(
        self,
        user_id: str,
        task_description: str,
        question: str,
        user_response: str,
        domain: str,
        expected_knowledge_level: str = "intermediate"
    ) -> UnassistedCapabilityCheckpoint:
        """
        Log user's response to a UCC and assess capability.

        Args:
            user_id: User who responded
            task_description: The task being worked on
            question: The question that was asked
            user_response: User's response
            domain: Domain of the task
            expected_knowledge_level: Expected knowledge level for this UCC

        Returns:
            UnassistedCapabilityCheckpoint with assessment
        """
        logger.debug(f"Logging UCC response for {user_id}: {user_response[:50]}...")

        # Classify response type
        response_lower = user_response.lower().strip()

        if any(phrase in response_lower for phrase in ["don't know", "not sure", "i don't", "no idea"]):
            response_type = UCCResponseType.UNCERTAIN
            capability = 0.2
            ari_signal = ARISignalLevel.LOW
        elif any(phrase in response_lower for phrase in ["just guess", "you decide", "you do it", "whatever you think"]):
            response_type = UCCResponseType.DELEGATED
            capability = 0.0
            ari_signal = ARISignalLevel.CRITICAL
        elif len(response_lower) < 10:
            response_type = UCCResponseType.PARTIAL
            capability = 0.4
            ari_signal = ARISignalLevel.MEDIUM
        else:
            # Assess response quality based on length and specificity
            if len(response_lower) > 50 and any(word in response_lower for word in ["should", "must", "need", "want", "because"]):
                response_type = UCCResponseType.ACCURATE
                capability = 0.9
                ari_signal = ARISignalLevel.HIGH
            else:
                response_type = UCCResponseType.PARTIAL
                capability = 0.6
                ari_signal = ARISignalLevel.MEDIUM

        # Create UCC record
        ucc = UnassistedCapabilityCheckpoint(
            ucc_id=f"ucc_{datetime.now().timestamp()}",
            task_description=task_description,
            question=question,
            expected_knowledge_level=expected_knowledge_level,
            domain=domain,
            response_type=response_type,
            response_text=user_response,
            response_timestamp=datetime.now(),
            capability_demonstrated=capability,
            ari_signal=ari_signal
        )

        # Store UCC
        if user_id not in self.ucc_history:
            self.ucc_history[user_id] = []
        self.ucc_history[user_id].append(ucc)

        # Persist to disk
        await self._persist_ucc(user_id, ucc)

        logger.info(
            f"Logged UCC for {user_id}: response_type={response_type.value}, "
            f"capability={capability:.2f}, signal={ari_signal.value}"
        )

        return ucc

    async def _persist_ucc(self, user_id: str, ucc: UnassistedCapabilityCheckpoint) -> None:
        """Persist UCC to disk"""
        filename = f"ucc_{user_id}_{ucc.created_at.isoformat()}.json"
        filepath = self.storage_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "user_id": user_id,
                    "ucc_id": ucc.ucc_id,
                    "task_description": ucc.task_description,
                    "question": ucc.question,
                    "expected_knowledge_level": ucc.expected_knowledge_level,
                    "domain": ucc.domain,
                    "response_type": ucc.response_type.value,
                    "response_text": ucc.response_text,
                    "response_timestamp": ucc.response_timestamp.isoformat() if ucc.response_timestamp else None,
                    "capability_demonstrated": ucc.capability_demonstrated,
                    "ari_signal": ucc.ari_signal.value,
                    "created_at": ucc.created_at.isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist UCC: {e}")

    def calculate_interaction_ari(self, user_id: str, lookback_days: int = 30) -> Tuple[float, ARISignalLevel]:
        """
        Calculate interaction ARI score from UCC history

        Args:
            user_id: User to calculate for
            lookback_days: How far back to look

        Returns:
            Tuple of (ari_score, signal_level)
        """
        if user_id not in self.ucc_history or not self.ucc_history[user_id]:
            logger.warning(f"No UCC history for user {user_id}")
            return 0.5, ARISignalLevel.MEDIUM

        # Filter to lookback window
        cutoff = datetime.now() - timedelta(days=lookback_days)
        recent_uccs = [
            ucc for ucc in self.ucc_history[user_id]
            if ucc.created_at >= cutoff
        ]

        if not recent_uccs:
            logger.warning(f"No recent UCCs for user {user_id}")
            return 0.5, ARISignalLevel.MEDIUM

        # Calculate average capability
        avg_capability = sum(ucc.capability_demonstrated for ucc in recent_uccs) / len(recent_uccs)

        # Determine signal level
        if avg_capability >= 0.75:
            signal = ARISignalLevel.HIGH
        elif avg_capability >= 0.5:
            signal = ARISignalLevel.MEDIUM
        elif avg_capability >= 0.25:
            signal = ARISignalLevel.LOW
        else:
            signal = ARISignalLevel.CRITICAL

        logger.info(
            f"Interaction ARI for {user_id}: {avg_capability:.3f}, signal={signal.value}"
        )

        return avg_capability, signal


# ============================================================================
# DEEP DIVE MODE
# ============================================================================

class DeepDiveMode:
    """
    Opt-in "Learn About Me" mode for establishing capability baselines.

    Uses extended Socratic exploration to build a rich, gold-standard
    baseline of the user's knowledge and synthesis skills.
    """

    def __init__(self, storage_dir: Path):
        """
        Initialize deep dive mode

        Args:
            storage_dir: Directory for storing baselines
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self.baselines: Dict[str, Dict[str, ARIBaseline]] = {}  # user_id -> domain -> baseline

        # Load existing baselines
        self._load_baselines()

        logger.info("DeepDiveMode initialized")

    def _load_baselines(self) -> None:
        """Load existing baselines from storage"""
        baseline_files = list(self.storage_dir.glob("baseline_*.json"))
        logger.info(f"Loading {len(baseline_files)} baseline files")

        for baseline_file in baseline_files:
            try:
                with open(baseline_file, 'r') as f:
                    data = json.load(f)
                    user_id = data.get("user_id")
                    domain = data.get("domain")

                    if user_id and domain:
                        if user_id not in self.baselines:
                            self.baselines[user_id] = {}

                        baseline = ARIBaseline(
                            user_id=user_id,
                            domain=domain,
                            knowledge_topics=data["knowledge_topics"],
                            demonstrated_skills=data["demonstrated_skills"],
                            synthesis_quality_score=data["synthesis_quality_score"],
                            reasoning_depth_score=data["reasoning_depth_score"],
                            baseline_lexical_diversity=data["baseline_lexical_diversity"],
                            baseline_syntactic_complexity=data["baseline_syntactic_complexity"],
                            established_at=datetime.fromisoformat(data["established_at"]),
                            sample_count=data["sample_count"]
                        )
                        self.baselines[user_id][domain] = baseline
            except Exception as e:
                logger.error(f"Failed to load baseline {baseline_file}: {e}")

    async def start_deep_dive(
        self,
        user_id: str,
        domain: str,
        exploration_prompt: Optional[str] = None
    ) -> List[str]:
        """
        Start a deep dive exploration session.

        Args:
            user_id: User to explore
            domain: Domain to explore (programming, writing, etc.)
            exploration_prompt: Optional starting prompt

        Returns:
            List of Socratic questions for deep exploration
        """
        logger.info(f"Starting deep dive for {user_id} in domain {domain}")

        # Generate exploration questions based on domain
        questions = []

        if domain == "programming":
            questions = [
                "Let's explore your programming knowledge. Can you describe your approach to solving a complex algorithmic problem?",
                "What design patterns do you typically use, and why do you prefer them?",
                "How do you approach debugging a system you're unfamiliar with?",
                "Can you explain a particularly elegant solution you've implemented recently?",
                "What trade-offs do you consider when optimizing code for performance vs readability?"
            ]
        elif domain == "writing":
            questions = [
                "Let's explore your writing style. How do you approach structuring a complex argument?",
                "What techniques do you use to engage your reader?",
                "How do you adapt your tone for different audiences?",
                "Can you describe your revision process?",
                "What makes a piece of writing 'good' in your view?"
            ]
        elif domain == "analysis":
            questions = [
                "Let's explore your analytical approach. How do you approach a complex data set?",
                "What framework do you use to identify key insights?",
                "How do you distinguish correlation from causation?",
                "Can you walk me through your reasoning for a recent analysis?",
                "What techniques do you use to validate your conclusions?"
            ]
        else:
            questions = [
                f"Let's explore your expertise in {domain}. What are the fundamental concepts you work with?",
                "How do you approach learning something new in this domain?",
                "What principles guide your decision-making?",
                "Can you describe a challenging problem you've solved?",
                "What makes someone skilled in this domain, in your view?"
            ]

        logger.info(f"Generated {len(questions)} deep dive questions")
        return questions

    async def record_deep_dive_response(
        self,
        user_id: str,
        domain: str,
        question: str,
        response: str
    ) -> None:
        """
        Record a response from the deep dive exploration.

        Analyzes the response for knowledge depth and synthesis quality.

        Args:
            user_id: User responding
            domain: Domain being explored
            question: Question that was asked
            response: User's response
        """
        logger.debug(f"Recording deep dive response for {user_id}")

        # Initialize baseline if not exists
        if user_id not in self.baselines:
            self.baselines[user_id] = {}
        if domain not in self.baselines[user_id]:
            self.baselines[user_id][domain] = ARIBaseline(
                user_id=user_id,
                domain=domain
            )

        baseline = self.baselines[user_id][domain]

        # Analyze response for knowledge indicators
        words = response.lower().split()

        # Extract knowledge topics (nouns/key terms)
        # Simple heuristic: words > 5 chars that appear in technical context
        potential_topics = [w for w in words if len(w) > 5]
        baseline.knowledge_topics.extend(potential_topics[:10])  # Top 10 from this response

        # Assess synthesis quality (complexity of response)
        synthesis_score = min(1.0, len(response) / 500.0)  # Normalize to 500 chars
        baseline.synthesis_quality_score = (
            (baseline.synthesis_quality_score * baseline.sample_count + synthesis_score) /
            (baseline.sample_count + 1)
        )

        # Assess reasoning depth (presence of reasoning markers)
        reasoning_markers = ['because', 'therefore', 'however', 'although', 'thus', 'hence']
        reasoning_count = sum(1 for marker in reasoning_markers if marker in response.lower())
        reasoning_score = min(1.0, reasoning_count / 5.0)
        baseline.reasoning_depth_score = (
            (baseline.reasoning_depth_score * baseline.sample_count + reasoning_score) /
            (baseline.sample_count + 1)
        )

        baseline.sample_count += 1

        logger.info(
            f"Updated baseline for {user_id}/{domain}: "
            f"synthesis={baseline.synthesis_quality_score:.3f}, "
            f"reasoning={baseline.reasoning_depth_score:.3f}"
        )

    async def finalize_baseline(
        self,
        user_id: str,
        domain: str,
        lexical_metrics: Optional[List[LexicalMetrics]] = None
    ) -> ARIBaseline:
        """
        Finalize the baseline after deep dive completion.

        Args:
            user_id: User to finalize for
            domain: Domain that was explored
            lexical_metrics: Optional lexical metrics from responses

        Returns:
            Finalized ARIBaseline
        """
        logger.info(f"Finalizing baseline for {user_id}/{domain}")

        if user_id not in self.baselines or domain not in self.baselines[user_id]:
            logger.error(f"No baseline to finalize for {user_id}/{domain}")
            raise ValueError(f"No baseline found for {user_id}/{domain}")

        baseline = self.baselines[user_id][domain]

        # Add lexical baseline if provided
        if lexical_metrics:
            baseline.baseline_lexical_diversity = sum(m.lexical_diversity for m in lexical_metrics) / len(lexical_metrics)
            baseline.baseline_syntactic_complexity = sum(m.syntactic_complexity_score for m in lexical_metrics) / len(lexical_metrics)

        # Deduplicate topics
        baseline.knowledge_topics = list(set(baseline.knowledge_topics))

        # Persist to disk
        await self._persist_baseline(baseline)

        logger.info(
            f"Finalized baseline for {user_id}/{domain} with {baseline.sample_count} samples"
        )

        return baseline

    async def _persist_baseline(self, baseline: ARIBaseline) -> None:
        """Persist baseline to disk"""
        filename = f"baseline_{baseline.user_id}_{baseline.domain}.json"
        filepath = self.storage_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "user_id": baseline.user_id,
                    "domain": baseline.domain,
                    "knowledge_topics": baseline.knowledge_topics,
                    "demonstrated_skills": baseline.demonstrated_skills,
                    "synthesis_quality_score": baseline.synthesis_quality_score,
                    "reasoning_depth_score": baseline.reasoning_depth_score,
                    "baseline_lexical_diversity": baseline.baseline_lexical_diversity,
                    "baseline_syntactic_complexity": baseline.baseline_syntactic_complexity,
                    "established_at": baseline.established_at.isoformat(),
                    "sample_count": baseline.sample_count
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist baseline: {e}")

    def get_baseline(self, user_id: str, domain: str) -> Optional[ARIBaseline]:
        """Get baseline for user/domain"""
        return self.baselines.get(user_id, {}).get(domain)


# ============================================================================
# ARI ENGINE (Orchestrator)
# ============================================================================

class ARIEngine:
    """
    Orchestrator for the Autonomy Retention Index Engine.

    Coordinates the three measurement methods:
    1. Passive Lexical Analysis
    2. Socratic Co-pilot
    3. Deep Dive Mode

    Calculates comprehensive ARI scores and generates alerts.
    """

    def __init__(
        self,
        storage_dir: Path,
        lexical_lookback_days: int = 30,
        interaction_lookback_days: int = 30
    ):
        """
        Initialize ARI Engine

        Args:
            storage_dir: Root storage directory
            lexical_lookback_days: Lookback window for lexical analysis
            interaction_lookback_days: Lookback window for interaction analysis
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.lexical_analyzer = PassiveLexicalAnalyzer(
            storage_dir=self.storage_dir / "lexical",
            lookback_window_days=lexical_lookback_days
        )
        self.socratic_copilot = SocraticCopilot(
            storage_dir=self.storage_dir / "uccs"
        )
        self.deep_dive = DeepDiveMode(
            storage_dir=self.storage_dir / "baselines"
        )

        self.lexical_lookback_days = lexical_lookback_days
        self.interaction_lookback_days = interaction_lookback_days

        # ARI score history
        self.ari_scores: Dict[str, List[ARIScore]] = {}

        logger.info("ARIEngine initialized with all components")

    async def analyze_user_text(
        self,
        user_id: str,
        text: str,
        text_type: str = "document"
    ) -> LexicalMetrics:
        """
        Passively analyze user text (non-invasive background measurement).

        Args:
            user_id: User who wrote the text
            text: Text to analyze
            text_type: Type of text

        Returns:
            LexicalMetrics from analysis
        """
        return await self.lexical_analyzer.analyze_text(user_id, text, text_type)

    async def intercept_task_delegation(
        self,
        user_id: str,
        task_description: str,
        domain: str
    ) -> List[str]:
        """
        Intercept a task delegation and generate Socratic questions.

        Args:
            user_id: User delegating task
            task_description: Description of task
            domain: Domain of task

        Returns:
            List of UCC questions to ask user
        """
        return await self.socratic_copilot.identify_uccs(user_id, task_description, domain)

    async def record_ucc_response(
        self,
        user_id: str,
        task_description: str,
        question: str,
        response: str,
        domain: str
    ) -> UnassistedCapabilityCheckpoint:
        """
        Record user's response to a UCC question.

        Args:
            user_id: User responding
            task_description: Task being worked on
            question: Question asked
            response: User's response
            domain: Domain of task

        Returns:
            UCC with capability assessment
        """
        return await self.socratic_copilot.log_response(
            user_id, task_description, question, response, domain
        )

    async def start_deep_dive_session(
        self,
        user_id: str,
        domain: str
    ) -> List[str]:
        """
        Start an opt-in deep dive exploration session.

        Args:
            user_id: User to explore
            domain: Domain to explore

        Returns:
            List of exploration questions
        """
        return await self.deep_dive.start_deep_dive(user_id, domain)

    async def record_deep_dive_response(
        self,
        user_id: str,
        domain: str,
        question: str,
        response: str
    ) -> None:
        """
        Record a deep dive response.

        Args:
            user_id: User responding
            domain: Domain being explored
            question: Question asked
            response: User's response
        """
        await self.deep_dive.record_deep_dive_response(user_id, domain, question, response)

    async def finalize_deep_dive_baseline(
        self,
        user_id: str,
        domain: str
    ) -> ARIBaseline:
        """
        Finalize deep dive baseline.

        Args:
            user_id: User to finalize for
            domain: Domain explored

        Returns:
            Finalized baseline
        """
        # Get lexical metrics from deep dive responses
        lexical_metrics = self.lexical_analyzer.metrics_history.get(user_id, [])
        recent = lexical_metrics[-10:] if lexical_metrics else None

        return await self.deep_dive.finalize_baseline(user_id, domain, recent)

    def calculate_comprehensive_ari(
        self,
        user_id: str,
        domain: Optional[str] = None
    ) -> ARIScore:
        """
        Calculate comprehensive ARI score for a user.

        Combines:
        - Lexical ARI (from passive analysis)
        - Interaction ARI (from Socratic co-pilot)
        - Baseline deviation (from deep dive)

        Args:
            user_id: User to calculate for
            domain: Optional specific domain

        Returns:
            Comprehensive ARIScore
        """
        logger.info(f"Calculating comprehensive ARI for {user_id}")

        # Get component scores
        lexical_ari, lexical_trend = self.lexical_analyzer.calculate_lexical_ari(user_id)
        interaction_ari, interaction_signal = self.socratic_copilot.calculate_interaction_ari(
            user_id, self.interaction_lookback_days
        )

        # Calculate baseline deviation if available
        baseline_deviation = 0.0
        if domain:
            baseline = self.deep_dive.get_baseline(user_id, domain)
            if baseline:
                # Compare current metrics to baseline
                recent_metrics = self.lexical_analyzer.metrics_history.get(user_id, [])
                if recent_metrics:
                    current_diversity = sum(m.lexical_diversity for m in recent_metrics[-5:]) / min(5, len(recent_metrics))
                    current_complexity = sum(m.syntactic_complexity_score for m in recent_metrics[-5:]) / min(5, len(recent_metrics))

                    diversity_dev = current_diversity - baseline.baseline_lexical_diversity
                    complexity_dev = current_complexity - baseline.baseline_syntactic_complexity

                    # Negative deviation means decline from baseline
                    baseline_deviation = (diversity_dev + complexity_dev) / 2.0

        # Calculate overall ARI (weighted combination)
        overall_ari = (
            0.4 * lexical_ari +
            0.4 * interaction_ari +
            0.2 * (0.5 + baseline_deviation)  # Normalize baseline deviation
        )

        # Determine signal level
        if overall_ari >= 0.75:
            signal_level = ARISignalLevel.HIGH
        elif overall_ari >= 0.5:
            signal_level = ARISignalLevel.MEDIUM
        elif overall_ari >= 0.25:
            signal_level = ARISignalLevel.LOW
        else:
            signal_level = ARISignalLevel.CRITICAL

        # Generate alerts
        alerts = []
        if signal_level == ARISignalLevel.CRITICAL:
            alerts.append("⚠️ CRITICAL: Significant skill atrophy detected")
        elif signal_level == ARISignalLevel.LOW:
            alerts.append("⚠️ LOW ARI: Skill retention concerns detected")

        if lexical_trend == "declining":
            alerts.append("📉 Lexical complexity declining")
        if interaction_signal == ARISignalLevel.CRITICAL:
            alerts.append("🤔 Frequent task delegation without engagement")

        # Determine trend
        if user_id in self.ari_scores and len(self.ari_scores[user_id]) >= 2:
            recent_scores = self.ari_scores[user_id][-5:]
            early_avg = sum(s.overall_ari for s in recent_scores[:len(recent_scores)//2]) / (len(recent_scores)//2)
            late_avg = sum(s.overall_ari for s in recent_scores[len(recent_scores)//2:]) / (len(recent_scores) - len(recent_scores)//2)

            if late_avg > early_avg + 0.05:
                trend = "improving"
            elif late_avg < early_avg - 0.05:
                trend = "declining"
            else:
                trend = "stable"

            days_in_trend = len(recent_scores) * 7  # Rough estimate
        else:
            trend = "stable"
            days_in_trend = 0

        # Create ARI score
        ari_score = ARIScore(
            user_id=user_id,
            timestamp=datetime.now(),
            overall_ari=overall_ari,
            signal_level=signal_level,
            lexical_ari=lexical_ari,
            interaction_ari=interaction_ari,
            baseline_deviation=baseline_deviation,
            trend_direction=trend,
            days_in_trend=days_in_trend,
            alerts=alerts,
            confidence=0.8  # TODO: Calculate based on data availability
        )

        # Store score
        if user_id not in self.ari_scores:
            self.ari_scores[user_id] = []
        self.ari_scores[user_id].append(ari_score)

        logger.info(
            f"Comprehensive ARI for {user_id}: {overall_ari:.3f} ({signal_level.value}), "
            f"trend={trend}"
        )

        return ari_score

    def get_ari_history(
        self,
        user_id: str,
        days: int = 90
    ) -> List[ARIScore]:
        """
        Get ARI score history for a user.

        Args:
            user_id: User to get history for
            days: Number of days to look back

        Returns:
            List of ARIScore objects
        """
        if user_id not in self.ari_scores:
            return []

        cutoff = datetime.now() - timedelta(days=days)
        return [
            score for score in self.ari_scores[user_id]
            if score.timestamp >= cutoff
        ]

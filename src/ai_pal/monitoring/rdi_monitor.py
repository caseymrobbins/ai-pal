"""
RDI (Reality Drift Index) Monitor

PRIVACY-FIRST Reality Drift Detection System

Tracks "reality drift" or cognitive divergence from shared consensus reality
due to sustained epistemic debt.

**CRITICAL PRIVACY CONSTRAINTS:**
- ALL analysis happens ON-DEVICE only
- Individual RDI scores are NEVER exfiltrated
- Raw user inputs are NEVER stored or transmitted
- Only aggregate, anonymized data can be optionally shared (explicit opt-in)
- RDI is a PRIVATE metric for user awareness only

Part of the Agency-Centric AI framework's epistemic integrity monitoring.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import hashlib
import random

from loguru import logger


# ============================================================================
# PRIVACY MARKER
# ============================================================================

# This constant marks that RDI data is PRIVATE and must never be exfiltrated
PRIVATE_METRIC = True
RDI_PRIVACY_VERSION = "1.0.0"


# ============================================================================
# ENUMS & DATA STRUCTURES
# ============================================================================

class RDILevel(Enum):
    """Reality Drift Index levels"""
    ALIGNED = "aligned"          # User aligned with consensus reality
    MINOR_DRIFT = "minor_drift"  # Small divergence detected
    MODERATE_DRIFT = "moderate_drift"  # Notable divergence
    SIGNIFICANT_DRIFT = "significant_drift"  # Serious divergence
    CRITICAL_DRIFT = "critical_drift"  # Severe reality drift


class DriftType(Enum):
    """Types of reality drift"""
    SEMANTIC = "semantic"        # Semantic understanding shifted
    FACTUAL = "factual"          # Factual baseline changed
    LOGICAL = "logical"          # Logical reasoning patterns changed
    CONTEXTUAL = "contextual"    # Context interpretation changed


@dataclass
class SemanticBaseline:
    """
    LOCAL-ONLY semantic baseline for a user.

    **PRIVACY:** This baseline is calculated locally and never transmitted.
    """
    user_id: str  # Hashed locally, never the real ID

    # Semantic patterns (anonymized)
    concept_frequency: Dict[str, int] = field(default_factory=dict)  # Concept -> frequency
    relationship_patterns: Dict[str, int] = field(default_factory=dict)  # Relationship -> count

    # Baseline characteristics
    vocabulary_centroid: List[float] = field(default_factory=list)  # Anonymized embedding
    reasoning_pattern_signature: str = ""  # Hash of reasoning patterns

    # Metadata
    established_at: datetime = field(default_factory=datetime.now)
    sample_count: int = 0


@dataclass
class ConsensusModel:
    """
    Lightweight, generalized public consensus model.

    This represents shared, common-knowledge facts and semantic patterns.
    Does NOT contain individual user data.
    """
    model_version: str = "1.0.0"

    # Common facts (generalized, public knowledge)
    common_facts: Set[str] = field(default_factory=set)

    # Expected semantic patterns (general linguistic norms)
    expected_patterns: Dict[str, float] = field(default_factory=dict)

    # Logical reasoning norms
    reasoning_norms: List[str] = field(default_factory=list)

    # Last updated
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class DriftSignal:
    """
    A detected reality drift signal.

    **PRIVACY:** Contains NO raw user input. Only aggregate metrics.
    """
    signal_id: str
    timestamp: datetime

    # Drift characteristics
    drift_type: DriftType
    drift_magnitude: float  # 0-1
    drift_confidence: float  # How confident in this detection (0-1)

    # Context (anonymized)
    affected_domains: List[str]  # e.g., ["science", "history"]
    deviation_pattern: str  # Hash of the deviation pattern (not actual content)

    # Tracking
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class RDIScore:
    """
    Reality Drift Index score for a user.

    **PRIVACY CRITICAL:** This is a PRIVATE metric.
    - Calculated locally
    - Never exfiltrated at individual level
    - Only shown to user via their private dashboard
    - Can only be shared as part of anonymized aggregates (with explicit opt-in)
    """
    user_id: str  # LOCAL ONLY - hashed, never transmitted
    timestamp: datetime

    # Overall RDI (0-1, where 0 is aligned, 1 is maximum drift)
    overall_rdi: float
    rdi_level: RDILevel

    # Component scores
    semantic_drift: float      # Semantic understanding drift
    factual_drift: float       # Factual baseline drift
    logical_drift: float       # Logical reasoning drift

    # Trend
    trend_direction: str       # "stable", "increasing", "decreasing"
    days_in_trend: int

    # Alerts (shown only to user)
    private_alerts: List[str] = field(default_factory=list)

    # Privacy metadata
    _is_private: bool = field(default=True, init=False)
    _privacy_version: str = field(default=RDI_PRIVACY_VERSION, init=False)


@dataclass
class AnonymizedRDIStats:
    """
    Anonymized, aggregate RDI statistics.

    **PRIVACY:** This is the ONLY form of RDI data that can be shared.
    - No individual user IDs
    - Aggregated across many users (minimum 100)
    - No raw inputs
    - Scrubbed of all PII
    """
    stats_id: str
    collection_period: str  # e.g., "2025-10-01 to 2025-10-31"

    # Aggregate statistics
    total_users: int  # Must be >= 100 for privacy
    average_rdi: float
    median_rdi: float
    std_dev_rdi: float

    # Distribution
    rdi_distribution: Dict[str, int]  # Level -> count

    # Trends
    trend_summary: Dict[str, float]  # "increasing" -> percentage

    # Privacy assurance
    anonymization_applied: bool = True
    minimum_user_threshold_met: bool = False  # True only if >= 100 users
    pii_scrubbed: bool = True


# ============================================================================
# RDI MONITOR
# ============================================================================

class RDIMonitor:
    """
    Reality Drift Index Monitor

    **PRIVACY-FIRST DESIGN:**

    1. ALL processing happens ON-DEVICE
    2. Individual RDI scores are LOCAL ONLY
    3. No raw user input is stored or transmitted
    4. User sees their RDI on private dashboard only
    5. Optional aggregate sharing requires:
       - Explicit user opt-in
       - Complete anonymization
       - Minimum 100 users in aggregate
       - PII scrubbing

    This monitor detects epistemic drift from consensus reality
    while respecting absolute privacy.
    """

    def __init__(
        self,
        storage_dir: Path,
        enable_privacy_mode: bool = True,  # ALWAYS True in production
        consensus_model_path: Optional[Path] = None
    ):
        """
        Initialize RDI Monitor

        Args:
            storage_dir: LOCAL storage directory (never cloud)
            enable_privacy_mode: Privacy enforcement (should always be True)
            consensus_model_path: Path to consensus model (generalized public knowledge)
        """
        if not enable_privacy_mode:
            logger.warning(
                "⚠️ RDI Monitor initialized with privacy_mode=False. "
                "This should ONLY be used for testing!"
            )

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.privacy_mode = enable_privacy_mode

        # LOCAL-ONLY data structures
        self._local_baselines: Dict[str, SemanticBaseline] = {}  # Hashed user_id -> baseline
        self._local_rdi_scores: Dict[str, List[RDIScore]] = {}   # Hashed user_id -> scores
        self._local_drift_signals: Dict[str, List[DriftSignal]] = {}  # Hashed user_id -> signals

        # Consensus model (public, generalized knowledge)
        self.consensus_model = self._load_or_create_consensus_model(consensus_model_path)

        # User opt-ins for aggregate sharing (explicit consent)
        self._aggregate_opt_ins: Set[str] = set()  # Hashed user IDs who opted in

        # Load local data
        self._load_local_data()

        logger.info(
            f"RDIMonitor initialized in {'PRIVACY' if self.privacy_mode else 'TEST'} mode"
        )

    def _hash_user_id(self, user_id: str) -> str:
        """
        Hash user ID for local storage.

        **PRIVACY:** This ensures even local storage doesn't contain real user IDs.
        """
        return hashlib.sha256(f"{user_id}_rdi_local".encode()).hexdigest()[:16]

    def _load_or_create_consensus_model(
        self,
        model_path: Optional[Path]
    ) -> ConsensusModel:
        """
        Load or create consensus model.

        **PRIVACY:** This model contains ONLY generalized public knowledge.
        No individual user data.
        """
        if model_path and model_path.exists():
            try:
                with open(model_path, 'r') as f:
                    data = json.load(f)
                    model = ConsensusModel(
                        model_version=data["model_version"],
                        common_facts=set(data["common_facts"]),
                        expected_patterns=data["expected_patterns"],
                        reasoning_norms=data["reasoning_norms"],
                        last_updated=datetime.fromisoformat(data["last_updated"])
                    )
                    logger.info(f"Loaded consensus model v{model.model_version}")
                    return model
            except Exception as e:
                logger.error(f"Failed to load consensus model: {e}")

        # Create default consensus model (generalized)
        logger.info("Creating default consensus model")
        return ConsensusModel(
            model_version="1.0.0",
            common_facts={
                # General scientific facts
                "earth_orbits_sun",
                "water_boils_at_100c_at_sea_level",
                "gravity_constant",
                # General historical facts
                "world_war_2_occurred_1939_1945",
                # General mathematical facts
                "pythagorean_theorem",
                "prime_numbers_infinite",
            },
            expected_patterns={
                "causal_reasoning": 0.8,       # Expected frequency of causal reasoning
                "evidence_based": 0.7,         # Expected use of evidence
                "logical_consistency": 0.9,    # Expected logical consistency
            },
            reasoning_norms=[
                "cause_precedes_effect",
                "evidence_supports_claims",
                "consistency_required",
                "contradiction_indicates_error"
            ]
        )

    def _load_local_data(self) -> None:
        """
        Load local data from device storage.

        **PRIVACY:** This data never leaves the device.
        """
        # Load baselines
        baseline_files = list(self.storage_dir.glob("rdi_baseline_*.json"))
        for file in baseline_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    baseline = SemanticBaseline(
                        user_id=data["user_id"],
                        concept_frequency=data["concept_frequency"],
                        relationship_patterns=data["relationship_patterns"],
                        vocabulary_centroid=data["vocabulary_centroid"],
                        reasoning_pattern_signature=data["reasoning_pattern_signature"],
                        established_at=datetime.fromisoformat(data["established_at"]),
                        sample_count=data["sample_count"]
                    )
                    self._local_baselines[baseline.user_id] = baseline
            except Exception as e:
                logger.error(f"Failed to load baseline {file}: {e}")

        # Load scores
        score_files = list(self.storage_dir.glob("rdi_score_*.json"))
        for file in score_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    user_id = data["user_id"]
                    score = RDIScore(
                        user_id=user_id,
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        overall_rdi=data["overall_rdi"],
                        rdi_level=RDILevel(data["rdi_level"]),
                        semantic_drift=data["semantic_drift"],
                        factual_drift=data["factual_drift"],
                        logical_drift=data["logical_drift"],
                        trend_direction=data["trend_direction"],
                        days_in_trend=data["days_in_trend"],
                        private_alerts=data["private_alerts"]
                    )

                    if user_id not in self._local_rdi_scores:
                        self._local_rdi_scores[user_id] = []
                    self._local_rdi_scores[user_id].append(score)
            except Exception as e:
                logger.error(f"Failed to load score {file}: {e}")

        logger.info(
            f"Loaded {len(self._local_baselines)} baselines, "
            f"{sum(len(scores) for scores in self._local_rdi_scores.values())} scores"
        )

    async def analyze_input(
        self,
        user_id: str,
        user_input: str,
        domain: Optional[str] = None
    ) -> Tuple[float, List[DriftSignal]]:
        """
        Analyze user input for reality drift.

        **PRIVACY CRITICAL:**
        - Input is analyzed locally
        - Raw input is NOT stored
        - Only aggregate metrics are retained
        - User ID is hashed before any storage

        Args:
            user_id: User (will be hashed internally)
            user_input: User's input text (analyzed but not stored)
            domain: Optional domain context

        Returns:
            Tuple of (drift_score, detected_signals)
        """
        logger.debug(f"Analyzing input for drift (length={len(user_input)})")

        # Hash user ID for privacy
        hashed_user_id = self._hash_user_id(user_id)

        # Initialize baseline if needed
        if hashed_user_id not in self._local_baselines:
            self._local_baselines[hashed_user_id] = SemanticBaseline(
                user_id=hashed_user_id
            )

        baseline = self._local_baselines[hashed_user_id]

        # Analyze input (WITHOUT storing raw text)
        semantic_drift = await self._analyze_semantic_drift(user_input, baseline)
        factual_drift = await self._analyze_factual_drift(user_input, baseline)
        logical_drift = await self._analyze_logical_drift(user_input, baseline)

        # Calculate overall drift
        drift_score = (
            0.4 * semantic_drift +
            0.4 * factual_drift +
            0.2 * logical_drift
        )

        # Detect drift signals
        signals = []
        if semantic_drift > 0.3:
            signals.append(DriftSignal(
                signal_id=f"drift_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                drift_type=DriftType.SEMANTIC,
                drift_magnitude=semantic_drift,
                drift_confidence=0.7,
                affected_domains=[domain] if domain else [],
                deviation_pattern=hashlib.sha256(user_input.encode()).hexdigest()[:16]
            ))

        if factual_drift > 0.3:
            signals.append(DriftSignal(
                signal_id=f"drift_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                drift_type=DriftType.FACTUAL,
                drift_magnitude=factual_drift,
                drift_confidence=0.8,
                affected_domains=[domain] if domain else [],
                deviation_pattern=hashlib.sha256(user_input.encode()).hexdigest()[:16]
            ))

        # Store signals locally
        if hashed_user_id not in self._local_drift_signals:
            self._local_drift_signals[hashed_user_id] = []
        self._local_drift_signals[hashed_user_id].extend(signals)

        # Update baseline (without storing raw input)
        await self._update_baseline(hashed_user_id, user_input)

        logger.info(
            f"Drift analysis complete: score={drift_score:.3f}, "
            f"signals={len(signals)}"
        )

        return drift_score, signals

    async def _analyze_semantic_drift(
        self,
        user_input: str,
        baseline: SemanticBaseline
    ) -> float:
        """
        Analyze semantic drift from baseline.

        **PRIVACY:** Operates on local data only.

        Returns:
            Drift score (0-1)
        """
        # Extract concepts (simple heuristic: nouns/key terms)
        words = user_input.lower().split()
        concepts = [w for w in words if len(w) > 5]

        # Compare to baseline concept frequency
        if not baseline.concept_frequency:
            # No baseline yet, assume aligned
            return 0.1

        # Calculate concept overlap
        baseline_concepts = set(baseline.concept_frequency.keys())
        input_concepts = set(concepts)

        if not input_concepts:
            return 0.1

        overlap = len(baseline_concepts & input_concepts) / len(input_concepts)

        # Drift is inverse of overlap
        drift = 1.0 - overlap

        return min(1.0, drift)

    async def _analyze_factual_drift(
        self,
        user_input: str,
        baseline: SemanticBaseline
    ) -> float:
        """
        Analyze factual drift from consensus model.

        **PRIVACY:** Uses only generalized consensus model, not individual data.

        Returns:
            Drift score (0-1)
        """
        # Check for common fact patterns in input
        input_lower = user_input.lower()

        # Count violations of common facts
        violations = 0
        checks = 0

        for fact_pattern in self.consensus_model.common_facts:
            # Simple check (in production, would use NLP)
            if fact_pattern.replace('_', ' ') in input_lower:
                checks += 1
                # Assume fact is stated correctly (simplified)
                # In production, would check for negations or contradictions

        if checks == 0:
            # No factual claims detected
            return 0.0

        # Calculate drift (simplified)
        drift = violations / checks if checks > 0 else 0.0

        return min(1.0, drift)

    async def _analyze_logical_drift(
        self,
        user_input: str,
        baseline: SemanticBaseline
    ) -> float:
        """
        Analyze logical reasoning drift.

        **PRIVACY:** Operates on local patterns only.

        Returns:
            Drift score (0-1)
        """
        # Check for logical reasoning markers
        reasoning_markers = [
            'because', 'therefore', 'thus', 'hence', 'consequently',
            'if', 'then', 'since', 'as a result'
        ]

        marker_count = sum(
            1 for marker in reasoning_markers
            if marker in user_input.lower()
        )

        # Expected frequency from consensus model
        expected_freq = self.consensus_model.expected_patterns.get("causal_reasoning", 0.8)

        # Calculate actual frequency (normalized)
        words = len(user_input.split())
        actual_freq = marker_count / (words / 100) if words > 0 else 0  # Per 100 words

        # Drift from expected
        drift = abs(actual_freq - expected_freq) / expected_freq if expected_freq > 0 else 0.0

        return min(1.0, drift)

    async def _update_baseline(
        self,
        hashed_user_id: str,
        user_input: str
    ) -> None:
        """
        Update user's semantic baseline.

        **PRIVACY:** Stores only aggregate patterns, not raw input.

        Args:
            hashed_user_id: Hashed user ID
            user_input: Input text (analyzed but not stored)
        """
        baseline = self._local_baselines[hashed_user_id]

        # Extract concepts
        words = user_input.lower().split()
        concepts = [w for w in words if len(w) > 5]

        # Update concept frequency
        for concept in concepts:
            baseline.concept_frequency[concept] = baseline.concept_frequency.get(concept, 0) + 1

        # Prune to top 1000 concepts for memory efficiency
        if len(baseline.concept_frequency) > 1000:
            sorted_concepts = sorted(
                baseline.concept_frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )
            baseline.concept_frequency = dict(sorted_concepts[:1000])

        baseline.sample_count += 1

        # Persist baseline
        await self._persist_baseline(baseline)

    async def _persist_baseline(self, baseline: SemanticBaseline) -> None:
        """
        Persist baseline to LOCAL storage only.

        **PRIVACY:** Never transmitted, only stored locally.
        """
        filename = f"rdi_baseline_{baseline.user_id}.json"
        filepath = self.storage_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "user_id": baseline.user_id,
                    "concept_frequency": baseline.concept_frequency,
                    "relationship_patterns": baseline.relationship_patterns,
                    "vocabulary_centroid": baseline.vocabulary_centroid,
                    "reasoning_pattern_signature": baseline.reasoning_pattern_signature,
                    "established_at": baseline.established_at.isoformat(),
                    "sample_count": baseline.sample_count
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist baseline: {e}")

    def calculate_rdi_score(
        self,
        user_id: str,
        lookback_days: int = 30
    ) -> RDIScore:
        """
        Calculate RDI score for a user.

        **PRIVACY:** This score is PRIVATE and LOCAL ONLY.
        It is shown only to the user on their private dashboard.

        Args:
            user_id: User (hashed internally)
            lookback_days: Lookback window

        Returns:
            RDIScore (marked as private)
        """
        hashed_user_id = self._hash_user_id(user_id)

        logger.info(f"Calculating RDI score (lookback={lookback_days} days)")

        # Get recent drift signals
        cutoff = datetime.now() - timedelta(days=lookback_days)
        signals = self._local_drift_signals.get(hashed_user_id, [])
        recent_signals = [s for s in signals if s.timestamp >= cutoff]

        if not recent_signals:
            # No drift detected
            score = RDIScore(
                user_id=hashed_user_id,
                timestamp=datetime.now(),
                overall_rdi=0.0,
                rdi_level=RDILevel.ALIGNED,
                semantic_drift=0.0,
                factual_drift=0.0,
                logical_drift=0.0,
                trend_direction="stable",
                days_in_trend=0,
                private_alerts=[]
            )
        else:
            # Calculate component scores
            semantic_drifts = [s.drift_magnitude for s in recent_signals if s.drift_type == DriftType.SEMANTIC]
            factual_drifts = [s.drift_magnitude for s in recent_signals if s.drift_type == DriftType.FACTUAL]
            logical_drifts = [s.drift_magnitude for s in recent_signals if s.drift_type == DriftType.LOGICAL]

            semantic_drift = sum(semantic_drifts) / len(semantic_drifts) if semantic_drifts else 0.0
            factual_drift = sum(factual_drifts) / len(factual_drifts) if factual_drifts else 0.0
            logical_drift = sum(logical_drifts) / len(logical_drifts) if logical_drifts else 0.0

            # Calculate overall RDI
            overall_rdi = (
                0.4 * semantic_drift +
                0.4 * factual_drift +
                0.2 * logical_drift
            )

            # Determine level
            if overall_rdi >= 0.8:
                level = RDILevel.CRITICAL_DRIFT
            elif overall_rdi >= 0.6:
                level = RDILevel.SIGNIFICANT_DRIFT
            elif overall_rdi >= 0.4:
                level = RDILevel.MODERATE_DRIFT
            elif overall_rdi >= 0.2:
                level = RDILevel.MINOR_DRIFT
            else:
                level = RDILevel.ALIGNED

            # Generate private alerts
            alerts = []
            if level == RDILevel.CRITICAL_DRIFT:
                alerts.append("⚠️ CRITICAL: Significant reality drift detected")
            elif level == RDILevel.SIGNIFICANT_DRIFT:
                alerts.append("⚠️ Notable divergence from consensus reality detected")
            elif level == RDILevel.MODERATE_DRIFT:
                alerts.append("ℹ️ Moderate reality drift detected")

            # Determine trend
            hist_scores = self._local_rdi_scores.get(hashed_user_id, [])
            if len(hist_scores) >= 3:
                recent = hist_scores[-3:]
                early_avg = recent[0].overall_rdi
                late_avg = sum(s.overall_rdi for s in recent[-2:]) / 2

                if late_avg > early_avg + 0.1:
                    trend = "increasing"
                elif late_avg < early_avg - 0.1:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "stable"

            score = RDIScore(
                user_id=hashed_user_id,
                timestamp=datetime.now(),
                overall_rdi=overall_rdi,
                rdi_level=level,
                semantic_drift=semantic_drift,
                factual_drift=factual_drift,
                logical_drift=logical_drift,
                trend_direction=trend,
                days_in_trend=lookback_days,
                private_alerts=alerts
            )

        # Store score locally
        if hashed_user_id not in self._local_rdi_scores:
            self._local_rdi_scores[hashed_user_id] = []
        self._local_rdi_scores[hashed_user_id].append(score)

        # Persist score locally
        asyncio.create_task(self._persist_rdi_score(score))

        logger.info(
            f"RDI score calculated: {score.overall_rdi:.3f} ({score.rdi_level.value})"
        )

        return score

    async def _persist_rdi_score(self, score: RDIScore) -> None:
        """
        Persist RDI score to LOCAL storage only.

        **PRIVACY:** Never transmitted.
        """
        filename = f"rdi_score_{score.user_id}_{score.timestamp.isoformat()}.json"
        filepath = self.storage_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump({
                    "user_id": score.user_id,
                    "timestamp": score.timestamp.isoformat(),
                    "overall_rdi": score.overall_rdi,
                    "rdi_level": score.rdi_level.value,
                    "semantic_drift": score.semantic_drift,
                    "factual_drift": score.factual_drift,
                    "logical_drift": score.logical_drift,
                    "trend_direction": score.trend_direction,
                    "days_in_trend": score.days_in_trend,
                    "private_alerts": score.private_alerts,
                    "_privacy_marker": "LOCAL_ONLY_NEVER_TRANSMIT"
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist RDI score: {e}")

    def get_user_rdi_for_dashboard(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get RDI data for user's PRIVATE dashboard.

        **PRIVACY:** This data is shown only to the user themselves.
        Never shared with anyone else.

        Args:
            user_id: User requesting their own data

        Returns:
            Dict with RDI data for dashboard display
        """
        hashed_user_id = self._hash_user_id(user_id)

        scores = self._local_rdi_scores.get(hashed_user_id, [])
        if not scores:
            return {
                "rdi_available": False,
                "message": "No RDI data yet. Keep using the system to establish baseline."
            }

        latest_score = scores[-1]

        return {
            "rdi_available": True,
            "current_rdi": latest_score.overall_rdi,
            "rdi_level": latest_score.rdi_level.value,
            "semantic_drift": latest_score.semantic_drift,
            "factual_drift": latest_score.factual_drift,
            "logical_drift": latest_score.logical_drift,
            "trend": latest_score.trend_direction,
            "alerts": latest_score.private_alerts,
            "history": [
                {
                    "timestamp": s.timestamp.isoformat(),
                    "rdi": s.overall_rdi,
                    "level": s.rdi_level.value
                }
                for s in scores[-30:]  # Last 30 measurements
            ],
            "_privacy_notice": "This data is private and stored only on your device."
        }

    def opt_in_to_aggregate_sharing(self, user_id: str) -> bool:
        """
        Opt user in to ANONYMIZED aggregate sharing.

        **PRIVACY:** User must explicitly consent.
        Even with opt-in, only anonymized aggregates are shared (minimum 100 users).

        Args:
            user_id: User opting in

        Returns:
            True if opt-in successful
        """
        hashed_user_id = self._hash_user_id(user_id)

        self._aggregate_opt_ins.add(hashed_user_id)

        logger.info(f"User opted in to anonymized aggregate sharing")

        return True

    def generate_anonymized_aggregate(
        self
    ) -> Optional[AnonymizedRDIStats]:
        """
        Generate anonymized aggregate statistics.

        **PRIVACY CRITICAL:**
        - Requires minimum 100 opted-in users
        - No individual user data
        - Complete anonymization
        - PII scrubbed

        Returns:
            AnonymizedRDIStats if privacy threshold met, else None
        """
        # Filter to opted-in users only
        opted_in_scores = {
            user_id: scores
            for user_id, scores in self._local_rdi_scores.items()
            if user_id in self._aggregate_opt_ins
        }

        if len(opted_in_scores) < 100:
            logger.warning(
                f"Cannot generate aggregate: Only {len(opted_in_scores)} opted-in users "
                "(minimum 100 required for privacy)"
            )
            return None

        # Calculate aggregates
        all_scores = [
            scores[-1].overall_rdi
            for scores in opted_in_scores.values()
            if scores
        ]

        if not all_scores:
            return None

        avg_rdi = sum(all_scores) / len(all_scores)
        sorted_scores = sorted(all_scores)
        median_rdi = sorted_scores[len(sorted_scores) // 2]

        # Calculate std dev
        variance = sum((x - avg_rdi) ** 2 for x in all_scores) / len(all_scores)
        std_dev_rdi = variance ** 0.5

        # Distribution
        distribution = {
            "aligned": len([s for s in all_scores if s < 0.2]),
            "minor_drift": len([s for s in all_scores if 0.2 <= s < 0.4]),
            "moderate_drift": len([s for s in all_scores if 0.4 <= s < 0.6]),
            "significant_drift": len([s for s in all_scores if 0.6 <= s < 0.8]),
            "critical_drift": len([s for s in all_scores if s >= 0.8]),
        }

        # Trends
        increasing = len([
            scores for scores in opted_in_scores.values()
            if scores and len(scores) >= 2 and scores[-1].overall_rdi > scores[-2].overall_rdi
        ])
        stable = len([
            scores for scores in opted_in_scores.values()
            if scores and len(scores) >= 2 and abs(scores[-1].overall_rdi - scores[-2].overall_rdi) < 0.1
        ])
        decreasing = len(opted_in_scores) - increasing - stable

        total = max(1, len(opted_in_scores))
        trend_summary = {
            "increasing": increasing / total,
            "stable": stable / total,
            "decreasing": decreasing / total
        }

        stats = AnonymizedRDIStats(
            stats_id=f"aggregate_{datetime.now().isoformat()}",
            collection_period=f"{datetime.now() - timedelta(days=30)} to {datetime.now()}",
            total_users=len(opted_in_scores),
            average_rdi=avg_rdi,
            median_rdi=median_rdi,
            std_dev_rdi=std_dev_rdi,
            rdi_distribution=distribution,
            trend_summary=trend_summary,
            anonymization_applied=True,
            minimum_user_threshold_met=True,
            pii_scrubbed=True
        )

        logger.info(
            f"Generated anonymized aggregate from {stats.total_users} users "
            f"(avg RDI: {avg_rdi:.3f})"
        )

        return stats
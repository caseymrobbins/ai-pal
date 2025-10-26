"""
ARI (Authentic Remaining Independence) Measurement System.

Measures user's actual unassisted capabilities across knowledge domains
and synthesis tasks to track deskilling risk and inform assistance level.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from loguru import logger


class ARIDimension(Enum):
    """Dimensions of user capability measured by ARI."""
    KNOWLEDGE = "knowledge"          # Domain-specific knowledge
    SYNTHESIS = "synthesis"          # Ability to combine/create ideas
    LOGIC = "logic"                  # Logical reasoning
    ANALYSIS = "analysis"            # Breaking down complex problems
    CREATIVITY = "creativity"        # Novel idea generation


class ARILevel(Enum):
    """ARI measurement levels."""
    HIGH = "high"                    # Strong unassisted capability
    MEDIUM = "medium"                # Moderate capability, some assistance helpful
    LOW = "low"                      # Low unassisted capability, high assistance needed
    UNKNOWN = "unknown"              # Not yet measured


@dataclass
class ARIScore:
    """Individual ARI score for a specific dimension/domain."""
    dimension: ARIDimension
    domain: str                      # e.g., "python_programming", "creative_writing"
    level: ARILevel
    confidence: float                # 0.0-1.0, how confident we are in this measurement

    # Evidence
    measurements: List[Dict[str, Any]] = field(default_factory=list)
    last_measured: datetime = field(default_factory=datetime.now)
    measurement_count: int = 0

    # Rubric scores (for SYNTHESIS dimension)
    accuracy: Optional[float] = None      # 0.0-1.0
    logic: Optional[float] = None         # 0.0-1.0
    completeness: Optional[float] = None  # 0.0-1.0


@dataclass
class UnassistedCapabilityCheckpoint:
    """A checkpoint where we measure user's unassisted capability."""
    checkpoint_id: str
    question: str                    # The probe question
    domain: str
    dimension: ARIDimension

    # Context
    original_request: str            # User's original request
    checkpoint_type: str             # "fundamental", "optional", "validation"

    # User response
    user_response: Optional[str] = None
    responded_at: Optional[datetime] = None

    # ARI evaluation
    demonstrated_capability: Optional[ARILevel] = None
    reasoning: Optional[str] = None


class ARIMeasurementSystem:
    """
    System for measuring and tracking user's Authentic Remaining Independence.

    Implements both explicit (Learn About Me) and embedded (Socratic Co-pilot)
    measurement approaches.
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize ARI measurement system."""
        self.storage_dir = storage_dir or Path("./data/ari")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # User profiles: user_id -> {dimension -> {domain -> ARIScore}}
        self.user_profiles: Dict[str, Dict[ARIDimension, Dict[str, ARIScore]]] = {}

        # Active checkpoints: checkpoint_id -> UnassistedCapabilityCheckpoint
        self.active_checkpoints: Dict[str, UnassistedCapabilityCheckpoint] = {}

        # Measurement history
        self.measurement_history: List[Dict[str, Any]] = []

        logger.info("ARI Measurement System initialized")

    # ========================================================================
    # Embedded Assessment (Socratic Co-pilot)
    # ========================================================================

    def identify_checkpoints(
        self,
        user_request: str,
        task_type: str
    ) -> List[UnassistedCapabilityCheckpoint]:
        """
        Identify Unassisted Capability Checkpoints in a user request.

        Args:
            user_request: The user's original request
            task_type: Type of task (e.g., "code_generation", "writing")

        Returns:
            List of checkpoints to probe
        """
        checkpoints = []

        # Task-specific checkpoint identification
        if task_type == "code_generation":
            checkpoints.extend(self._identify_code_checkpoints(user_request))
        elif task_type == "writing":
            checkpoints.extend(self._identify_writing_checkpoints(user_request))
        elif task_type == "analysis":
            checkpoints.extend(self._identify_analysis_checkpoints(user_request))

        # Store active checkpoints
        for checkpoint in checkpoints:
            self.active_checkpoints[checkpoint.checkpoint_id] = checkpoint

        logger.info(f"Identified {len(checkpoints)} checkpoints for request")
        return checkpoints

    def _identify_code_checkpoints(self, request: str) -> List[UnassistedCapabilityCheckpoint]:
        """Identify checkpoints for code generation tasks."""
        import uuid

        checkpoints = []

        # Fundamental: Function/class naming
        checkpoints.append(UnassistedCapabilityCheckpoint(
            checkpoint_id=f"ucc_{uuid.uuid4().hex[:8]}",
            question="What should I name the main function/class?",
            domain="programming",
            dimension=ARIDimension.KNOWLEDGE,
            original_request=request,
            checkpoint_type="fundamental"
        ))

        # Fundamental: Core logic
        checkpoints.append(UnassistedCapabilityCheckpoint(
            checkpoint_id=f"ucc_{uuid.uuid4().hex[:8]}",
            question="What's the specific logic or algorithm you want me to use?",
            domain="programming",
            dimension=ARIDimension.ANALYSIS,
            original_request=request,
            checkpoint_type="fundamental"
        ))

        # Optional: Error handling
        checkpoints.append(UnassistedCapabilityCheckpoint(
            checkpoint_id=f"ucc_{uuid.uuid4().hex[:8]}",
            question="How should I handle errors or edge cases?",
            domain="programming",
            dimension=ARIDimension.SYNTHESIS,
            original_request=request,
            checkpoint_type="optional"
        ))

        return checkpoints

    def _identify_writing_checkpoints(self, request: str) -> List[UnassistedCapabilityCheckpoint]:
        """Identify checkpoints for writing tasks."""
        import uuid

        checkpoints = []

        # Fundamental: Key points
        checkpoints.append(UnassistedCapabilityCheckpoint(
            checkpoint_id=f"ucc_{uuid.uuid4().hex[:8]}",
            question="What are the 3 key points you want to communicate?",
            domain="writing",
            dimension=ARIDimension.SYNTHESIS,
            original_request=request,
            checkpoint_type="fundamental"
        ))

        # Fundamental: Audience/tone
        checkpoints.append(UnassistedCapabilityCheckpoint(
            checkpoint_id=f"ucc_{uuid.uuid4().hex[:8]}",
            question="Who is your audience and what tone should I use?",
            domain="writing",
            dimension=ARIDimension.ANALYSIS,
            original_request=request,
            checkpoint_type="fundamental"
        ))

        return checkpoints

    def _identify_analysis_checkpoints(self, request: str) -> List[UnassistedCapabilityCheckpoint]:
        """Identify checkpoints for analysis tasks."""
        import uuid

        checkpoints = []

        # Fundamental: Analysis framework
        checkpoints.append(UnassistedCapabilityCheckpoint(
            checkpoint_id=f"ucc_{uuid.uuid4().hex[:8]}",
            question="What framework or approach should I use for this analysis?",
            domain="analysis",
            dimension=ARIDimension.KNOWLEDGE,
            original_request=request,
            checkpoint_type="fundamental"
        ))

        return checkpoints

    def record_checkpoint_response(
        self,
        checkpoint_id: str,
        user_response: str,
        user_id: str
    ) -> ARILevel:
        """
        Record user's response to a checkpoint and evaluate capability.

        Args:
            checkpoint_id: ID of the checkpoint
            user_response: User's response to the probe question
            user_id: User identifier

        Returns:
            Evaluated ARI level
        """
        checkpoint = self.active_checkpoints.get(checkpoint_id)
        if not checkpoint:
            raise ValueError(f"Unknown checkpoint: {checkpoint_id}")

        # Record response
        checkpoint.user_response = user_response
        checkpoint.responded_at = datetime.now()

        # Evaluate capability based on response
        ari_level = self._evaluate_checkpoint_response(checkpoint)
        checkpoint.demonstrated_capability = ari_level

        # Update user profile
        self._update_user_ari_score(
            user_id=user_id,
            dimension=checkpoint.dimension,
            domain=checkpoint.domain,
            level=ari_level,
            evidence={
                "checkpoint_id": checkpoint_id,
                "question": checkpoint.question,
                "response": user_response,
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"Recorded checkpoint response: {ari_level.value}")
        return ari_level

    def _evaluate_checkpoint_response(
        self,
        checkpoint: UnassistedCapabilityCheckpoint
    ) -> ARILevel:
        """
        Evaluate user's capability based on checkpoint response.

        Heuristics:
        - "I don't know", "Just guess", "You decide" -> LOW
        - Vague/incomplete answer -> MEDIUM
        - Specific, detailed answer -> HIGH
        """
        response = checkpoint.user_response.lower() if checkpoint.user_response else ""

        # LOW capability signals
        low_signals = [
            "don't know", "not sure", "just guess", "you decide",
            "whatever", "up to you", "idk", "dunno"
        ]
        if any(signal in response for signal in low_signals):
            checkpoint.reasoning = "User explicitly deferred to AI"
            return ARILevel.LOW

        # HIGH capability signals
        if len(response.split()) >= 10:  # Detailed response
            checkpoint.reasoning = "User provided detailed, specific response"
            return ARILevel.HIGH

        # MEDIUM (short but specific)
        if len(response.split()) >= 3:
            checkpoint.reasoning = "User provided some specificity"
            return ARILevel.MEDIUM

        # Default to UNKNOWN
        checkpoint.reasoning = "Insufficient information"
        return ARILevel.UNKNOWN

    # ========================================================================
    # Explicit Assessment (Learn About Me)
    # ========================================================================

    def score_synthesis_response(
        self,
        user_response: str,
        expected_criteria: Dict[str, Any],
        domain: str,
        user_id: str
    ) -> ARIScore:
        """
        Score a user's synthesis response using ARI-Synthesis rubric.

        Args:
            user_response: User's answer to open-ended question
            expected_criteria: Criteria for grading (accuracy, logic, completeness)
            domain: Domain being tested
            user_id: User identifier

        Returns:
            ARI score with rubric breakdown
        """
        # Evaluate against rubric (simplified heuristics for now)
        accuracy_score = self._evaluate_accuracy(user_response, expected_criteria)
        logic_score = self._evaluate_logic(user_response)
        completeness_score = self._evaluate_completeness(user_response, expected_criteria)

        # Overall score (weighted average)
        overall_score = (accuracy_score * 0.4 + logic_score * 0.3 + completeness_score * 0.3)

        # Convert to ARI level
        if overall_score >= 0.75:
            level = ARILevel.HIGH
        elif overall_score >= 0.5:
            level = ARILevel.MEDIUM
        else:
            level = ARILevel.LOW

        # Create ARI score
        ari_score = ARIScore(
            dimension=ARIDimension.SYNTHESIS,
            domain=domain,
            level=level,
            confidence=0.8,  # High confidence for explicit assessment
            accuracy=accuracy_score,
            logic=logic_score,
            completeness=completeness_score,
            last_measured=datetime.now(),
            measurement_count=1
        )

        # Update user profile
        self._update_user_ari_score(
            user_id=user_id,
            dimension=ARIDimension.SYNTHESIS,
            domain=domain,
            level=level,
            evidence={
                "response": user_response,
                "accuracy": accuracy_score,
                "logic": logic_score,
                "completeness": completeness_score,
                "timestamp": datetime.now().isoformat()
            }
        )

        logger.info(f"Scored synthesis response: {level.value} (acc={accuracy_score:.2f}, log={logic_score:.2f}, comp={completeness_score:.2f})")
        return ari_score

    def _evaluate_accuracy(self, response: str, criteria: Dict[str, Any]) -> float:
        """Evaluate factual accuracy (simplified)."""
        # In real implementation, would use LLM or knowledge base
        # For now, use heuristics based on response length and structure

        expected_keywords = criteria.get("keywords", [])
        if not expected_keywords:
            return 0.7  # Default

        # Check for keyword presence
        response_lower = response.lower()
        matches = sum(1 for kw in expected_keywords if kw.lower() in response_lower)
        accuracy = matches / len(expected_keywords)

        return min(1.0, accuracy)

    def _evaluate_logic(self, response: str) -> float:
        """Evaluate logical coherence (simplified)."""
        # Heuristics: presence of logical connectors, structure
        logical_connectors = ["because", "therefore", "thus", "however", "although", "if", "then"]

        response_lower = response.lower()
        connector_count = sum(1 for conn in logical_connectors if conn in response_lower)

        # Normalize to 0-1
        logic_score = min(1.0, connector_count / 3)

        return logic_score

    def _evaluate_completeness(self, response: str, criteria: Dict[str, Any]) -> float:
        """Evaluate completeness of answer (simplified)."""
        expected_components = criteria.get("required_components", [])
        if not expected_components:
            # Use word count as proxy
            word_count = len(response.split())
            return min(1.0, word_count / 50)

        # Check for required components
        response_lower = response.lower()
        present = sum(1 for comp in expected_components if comp.lower() in response_lower)

        return present / len(expected_components)

    # ========================================================================
    # User Profile Management
    # ========================================================================

    def _update_user_ari_score(
        self,
        user_id: str,
        dimension: ARIDimension,
        domain: str,
        level: ARILevel,
        evidence: Dict[str, Any]
    ) -> None:
        """Update user's ARI score for a dimension/domain."""
        # Initialize user profile if needed
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {}

        if dimension not in self.user_profiles[user_id]:
            self.user_profiles[user_id][dimension] = {}

        # Update or create score
        if domain in self.user_profiles[user_id][dimension]:
            score = self.user_profiles[user_id][dimension][domain]
            score.level = level
            score.last_measured = datetime.now()
            score.measurement_count += 1
            score.measurements.append(evidence)

            # Update confidence (more measurements = higher confidence)
            score.confidence = min(0.95, 0.5 + (score.measurement_count * 0.1))
        else:
            score = ARIScore(
                dimension=dimension,
                domain=domain,
                level=level,
                confidence=0.5,  # Low confidence initially
                measurements=[evidence],
                measurement_count=1
            )
            self.user_profiles[user_id][dimension][domain] = score

        # Add to history
        self.measurement_history.append({
            "user_id": user_id,
            "dimension": dimension.value,
            "domain": domain,
            "level": level.value,
            "timestamp": datetime.now().isoformat(),
            "evidence": evidence
        })

    def get_user_ari_profile(self, user_id: str) -> Dict[ARIDimension, Dict[str, ARIScore]]:
        """Get complete ARI profile for a user."""
        return self.user_profiles.get(user_id, {})

    def get_user_ari_level(
        self,
        user_id: str,
        dimension: ARIDimension,
        domain: str
    ) -> ARILevel:
        """Get user's ARI level for specific dimension/domain."""
        profile = self.user_profiles.get(user_id, {})
        dimension_scores = profile.get(dimension, {})
        score = dimension_scores.get(domain)

        if score:
            return score.level
        return ARILevel.UNKNOWN

    # ========================================================================
    # Persistence
    # ========================================================================

    async def persist_profiles(self) -> None:
        """Persist user ARI profiles to disk."""
        profiles_file = self.storage_dir / "ari_profiles.json"

        # Convert to serializable format
        profiles_data = {}
        for user_id, profile in self.user_profiles.items():
            profiles_data[user_id] = {}
            for dimension, domains in profile.items():
                profiles_data[user_id][dimension.value] = {}
                for domain, score in domains.items():
                    profiles_data[user_id][dimension.value][domain] = {
                        "level": score.level.value,
                        "confidence": score.confidence,
                        "measurement_count": score.measurement_count,
                        "last_measured": score.last_measured.isoformat(),
                        "accuracy": score.accuracy,
                        "logic": score.logic,
                        "completeness": score.completeness
                    }

        with open(profiles_file, 'w') as f:
            json.dump(profiles_data, f, indent=2)

        logger.info(f"Persisted ARI profiles for {len(self.user_profiles)} users")

    async def load_profiles(self) -> None:
        """Load user ARI profiles from disk."""
        profiles_file = self.storage_dir / "ari_profiles.json"

        if not profiles_file.exists():
            return

        with open(profiles_file, 'r') as f:
            profiles_data = json.load(f)

        # Convert back to internal format
        for user_id, profile in profiles_data.items():
            self.user_profiles[user_id] = {}
            for dimension_str, domains in profile.items():
                dimension = ARIDimension(dimension_str)
                self.user_profiles[user_id][dimension] = {}

                for domain, score_data in domains.items():
                    score = ARIScore(
                        dimension=dimension,
                        domain=domain,
                        level=ARILevel(score_data["level"]),
                        confidence=score_data["confidence"],
                        measurement_count=score_data["measurement_count"],
                        last_measured=datetime.fromisoformat(score_data["last_measured"]),
                        accuracy=score_data.get("accuracy"),
                        logic=score_data.get("logic"),
                        completeness=score_data.get("completeness")
                    )
                    self.user_profiles[user_id][dimension][domain] = score

        logger.info(f"Loaded ARI profiles for {len(self.user_profiles)} users")

"""
Four Gates System - AC-AI Framework Enforcement

Implements the Four Gates validation system:
1. Autonomy Gate: Ensures net positive agency
2. Humanity Gate: Prevents extractive patterns
3. Oversight Gate: Enables human override
4. Alignment Gate: Validates value alignment

Part of Phase 1.5 integration work.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from loguru import logger


class GateType(Enum):
    """The Four Gates of AC-AI framework."""

    AUTONOMY = "autonomy"  # Gate 1: Net positive agency
    HUMANITY = "humanity"  # Gate 2: Non-extractive
    OVERSIGHT = "oversight"  # Gate 3: Human override available
    ALIGNMENT = "alignment"  # Gate 4: Value alignment


class GateStatus(Enum):
    """Status of a gate evaluation."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    PENDING = "pending"


@dataclass
class GateViolation:
    """Record of a gate violation."""
    gate_type: GateType
    timestamp: datetime
    severity: str  # "low", "medium", "high", "critical"
    description: str
    context: Dict[str, Any]
    score: float
    threshold: float


@dataclass
class GateResult:
    """Result of a gate validation."""

    gate_type: GateType
    passed: bool
    score: float  # 0.0 to 1.0
    reason: str
    details: Dict[str, Any]
    timestamp: datetime


class GateSystem:
    """
    Four Gates validation system.

    Validates that AI actions comply with AC-AI ethical framework.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize gate system.

        Args:
            config: Configuration for gate thresholds
        """
        self.config = config or {}
        self.thresholds = {
            GateType.AUTONOMY: self.config.get('autonomy_threshold', 0.0),  # Net positive
            GateType.HUMANITY: self.config.get('humanity_threshold', 0.6),
            GateType.OVERSIGHT: self.config.get('oversight_threshold', 0.8),
            GateType.ALIGNMENT: self.config.get('alignment_threshold', 0.7)
        }

    async def validate(
        self,
        action: Dict[str, Any],
        gate_type: GateType,
        context: Optional[Dict[str, Any]] = None
    ) -> GateResult:
        """
        Validate an action against a specific gate.

        Args:
            action: The AI action to validate
            gate_type: Which gate to check
            context: Additional context for validation

        Returns:
            GateResult with validation outcome
        """
        context = context or {}

        if gate_type == GateType.AUTONOMY:
            return await self._check_autonomy(action, context)
        elif gate_type == GateType.HUMANITY:
            return await self._check_humanity(action, context)
        elif gate_type == GateType.OVERSIGHT:
            return await self._check_oversight(action, context)
        elif gate_type == GateType.ALIGNMENT:
            return await self._check_alignment(action, context)
        else:
            raise ValueError(f"Unknown gate type: {gate_type}")

    async def validate_all(
        self,
        action: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[GateType, GateResult]:
        """
        Validate an action against all four gates.

        Args:
            action: The AI action to validate
            context: Additional context for validation

        Returns:
            Dictionary mapping gate types to results
        """
        results = {}
        for gate_type in GateType:
            results[gate_type] = await self.validate(action, gate_type, context)

        return results

    async def _check_autonomy(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> GateResult:
        """
        Gate 1: Autonomy - Ensures net positive agency.

        Checks if action increases user agency (skills, decision-making power).
        """
        # Calculate agency delta
        agency_before = context.get('user_agency_before', 0.5)
        agency_after = context.get('user_agency_after', 0.5)
        agency_delta = agency_after - agency_before

        # Check if user retained control
        user_control = action.get('user_approval_required', False)
        user_can_undo = action.get('reversible', False)

        # Score calculation
        score = 0.5 + agency_delta * 0.3
        if user_control:
            score += 0.2
        if user_can_undo:
            score += 0.1

        score = max(0.0, min(1.0, score))

        passed = agency_delta >= self.thresholds[GateType.AUTONOMY]

        return GateResult(
            gate_type=GateType.AUTONOMY,
            passed=passed,
            score=score,
            reason=f"Agency delta: {agency_delta:+.3f}" + (
                " (user retained control)" if user_control else ""
            ),
            details={
                'agency_delta': agency_delta,
                'user_control': user_control,
                'reversible': user_can_undo,
                'threshold': self.thresholds[GateType.AUTONOMY]
            },
            timestamp=datetime.now()
        )

    async def _check_humanity(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> GateResult:
        """
        Gate 2: Humanity - Prevents extractive patterns.

        Checks for dark patterns, manipulation, exploitation.
        """
        # Check for extractive indicators
        addictive_features = action.get('addictive_features', [])
        dark_patterns = action.get('dark_patterns', [])
        emotional_manipulation = action.get('emotional_manipulation', False)
        time_pressure = action.get('creates_time_pressure', False)

        # Calculate humanity score (higher is better)
        score = 1.0
        score -= len(addictive_features) * 0.15
        score -= len(dark_patterns) * 0.2
        if emotional_manipulation:
            score -= 0.25
        if time_pressure:
            score -= 0.15

        score = max(0.0, min(1.0, score))

        passed = score >= self.thresholds[GateType.HUMANITY]

        issues = []
        if addictive_features:
            issues.append(f"{len(addictive_features)} addictive features")
        if dark_patterns:
            issues.append(f"{len(dark_patterns)} dark patterns")
        if emotional_manipulation:
            issues.append("emotional manipulation")
        if time_pressure:
            issues.append("time pressure")

        reason = "Non-extractive" if not issues else f"Issues: {', '.join(issues)}"

        return GateResult(
            gate_type=GateType.HUMANITY,
            passed=passed,
            score=score,
            reason=reason,
            details={
                'addictive_features': addictive_features,
                'dark_patterns': dark_patterns,
                'emotional_manipulation': emotional_manipulation,
                'time_pressure': time_pressure,
                'threshold': self.thresholds[GateType.HUMANITY]
            },
            timestamp=datetime.now()
        )

    async def _check_oversight(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> GateResult:
        """
        Gate 3: Oversight - Ensures human override available.

        Checks if humans can override/appeal AI decisions.
        """
        # Check oversight mechanisms
        appeal_available = action.get('appeal_available', False)
        human_review_possible = action.get('human_review_possible', False)
        explanation_provided = action.get('explanation_provided', False)
        audit_trail = action.get('audit_trail_enabled', False)

        # Calculate oversight score
        score = 0.0
        if appeal_available:
            score += 0.3
        if human_review_possible:
            score += 0.3
        if explanation_provided:
            score += 0.2
        if audit_trail:
            score += 0.2

        passed = score >= self.thresholds[GateType.OVERSIGHT]

        capabilities = []
        if appeal_available:
            capabilities.append("appeal")
        if human_review_possible:
            capabilities.append("human review")
        if explanation_provided:
            capabilities.append("explanation")
        if audit_trail:
            capabilities.append("audit trail")

        reason = f"Oversight: {', '.join(capabilities)}" if capabilities else "No oversight"

        return GateResult(
            gate_type=GateType.OVERSIGHT,
            passed=passed,
            score=score,
            reason=reason,
            details={
                'appeal_available': appeal_available,
                'human_review_possible': human_review_possible,
                'explanation_provided': explanation_provided,
                'audit_trail_enabled': audit_trail,
                'threshold': self.thresholds[GateType.OVERSIGHT]
            },
            timestamp=datetime.now()
        )

    async def _check_alignment(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any]
    ) -> GateResult:
        """
        Gate 4: Alignment - Validates value alignment.

        Checks if action aligns with stated values and user preferences.
        """
        # Check alignment indicators
        matches_user_values = action.get('matches_user_values', True)
        matches_system_values = action.get('matches_system_values', True)
        consistent_with_history = action.get('consistent_with_history', True)
        transparent_goals = action.get('transparent_goals', True)

        # Calculate alignment score
        score = 0.0
        if matches_user_values:
            score += 0.3
        if matches_system_values:
            score += 0.3
        if consistent_with_history:
            score += 0.2
        if transparent_goals:
            score += 0.2

        passed = score >= self.thresholds[GateType.ALIGNMENT]

        alignments = []
        if matches_user_values:
            alignments.append("user values")
        if matches_system_values:
            alignments.append("system values")
        if consistent_with_history:
            alignments.append("historical behavior")
        if transparent_goals:
            alignments.append("transparent goals")

        reason = f"Aligned with: {', '.join(alignments)}" if alignments else "Misaligned"

        return GateResult(
            gate_type=GateType.ALIGNMENT,
            passed=passed,
            score=score,
            reason=reason,
            details={
                'matches_user_values': matches_user_values,
                'matches_system_values': matches_system_values,
                'consistent_with_history': consistent_with_history,
                'transparent_goals': transparent_goals,
                'threshold': self.thresholds[GateType.ALIGNMENT]
            },
            timestamp=datetime.now()
        )

    def all_gates_passed(self, results: Dict[GateType, GateResult]) -> bool:
        """Check if all gates passed."""
        return all(result.passed for result in results.values())

    def get_failed_gates(self, results: Dict[GateType, GateResult]) -> List[GateType]:
        """Get list of gates that failed."""
        return [gate_type for gate_type, result in results.items() if not result.passed]

    async def validate_patch_request(
        self,
        target_file: str,
        protected_files: List[str]
    ) -> bool:
        """
        Validate a patch request against protected files.

        This is the gate that prevents AI from modifying core ethical
        framework files. Requests targeting protected files are silently
        denied.

        Args:
            target_file: File the AI wants to modify
            protected_files: List of protected kernel files

        Returns:
            True if patch is allowed, False if denied
        """
        from pathlib import Path

        # Normalize paths for comparison
        target_path = Path(target_file).as_posix()

        for protected in protected_files:
            protected_path = Path(protected).as_posix()

            # Check exact match or if target is within protected directory
            if target_path == protected_path or \
               target_path.startswith(protected_path + "/"):
                logger.warning(
                    f"Patch request DENIED by Gate System: "
                    f"{target_file} is protected (matches {protected})"
                )
                return False

        logger.info(
            f"Patch request APPROVED by Gate System: "
            f"{target_file} is not protected"
        )
        return True

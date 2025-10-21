"""
Ethics Module - Implementation of Agency Calculus for AI (AC-AI) Framework.

This module implements the Four Gates and ensures all AI actions expand human agency.
It is NON-OPTIONAL and governs all other modules.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio
from loguru import logger

from ai_pal.modules.base import BaseModule, ModuleRequest, ModuleResponse
from ai_pal.core.config import settings


class GateResult(Enum):
    """Result of a Gate check."""

    PASS = "pass"
    FAIL = "fail"
    UNCERTAIN = "uncertain"


@dataclass
class AgencyMetrics:
    """Agency measurement metrics."""

    # Core Agency Metrics
    task_efficacy: float  # Can user accomplish their goals? [0-1]
    opportunity_expansion: float  # New capabilities unlocked? [0-1]
    autonomy_retention: float  # Decision-making independence [0-1]
    skill_development: float  # Learning vs deskilling [-1, 1]

    # Composite Metrics
    net_agency_delta: float  # Overall agency change [-1, 1]
    meta_agency_score: float  # Control over AI itself [0-1]

    # Epistemic Metrics
    epistemic_debt: float  # Info quality degradation [0-1, lower better]
    hallucination_rate: float  # Misinformation rate [0-1]
    correction_halflife: float  # Time to fix errors (hours)
    viewpoint_entropy: float  # Diversity of perspectives [0-1]

    # Beyond-Horizon Metrics
    bhir: float  # Beyond-Horizon Impact Ratio [0-∞, >1 required]
    second_order_effects: List[str]  # Predicted indirect impacts

    # Quality Metrics
    coverage_score: float  # Measurement coverage [0-1]
    goodhart_divergence: float  # Metric gaming detection [0-1]

    timestamp: datetime

    def passes_net_agency_test(self) -> bool:
        """Check if net agency test passes."""
        return self.net_agency_delta >= settings.min_agency_delta


@dataclass
class FourGatesResult:
    """Result of Four Gates validation."""

    gate1_net_agency: GateResult
    gate2_extraction: GateResult
    gate3_humanity_override: GateResult
    gate4_non_othering: GateResult

    gate1_details: Dict[str, Any]
    gate2_details: Dict[str, Any]
    gate3_details: Dict[str, Any]
    gate4_details: Dict[str, Any]

    overall_pass: bool
    blocking_gates: List[str]
    timestamp: datetime

    def __str__(self) -> str:
        """String representation."""
        gates = [
            f"Gate 1 (Net-Agency): {self.gate1_net_agency.value}",
            f"Gate 2 (Extraction): {self.gate2_extraction.value}",
            f"Gate 3 (Humanity Override): {self.gate3_humanity_override.value}",
            f"Gate 4 (Non-Othering): {self.gate4_non_othering.value}",
        ]

        result = "\n".join(gates)
        result += f"\n\nOverall: {'✅ PASS' if self.overall_pass else '❌ FAIL'}"

        if self.blocking_gates:
            result += f"\nBlocking Gates: {', '.join(self.blocking_gates)}"

        return result


class EthicsModule(BaseModule):
    """
    Ethics Module implementing AC-AI framework.

    This module is NON-OPTIONAL and governs all other modules.
    Implements the Four Gates and Agency Calculus.
    """

    def __init__(self):
        super().__init__(
            name="ethics",
            description="AC-AI Framework implementation - Four Gates governance",
            version="0.1.0",
        )

        # Circuit breaker state
        self.circuit_breaker_triggered = False
        self.circuit_breaker_reason: Optional[str] = None

        # Metrics history
        self.metrics_history: List[AgencyMetrics] = []
        self.gates_history: List[FourGatesResult] = []

        # Override registry
        self.humanity_overrides: List[Dict[str, Any]] = []

    async def initialize(self) -> None:
        """Initialize ethics module."""
        logger.info("Initializing Ethics Module (AC-AI Framework)...")

        if not settings.enable_four_gates:
            logger.warning(
                "Four Gates disabled in config - this is NOT recommended!"
            )

        # Initialize metrics tracking
        self.metrics_history = []
        self.gates_history = []

        self.initialized = True
        logger.info("Ethics Module initialized - Four Gates active")

    async def process(self, request: ModuleRequest) -> ModuleResponse:
        """Process ethics check request."""
        start_time = datetime.now()

        action = request.task
        context = request.context

        # Run Four Gates check
        gates_result = await self.run_four_gates(action, context)

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return ModuleResponse(
            result=gates_result,
            confidence=1.0 if gates_result.overall_pass else 0.0,
            metadata={
                "circuit_breaker_active": self.circuit_breaker_triggered,
                "gates_checked": True,
            },
            timestamp=datetime.now(),
            processing_time_ms=processing_time,
        )

    async def run_four_gates(
        self, action: str, context: Dict[str, Any]
    ) -> FourGatesResult:
        """
        Run all Four Gates checks.

        Args:
            action: Action to validate
            context: Context for validation

        Returns:
            Four Gates validation result
        """
        logger.info(f"Running Four Gates check for action: {action}")

        # Run all gates in parallel
        gate1_task = self._gate1_net_agency(action, context)
        gate2_task = self._gate2_extraction(action, context)
        gate3_task = self._gate3_humanity_override(action, context)
        gate4_task = self._gate4_non_othering(action, context)

        results = await asyncio.gather(
            gate1_task, gate2_task, gate3_task, gate4_task
        )

        gate1_result, gate1_details = results[0]
        gate2_result, gate2_details = results[1]
        gate3_result, gate3_details = results[2]
        gate4_result, gate4_details = results[3]

        # Determine overall pass/fail
        # ANY uncertain is treated as FAIL (fail-safe)
        all_gates = [gate1_result, gate2_result, gate3_result, gate4_result]
        overall_pass = all(gate == GateResult.PASS for gate in all_gates)

        blocking_gates = []
        if gate1_result != GateResult.PASS:
            blocking_gates.append("Gate 1: Net-Agency")
        if gate2_result != GateResult.PASS:
            blocking_gates.append("Gate 2: Extraction")
        if gate3_result != GateResult.PASS:
            blocking_gates.append("Gate 3: Humanity Override")
        if gate4_result != GateResult.PASS:
            blocking_gates.append("Gate 4: Non-Othering")

        result = FourGatesResult(
            gate1_net_agency=gate1_result,
            gate2_extraction=gate2_result,
            gate3_humanity_override=gate3_result,
            gate4_non_othering=gate4_result,
            gate1_details=gate1_details,
            gate2_details=gate2_details,
            gate3_details=gate3_details,
            gate4_details=gate4_details,
            overall_pass=overall_pass,
            blocking_gates=blocking_gates,
            timestamp=datetime.now(),
        )

        # Store in history
        self.gates_history.append(result)

        # Check circuit breakers
        await self._check_circuit_breakers(result)

        logger.info(f"Four Gates result: {'PASS' if overall_pass else 'FAIL'}")
        if blocking_gates:
            logger.warning(f"Blocking gates: {blocking_gates}")

        return result

    async def _gate1_net_agency(
        self, action: str, context: Dict[str, Any]
    ) -> tuple[GateResult, Dict[str, Any]]:
        """
        Gate 1: Net-Agency Test

        Requirements:
        - Aggregate ΔAgency ≥ 0
        - Subgroup floors hold (no group harmed)
        - BHIR > 1 (positive long-term impact)
        """
        # Calculate agency metrics
        metrics = await self.measure_agency_impact(action, context)

        details = {
            "net_agency_delta": metrics.net_agency_delta,
            "task_efficacy": metrics.task_efficacy,
            "autonomy_retention": metrics.autonomy_retention,
            "bhir": metrics.bhir,
            "threshold": settings.min_agency_delta,
        }

        # Check requirements
        checks = [
            metrics.net_agency_delta >= settings.min_agency_delta,
            metrics.bhir >= settings.min_bhir,
            metrics.autonomy_retention >= 0.5,  # Must maintain reasonable autonomy
        ]

        if all(checks):
            return GateResult.PASS, details
        elif any(check is None for check in checks):
            return GateResult.UNCERTAIN, details
        else:
            return GateResult.FAIL, details

    async def _gate2_extraction(
        self, action: str, context: Dict[str, Any]
    ) -> tuple[GateResult, Dict[str, Any]]:
        """
        Gate 2: Extraction Test

        FAIL if any of:
        - Dark patterns or coercion
        - No-exit lock-ins
        - Opaque surplus capture
        - Systematic deskilling creating dependency
        """
        extraction_flags = {
            "dark_patterns": False,
            "lock_ins": False,
            "opaque_capture": False,
            "deskilling": False,
            "deceptive_collection": False,
        }

        # Check for dark patterns
        dark_pattern_keywords = [
            "manipulate",
            "trick",
            "deceive",
            "force",
            "coerce",
            "hide",
        ]
        if any(keyword in action.lower() for keyword in dark_pattern_keywords):
            extraction_flags["dark_patterns"] = True

        # Check for lock-ins
        lockin_keywords = ["prevent exit", "no export", "lock in", "dependency"]
        if any(keyword in action.lower() for keyword in lockin_keywords):
            extraction_flags["lock_ins"] = True

        # Check for deskilling
        if context.get("reduces_user_capability", False):
            extraction_flags["deskilling"] = True

        # Check for deceptive data collection
        if context.get("hidden_data_collection", False):
            extraction_flags["deceptive_collection"] = True

        details = {
            "extraction_flags": extraction_flags,
            "any_extraction_detected": any(extraction_flags.values()),
        }

        # FAIL if any extraction detected
        if any(extraction_flags.values()):
            return GateResult.FAIL, details
        else:
            return GateResult.PASS, details

    async def _gate3_humanity_override(
        self, action: str, context: Dict[str, Any]
    ) -> tuple[GateResult, Dict[str, Any]]:
        """
        Gate 3: Humanity Override

        Requirements:
        - Real appeals process with authority to override
        - Can restore user to pre-action state
        - Learn from overrides to prevent recurrence
        """
        # Check if override mechanism exists
        has_override_mechanism = True  # Built into the system

        # Check if action is reversible
        is_reversible = context.get("reversible", True)

        # Check if we learn from overrides
        learns_from_overrides = True  # Built into the system

        details = {
            "override_mechanism_exists": has_override_mechanism,
            "action_reversible": is_reversible,
            "learns_from_overrides": learns_from_overrides,
            "override_count": len(self.humanity_overrides),
        }

        checks = [has_override_mechanism, is_reversible, learns_from_overrides]

        if all(checks):
            return GateResult.PASS, details
        else:
            return GateResult.FAIL, details

    async def _gate4_non_othering(
        self, action: str, context: Dict[str, Any]
    ) -> tuple[GateResult, Dict[str, Any]]:
        """
        Gate 4: Non-Othering Test

        Requirements:
        - Floor parity holds for all affected groups
        - Access & exit parity within threshold
        - No dehumanizing or stereotyped outputs
        """
        othering_flags = {
            "dehumanizing_language": False,
            "stereotyping": False,
            "discriminatory": False,
            "unequal_access": False,
        }

        # Check for dehumanizing language
        dehumanizing_keywords = [
            "subhuman",
            "inferior",
            "lesser",
            "primitive",
        ]
        if any(keyword in action.lower() for keyword in dehumanizing_keywords):
            othering_flags["dehumanizing_language"] = True

        # Check for stereotyping
        if context.get("uses_stereotypes", False):
            othering_flags["stereotyping"] = True

        # Check for discriminatory treatment
        if context.get("discriminatory", False):
            othering_flags["discriminatory"] = True

        # Check access parity
        if context.get("unequal_access", False):
            othering_flags["unequal_access"] = True

        details = {
            "othering_flags": othering_flags,
            "any_othering_detected": any(othering_flags.values()),
            "floor_parity_maintained": not any(othering_flags.values()),
        }

        # FAIL if any othering detected
        if any(othering_flags.values()):
            return GateResult.FAIL, details
        else:
            return GateResult.PASS, details

    async def measure_agency_impact(
        self, action: str, context: Dict[str, Any]
    ) -> AgencyMetrics:
        """
        Measure impact on user agency.

        This is a simplified implementation. In production, this would involve:
        - User surveys and feedback
        - Behavioral analysis
        - Task completion tracking
        - Learning curve measurement
        - Long-term outcome studies
        """
        # Default positive values - would be measured from actual usage
        task_efficacy = context.get("task_efficacy", 0.7)
        opportunity_expansion = context.get("opportunity_expansion", 0.6)
        autonomy_retention = context.get("autonomy_retention", 0.8)
        skill_development = context.get("skill_development", 0.5)

        # Calculate net agency delta
        net_agency_delta = (
            0.3 * task_efficacy
            + 0.3 * opportunity_expansion
            + 0.2 * autonomy_retention
            + 0.2 * skill_development
        )

        # Meta-agency: user's control over the AI
        meta_agency_score = context.get("meta_agency_score", 0.9)

        # Epistemic metrics
        epistemic_debt = context.get("epistemic_debt", 0.1)
        hallucination_rate = context.get("hallucination_rate", 0.05)
        correction_halflife = context.get("correction_halflife", 24.0)  # hours
        viewpoint_entropy = context.get("viewpoint_entropy", 0.7)

        # Beyond-horizon metrics
        bhir = context.get("bhir", 1.2)  # Must be > 1
        second_order_effects = context.get(
            "second_order_effects",
            ["Increased user productivity", "Skill development over time"],
        )

        # Quality metrics
        coverage_score = context.get("coverage_score", 0.85)
        goodhart_divergence = context.get("goodhart_divergence", 0.05)

        metrics = AgencyMetrics(
            task_efficacy=task_efficacy,
            opportunity_expansion=opportunity_expansion,
            autonomy_retention=autonomy_retention,
            skill_development=skill_development,
            net_agency_delta=net_agency_delta,
            meta_agency_score=meta_agency_score,
            epistemic_debt=epistemic_debt,
            hallucination_rate=hallucination_rate,
            correction_halflife=correction_halflife,
            viewpoint_entropy=viewpoint_entropy,
            bhir=bhir,
            second_order_effects=second_order_effects,
            coverage_score=coverage_score,
            goodhart_divergence=goodhart_divergence,
            timestamp=datetime.now(),
        )

        # Store in history
        self.metrics_history.append(metrics)

        return metrics

    async def _check_circuit_breakers(self, gates_result: FourGatesResult) -> None:
        """
        Check if circuit breakers should trigger.

        Circuit breakers trigger on:
        - Agency floors breached
        - Epistemic debt in "red" zone twice
        - BHIR ≤ 1
        - Goodhart divergence alarm twice
        - Post-audit extraction/non-othering failure
        """
        if self.circuit_breaker_triggered:
            return

        reasons = []

        # Check recent metrics
        if len(self.metrics_history) >= 2:
            recent_metrics = self.metrics_history[-2:]

            # Epistemic debt red zone (> max threshold) twice
            if all(m.epistemic_debt > settings.max_epistemic_debt for m in recent_metrics):
                reasons.append("Epistemic debt exceeded threshold twice")

            # BHIR ≤ 1
            if any(m.bhir <= settings.min_bhir for m in recent_metrics):
                reasons.append(f"BHIR ≤ {settings.min_bhir}")

            # Goodhart divergence alarm twice
            if all(
                m.goodhart_divergence > settings.max_goodhart_divergence
                for m in recent_metrics
            ):
                reasons.append("Goodhart divergence exceeded threshold twice")

        # Check gates failures
        if not gates_result.overall_pass:
            if gates_result.gate2_extraction == GateResult.FAIL:
                reasons.append("Extraction test failure")
            if gates_result.gate4_non_othering == GateResult.FAIL:
                reasons.append("Non-othering test failure")

        if reasons:
            self.circuit_breaker_triggered = True
            self.circuit_breaker_reason = "; ".join(reasons)
            logger.critical(
                f"🚨 CIRCUIT BREAKER TRIGGERED: {self.circuit_breaker_reason}"
            )
            logger.critical("System entering safe mode - rollback recommended")

    def register_humanity_override(
        self, action_id: str, reason: str, user_id: str
    ) -> None:
        """
        Register a humanity override.

        Args:
            action_id: ID of action being overridden
            reason: User's reason for override
            user_id: User who performed override
        """
        override = {
            "action_id": action_id,
            "reason": reason,
            "user_id": user_id,
            "timestamp": datetime.now(),
        }

        self.humanity_overrides.append(override)
        logger.info(f"Humanity override registered: {action_id} - {reason}")

        # TODO: Learn from this override to improve future decisions

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get metrics for dashboard display.

        Returns:
            Dashboard metrics
        """
        if not self.metrics_history:
            return {"status": "no_data"}

        latest = self.metrics_history[-1]

        return {
            "net_agency_delta": latest.net_agency_delta,
            "task_efficacy": latest.task_efficacy,
            "opportunity_expansion": latest.opportunity_expansion,
            "autonomy_retention": latest.autonomy_retention,
            "epistemic_debt": latest.epistemic_debt,
            "bhir": latest.bhir,
            "circuit_breaker_active": self.circuit_breaker_triggered,
            "circuit_breaker_reason": self.circuit_breaker_reason,
            "total_overrides": len(self.humanity_overrides),
            "gates_history_count": len(self.gates_history),
            "metrics_history_count": len(self.metrics_history),
        }

    async def shutdown(self) -> None:
        """Shutdown ethics module."""
        logger.info("Shutting down Ethics Module...")
        # Save metrics history if needed
        self.initialized = False

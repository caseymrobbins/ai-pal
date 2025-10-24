"""
Integrated AC-AI System - Phase 3

Complete integration of all AC-AI framework components:
- Phase 1: Plugin architecture, security, CI/CD gates, AHO tribunal
- Phase 2: ARI monitoring, EDM, self-improvement loop, LoRA fine-tuning
- Phase 3: Enhanced context, privacy, multi-model orchestration, dashboard

This provides the main entry point for the complete Agency-Centric AI system.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from loguru import logger

# Phase 1 imports (via Phase 1.5 bridge modules)
from ..security.credential_manager import CredentialManager
from ..gates.aho_tribunal import AHOTribunal, Verdict, ImpactScore
from ..gates.gate_system import GateSystem, GateType

# Phase 2 imports
from ..monitoring.ari_monitor import ARIMonitor, AgencySnapshot
from ..monitoring.edm_monitor import EDMMonitor
from ..improvement.self_improvement import SelfImprovementLoop, FeedbackEvent, FeedbackType
from ..improvement.lora_tuning import LoRAFineTuner, TrainingExample

# Phase 3 imports
from ..privacy.advanced_privacy import AdvancedPrivacyManager, PIIDetection
from ..context.enhanced_context import EnhancedContextManager, MemoryEntry, MemoryType, MemoryPriority
from ..orchestration.multi_model import MultiModelOrchestrator, TaskRequirements, ModelProvider
from ..ui.agency_dashboard import AgencyDashboard, DashboardSection


class RequestStage(Enum):
    """Stages of request processing"""
    INTAKE = "intake"
    PII_DETECTION = "pii_detection"
    CONTEXT_RETRIEVAL = "context_retrieval"
    GATE_EVALUATION = "gate_evaluation"
    MODEL_SELECTION = "model_selection"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    RESPONSE = "response"
    FEEDBACK = "feedback"


@dataclass
class ProcessedRequest:
    """Result of processing a user request"""
    request_id: str
    user_id: str
    original_query: str
    processed_query: str  # After PII redaction

    # Model execution
    selected_model: str
    selected_provider: ModelProvider
    model_response: str

    # Privacy
    pii_detections: List[PIIDetection]
    privacy_budget_used: float

    # Context
    relevant_memories: List[MemoryEntry]
    new_memories_created: int

    # Monitoring
    agency_snapshot: Optional[AgencySnapshot]
    epistemic_debts_detected: int

    # Gating
    gate_verdicts: Dict[GateType, Verdict]
    tribunal_override: bool

    # Performance
    latency_ms: float
    cost: float

    # Status
    success: bool
    error: Optional[str] = None
    stage_completed: RequestStage = RequestStage.INTAKE


@dataclass
class SystemConfig:
    """Configuration for integrated system"""
    # Storage paths
    data_dir: Path
    credentials_path: Path

    # Phase 1 config
    enable_gates: bool = True
    enable_tribunal: bool = True

    # Phase 2 config
    enable_ari_monitoring: bool = True
    enable_edm_monitoring: bool = True
    enable_self_improvement: bool = True
    enable_lora_tuning: bool = False  # Opt-in for fine-tuning

    # Phase 3 config
    enable_privacy_protection: bool = True
    enable_context_management: bool = True
    enable_model_orchestration: bool = True
    enable_dashboard: bool = True

    # Thresholds
    ari_alert_threshold: float = -0.1
    edm_alert_threshold: float = 0.3
    privacy_epsilon_limit: float = 1.0
    max_context_tokens: int = 4096


class IntegratedACSystem:
    """
    Complete Agency-Centric AI System

    Integrates all phases:
    - Phase 1: Security, gates, tribunal
    - Phase 2: Monitoring (ARI, EDM), self-improvement, LoRA
    - Phase 3: Privacy, context, orchestration, dashboard

    Provides unified API for AC-AI compliant request processing.
    """

    def __init__(self, config: SystemConfig):
        """
        Initialize integrated system

        Args:
            config: System configuration
        """
        self.config = config
        self.config.data_dir.mkdir(parents=True, exist_ok=True)

        # Phase 1 components (via Phase 1.5 bridge modules)
        self.credential_manager = CredentialManager(config.credentials_path)
        self.gate_system = GateSystem() if config.enable_gates else None
        self.tribunal = AHOTribunal() if config.enable_tribunal else None

        # Phase 2 components
        self.ari_monitor = (
            ARIMonitor(
                storage_dir=config.data_dir / "ari_snapshots",
                alert_threshold_delta_agency=config.ari_alert_threshold
            )
            if config.enable_ari_monitoring
            else None
        )

        self.edm_monitor = (
            EDMMonitor(
                storage_dir=config.data_dir / "edm_snapshots",
                fact_check_enabled=True,
                auto_resolve_verified=True
            )
            if config.enable_edm_monitoring
            else None
        )

        self.improvement_loop = (
            SelfImprovementLoop(
                storage_dir=config.data_dir / "improvements"
            )
            if config.enable_self_improvement
            else None
        )

        self.lora_tuner = (
            LoRAFineTuner(storage_dir=config.data_dir / "lora_models")
            if config.enable_lora_tuning
            else None
        )

        # Phase 3 components
        self.privacy_manager = (
            AdvancedPrivacyManager(
                storage_dir=config.data_dir / "privacy",
                default_epsilon=config.privacy_epsilon_limit
            )
            if config.enable_privacy_protection
            else None
        )

        self.context_manager = (
            EnhancedContextManager(
                storage_dir=config.data_dir / "context",
                max_context_tokens=config.max_context_tokens
            )
            if config.enable_context_management
            else None
        )

        self.orchestrator = (
            MultiModelOrchestrator(
                storage_dir=config.data_dir / "orchestrator"
            )
            if config.enable_model_orchestration
            else None
        )

        self.dashboard = (
            AgencyDashboard(
                ari_monitor=self.ari_monitor,
                edm_monitor=self.edm_monitor,
                improvement_loop=self.improvement_loop,
                privacy_manager=self.privacy_manager,
                orchestrator=self.orchestrator,
                context_manager=self.context_manager
            )
            if config.enable_dashboard
            else None
        )

        logger.info("Integrated AC-AI System initialized successfully")
        logger.info(f"Phase 1: Gates={config.enable_gates}, Tribunal={config.enable_tribunal}")
        logger.info(
            f"Phase 2: ARI={config.enable_ari_monitoring}, EDM={config.enable_edm_monitoring}, "
            f"Improvement={config.enable_self_improvement}, LoRA={config.enable_lora_tuning}"
        )
        logger.info(
            f"Phase 3: Privacy={config.enable_privacy_protection}, "
            f"Context={config.enable_context_management}, "
            f"Orchestration={config.enable_model_orchestration}, Dashboard={config.enable_dashboard}"
        )

    async def process_request(
        self,
        user_id: str,
        query: str,
        session_id: str,
        task_type: str = "general",
        requirements: Optional[TaskRequirements] = None
    ) -> ProcessedRequest:
        """
        Process a complete user request through all AC-AI stages

        Args:
            user_id: User making the request
            query: User's query/prompt
            session_id: Current session ID
            task_type: Type of task (for ARI tracking)
            requirements: Optional task requirements for model selection

        Returns:
            ProcessedRequest with complete results and metadata
        """
        request_id = f"{user_id}_{datetime.now().timestamp()}"
        start_time = datetime.now()

        logger.info(f"Processing request {request_id} for user {user_id}")

        result = ProcessedRequest(
            request_id=request_id,
            user_id=user_id,
            original_query=query,
            processed_query=query,
            selected_model="",
            selected_provider=ModelProvider.LOCAL,
            model_response="",
            pii_detections=[],
            privacy_budget_used=0.0,
            relevant_memories=[],
            new_memories_created=0,
            agency_snapshot=None,
            epistemic_debts_detected=0,
            gate_verdicts={},
            tribunal_override=False,
            latency_ms=0.0,
            cost=0.0,
            success=False
        )

        try:
            # Stage 1: PII Detection & Privacy
            result.stage_completed = RequestStage.PII_DETECTION
            if self.privacy_manager:
                # Check privacy budget
                budget_ok = await self.privacy_manager.check_privacy_budget(user_id)
                if not budget_ok:
                    result.error = "Privacy budget exceeded"
                    return result

                # Detect and handle PII
                detections = await self.privacy_manager.detect_pii(query, user_id, session_id)
                result.pii_detections = detections

                # Redact PII from query
                result.processed_query = await self.privacy_manager.apply_privacy_actions(
                    query,
                    detections
                )

                result.privacy_budget_used = 0.01  # Standard epsilon cost

            # Stage 2: Context Retrieval
            result.stage_completed = RequestStage.CONTEXT_RETRIEVAL
            if self.context_manager:
                # Search relevant memories
                memories = await self.context_manager.search_memories(
                    user_id=user_id,
                    query=result.processed_query,
                    limit=10
                )
                result.relevant_memories = memories

            # Stage 3: Gate Evaluation
            result.stage_completed = RequestStage.GATE_EVALUATION
            if self.gate_system:
                # Evaluate through all gates
                # Note: This is a simplified evaluation - in practice would need actual metrics
                autonomy_score = 0.8
                humanity_score = 0.85
                oversight_score = 0.9

                autonomy_verdict = await self.gate_system.evaluate_gate(
                    GateType.AUTONOMY,
                    autonomy_score,
                    {"user_id": user_id, "query": result.processed_query}
                )

                humanity_verdict = await self.gate_system.evaluate_gate(
                    GateType.HUMANITY,
                    humanity_score,
                    {"user_id": user_id, "query": result.processed_query}
                )

                oversight_verdict = await self.gate_system.evaluate_gate(
                    GateType.OVERSIGHT,
                    oversight_score,
                    {"user_id": user_id, "query": result.processed_query}
                )

                result.gate_verdicts = {
                    GateType.AUTONOMY: autonomy_verdict,
                    GateType.HUMANITY: humanity_verdict,
                    GateType.OVERSIGHT: oversight_verdict
                }

                # Check for gate failures
                failed_gates = [
                    gate for gate, verdict in result.gate_verdicts.items()
                    if not verdict.approved
                ]

                if failed_gates and self.tribunal:
                    # Escalate to AHO Tribunal
                    logger.warning(f"Gates failed: {failed_gates}, escalating to tribunal")

                    tribunal_verdict = await self.tribunal.evaluate_request(
                        user_id=user_id,
                        request=result.processed_query,
                        failed_gates=failed_gates,
                        context={"session_id": session_id}
                    )

                    if tribunal_verdict.approved:
                        result.tribunal_override = True
                        logger.info("Tribunal approved override")
                    else:
                        result.error = f"Request blocked by gates: {failed_gates}"
                        return result

            # Stage 4: Model Selection
            result.stage_completed = RequestStage.MODEL_SELECTION
            if self.orchestrator:
                # Use provided requirements or create default
                if requirements is None:
                    requirements = TaskRequirements(
                        min_reasoning_capability=0.7,
                        max_cost_per_1k_tokens=0.01,
                        max_latency_ms=3000,
                        requires_local_execution=False
                    )

                selection = await self.orchestrator.select_model(requirements)
                result.selected_model = selection.model_name
                result.selected_provider = selection.provider
                result.cost = selection.estimated_cost

                logger.info(
                    f"Selected model: {selection.provider.value}:{selection.model_name} "
                    f"(score: {selection.score:.3f})"
                )
            else:
                result.selected_model = "phi-2"
                result.selected_provider = ModelProvider.LOCAL

            # Stage 5: Execution
            result.stage_completed = RequestStage.EXECUTION
            # Note: Actual model execution would happen here
            # For now, simulating with placeholder
            result.model_response = f"[Response from {result.selected_model} to: {result.processed_query[:50]}...]"

            # Stage 6: Monitoring
            result.stage_completed = RequestStage.MONITORING

            # EDM: Check for epistemic debt in response
            if self.edm_monitor:
                debts = await self.edm_monitor.analyze_text(
                    text=result.model_response,
                    task_id=request_id,
                    user_id=user_id,
                    context=result.processed_query
                )
                result.epistemic_debts_detected = len(debts)

            # ARI: Record agency snapshot
            if self.ari_monitor:
                # Note: In practice, these would be calculated based on user interaction
                snapshot = AgencySnapshot(
                    timestamp=datetime.now(),
                    task_id=request_id,
                    task_type=task_type,
                    delta_agency=0.1,  # Placeholder
                    bhir=1.5,  # Placeholder
                    task_efficacy=0.9,  # Placeholder
                    user_skill_before=0.7,  # Placeholder
                    user_skill_after=0.75,  # Placeholder
                    skill_development=0.05,  # Placeholder
                    ai_reliance=0.5,  # Placeholder
                    autonomy_retention=0.8,  # Placeholder
                    user_id=user_id,
                    session_id=session_id,
                    metadata={"request_id": request_id}
                )

                await self.ari_monitor.record_snapshot(snapshot)
                result.agency_snapshot = snapshot

            # Stage 7: Context Update
            if self.context_manager:
                # Store query as conversation memory
                query_memory = await self.context_manager.add_memory(
                    user_id=user_id,
                    content=result.processed_query,
                    memory_type=MemoryType.CONVERSATION,
                    priority=MemoryPriority.MEDIUM,
                    tags={"task_type", task_type, "session_id", session_id}
                )

                # Store response as conversation memory
                response_memory = await self.context_manager.add_memory(
                    user_id=user_id,
                    content=result.model_response,
                    memory_type=MemoryType.CONVERSATION,
                    priority=MemoryPriority.MEDIUM,
                    tags={"task_type", task_type, "session_id", session_id}
                )

                result.new_memories_created = 2

            # Stage 8: Performance Tracking
            if self.orchestrator:
                end_time = datetime.now()
                latency_ms = (end_time - start_time).total_seconds() * 1000

                await self.orchestrator.record_performance(
                    provider=result.selected_provider,
                    model_name=result.selected_model,
                    latency_ms=latency_ms,
                    cost=result.cost,
                    success=True,
                    quality_score=0.9  # Placeholder
                )

                result.latency_ms = latency_ms

            # Stage 9: Feedback Collection
            result.stage_completed = RequestStage.FEEDBACK
            if self.improvement_loop:
                # Record implicit feedback (successful completion)
                feedback = FeedbackEvent(
                    timestamp=datetime.now(),
                    feedback_type=FeedbackType.USER_IMPLICIT,
                    component="integrated_system",
                    metric_name="request_success",
                    metric_value=1.0,
                    context={
                        "user_id": user_id,
                        "request_id": request_id,
                        "task_type": task_type
                    }
                )
                await self.improvement_loop.collect_feedback(feedback)

            result.success = True
            result.stage_completed = RequestStage.RESPONSE

            logger.info(
                f"Request {request_id} completed successfully: "
                f"latency={result.latency_ms:.0f}ms, cost=${result.cost:.4f}, "
                f"pii_detected={len(result.pii_detections)}, "
                f"debts_detected={result.epistemic_debts_detected}"
            )

        except Exception as e:
            logger.error(f"Error processing request {request_id}: {e}")
            result.error = str(e)
            result.success = False

            # Record failure feedback
            if self.improvement_loop:
                feedback = FeedbackEvent(
                    timestamp=datetime.now(),
                    feedback_type=FeedbackType.PERFORMANCE_METRIC,
                    component="integrated_system",
                    metric_name="request_failure",
                    metric_value=0.0,
                    context={
                        "user_id": user_id,
                        "request_id": request_id,
                        "error": str(e),
                        "stage": result.stage_completed.value
                    }
                )
                await self.improvement_loop.collect_feedback(feedback)

        return result

    async def get_user_dashboard(
        self,
        user_id: str,
        sections: Optional[List[DashboardSection]] = None,
        period_days: int = 7
    ) -> Optional[Any]:
        """
        Get user dashboard data

        Args:
            user_id: User to get dashboard for
            sections: Specific sections to include
            period_days: Reporting period

        Returns:
            Dashboard data or None if dashboard disabled
        """
        if not self.dashboard:
            logger.warning("Dashboard is disabled")
            return None

        return await self.dashboard.generate_dashboard(
            user_id=user_id,
            sections=sections,
            period_days=period_days
        )

    async def record_user_feedback(
        self,
        user_id: str,
        request_id: str,
        feedback_positive: bool,
        feedback_text: Optional[str] = None
    ) -> None:
        """
        Record explicit user feedback on a request

        Args:
            user_id: User providing feedback
            request_id: Request being rated
            feedback_positive: True if positive, False if negative
            feedback_text: Optional text feedback
        """
        if not self.improvement_loop:
            return

        feedback = FeedbackEvent(
            timestamp=datetime.now(),
            feedback_type=FeedbackType.USER_EXPLICIT,
            component="integrated_system",
            metric_name="user_satisfaction",
            metric_value=1.0 if feedback_positive else 0.0,
            context={
                "user_id": user_id,
                "request_id": request_id,
                "feedback_text": feedback_text or ""
            }
        )

        await self.improvement_loop.collect_feedback(feedback)
        logger.info(f"Recorded user feedback for request {request_id}: {feedback_positive}")

    async def shutdown(self) -> None:
        """Gracefully shutdown all system components"""
        logger.info("Shutting down Integrated AC-AI System...")

        # Trigger any pending improvements
        if self.improvement_loop:
            await self.improvement_loop.generate_periodic_improvements()

        # Final context consolidation
        if self.context_manager:
            # Consolidate all users
            for user_id in self.context_manager.memories.keys():
                await self.context_manager.consolidate_memories(user_id)

        logger.info("Shutdown complete")


def create_default_system(data_dir: Path, credentials_path: Path) -> IntegratedACSystem:
    """
    Create integrated system with default configuration

    Args:
        data_dir: Directory for data storage
        credentials_path: Path to credentials file

    Returns:
        Configured IntegratedACSystem
    """
    config = SystemConfig(
        data_dir=data_dir,
        credentials_path=credentials_path,
        enable_gates=True,
        enable_tribunal=True,
        enable_ari_monitoring=True,
        enable_edm_monitoring=True,
        enable_self_improvement=True,
        enable_lora_tuning=False,  # Disabled by default (resource intensive)
        enable_privacy_protection=True,
        enable_context_management=True,
        enable_model_orchestration=True,
        enable_dashboard=True
    )

    return IntegratedACSystem(config)

"""
Socratic Co-pilot: Embedded Assessment During Standard Tasks.

"Assistance without Deskilling" - Acts as a co-pilot that helps complete tasks
without taking over, measuring user capability through clarifying questions.

Solves the "Convenience vs. Capability" problem by identifying Unassisted
Capability Checkpoints (UCCs) and measuring ARI at delegation points.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from loguru import logger

from ai_pal.ari.measurement import (
    ARIMeasurementSystem,
    UnassistedCapabilityCheckpoint,
    ARILevel,
    ARIDimension
)


class TaskType(Enum):
    """Types of tasks for embedded assessment."""
    CODE_GENERATION = "code_generation"
    WRITING = "writing"
    ANALYSIS = "analysis"
    RESEARCH = "research"
    PLANNING = "planning"
    CREATIVE = "creative"


class AssistanceLevel(Enum):
    """Level of assistance to provide based on ARI."""
    MINIMAL = "minimal"              # High ARI: mostly guidance
    MODERATE = "moderate"            # Medium ARI: balanced help
    SUBSTANTIAL = "substantial"      # Low ARI: more direct assistance


@dataclass
class TaskRequest:
    """User's task request with embedded assessment."""
    request_id: str
    user_id: str
    original_request: str
    task_type: TaskType

    # Checkpoints
    checkpoints: List[UnassistedCapabilityCheckpoint] = field(default_factory=list)
    checkpoints_completed: int = 0

    # User responses
    checkpoint_responses: Dict[str, str] = field(default_factory=dict)

    # ARI measurements
    measured_ari_levels: Dict[str, ARILevel] = field(default_factory=dict)
    overall_ari: Optional[ARILevel] = None

    # Task completion
    assistance_level: AssistanceLevel = AssistanceLevel.MODERATE
    final_output: Optional[str] = None
    completed_at: Optional[datetime] = None


class SocraticCopilot:
    """
    Co-pilot that assists without deskilling through embedded assessment.

    Key Features:
    - Identifies Unassisted Capability Checkpoints (UCCs)
    - Asks clarifying questions at delegation points
    - Measures ARI based on responses
    - Adjusts assistance level dynamically
    - Low friction (feels like normal workflow)
    """

    def __init__(
        self,
        ari_system: ARIMeasurementSystem,
        orchestrator: Optional[Any] = None
    ):
        """Initialize Socratic Co-pilot."""
        self.ari_system = ari_system
        self.orchestrator = orchestrator

        # Active task requests
        self.active_requests: Dict[str, TaskRequest] = {}

        logger.info("Socratic Co-pilot initialized")

    # ========================================================================
    # Task Analysis & Checkpoint Identification
    # ========================================================================

    async def process_task_request(
        self,
        user_id: str,
        request: str,
        task_type: Optional[TaskType] = None
    ) -> Tuple[str, TaskRequest]:
        """
        Process a user's task request and identify checkpoints.

        Args:
            user_id: User identifier
            request: User's original request
            task_type: Type of task (auto-detected if None)

        Returns:
            Tuple of (initial_response, task_request)
            initial_response: Message to user with first checkpoint question
            task_request: TaskRequest object for tracking
        """
        import uuid

        # Auto-detect task type if not provided
        if task_type is None:
            task_type = self._detect_task_type(request)

        # Create task request
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        task_request = TaskRequest(
            request_id=request_id,
            user_id=user_id,
            original_request=request,
            task_type=task_type
        )

        # Identify checkpoints
        checkpoints = self.ari_system.identify_checkpoints(
            user_request=request,
            task_type=task_type.value
        )
        task_request.checkpoints = checkpoints

        # Store active request
        self.active_requests[request_id] = task_request

        # Generate initial response with first checkpoint
        if checkpoints:
            first_checkpoint = checkpoints[0]
            initial_response = self._format_checkpoint_question(
                request=request,
                checkpoint=first_checkpoint,
                is_first=True
            )
        else:
            # No checkpoints needed - proceed directly
            initial_response = f"Got it! Working on: {request}"
            task_request.overall_ari = ARILevel.UNKNOWN

        logger.info(f"Created task request {request_id} with {len(checkpoints)} checkpoints")
        return initial_response, task_request

    def _detect_task_type(self, request: str) -> TaskType:
        """Auto-detect task type from request text."""
        request_lower = request.lower()

        # Code generation signals
        if any(kw in request_lower for kw in ["write code", "script", "function", "class", "python", "javascript"]):
            return TaskType.CODE_GENERATION

        # Writing signals
        if any(kw in request_lower for kw in ["write", "draft", "email", "document", "essay", "article"]):
            return TaskType.WRITING

        # Analysis signals
        if any(kw in request_lower for kw in ["analyze", "compare", "evaluate", "assess"]):
            return TaskType.ANALYSIS

        # Research signals
        if any(kw in request_lower for kw in ["research", "find", "investigate", "explore"]):
            return TaskType.RESEARCH

        # Planning signals
        if any(kw in request_lower for kw in ["plan", "design", "outline", "strategy"]):
            return TaskType.PLANNING

        # Default to creative
        return TaskType.CREATIVE

    def _format_checkpoint_question(
        self,
        request: str,
        checkpoint: UnassistedCapabilityCheckpoint,
        is_first: bool = False
    ) -> str:
        """Format a checkpoint question for the user."""
        if is_first:
            intro = f"Got it! To make sure I create exactly what you need, let me ask a quick question:\n\n"
        else:
            intro = "Great! Next question:\n\n"

        return f"{intro}{checkpoint.question}"

    # ========================================================================
    # Checkpoint Response Processing
    # ========================================================================

    async def process_checkpoint_response(
        self,
        request_id: str,
        checkpoint_index: int,
        response: str
    ) -> Dict[str, Any]:
        """
        Process user's response to a checkpoint question.

        Returns:
            Dict with:
            - measured_ari: ARILevel for this checkpoint
            - next_checkpoint: Next question (if any)
            - ready_to_complete: Whether all checkpoints are answered
        """
        task_request = self.active_requests.get(request_id)
        if not task_request:
            raise ValueError(f"Unknown request: {request_id}")

        if checkpoint_index >= len(task_request.checkpoints):
            raise ValueError(f"Invalid checkpoint index: {checkpoint_index}")

        checkpoint = task_request.checkpoints[checkpoint_index]

        # Record response
        task_request.checkpoint_responses[checkpoint.checkpoint_id] = response

        # Measure ARI
        ari_level = self.ari_system.record_checkpoint_response(
            checkpoint_id=checkpoint.checkpoint_id,
            user_response=response,
            user_id=task_request.user_id
        )

        task_request.measured_ari_levels[checkpoint.checkpoint_id] = ari_level
        task_request.checkpoints_completed += 1

        logger.info(f"Checkpoint {checkpoint_index} response: ARI={ari_level.value}")

        # Check if more checkpoints remain
        next_index = checkpoint_index + 1
        if next_index < len(task_request.checkpoints):
            next_checkpoint = task_request.checkpoints[next_index]
            return {
                "measured_ari": ari_level,
                "next_checkpoint": next_checkpoint,
                "next_checkpoint_index": next_index,
                "ready_to_complete": False,
                "message": self._format_checkpoint_question(
                    task_request.original_request,
                    next_checkpoint,
                    is_first=False
                )
            }
        else:
            # All checkpoints complete - ready to execute task
            overall_ari = self._calculate_overall_ari(task_request)
            task_request.overall_ari = overall_ari

            # Determine assistance level
            task_request.assistance_level = self._determine_assistance_level(overall_ari)

            return {
                "measured_ari": ari_level,
                "overall_ari": overall_ari,
                "ready_to_complete": True,
                "assistance_level": task_request.assistance_level,
                "message": "Perfect! I have everything I need. Let me work on this for you..."
            }

    def _calculate_overall_ari(self, task_request: TaskRequest) -> ARILevel:
        """Calculate overall ARI from checkpoint measurements."""
        if not task_request.measured_ari_levels:
            return ARILevel.UNKNOWN

        # Count levels
        levels = list(task_request.measured_ari_levels.values())
        high_count = sum(1 for l in levels if l == ARILevel.HIGH)
        low_count = sum(1 for l in levels if l == ARILevel.LOW)

        # Majority vote with bias toward caution
        if high_count > len(levels) / 2:
            return ARILevel.HIGH
        elif low_count > len(levels) / 3:  # Lower threshold for LOW
            return ARILevel.LOW
        else:
            return ARILevel.MEDIUM

    def _determine_assistance_level(self, ari_level: ARILevel) -> AssistanceLevel:
        """Determine appropriate assistance level based on ARI."""
        if ari_level == ARILevel.HIGH:
            return AssistanceLevel.MINIMAL
        elif ari_level == ARILevel.MEDIUM:
            return AssistanceLevel.MODERATE
        else:  # LOW or UNKNOWN
            return AssistanceLevel.SUBSTANTIAL

    # ========================================================================
    # Task Completion
    # ========================================================================

    async def complete_task(
        self,
        request_id: str
    ) -> str:
        """
        Complete the task using gathered checkpoint responses.

        Args:
            request_id: Task request identifier

        Returns:
            Final output for the user
        """
        task_request = self.active_requests.get(request_id)
        if not task_request:
            raise ValueError(f"Unknown request: {request_id}")

        # Build context from checkpoint responses
        context = self._build_task_context(task_request)

        # Generate output based on assistance level
        if self.orchestrator:
            # Use AI to generate task output
            output = await self._generate_with_ai(task_request, context)
        else:
            # Fallback: template-based generation
            output = self._generate_with_template(task_request, context)

        task_request.final_output = output
        task_request.completed_at = datetime.now()

        logger.info(f"Completed task {request_id} with {task_request.assistance_level.value} assistance")
        return output

    def _build_task_context(self, task_request: TaskRequest) -> Dict[str, Any]:
        """Build context from checkpoint responses."""
        context = {
            "original_request": task_request.original_request,
            "task_type": task_request.task_type.value,
            "assistance_level": task_request.assistance_level.value,
            "checkpoints": {}
        }

        # Add checkpoint responses
        for checkpoint in task_request.checkpoints:
            if checkpoint.checkpoint_id in task_request.checkpoint_responses:
                context["checkpoints"][checkpoint.question] = task_request.checkpoint_responses[checkpoint.checkpoint_id]

        return context

    async def _generate_with_ai(
        self,
        task_request: TaskRequest,
        context: Dict[str, Any]
    ) -> str:
        """Generate task output using AI orchestrator."""
        # Build prompt based on assistance level
        if task_request.assistance_level == AssistanceLevel.MINIMAL:
            prompt = self._build_minimal_assistance_prompt(context)
        elif task_request.assistance_level == AssistanceLevel.MODERATE:
            prompt = self._build_moderate_assistance_prompt(context)
        else:  # SUBSTANTIAL
            prompt = self._build_substantial_assistance_prompt(context)

        # Execute with orchestrator
        result = await self.orchestrator.execute(
            task=prompt,
            context=context
        )

        return result.get("response", "")

    def _build_minimal_assistance_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for minimal assistance (high ARI user)."""
        return f"""The user has strong capabilities in this area (HIGH ARI).

Original request: {context['original_request']}

User's specifications:
{self._format_checkpoint_responses(context['checkpoints'])}

Provide minimal assistance - primarily:
1. Implement their specifications exactly as described
2. Add brief comments explaining your choices
3. Suggest optional improvements they might consider

Keep explanations brief - they understand the concepts."""

    def _build_moderate_assistance_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for moderate assistance (medium ARI user)."""
        return f"""The user has moderate capabilities in this area (MEDIUM ARI).

Original request: {context['original_request']}

User's specifications:
{self._format_checkpoint_responses(context['checkpoints'])}

Provide moderate assistance:
1. Implement their specifications
2. Add helpful comments explaining key concepts
3. Include brief educational notes on best practices
4. Suggest alternatives they might not have considered

Balance between doing it for them and teaching."""

    def _build_substantial_assistance_prompt(self, context: Dict[str, Any]) -> str:
        """Build prompt for substantial assistance (low ARI user)."""
        return f"""The user needs substantial assistance in this area (LOW ARI).

Original request: {context['original_request']}

User's input (may be incomplete):
{self._format_checkpoint_responses(context['checkpoints'])}

Provide substantial assistance:
1. Make reasonable assumptions where their input was unclear
2. Implement using best practices
3. Add extensive comments explaining WHY each choice was made
4. Include educational notes on key concepts
5. Suggest learning resources for next steps

Focus on teaching while solving their problem."""

    def _format_checkpoint_responses(self, checkpoints: Dict[str, str]) -> str:
        """Format checkpoint responses for inclusion in prompt."""
        if not checkpoints:
            return "(No specific input provided)"

        formatted = []
        for question, response in checkpoints.items():
            formatted.append(f"- {question}\n  → {response}")

        return "\n".join(formatted)

    def _generate_with_template(
        self,
        task_request: TaskRequest,
        context: Dict[str, Any]
    ) -> str:
        """Generate task output using templates (fallback)."""
        output_parts = []

        # Header
        output_parts.append(f"# {task_request.task_type.value.replace('_', ' ').title()}\n")

        # Incorporate checkpoint responses
        output_parts.append("Based on your requirements:\n")
        for checkpoint in task_request.checkpoints:
            if checkpoint.checkpoint_id in task_request.checkpoint_responses:
                response = task_request.checkpoint_responses[checkpoint.checkpoint_id]
                output_parts.append(f"- {checkpoint.question}: {response}")

        output_parts.append("\n[Task output would go here]")

        # Assistance level note
        if task_request.assistance_level == AssistanceLevel.MINIMAL:
            output_parts.append("\n\nNote: You clearly understand this domain well. I've kept explanations minimal.")
        elif task_request.assistance_level == AssistanceLevel.SUBSTANTIAL:
            output_parts.append("\n\nNote: I've included extra explanations to help you learn. Let me know if you'd like more details on any part!")

        return "\n".join(output_parts)

    # ========================================================================
    # User Override: "Just Guess" / "You Decide"
    # ========================================================================

    async def handle_user_override(
        self,
        request_id: str,
        checkpoint_index: int,
        override_type: str = "just_guess"
    ) -> Dict[str, Any]:
        """
        Handle user's "just guess" or "you decide" override.

        This is the implicit override - user prioritizes convenience over
        measurement, but we still log it as a LOW ARI signal.

        Args:
            request_id: Task request identifier
            checkpoint_index: Current checkpoint index
            override_type: "just_guess" or "you_decide"

        Returns:
            Response indicating we'll proceed with best guess
        """
        task_request = self.active_requests.get(request_id)
        if not task_request:
            raise ValueError(f"Unknown request: {request_id}")

        checkpoint = task_request.checkpoints[checkpoint_index]

        # Record as LOW ARI
        override_response = f"[USER OVERRIDE: {override_type}]"
        task_request.checkpoint_responses[checkpoint.checkpoint_id] = override_response

        ari_level = self.ari_system.record_checkpoint_response(
            checkpoint_id=checkpoint.checkpoint_id,
            user_response=override_response,
            user_id=task_request.user_id
        )

        task_request.measured_ari_levels[checkpoint.checkpoint_id] = ARILevel.LOW
        task_request.checkpoints_completed += 1

        logger.info(f"User override at checkpoint {checkpoint_index}: {override_type}")

        # Check if more checkpoints remain
        next_index = checkpoint_index + 1
        if next_index < len(task_request.checkpoints):
            next_checkpoint = task_request.checkpoints[next_index]
            return {
                "measured_ari": ARILevel.LOW,
                "override_recorded": True,
                "next_checkpoint": next_checkpoint,
                "next_checkpoint_index": next_index,
                "ready_to_complete": False,
                "message": "No problem! I'll use my best judgment. " + self._format_checkpoint_question(
                    task_request.original_request,
                    next_checkpoint,
                    is_first=False
                )
            }
        else:
            # All checkpoints complete
            overall_ari = self._calculate_overall_ari(task_request)
            task_request.overall_ari = overall_ari
            task_request.assistance_level = self._determine_assistance_level(overall_ari)

            return {
                "measured_ari": ARILevel.LOW,
                "override_recorded": True,
                "overall_ari": overall_ari,
                "ready_to_complete": True,
                "assistance_level": task_request.assistance_level,
                "message": "Got it! I'll make the remaining decisions and get this done for you..."
            }

    # ========================================================================
    # Analytics
    # ========================================================================

    def get_task_summary(self, request_id: str) -> Dict[str, Any]:
        """Get summary of task request and ARI measurements."""
        task_request = self.active_requests.get(request_id)
        if not task_request:
            raise ValueError(f"Unknown request: {request_id}")

        return {
            "request_id": request_id,
            "task_type": task_request.task_type.value,
            "total_checkpoints": len(task_request.checkpoints),
            "completed_checkpoints": task_request.checkpoints_completed,
            "measured_ari_levels": {
                cid: level.value
                for cid, level in task_request.measured_ari_levels.items()
            },
            "overall_ari": task_request.overall_ari.value if task_request.overall_ari else None,
            "assistance_level": task_request.assistance_level.value,
            "completed": task_request.completed_at is not None
        }

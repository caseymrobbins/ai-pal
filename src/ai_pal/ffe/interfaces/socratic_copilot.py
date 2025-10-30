"""
Socratic Co-pilot - Embedded Assessment

"Assistance without Deskilling" - The AI acts as a "co-pilot" that helps complete tasks
without deskilling the user by doing everything for them.

Core Function:
- Accurately measure ARI during standard assistive requests
- Solve the "Convenience vs. Capability" problem
- Force user to reveal unassisted skill at moment of delegation
- Low-friction assessment embedded in normal workflow

Key Innovation:
Instead of delivering finished product, AI pauses at Unassisted Capability Checkpoints (UCCs)
and asks clarifying questions. User's answers reveal their true capability level.

High ARI (Convenience): User answers quickly and accurately → has the skill
Low ARI (Inability): User says "I don't know" or "Just guess" → capability gap

Powered by:
- ARIMonitor (for tracking capability vs. delegation)
- EnhancedContextManager (for tracking skill gaps over time)
- MultiModelOrchestrator (for generating probes and completing tasks)
"""

import uuid
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger

from ...monitoring.ari_monitor import ARIMonitor, AgencySnapshot
from ...context.enhanced_context import (
    EnhancedContextManager,
    MemoryType,
    MemoryPriority,
)
from ...orchestration.multi_model import MultiModelOrchestrator, TaskComplexity


class CheckpointType(Enum):
    """Types of Unassisted Capability Checkpoints"""
    PARAMETER = "parameter"  # Function parameter, variable value
    LOGIC = "logic"          # Core algorithm or logic decision
    STRUCTURE = "structure"  # High-level structure/organization
    CONTENT = "content"      # Key content points
    DESIGN = "design"        # Design/architecture decision


class CheckpointResponse(Enum):
    """User's response to capability checkpoint"""
    PROVIDED = "provided"       # User provided answer
    DELEGATED = "delegated"     # User said "just guess" / "you do it"
    PARTIAL = "partial"         # User provided partial answer
    CLARIFIED = "clarified"     # User asked for clarification


@dataclass
class UnassistedCapabilityCheckpoint:
    """
    A checkpoint in the task where we probe unassisted capability

    These are the "fundamental parts" or key variables the AI would normally
    guess at, but instead we ask the user to reveal their capability.
    """
    checkpoint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    checkpoint_type: CheckpointType = CheckpointType.PARAMETER
    probe_question: str = ""
    context: Optional[str] = None  # Why this checkpoint matters
    expected_knowledge_level: float = 0.5  # 0-1: How hard should this be?


@dataclass
class CheckpointResponseData:
    """
    User's response to a checkpoint probe

    Records whether user had the capability or delegated.
    """
    checkpoint_id: str
    response_type: CheckpointResponse
    response_text: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    # Capability assessment
    demonstrated_capability: bool = False  # Did they show they can do this?
    capability_score: float = 0.0  # 0-1: How well did they demonstrate capability?


@dataclass
class CopilotRequest:
    """
    A user request being processed by Socratic Co-pilot

    Tracks checkpoints, responses, and ARI measurements.
    """
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    original_request: str = ""
    task_category: str = ""  # e.g., "code", "writing", "analysis"

    # Checkpoints
    checkpoints: List[UnassistedCapabilityCheckpoint] = field(default_factory=list)
    responses: List[CheckpointResponseData] = field(default_factory=list)
    current_checkpoint_index: int = 0

    # Final product
    final_output: Optional[str] = None
    completed: bool = False

    # ARI measurement
    high_ari_count: int = 0  # Number of provided answers (HIGH ARI)
    low_ari_count: int = 0   # Number of delegated answers (LOW ARI)
    overall_ari_score: float = 0.0  # Aggregated ARI for this request

    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


@dataclass
class CopilotProbe:
    """
    A probe (clarifying question) presented to the user

    Low-friction, feels like helpful clarification, not a test.
    """
    checkpoint_id: str
    question: str
    context: Optional[str] = None
    examples: List[str] = field(default_factory=list)  # Example answers if helpful
    delegation_trigger: str = "or say 'just guess' if you'd like me to decide"


class SocraticCopilotInterface:
    """
    Socratic Co-pilot Interface for embedded capability assessment

    Integrates into normal assistance workflow to measure ARI without
    creating friction or feeling like a test.

    Key Principles:
    - Low friction: feels like normal clarification
    - Implicit override: "just guess" is respected
    - Accurate ARI measurement: reveals true capability vs. delegation
    - Assistance without deskilling: user maintains agency

    Usage:
    1. User makes request: "Write Python script to parse file"
    2. Copilot identifies checkpoints: function name, parsing logic, etc.
    3. Copilot asks probes: "What should I name the main function?"
    4. User response measured:
       - Provides answer → HIGH ARI (has capability)
       - Says "just guess" → LOW ARI (capability gap)
    5. Complete task using user's answers + AI filling gaps
    """

    def __init__(
        self,
        ari_monitor: ARIMonitor,
        context_manager: EnhancedContextManager,
        orchestrator: MultiModelOrchestrator,
    ):
        """
        Initialize Socratic Co-pilot interface

        Args:
            ari_monitor: For recording ARI-Knowledge and ARI-Capability metrics
            context_manager: For tracking capability gaps over time
            orchestrator: For generating probes and completing tasks
        """
        self.ari_monitor = ari_monitor
        self.context_manager = context_manager
        self.orchestrator = orchestrator

        # Active requests being processed
        self.active_requests: Dict[str, CopilotRequest] = {}

        logger.info("Socratic Co-pilot Interface initialized")

    async def process_request(
        self,
        user_id: str,
        request: str,
        session_id: str,
    ) -> CopilotRequest:
        """
        Start processing user request with embedded assessment

        Args:
            user_id: User making request
            request: User's request text
            session_id: Current session ID

        Returns:
            CopilotRequest with checkpoints identified
        """
        logger.info(f"Processing copilot request for {user_id}: '{request[:100]}...'")

        # Identify task category
        task_category = await self._identify_task_category(request)

        # Create copilot request
        copilot_request = CopilotRequest(
            user_id=user_id,
            original_request=request,
            task_category=task_category,
        )

        # Identify Unassisted Capability Checkpoints (UCCs)
        checkpoints = await self._identify_checkpoints(request, task_category)
        copilot_request.checkpoints = checkpoints

        # Store active request
        self.active_requests[copilot_request.request_id] = copilot_request

        logger.info(
            f"Identified {len(checkpoints)} checkpoints for request {copilot_request.request_id}"
        )

        return copilot_request

    async def get_next_probe(
        self,
        request_id: str
    ) -> Optional[CopilotProbe]:
        """
        Get next probe (clarifying question) for user

        Args:
            request_id: Request being processed

        Returns:
            CopilotProbe if more checkpoints remain, else None
        """
        copilot_request = self.active_requests.get(request_id)
        if not copilot_request:
            raise ValueError(f"Request {request_id} not found")

        # Check if more checkpoints remain
        if copilot_request.current_checkpoint_index >= len(copilot_request.checkpoints):
            return None  # All checkpoints complete

        # Get current checkpoint
        checkpoint = copilot_request.checkpoints[copilot_request.current_checkpoint_index]

        # Create probe
        probe = CopilotProbe(
            checkpoint_id=checkpoint.checkpoint_id,
            question=checkpoint.probe_question,
            context=checkpoint.context,
            examples=await self._generate_examples(checkpoint),
        )

        logger.debug(f"Generated probe: '{probe.question}'")

        return probe

    async def submit_checkpoint_response(
        self,
        request_id: str,
        checkpoint_id: str,
        response_text: str,
    ) -> CheckpointResponseData:
        """
        Submit user's response to checkpoint probe

        Args:
            request_id: Request being processed
            checkpoint_id: Checkpoint being answered
            response_text: User's response

        Returns:
            CheckpointResponseData with capability assessment
        """
        copilot_request = self.active_requests.get(request_id)
        if not copilot_request:
            raise ValueError(f"Request {request_id} not found")

        # Find checkpoint
        checkpoint = next(
            (c for c in copilot_request.checkpoints if c.checkpoint_id == checkpoint_id),
            None,
        )
        if not checkpoint:
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        logger.info(
            f"Received response for checkpoint {checkpoint_id}: '{response_text[:100]}...'"
        )

        # Analyze response type
        response_type, demonstrated_capability, capability_score = (
            await self._analyze_checkpoint_response(response_text, checkpoint)
        )

        # Create response record
        response_data = CheckpointResponseData(
            checkpoint_id=checkpoint_id,
            response_type=response_type,
            response_text=response_text,
            demonstrated_capability=demonstrated_capability,
            capability_score=capability_score,
        )

        # Record response
        copilot_request.responses.append(response_data)

        # Update ARI counters
        if demonstrated_capability:
            copilot_request.high_ari_count += 1
            logger.info(f"HIGH ARI: User demonstrated capability")
        else:
            copilot_request.low_ari_count += 1
            logger.info(f"LOW ARI: User delegated or couldn't answer")

        # Move to next checkpoint
        copilot_request.current_checkpoint_index += 1

        return response_data

    async def complete_request(
        self,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Complete the request using user's answers + AI filling gaps

        Args:
            request_id: Request to complete

        Returns:
            Dict with final output and ARI assessment
        """
        copilot_request = self.active_requests.get(request_id)
        if not copilot_request:
            raise ValueError(f"Request {request_id} not found")

        logger.info(f"Completing copilot request {request_id}")

        # Calculate overall ARI score
        total_checkpoints = len(copilot_request.checkpoints)
        if total_checkpoints > 0:
            copilot_request.overall_ari_score = (
                copilot_request.high_ari_count / total_checkpoints
            )
        else:
            copilot_request.overall_ari_score = 0.5  # Default if no checkpoints

        # Generate final output using user's answers
        final_output = await self._generate_final_output(copilot_request)
        copilot_request.final_output = final_output
        copilot_request.completed = True
        copilot_request.completed_at = datetime.now()

        # Record ARI snapshot
        await self._record_ari_snapshot(copilot_request)

        # Track capability gaps in context manager
        await self._track_capability_gaps(copilot_request)

        # Clean up active request
        del self.active_requests[request_id]

        logger.info(
            f"Request completed: ARI={copilot_request.overall_ari_score:.2f} "
            f"(High: {copilot_request.high_ari_count}, Low: {copilot_request.low_ari_count})"
        )

        return {
            "request_id": request_id,
            "final_output": final_output,
            "ari_score": copilot_request.overall_ari_score,
            "high_ari_count": copilot_request.high_ari_count,
            "low_ari_count": copilot_request.low_ari_count,
            "capability_demonstrated": copilot_request.overall_ari_score >= 0.6,
        }

    async def get_capability_profile(
        self,
        user_id: str,
        task_category: str,
    ) -> Dict[str, Any]:
        """
        Get user's capability profile for task category

        Shows which checkpoints user typically handles vs. delegates.

        Args:
            user_id: User to analyze
            task_category: Task category to analyze

        Returns:
            Dict with capability profile
        """
        # Search for capability gap memories
        memories = await self.context_manager.search_memories(
            user_id=user_id,
            query=f"capability_gap_{task_category}",
            memory_types=[MemoryType.SKILL],
            tags={"capability_gap", task_category},
            limit=50,
        )

        # Analyze patterns
        if not memories:
            return {
                "task_category": task_category,
                "requests_processed": 0,
                "average_ari": 0.5,
                "common_gaps": [],
            }

        # Aggregate gap patterns
        gap_counts: Dict[str, int] = {}
        total_ari = 0.0

        for memory in memories:
            metadata = memory.metadata
            gap_type = metadata.get("checkpoint_type", "unknown")
            gap_counts[gap_type] = gap_counts.get(gap_type, 0) + 1
            total_ari += metadata.get("ari_score", 0.5)

        # Find common gaps (most frequently delegated)
        common_gaps = sorted(gap_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "task_category": task_category,
            "requests_processed": len(memories),
            "average_ari": total_ari / len(memories) if memories else 0.5,
            "common_gaps": [{"type": gap[0], "count": gap[1]} for gap in common_gaps],
        }

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    async def _identify_task_category(self, request: str) -> str:
        """Identify task category from request"""

        prompt = f"""Identify the task category for this request:

"{request}"

Common categories:
- code: Programming, scripting
- writing: Documents, emails, content
- analysis: Data analysis, research
- design: Architecture, system design
- planning: Task planning, organization

Return just the category name (lowercase, one word).
"""

        response = await self.orchestrator.route_request(
            prompt=prompt,
            task_complexity=TaskComplexity.TRIVIAL,
            optimization_goal="speed",
        )

        category = response["response"].strip().lower()
        return category if category else "general"

    async def _identify_checkpoints(
        self,
        request: str,
        task_category: str,
    ) -> List[UnassistedCapabilityCheckpoint]:
        """Identify Unassisted Capability Checkpoints in request"""

        prompt = f"""Analyze this {task_category} request and identify the key checkpoints where we should probe user capability:

Request: "{request}"

Identify 2-4 "fundamental parts" or key variables that:
1. The user should be able to specify if they truly understand the task
2. Would normally require guessing or assumptions
3. Are not trivial details but core decisions

For a coding example:
- Function/variable names
- Core algorithm logic
- Data structure choices

For a writing example:
- Key points to communicate
- Target audience
- Tone/style

Return as JSON array:
[
  {{
    "type": "parameter|logic|structure|content|design",
    "probe_question": "Clarifying question to ask user",
    "context": "Why this matters",
    "expected_level": 0.0-1.0
  }}
]
"""

        response = await self.orchestrator.route_request(
            prompt=prompt,
            task_complexity=TaskComplexity.MODERATE,
            optimization_goal="quality",
        )

        # Parse checkpoints
        checkpoints_data = self._parse_checkpoints_response(response["response"])

        checkpoints = []
        for data in checkpoints_data:
            checkpoint = UnassistedCapabilityCheckpoint(
                checkpoint_type=CheckpointType(data.get("type", "parameter")),
                probe_question=data["probe_question"],
                context=data.get("context"),
                expected_knowledge_level=data.get("expected_level", 0.5),
            )
            checkpoints.append(checkpoint)

        logger.info(f"Identified {len(checkpoints)} checkpoints")

        return checkpoints

    def _parse_checkpoints_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse AI response into checkpoint data"""
        import json
        try:
            data = json.loads(response)
            if isinstance(data, list):
                return data
            return [data]
        except json.JSONDecodeError:
            # Fallback: create generic checkpoint
            return [
                {
                    "type": "parameter",
                    "probe_question": "Can you provide more details on what you're looking for?",
                    "context": "This will help me create exactly what you need.",
                    "expected_level": 0.5,
                }
            ]

    async def _generate_examples(
        self,
        checkpoint: UnassistedCapabilityCheckpoint,
    ) -> List[str]:
        """Generate example answers if helpful"""

        # Only provide examples for certain checkpoint types
        if checkpoint.checkpoint_type not in [
            CheckpointType.PARAMETER,
            CheckpointType.CONTENT,
        ]:
            return []

        # Keep it simple - just 1-2 examples
        if checkpoint.checkpoint_type == CheckpointType.PARAMETER:
            return ["e.g., 'parse_data'", "e.g., 'process_file'"]
        elif checkpoint.checkpoint_type == CheckpointType.CONTENT:
            return ["e.g., 'key point 1: ...'", "e.g., 'main idea: ...'"]

        return []

    async def _analyze_checkpoint_response(
        self,
        response_text: str,
        checkpoint: UnassistedCapabilityCheckpoint,
    ) -> Tuple[CheckpointResponse, bool, float]:
        """
        Analyze user's response to checkpoint

        Returns:
            (response_type, demonstrated_capability, capability_score)
        """

        # Check for explicit delegation phrases
        delegation_phrases = [
            "just guess",
            "you decide",
            "you do it",
            "i don't know",
            "not sure",
            "whatever you think",
            "up to you",
        ]

        response_lower = response_text.lower().strip()

        # Check for delegation
        if any(phrase in response_lower for phrase in delegation_phrases):
            return CheckpointResponse.DELEGATED, False, 0.0

        # Check if response is too short (likely not thoughtful)
        if len(response_text.strip()) < 3:
            return CheckpointResponse.DELEGATED, False, 0.0

        # Check if response asks for clarification
        clarification_phrases = ["what do you mean", "can you explain", "clarify", "?"]
        if any(phrase in response_lower for phrase in clarification_phrases):
            return CheckpointResponse.CLARIFIED, False, 0.3

        # Otherwise, user provided an answer
        # Score based on length and expected level
        score = min(1.0, len(response_text) / 100.0)  # Basic scoring
        score = max(score, checkpoint.expected_knowledge_level * 0.8)

        return CheckpointResponse.PROVIDED, True, score

    async def _generate_final_output(
        self,
        copilot_request: CopilotRequest,
    ) -> str:
        """Generate final output using user's answers + AI filling gaps"""

        # Build context from user's responses
        user_context = ""
        for checkpoint, response in zip(
            copilot_request.checkpoints, copilot_request.responses
        ):
            if response.demonstrated_capability and response.response_text:
                user_context += f"- {checkpoint.probe_question}: {response.response_text}\n"
            else:
                user_context += f"- {checkpoint.probe_question}: [AI will decide]\n"

        prompt = f"""Complete this {copilot_request.task_category} task:

Original request: {copilot_request.original_request}

User provided these specifications:
{user_context}

Complete the task using:
1. User's specified answers where provided
2. Your best judgment for unspecified parts
3. High quality implementation

Return the final output.
"""

        response = await self.orchestrator.route_request(
            prompt=prompt,
            task_complexity=TaskComplexity.MODERATE,
            optimization_goal="quality",
        )

        return response["response"]

    async def _record_ari_snapshot(
        self,
        copilot_request: CopilotRequest,
    ) -> None:
        """Record ARI snapshot for capability measurement"""

        # Map copilot metrics to ARI metrics
        ari_score = copilot_request.overall_ari_score

        # High ARI = low AI reliance (user has capability)
        # Low ARI = high AI reliance (user delegated)
        ai_reliance = 1.0 - ari_score

        snapshot = AgencySnapshot(
            timestamp=datetime.now(),
            task_id=copilot_request.request_id,
            task_type=f"copilot_{copilot_request.task_category}",
            # Low ARI = loss of agency (delegated to AI)
            delta_agency=ari_score - 0.5,  # Positive if demonstrated capability
            bhir=0.9,  # Good benefit/input ratio
            task_efficacy=0.85,  # Task completed successfully
            # User skill measured by capability demonstration
            user_skill_before=ari_score,
            user_skill_after=ari_score,
            skill_development=0.0,  # Not a learning task, just measurement
            ai_reliance=ai_reliance,
            autonomy_retention=ari_score,  # High if user provided answers
            user_id=copilot_request.user_id,
            session_id=copilot_request.request_id,
            metadata={
                "mode": "copilot",
                "task_category": copilot_request.task_category,
                "high_ari_count": copilot_request.high_ari_count,
                "low_ari_count": copilot_request.low_ari_count,
                "total_checkpoints": len(copilot_request.checkpoints),
            },
        )

        await self.ari_monitor.record_snapshot(snapshot)

        logger.debug(
            f"ARI-Capability snapshot recorded: "
            f"score={ari_score:.2f}, ai_reliance={ai_reliance:.2f}"
        )

    async def _track_capability_gaps(
        self,
        copilot_request: CopilotRequest,
    ) -> None:
        """Track capability gaps in context manager for future reference"""

        # Identify gaps (delegated checkpoints)
        gaps = []
        for checkpoint, response in zip(
            copilot_request.checkpoints, copilot_request.responses
        ):
            if not response.demonstrated_capability:
                gaps.append(
                    {
                        "type": checkpoint.checkpoint_type.value,
                        "question": checkpoint.probe_question,
                    }
                )

        if not gaps:
            return  # No gaps to track

        # Store capability gaps as memories
        gap_summary = f"Capability gaps in {copilot_request.task_category}: " + ", ".join(
            g["type"] for g in gaps
        )

        await self.context_manager.add_memory(
            user_id=copilot_request.user_id,
            content=gap_summary,
            memory_type=MemoryType.SKILL,
            priority=MemoryPriority.MEDIUM,
            tags={"capability_gap", copilot_request.task_category},
            metadata={
                "gaps": gaps,
                "ari_score": copilot_request.overall_ari_score,
                "checkpoint_type": gaps[0]["type"] if gaps else "unknown",
                "request_id": copilot_request.request_id,
            },
        )

        logger.info(f"Tracked {len(gaps)} capability gaps for future reference")

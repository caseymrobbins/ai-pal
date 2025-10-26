"""
Integration of Learn About Me and Socratic Co-pilot with IntegratedACSystem.

Connects the new modes with existing FFE, context management, and orchestration.
"""

from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger

from ai_pal.ari.measurement import ARIMeasurementSystem, ARILevel, ARIDimension
from ai_pal.modes.learn_about_me import LearnAboutMeMode, DifficultyLevel
from ai_pal.modes.socratic_copilot import SocraticCopilot, TaskType, AssistanceLevel
from ai_pal.context.enhanced_context import EnhancedContextManager, MemoryType, MemoryPriority
from ai_pal.orchestration.multi_model import MultiModelOrchestrator


class ModeRouter:
    """
    Routes user requests to appropriate modes based on context and intent.

    Manages:
    - Learn About Me (explicit learning mode)
    - Socratic Co-pilot (embedded assessment)
    - Standard chat (when no assessment needed)
    """

    def __init__(
        self,
        ari_system: ARIMeasurementSystem,
        learn_about_me: LearnAboutMeMode,
        socratic_copilot: SocraticCopilot,
        context_manager: EnhancedContextManager,
        orchestrator: MultiModelOrchestrator,
        storage_dir: Optional[Path] = None
    ):
        """Initialize mode router."""
        self.ari_system = ari_system
        self.learn_about_me = learn_about_me
        self.socratic_copilot = socratic_copilot
        self.context_manager = context_manager
        self.orchestrator = orchestrator
        self.storage_dir = storage_dir or Path("./data/mode_router")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # Track active modes per user
        self.active_modes: Dict[str, str] = {}  # user_id -> mode_name

        # Track active sessions
        self.learn_sessions: Dict[str, str] = {}  # user_id -> session_id
        self.copilot_requests: Dict[str, str] = {}  # user_id -> request_id

        logger.info("Mode Router initialized")

    async def route_user_message(
        self,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Route user message to appropriate mode.

        Returns:
            Dict with:
            - mode: Active mode
            - response: Response to user
            - next_action: What user should do next
            - metadata: Mode-specific metadata
        """
        # Check if user has active Learn About Me session
        if user_id in self.learn_sessions:
            return await self._handle_learn_about_me(user_id, message)

        # Check if user has active Socratic Co-pilot request
        if user_id in self.copilot_requests:
            return await self._handle_socratic_copilot(user_id, message)

        # Detect mode based on message
        detected_mode = self._detect_mode_intent(message)

        if detected_mode == "learn_about_me":
            return await self._initiate_learn_about_me(user_id, message)

        elif detected_mode == "task_request":
            return await self._initiate_socratic_copilot(user_id, message)

        else:  # standard_chat
            return await self._handle_standard_chat(user_id, message)

    def _detect_mode_intent(self, message: str) -> str:
        """Detect which mode is appropriate for this message."""
        message_lower = message.lower()

        # Learn About Me signals
        learn_signals = [
            "deep dive", "learn about me", "test my knowledge",
            "challenge me", "explore an idea", "help me think",
            "teach me", "understand me better"
        ]
        if any(signal in message_lower for signal in learn_signals):
            return "learn_about_me"

        # Task request signals (for Socratic Co-pilot)
        task_signals = [
            "write code", "create a", "help me write",
            "draft", "design", "implement", "build"
        ]
        if any(signal in message_lower for signal in task_signals):
            return "task_request"

        return "standard_chat"

    # ========================================================================
    # Learn About Me Mode
    # ========================================================================

    async def _initiate_learn_about_me(
        self,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Initiate a Learn About Me session."""
        # Extract domain from message or ask
        domain = self._extract_domain(message)

        if not domain:
            return {
                "mode": "learn_about_me_setup",
                "response": "I'd love to dive deep with you! What domain would you like to explore?\n\nSome options:\n- Python Programming\n- Machine Learning\n- Creative Writing\n- Data Analysis\n- Or suggest your own!",
                "next_action": "specify_domain"
            }

        # Start session
        session = await self.learn_about_me.start_session(
            user_id=user_id,
            domain=domain
        )

        self.learn_sessions[user_id] = session.session_id
        self.active_modes[user_id] = "learn_about_me"

        # Get first question
        first_question = await self.learn_about_me.get_current_question(session.session_id)

        # Record in context
        await self.context_manager.add_memory(
            user_id=user_id,
            content=f"Started Learn About Me session in {domain} domain",
            memory_type=MemoryType.SYSTEM,
            priority=MemoryPriority.MEDIUM
        )

        return {
            "mode": "learn_about_me",
            "session_id": session.session_id,
            "domain": domain,
            "response": f"Great! Let's explore **{domain}**.\n\n🧠 **Deep Dive Mode Activated**\n\nI'll start with foundational questions and adapt to your level. You can say 'regular chat' anytime to switch back.\n\n{first_question.question_text}",
            "next_action": "answer_question",
            "difficulty": first_question.difficulty.value
        }

    async def _handle_learn_about_me(
        self,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle message in active Learn About Me session."""
        session_id = self.learn_sessions[user_id]

        # Check for opt-out commands
        message_lower = message.lower()
        if any(cmd in message_lower for cmd in ["regular chat", "exit", "stop", "switch mode"]):
            response = await self.learn_about_me.request_regular_chat(session_id)
            del self.learn_sessions[user_id]
            del self.active_modes[user_id]

            return {
                "mode": "standard_chat",
                "response": response,
                "next_action": "continue_chat"
            }

        # Check for "just answer" override
        if any(cmd in message_lower for cmd in ["just answer", "tell me", "give me the answer"]):
            response = await self.learn_about_me.request_just_answer(session_id)
            return {
                "mode": "learn_about_me",
                "session_id": session_id,
                "response": response,
                "next_action": "continue_or_exit"
            }

        # Submit response to current question
        current_question = await self.learn_about_me.get_current_question(session_id)
        result = await self.learn_about_me.submit_response(session_id, message)

        # Format response based on result
        response_parts = [result["feedback"]]

        if result["next_action"] == "scaffold":
            response_parts.append(f"\n{result['scaffold']}\n\nTake another shot at it!")
            next_action = "answer_question"

        elif result["next_action"] == "advance":
            if result.get("difficulty_increased"):
                response_parts.append("\n🎯 Moving to a higher difficulty level!\n")
            elif result.get("difficulty_decreased"):
                response_parts.append("\n📚 Let's solidify your foundation.\n")

            if result["next_question"]:
                response_parts.append(f"\n{result['next_question'].question_text}")
                next_action = "answer_question"
            else:
                next_action = "continue_chat"

        elif result["next_action"] == "complete":
            summary = await self.learn_about_me.get_session_summary(session_id)
            response_parts.append(f"\n\n📊 **Session Summary**:")
            response_parts.append(f"- Questions answered: {summary['questions_answered']}")
            response_parts.append(f"- Ceiling reached: {summary['demonstrated_ceiling']}")
            response_parts.append(f"- Duration: {summary['duration_minutes']:.1f} minutes")

            # Clean up
            del self.learn_sessions[user_id]
            del self.active_modes[user_id]
            next_action = "session_complete"

        else:
            next_action = "continue_chat"

        # Record achievement in context if high score
        if result["ari_score"].level == ARILevel.HIGH:
            await self.context_manager.add_memory(
                user_id=user_id,
                content=f"Demonstrated high capability in {current_question.domain} ({current_question.difficulty.value} level)",
                memory_type=MemoryType.ACHIEVEMENT,
                priority=MemoryPriority.HIGH
            )

        return {
            "mode": "learn_about_me",
            "session_id": session_id,
            "response": "\n".join(response_parts),
            "next_action": next_action,
            "ari_level": result["ari_score"].level.value,
            "current_difficulty": current_question.difficulty.value
        }

    # ========================================================================
    # Socratic Co-pilot Mode
    # ========================================================================

    async def _initiate_socratic_copilot(
        self,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Initiate Socratic Co-pilot for a task request."""
        # Process task request
        initial_response, task_request = await self.socratic_copilot.process_task_request(
            user_id=user_id,
            request=message
        )

        self.copilot_requests[user_id] = task_request.request_id
        self.active_modes[user_id] = "socratic_copilot"

        # Record in context
        await self.context_manager.add_memory(
            user_id=user_id,
            content=f"Task request: {message} (type: {task_request.task_type.value})",
            memory_type=MemoryType.CONTEXT,
            priority=MemoryPriority.MEDIUM
        )

        return {
            "mode": "socratic_copilot",
            "request_id": task_request.request_id,
            "task_type": task_request.task_type.value,
            "response": initial_response,
            "next_action": "answer_checkpoint",
            "total_checkpoints": len(task_request.checkpoints),
            "checkpoint_index": 0
        }

    async def _handle_socratic_copilot(
        self,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle response in active Socratic Co-pilot session."""
        request_id = self.copilot_requests[user_id]
        task_request = self.socratic_copilot.active_requests[request_id]

        message_lower = message.lower()

        # Check for override signals
        if any(signal in message_lower for signal in ["don't know", "not sure", "just guess", "you decide", "whatever", "idk"]):
            # Handle override
            checkpoint_index = task_request.checkpoints_completed
            result = await self.socratic_copilot.handle_user_override(
                request_id=request_id,
                checkpoint_index=checkpoint_index,
                override_type="just_guess"
            )

            # Record LOW ARI in context
            await self.context_manager.add_memory(
                user_id=user_id,
                content=f"Low ARI signal in {task_request.task_type.value} task",
                memory_type=MemoryType.SYSTEM,
                priority=MemoryPriority.MEDIUM
            )

        else:
            # Process checkpoint response
            checkpoint_index = task_request.checkpoints_completed
            result = await self.socratic_copilot.process_checkpoint_response(
                request_id=request_id,
                checkpoint_index=checkpoint_index,
                response=message
            )

        # Check if ready to complete
        if result["ready_to_complete"]:
            # Complete task
            output = await self.socratic_copilot.complete_task(request_id)

            # Record completion in context
            await self.context_manager.add_memory(
                user_id=user_id,
                content=f"Completed {task_request.task_type.value} task with {result['assistance_level'].value} assistance (ARI: {result['overall_ari'].value})",
                memory_type=MemoryType.ACHIEVEMENT,
                priority=MemoryPriority.MEDIUM
            )

            # Clean up
            del self.copilot_requests[user_id]
            del self.active_modes[user_id]

            response_parts = [result["message"], "\n", output]

            # Add note based on assistance level
            if result["assistance_level"] == AssistanceLevel.MINIMAL:
                response_parts.append("\n\n💡 You clearly have strong skills here. I focused on implementing your specifications.")
            elif result["assistance_level"] == AssistanceLevel.SUBSTANTIAL:
                response_parts.append("\n\n📚 I've added detailed explanations to help you learn. Let me know if you'd like me to explain any part!")

            return {
                "mode": "standard_chat",
                "response": "\n".join(response_parts),
                "next_action": "task_complete",
                "assistance_level": result["assistance_level"].value,
                "overall_ari": result["overall_ari"].value
            }

        else:
            # More checkpoints to process
            return {
                "mode": "socratic_copilot",
                "request_id": request_id,
                "response": result["message"],
                "next_action": "answer_checkpoint",
                "checkpoint_index": result["next_checkpoint_index"],
                "total_checkpoints": len(task_request.checkpoints),
                "measured_ari": result["measured_ari"].value
            }

    # ========================================================================
    # Standard Chat Mode
    # ========================================================================

    async def _handle_standard_chat(
        self,
        user_id: str,
        message: str
    ) -> Dict[str, Any]:
        """Handle standard chat (no special mode)."""
        # Use orchestrator for standard response
        result = await self.orchestrator.execute(
            task=message,
            context={"user_id": user_id}
        )

        response = result.get("response", "I'm here to help!")

        return {
            "mode": "standard_chat",
            "response": response,
            "next_action": "continue_chat"
        }

    # ========================================================================
    # Helpers
    # ========================================================================

    def _extract_domain(self, message: str) -> Optional[str]:
        """Extract domain from user message."""
        message_lower = message.lower()

        domain_keywords = {
            "python": "python_programming",
            "programming": "python_programming",
            "code": "python_programming",
            "machine learning": "machine_learning",
            "ml": "machine_learning",
            "ai": "machine_learning",
            "writing": "creative_writing",
            "analysis": "data_analysis",
            "data": "data_analysis"
        }

        for keyword, domain in domain_keywords.items():
            if keyword in message_lower:
                return domain

        return None

    async def get_user_ari_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of user's ARI across dimensions."""
        profile = self.ari_system.get_user_ari_profile(user_id)

        summary = {}
        for dimension, domains in profile.items():
            summary[dimension.value] = {}
            for domain, score in domains.items():
                summary[dimension.value][domain] = {
                    "level": score.level.value,
                    "confidence": score.confidence,
                    "measurement_count": score.measurement_count,
                    "last_measured": score.last_measured.isoformat()
                }

        return summary

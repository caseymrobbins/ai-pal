"""
Main Orchestrator - The Central Brain of AI Pal.

The orchestrator:
1. Manages user state and conversation history
2. Scrubs PII before sending to external LLMs
3. Routes tasks to specialized modules
4. Enforces ethics via the Ethics Module
5. Synthesizes final responses from multiple sources
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
from loguru import logger

from ai_pal.core.config import settings
from ai_pal.core.privacy import get_scrubber, ScrubResult
from ai_pal.core.hardware import get_hardware_info
from ai_pal.models.router import LLMRouter, TaskComplexity
from ai_pal.models.base import LLMRequest, LLMResponse
from ai_pal.modules.base import BaseModule, ModuleRequest, ModuleResponse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ai_pal.modules.ethics import EthicsModule


@dataclass
class OrchestratorRequest:
    """Request to the orchestrator."""

    user_id: str
    message: str
    context: Optional[Dict[str, Any]] = None
    prefer_local: bool = True
    enable_pii_scrubbing: bool = True


@dataclass
class OrchestratorResponse:
    """Response from the orchestrator."""

    message: str
    sources: List[str]
    pii_scrubbed: bool
    scrub_details: Optional[ScrubResult]
    ethics_check_passed: bool
    model_used: str
    processing_time_ms: float
    metadata: Dict[str, Any]
    timestamp: datetime


class Orchestrator:
    """
    The central orchestrator for AI Pal.

    This is the main brain that coordinates all modules and LLMs.
    """

    def __init__(self, ethics_module: 'EthicsModule'):
        self.ethics_module = ethics_module
        """Initialize orchestrator."""
        logger.info("Initializing AI Pal Orchestrator...")

        # Core components
        self.scrubber = get_scrubber() if settings.enable_pii_scrubbing else None
        self.router = LLMRouter()
        self.hardware_info = get_hardware_info()

        # Modules
        self.modules: Dict[str, BaseModule] = {}
        self.ethics_module: Optional[EthicsModule] = None

        # State
        self.initialized = False
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}

        logger.info("Orchestrator created")

    async def initialize(self) -> None:
        """Initialize orchestrator and all modules."""
        logger.info("Initializing orchestrator components...")

        # Initialize Ethics Module (required, non-optional)
        logger.info("Initializing Ethics Module...")
        self.ethics_module = EthicsModule()
        await self.ethics_module.initialize()
        self.modules["ethics"] = self.ethics_module

        # Initialize other enabled modules
        enabled_modules = settings.get_enabled_modules()
        logger.info(f"Enabled modules: {enabled_modules}")

        # Initialize local LLM if needed
        if self.router.local_provider:
            try:
                logger.info("Initializing local LLM...")
                await self.router.local_provider.initialize()
            except Exception as e:
                logger.warning(f"Failed to initialize local LLM: {e}")

        self.initialized = True
        logger.info("Orchestrator initialization complete")

    async def process(
        self, request: OrchestratorRequest
    ) -> OrchestratorResponse:
        """
        Process a user request.

        This is the main entry point for all user interactions.

        Args:
            request: Orchestrator request

        Returns:
            Orchestrator response
        """
        if not self.initialized:
            await self.initialize()

        start_time = datetime.now()
        sources = []
        pii_scrubbed = False
        scrub_details = None

        logger.info(f"Processing request from user {request.user_id}")

        # Step 1: PII Scrubbing (Privacy Layer)
        processed_message = request.message
        if request.enable_pii_scrubbing and self.scrubber:
            scrub_result = self.scrubber.scrub(request.message)

            if scrub_result.pii_detected:
                logger.warning(f"PII detected and scrubbed: {scrub_result}")
                processed_message = scrub_result.scrubbed_text
                pii_scrubbed = True
                scrub_details = scrub_result

        # Step 2: Ethics Check
        ethics_context = {
            "user_id": request.user_id,
            "message": processed_message,
            "pii_scrubbed": pii_scrubbed,
            **(request.context or {}),
        }

        ethics_request = ModuleRequest(
            task="check_request",
            context=ethics_context,
            user_id=request.user_id,
            timestamp=datetime.now(),
            metadata={},
        )

        ethics_response = await self.ethics_module.process(ethics_request)
        gates_result = ethics_response.result

        if not gates_result.overall_pass:
            logger.warning(f"Ethics check failed: {gates_result.blocking_gates}")

            return OrchestratorResponse(
                message=(
                    f"I cannot fulfill this request as it failed ethical validation:\n"
                    f"{', '.join(gates_result.blocking_gates)}\n\n"
                    f"This system is designed to expand your agency and autonomy, "
                    f"not to enable harmful actions."
                ),
                sources=["ethics_module"],
                pii_scrubbed=pii_scrubbed,
                scrub_details=scrub_details,
                ethics_check_passed=False,
                model_used="none",
                processing_time_ms=(datetime.now() - start_time).total_seconds()
                * 1000,
                metadata={"gates_result": str(gates_result)},
                timestamp=datetime.now(),
            )

        sources.append("ethics_check")

        # Step 3: Determine task complexity
        complexity = self._assess_complexity(processed_message, request.context or {})

        # Step 4: Route to specialized modules if needed
        module_responses = await self._route_to_modules(
            processed_message, request.user_id, request.context or {}
        )

        if module_responses:
            sources.extend(module_responses.keys())

        # Step 5: Generate response using LLM
        llm_request = self._build_llm_request(
            processed_message, request.context or {}, module_responses
        )

        llm_response = await self.router.generate(
            llm_request, complexity=complexity, prefer_local=request.prefer_local
        )

        sources.append(f"{llm_response.provider}:{llm_response.model_name}")

        # Step 6: Store conversation history
        self._store_conversation(
            request.user_id,
            request.message,
            llm_response.generated_text,
            pii_scrubbed=pii_scrubbed,
        )

        # Step 7: Build final response
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return OrchestratorResponse(
            message=llm_response.generated_text,
            sources=sources,
            pii_scrubbed=pii_scrubbed,
            scrub_details=scrub_details,
            ethics_check_passed=True,
            model_used=f"{llm_response.provider}:{llm_response.model}",
            processing_time_ms=processing_time,
            metadata={
                "llm_tokens": llm_response.tokens_used,
                "llm_cost": llm_response.cost_usd,
                "llm_latency_ms": llm_response.latency_ms,
                "complexity": complexity.value,
                "module_responses": len(module_responses),
            },
            timestamp=datetime.now(),
        )

    def _assess_complexity(
        self, message: str, context: Dict[str, Any]
    ) -> TaskComplexity:
        """
        Assess task complexity.

        Args:
            message: User message
            context: Request context

        Returns:
            Task complexity level
        """
        # Simple heuristics (would be ML-based in production)
        message_lower = message.lower()

        # Critical keywords
        critical_keywords = [
            "medical",
            "legal",
            "financial advice",
            "safety",
            "emergency",
        ]
        if any(kw in message_lower for kw in critical_keywords):
            return TaskComplexity.CRITICAL

        # Complex keywords
        complex_keywords = [
            "explain",
            "analyze",
            "compare",
            "design",
            "architect",
            "debug",
            "optimize",
        ]
        if any(kw in message_lower for kw in complex_keywords):
            return TaskComplexity.COMPLEX

        # Simple keywords
        simple_keywords = ["what is", "define", "hello", "hi", "thanks", "ok"]
        if any(kw in message_lower for kw in simple_keywords):
            return TaskComplexity.SIMPLE

        # Default to moderate
        return TaskComplexity.MODERATE

    async def _route_to_modules(
        self, message: str, user_id: str, context: Dict[str, Any]
    ) -> Dict[str, ModuleResponse]:
        """
        Route request to relevant specialized modules.

        Args:
            message: User message
            user_id: User ID
            context: Request context

        Returns:
            Module responses
        """
        responses: Dict[str, ModuleResponse] = {}

        # Determine which modules to invoke
        # (simplified - would use ML-based routing in production)

        # Echo Chamber Buster for controversial/complex topics
        if self._is_complex_topic(message):
            if "echo_chamber_buster" in self.modules:
                # Would invoke Echo Chamber Buster module
                pass

        # Learning Module for educational queries
        if self._is_learning_query(message):
            if "learning" in self.modules:
                # Would invoke Learning Module
                pass

        return responses

    def _is_complex_topic(self, message: str) -> bool:
        """Check if message is about a complex/controversial topic."""
        keywords = [
            "debate",
            "controversy",
            "argue",
            "perspective",
            "viewpoint",
            "opinion",
        ]
        return any(kw in message.lower() for kw in keywords)

    def _is_learning_query(self, message: str) -> bool:
        """Check if message is a learning-related query."""
        keywords = [
            "learn",
            "teach",
            "explain",
            "understand",
            "how does",
            "what is",
            "tutorial",
        ]
        return any(kw in message.lower() for kw in keywords)

    def _build_llm_request(
        self,
        message: str,
        context: Dict[str, Any],
        module_responses: Dict[str, ModuleResponse],
    ) -> LLMRequest:
        """
        Build LLM request with context from modules.

        Args:
            message: User message
            context: Request context
            module_responses: Responses from modules

        Returns:
            LLM request
        """
        # Build system prompt
        system_prompt = (
            "You are AI Pal, a privacy-first cognitive partner. "
            "Your goal is to expand the user's agency and autonomy. "
            "Always prioritize the user's learning and skill development. "
            "Never create harmful dependencies or deskill the user."
        )

        # Add module context if available
        if module_responses:
            system_prompt += "\n\nAdditional context from specialized modules:\n"
            for module_name, response in module_responses.items():
                system_prompt += f"\n{module_name}: {response.result}"

        # Build prompt
        prompt = message

        return LLMRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=context.get("max_tokens", 1000),
            temperature=context.get("temperature", 0.7),
        )

    def _store_conversation(
        self, user_id: str, user_message: str, ai_response: str, pii_scrubbed: bool
    ) -> None:
        """
        Store conversation in history.

        Args:
            user_id: User ID
            user_message: Original user message
            ai_response: AI response
            pii_scrubbed: Whether PII was scrubbed
        """
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        self.conversation_history[user_id].append(
            {
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message,
                "ai_response": ai_response,
                "pii_scrubbed": pii_scrubbed,
            }
        )

        # Limit history size
        max_history = 100
        if len(self.conversation_history[user_id]) > max_history:
            self.conversation_history[user_id] = self.conversation_history[user_id][
                -max_history:
            ]

    async def get_ethics_dashboard(self) -> Dict[str, Any]:
        """Get ethics metrics for dashboard."""
        if not self.ethics_module:
            return {"error": "Ethics module not initialized"}

        return self.ethics_module.get_dashboard_metrics()

    async def register_humanity_override(
        self, action_id: str, reason: str, user_id: str
    ) -> None:
        """Register a humanity override."""
        if self.ethics_module:
            self.ethics_module.register_humanity_override(action_id, reason, user_id)

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all components.

        Returns:
            Health status
        """
        health = {
            "orchestrator_initialized": self.initialized,
            "pii_scrubbing_enabled": settings.enable_pii_scrubbing,
            "ethics_module_active": (
                self.ethics_module is not None and self.ethics_module.initialized
            ),
            "modules": {},
            "llm_providers": {},
        }

        # Check modules
        for name, module in self.modules.items():
            health["modules"][name] = await module.health_check()

        # Check LLM providers
        health["llm_providers"] = await self.router.health_check_all()

        return health

    async def shutdown(self) -> None:
        """Shutdown orchestrator and all modules."""
        logger.info("Shutting down orchestrator...")

        # Shutdown modules
        for module in self.modules.values():
            try:
                await module.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down module {module.name}: {e}")

        self.initialized = False
        logger.info("Orchestrator shutdown complete")

    def __repr__(self) -> str:
        """String representation."""
        status = "initialized" if self.initialized else "not initialized"
        return f"<Orchestrator ({status}, {len(self.modules)} modules)>"

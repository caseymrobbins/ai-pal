"""
Echo Chamber Buster Module.

Provides balanced, multi-perspective analysis of complex topics using
a three-stage deliberation process:
1. The Critic - Challenges assumptions
2. The Challenger - Builds strongest counter-argument
3. The Synthesizer - Creates balanced conclusion
"""

from typing import Dict, Any
from datetime import datetime
from loguru import logger

from ai_pal.modules.base import BaseModule, ModuleRequest, ModuleResponse
from ai_pal.models.router import LLMRouter, TaskComplexity
from ai_pal.models.base import LLMRequest


class EchoChamberBuster(BaseModule):
    """Module for balanced multi-perspective analysis."""

    def __init__(self):
        super().__init__(
            name="echo_chamber_buster",
            description="Multi-perspective analysis using deliberative AI",
            version="0.1.0",
        )
        self.router: Optional[LLMRouter] = None

    async def initialize(self) -> None:
        """Initialize the module."""
        logger.info("Initializing Echo Chamber Buster module...")
        self.router = LLMRouter()
        self.initialized = True
        logger.info("Echo Chamber Buster module initialized")

    async def process(self, request: ModuleRequest) -> ModuleResponse:
        """
        Process a request for multi-perspective analysis.

        Workflow:
        1. Send to LLM A (The Critic) - Challenge the premise
        2. Send to LLM B (The Challenger) - Steel-man counter-argument
        3. Send to LLM C (The Synthesizer) - Balanced synthesis

        Args:
            request: Module request

        Returns:
            Module response with synthesized analysis
        """
        start_time = datetime.now()

        topic = request.task
        context = request.context

        logger.info(f"Running Echo Chamber Buster analysis on: {topic[:100]}...")

        # Stage 1: The Critic
        critic_response = await self._run_critic(topic, context)

        # Stage 2: The Challenger
        challenger_response = await self._run_challenger(
            topic, critic_response, context
        )

        # Stage 3: The Synthesizer
        synthesis = await self._run_synthesizer(
            topic, critic_response, challenger_response, context
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        result = {
            "synthesis": synthesis,
            "critic_perspective": critic_response,
            "challenger_perspective": challenger_response,
            "stages_completed": 3,
        }

        return ModuleResponse(
            result=result,
            confidence=0.85,
            metadata={
                "topic": topic[:200],
                "perspectives_considered": 3,
            },
            timestamp=datetime.now(),
            processing_time_ms=processing_time,
        )

    async def _run_critic(
        self, topic: str, context: Dict[str, Any]
    ) -> str:
        """
        Stage 1: The Critic

        Challenges assumptions, identifies flaws, questions the premise.
        """
        prompt = f"""You are The Critic in a deliberative reasoning process.

Your task is to critically analyze the following statement, question, or premise:

"{topic}"

Your goal:
- Challenge the core assumptions
- Identify logical flaws or gaps
- Question the framing of the issue
- Point out what might be missing or oversimplified
- Consider edge cases and exceptions

Be rigorous but constructive. Focus on intellectual honesty.

Provide your critical analysis:"""

        request = LLMRequest(
            prompt=prompt,
            system_prompt="You are a rigorous critical thinker who helps identify flaws in reasoning.",
            max_tokens=800,
            temperature=0.7,
        )

        response = await self.router.generate(
            request, complexity=TaskComplexity.COMPLEX, prefer_local=False
        )

        return response.text

    async def _run_challenger(
        self, topic: str, critic_response: str, context: Dict[str, Any]
    ) -> str:
        """
        Stage 2: The Challenger

        Builds the strongest possible defense of the original premise,
        responding to The Critic's points ("steel-manning").
        """
        prompt = f"""You are The Challenger in a deliberative reasoning process.

Original premise:
"{topic}"

The Critic has raised these concerns:
{critic_response}

Your task is to "steel-man" the original premise:
- Build the STRONGEST possible argument in its defense
- Address The Critic's concerns directly
- Provide evidence or reasoning that supports the premise
- Acknowledge valid criticisms while showing why the core idea still holds merit
- Be intellectually honest - strengthen, don't strawman

Provide your strongest defense of the premise:"""

        request = LLMRequest(
            prompt=prompt,
            system_prompt="You are a constructive debater who builds the strongest version of an argument.",
            max_tokens=800,
            temperature=0.7,
        )

        response = await self.router.generate(
            request, complexity=TaskComplexity.COMPLEX, prefer_local=False
        )

        return response.text

    async def _run_synthesizer(
        self,
        topic: str,
        critic_response: str,
        challenger_response: str,
        context: Dict[str, Any],
    ) -> str:
        """
        Stage 3: The Synthesizer

        Creates a balanced, nuanced synthesis of both perspectives.
        """
        prompt = f"""You are The Synthesizer in a deliberative reasoning process.

Original question/premise:
"{topic}"

The Critic's analysis (challenging the premise):
{critic_response}

The Challenger's defense (steel-manning the premise):
{challenger_response}

Your task is to synthesize these perspectives into a balanced, nuanced conclusion:
- Acknowledge valid points from both sides
- Identify areas of agreement and disagreement
- Highlight key insights from the deliberation
- Provide a balanced final perspective (1-2 paragraphs)
- Note remaining uncertainties or areas needing more exploration

Provide your synthesized conclusion:"""

        request = LLMRequest(
            prompt=prompt,
            system_prompt=(
                "You are a wise synthesizer who integrates multiple perspectives "
                "into balanced, nuanced conclusions."
            ),
            max_tokens=600,
            temperature=0.6,
        )

        response = await self.router.generate(
            request, complexity=TaskComplexity.COMPLEX, prefer_local=False
        )

        return response.text

    async def shutdown(self) -> None:
        """Cleanup resources."""
        logger.info("Shutting down Echo Chamber Buster module...")
        self.initialized = False

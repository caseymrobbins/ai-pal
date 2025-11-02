"""
Tests for Curiosity Compass - Exploration Opportunity Discovery

Tests the interface that transforms bottlenecks into curiosity-driven explorations.
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

from ai_pal.ffe.interfaces.curiosity_compass import (
    CuriosityCompass,
    CuriosityMap,
    ExplorationOpportunity,
)
from ai_pal.ffe.components.growth_scaffold import GrowthScaffold
from ai_pal.ffe.components.scoping_agent import ScopingAgent
from ai_pal.ffe.components.strength_amplifier import StrengthAmplifier
from ai_pal.ffe.models import (
    BottleneckTask,
    BottleneckReason,
    SignatureStrength,
    StrengthType,
    AtomicBlock,
    TimeBlockSize,
)


@pytest.fixture
def test_user_id():
    """Test user ID"""
    return "test_user_compass"


@pytest.fixture
def mock_growth_scaffold():
    """Mock GrowthScaffold for testing"""
    class MockGrowthScaffold:
        def __init__(self):
            self.bottlenecks = []
            self.next_bottleneck_index = 0

        async def detect_bottlenecks(self, user_id, lookback_days=90):
            """Return mock bottlenecks"""
            return self.bottlenecks

        async def get_next_bottleneck(self, user_id):
            """Return next bottleneck"""
            if self.next_bottleneck_index < len(self.bottlenecks):
                bottleneck = self.bottlenecks[self.next_bottleneck_index]
                self.next_bottleneck_index += 1
                return bottleneck
            return None

        def add_bottleneck(self, bottleneck):
            """Add bottleneck for testing"""
            self.bottlenecks.append(bottleneck)

    return MockGrowthScaffold()


@pytest.fixture
def mock_scoping_agent():
    """Mock ScopingAgent for testing"""
    class MockScopingAgent:
        async def scope_task(self, task, complexity):
            """Mock scoping"""
            return [
                AtomicBlock(
                    user_id="test_user",
                    goal_id="goal_1",
                    title=f"Explore {task[:30]}",
                    description=f"15-minute exploration of {task}",
                    time_block_size=TimeBlockSize.SPRINT_15,
                )
            ]

    return MockScopingAgent()


@pytest.fixture
def mock_strength_amplifier():
    """Mock StrengthAmplifier for testing"""
    class MockStrengthAmplifier:
        async def reframe_task_via_strength(self, task, strength):
            """Mock reframing"""
            return f"{task} [reframed via {strength.identity_label}]"

    return MockStrengthAmplifier()


@pytest.fixture
def curiosity_compass(mock_growth_scaffold, mock_scoping_agent, mock_strength_amplifier):
    """Create CuriosityCompass instance"""
    return CuriosityCompass(
        growth_scaffold=mock_growth_scaffold,
        scoping_agent=mock_scoping_agent,
        strength_amplifier=mock_strength_amplifier,
    )


@pytest.fixture
def sample_bottlenecks(test_user_id):
    """Create sample bottlenecks for testing"""
    return [
        BottleneckTask(
            bottleneck_id="bn_1",
            user_id=test_user_id,
            task_description="Learn advanced Python decorators",
            bottleneck_reason=BottleneckReason.DIFFICULT,
            avoidance_count=3,
        ),
        BottleneckTask(
            bottleneck_id="bn_2",
            user_id=test_user_id,
            task_description="Write documentation for API",
            bottleneck_reason=BottleneckReason.BORING,
            avoidance_count=1,
        ),
        BottleneckTask(
            bottleneck_id="bn_3",
            user_id=test_user_id,
            task_description="Refactor legacy codebase",
            bottleneck_reason=BottleneckReason.ANXIETY_INDUCING,
            avoidance_count=5,
        ),
        BottleneckTask(
            bottleneck_id="bn_4",
            user_id=test_user_id,
            task_description="Set up CI/CD pipeline",
            bottleneck_reason=BottleneckReason.SKILL_GAP,
            avoidance_count=2,
        ),
        BottleneckTask(
            bottleneck_id="bn_5",
            user_id=test_user_id,
            task_description="Organize project files",
            bottleneck_reason=BottleneckReason.AVOIDED,
            avoidance_count=4,
        ),
    ]


class TestCuriosityCompassInitialization:
    """Test Curiosity Compass initialization"""

    def test_initialization(self, curiosity_compass):
        """Test: Compass initializes correctly"""
        assert curiosity_compass is not None
        assert curiosity_compass.growth_scaffold is not None
        assert curiosity_compass.scoping_agent is not None
        assert curiosity_compass.strength_amplifier is not None

    def test_curiosity_frames_loaded(self, curiosity_compass):
        """Test: Curiosity frames for all bottleneck reasons"""
        assert len(curiosity_compass.curiosity_frames) == 6

        # Check each reason has templates
        for reason in BottleneckReason:
            assert reason in curiosity_compass.curiosity_frames
            templates = curiosity_compass.curiosity_frames[reason]
            assert len(templates) > 0
            # Each template should have {task} placeholder
            assert all("{task}" in t for t in templates)


class TestCuriosityMap:
    """Test curiosity map generation"""

    @pytest.mark.asyncio
    async def test_show_empty_map(self, curiosity_compass, test_user_id):
        """Test: Show map with no bottlenecks"""
        curiosity_map = await curiosity_compass.show_curiosity_map(test_user_id)

        assert isinstance(curiosity_map, CuriosityMap)
        assert curiosity_map.user_id == test_user_id
        assert len(curiosity_map.unexplored_areas) == 0
        assert len(curiosity_map.exploration_suggestions) == 0

    @pytest.mark.asyncio
    async def test_show_map_with_bottlenecks(
        self, curiosity_compass, test_user_id, sample_bottlenecks
    ):
        """Test: Show map with bottlenecks"""
        # Add bottlenecks to growth scaffold
        for bn in sample_bottlenecks:
            curiosity_compass.growth_scaffold.add_bottleneck(bn)

        curiosity_map = await curiosity_compass.show_curiosity_map(test_user_id)

        # Should have all bottlenecks as unexplored areas
        assert len(curiosity_map.unexplored_areas) == len(sample_bottlenecks)

        # Should have up to 5 suggestions (top 5)
        assert len(curiosity_map.exploration_suggestions) <= 5
        assert len(curiosity_map.exploration_suggestions) > 0

    @pytest.mark.asyncio
    async def test_map_suggestions_structure(
        self, curiosity_compass, test_user_id, sample_bottlenecks
    ):
        """Test: Map suggestions have correct structure"""
        curiosity_compass.growth_scaffold.add_bottleneck(sample_bottlenecks[0])

        curiosity_map = await curiosity_compass.show_curiosity_map(test_user_id)

        suggestion = curiosity_map.exploration_suggestions[0]
        assert "bottleneck_id" in suggestion
        assert "task" in suggestion
        assert "reason" in suggestion
        assert "curiosity_prompt" in suggestion
        assert "duration" in suggestion
        assert "commitment_level" in suggestion
        assert suggestion["duration"] == "15 minutes"

    @pytest.mark.asyncio
    async def test_map_limits_suggestions(
        self, curiosity_compass, test_user_id, sample_bottlenecks
    ):
        """Test: Map shows max 5 suggestions even with more bottlenecks"""
        # Add 10 bottlenecks
        for i in range(10):
            bn = BottleneckTask(
                bottleneck_id=f"bn_{i}",
                user_id=test_user_id,
                task_description=f"Task {i}",
                bottleneck_reason=BottleneckReason.DIFFICULT,
                avoidance_count=1,
            )
            curiosity_compass.growth_scaffold.add_bottleneck(bn)

        curiosity_map = await curiosity_compass.show_curiosity_map(test_user_id)

        # Should have all 10 as unexplored
        assert len(curiosity_map.unexplored_areas) == 10

        # But only top 5 as suggestions
        assert len(curiosity_map.exploration_suggestions) == 5


class TestExplorationSuggestions:
    """Test exploration opportunity suggestions"""

    @pytest.mark.asyncio
    async def test_suggest_exploration(
        self, curiosity_compass, test_user_id, sample_bottlenecks
    ):
        """Test: Suggest exploration from bottleneck"""
        curiosity_compass.growth_scaffold.add_bottleneck(sample_bottlenecks[0])

        opportunity = await curiosity_compass.suggest_exploration(test_user_id)

        assert isinstance(opportunity, ExplorationOpportunity)
        assert opportunity.user_id == test_user_id
        assert opportunity.bottleneck_id == sample_bottlenecks[0].bottleneck_id
        assert opportunity.exploration_prompt is not None
        assert len(opportunity.exploration_prompt) > 0

    @pytest.mark.asyncio
    async def test_suggest_no_bottlenecks(self, curiosity_compass, test_user_id):
        """Test: Suggest with no bottlenecks returns None"""
        opportunity = await curiosity_compass.suggest_exploration(test_user_id)

        assert opportunity is None

    @pytest.mark.asyncio
    async def test_exploration_opportunity_structure(
        self, curiosity_compass, test_user_id, sample_bottlenecks
    ):
        """Test: Exploration opportunity has complete structure"""
        curiosity_compass.growth_scaffold.add_bottleneck(sample_bottlenecks[0])

        opportunity = await curiosity_compass.suggest_exploration(test_user_id)

        # Core fields
        assert opportunity.opportunity_id is not None
        assert opportunity.bottleneck_id == sample_bottlenecks[0].bottleneck_id
        assert opportunity.avoided_task == sample_bottlenecks[0].task_description
        assert opportunity.avoidance_reason == sample_bottlenecks[0].bottleneck_reason

        # Exploration details
        assert opportunity.exploration_prompt is not None
        assert isinstance(opportunity.exploration_block, AtomicBlock)
        assert opportunity.exploration_block.time_block_size == TimeBlockSize.SPRINT_15

        # Discovery potential
        assert len(opportunity.what_you_might_discover) > 0
        assert opportunity.why_this_is_interesting is not None

        # Safety messages
        assert "15 minutes" in opportunity.no_commitment_message
        assert "stop" in opportunity.escape_hatch.lower()

    @pytest.mark.asyncio
    async def test_exploration_with_strength_reframe(
        self, curiosity_compass, test_user_id, sample_bottlenecks
    ):
        """Test: Exploration with strength reframing"""
        curiosity_compass.growth_scaffold.add_bottleneck(sample_bottlenecks[0])

        strength = SignatureStrength(
            strength_type=StrengthType.ANALYTICAL,
            identity_label="Problem Solver",
            strength_description="Breaks problems into pieces",
            confidence_score=0.8,
        )

        opportunity = await curiosity_compass.suggest_exploration(
            user_id=test_user_id,
            strength=strength
        )

        # Should have strength reframe
        assert opportunity.exploration_block.strength_reframe is not None
        assert "Problem Solver" in opportunity.exploration_block.strength_reframe


class TestCuriosityFraming:
    """Test curiosity-driven framing for different bottleneck reasons"""

    @pytest.mark.asyncio
    async def test_avoided_task_framing(self, curiosity_compass, test_user_id):
        """Test: Avoided tasks get exploration framing"""
        bn = BottleneckTask(
            bottleneck_id="bn_avoided",
            user_id=test_user_id,
            task_description="Clean up old code",
            bottleneck_reason=BottleneckReason.AVOIDED,
            avoidance_count=1,
        )
        curiosity_compass.growth_scaffold.add_bottleneck(bn)

        opportunity = await curiosity_compass.suggest_exploration(test_user_id)

        prompt = opportunity.exploration_prompt.lower()
        # Should have low-stakes language
        assert any(word in prompt for word in ["peek", "explore", "curious", "wonder"])

    @pytest.mark.asyncio
    async def test_difficult_task_framing(self, curiosity_compass, test_user_id):
        """Test: Difficult tasks get puzzle framing"""
        bn = BottleneckTask(
            bottleneck_id="bn_difficult",
            user_id=test_user_id,
            task_description="Implement complex algorithm",
            bottleneck_reason=BottleneckReason.DIFFICULT,
            avoidance_count=1,
        )
        curiosity_compass.growth_scaffold.add_bottleneck(bn)

        opportunity = await curiosity_compass.suggest_exploration(test_user_id)

        prompt = opportunity.exploration_prompt.lower()
        # Should frame as interesting puzzle
        assert any(word in prompt for word in ["tricky", "puzzle", "interesting", "curious"])

    @pytest.mark.asyncio
    async def test_boring_task_framing(self, curiosity_compass, test_user_id):
        """Test: Boring tasks get hidden-depth framing"""
        bn = BottleneckTask(
            bottleneck_id="bn_boring",
            user_id=test_user_id,
            task_description="Update documentation",
            bottleneck_reason=BottleneckReason.BORING,
            avoidance_count=1,
        )
        curiosity_compass.growth_scaffold.add_bottleneck(bn)

        opportunity = await curiosity_compass.suggest_exploration(test_user_id)

        prompt = opportunity.exploration_prompt.lower()
        # Should suggest hidden interest
        assert any(word in prompt for word in ["interesting", "find", "angle", "hiding"])

    @pytest.mark.asyncio
    async def test_anxiety_task_framing(self, curiosity_compass, test_user_id):
        """Test: Anxiety-inducing tasks get safety framing"""
        bn = BottleneckTask(
            bottleneck_id="bn_anxiety",
            user_id=test_user_id,
            task_description="Present project to team",
            bottleneck_reason=BottleneckReason.ANXIETY_INDUCING,
            avoidance_count=1,
        )
        curiosity_compass.growth_scaffold.add_bottleneck(bn)

        opportunity = await curiosity_compass.suggest_exploration(test_user_id)

        prompt = opportunity.exploration_prompt.lower()
        # Should emphasize safety and low pressure
        assert any(word in prompt for word in ["safe", "pressure", "distance", "curious"])

    @pytest.mark.asyncio
    async def test_skill_gap_framing(self, curiosity_compass, test_user_id):
        """Test: Skill gaps get learning framing"""
        bn = BottleneckTask(
            bottleneck_id="bn_skill",
            user_id=test_user_id,
            task_description="Learn TypeScript",
            bottleneck_reason=BottleneckReason.SKILL_GAP,
            avoidance_count=1,
        )
        curiosity_compass.growth_scaffold.add_bottleneck(bn)

        opportunity = await curiosity_compass.suggest_exploration(test_user_id)

        prompt = opportunity.exploration_prompt.lower()
        # Should focus on learning opportunity
        assert any(word in prompt for word in ["learn", "skill", "discover", "curious"])


class TestDiscoveryTracking:
    """Test discovery recording and celebration"""

    @pytest.mark.asyncio
    async def test_record_discovery(self, curiosity_compass, test_user_id):
        """Test: Record user discovery"""
        discovery = "I learned that decorators are just higher-order functions!"

        result = await curiosity_compass.record_discovery(
            user_id=test_user_id,
            bottleneck_id="bn_1",
            discovery=discovery,
            wants_to_continue=False
        )

        assert result is not None
        assert result["discovery"] == discovery
        assert "celebration_message" in result
        assert "wants_more" in result
        assert result["wants_more"] is False
        assert "closure_message" in result

    @pytest.mark.asyncio
    async def test_discovery_celebration(self, curiosity_compass, test_user_id):
        """Test: Discovery gets celebration message"""
        result = await curiosity_compass.record_discovery(
            user_id=test_user_id,
            bottleneck_id="bn_1",
            discovery="Found a better approach!",
            wants_to_continue=False
        )

        celebration = result["celebration_message"]
        assert len(celebration) > 0
        # Should celebrate discovery
        assert any(word in celebration.lower() for word in [
            "fascinating", "great", "excellent", "discovery", "learned", "uncovered"
        ])

    @pytest.mark.asyncio
    async def test_discovery_with_continue(
        self, curiosity_compass, test_user_id, sample_bottlenecks
    ):
        """Test: Discovery with want to continue suggests next exploration"""
        # Add bottleneck for next exploration
        curiosity_compass.growth_scaffold.add_bottleneck(sample_bottlenecks[0])

        result = await curiosity_compass.record_discovery(
            user_id=test_user_id,
            bottleneck_id="bn_1",
            discovery="This is fascinating!",
            wants_to_continue=True
        )

        assert result["wants_more"] is True
        assert result["next_exploration"] is not None
        assert isinstance(result["next_exploration"], ExplorationOpportunity)

    @pytest.mark.asyncio
    async def test_discovery_without_continue(self, curiosity_compass, test_user_id):
        """Test: Discovery without continue gives closure"""
        result = await curiosity_compass.record_discovery(
            user_id=test_user_id,
            bottleneck_id="bn_1",
            discovery="Interesting insight",
            wants_to_continue=False
        )

        assert result["wants_more"] is False
        assert result["next_exploration"] is None
        assert "closure_message" in result
        assert "come back" in result["closure_message"].lower()


class TestDiscoveryLog:
    """Test discovery history"""

    @pytest.mark.asyncio
    async def test_get_discovery_log(self, curiosity_compass, test_user_id):
        """Test: Get discovery log"""
        log = await curiosity_compass.get_discovery_log(test_user_id)

        # Structure exists (even if empty in mock)
        assert isinstance(log, list)

    @pytest.mark.asyncio
    async def test_discovery_log_with_lookback(self, curiosity_compass, test_user_id):
        """Test: Discovery log with lookback period"""
        log = await curiosity_compass.get_discovery_log(
            user_id=test_user_id,
            lookback_days=7
        )

        assert isinstance(log, list)


class TestDiscoveryPotential:
    """Test discovery potential generation"""

    @pytest.mark.asyncio
    async def test_generate_discovery_potential(
        self, curiosity_compass, sample_bottlenecks
    ):
        """Test: Generate what user might discover"""
        discoveries = await curiosity_compass._generate_discovery_potential(
            sample_bottlenecks[0]
        )

        assert len(discoveries) > 0
        # Should mention the task
        task = sample_bottlenecks[0].task_description
        assert any(task in d for d in discoveries)

    @pytest.mark.asyncio
    async def test_discovery_potential_structure(
        self, curiosity_compass, sample_bottlenecks
    ):
        """Test: Discovery potential has encouraging structure"""
        discoveries = await curiosity_compass._generate_discovery_potential(
            sample_bottlenecks[0]
        )

        # Each discovery should be a reasonable sentence
        for discovery in discoveries:
            assert len(discovery) > 10
            assert isinstance(discovery, str)


class TestInterestingExplanations:
    """Test why-interesting explanations"""

    @pytest.mark.asyncio
    async def test_explain_why_interesting_avoided(self, curiosity_compass):
        """Test: Explanation for avoided tasks"""
        bn = BottleneckTask(
            bottleneck_id="bn_1",
            user_id="test",
            task_description="Test task",
            bottleneck_reason=BottleneckReason.AVOIDED,
            avoidance_count=1,
        )

        explanation = await curiosity_compass._explain_why_interesting(bn)

        assert len(explanation) > 0
        assert "avoid" in explanation.lower()

    @pytest.mark.asyncio
    async def test_explain_why_interesting_difficult(self, curiosity_compass):
        """Test: Explanation for difficult tasks"""
        bn = BottleneckTask(
            bottleneck_id="bn_1",
            user_id="test",
            task_description="Test task",
            bottleneck_reason=BottleneckReason.DIFFICULT,
            avoidance_count=1,
        )

        explanation = await curiosity_compass._explain_why_interesting(bn)

        assert "puzzle" in explanation.lower() or "interesting" in explanation.lower()

    @pytest.mark.asyncio
    async def test_explain_why_interesting_all_reasons(self, curiosity_compass):
        """Test: Explanation exists for all bottleneck reasons"""
        for reason in BottleneckReason:
            bn = BottleneckTask(
                bottleneck_id="bn_1",
                user_id="test",
                task_description="Test task",
                bottleneck_reason=reason,
                avoidance_count=1,
            )

            explanation = await curiosity_compass._explain_why_interesting(bn)

            assert explanation is not None
            assert len(explanation) > 0


class TestExplorationBlocks:
    """Test 15-minute exploration block creation"""

    @pytest.mark.asyncio
    async def test_exploration_block_is_15_minutes(
        self, curiosity_compass, test_user_id, sample_bottlenecks
    ):
        """Test: Exploration blocks are always 15 minutes"""
        curiosity_compass.growth_scaffold.add_bottleneck(sample_bottlenecks[0])

        opportunity = await curiosity_compass.suggest_exploration(test_user_id)

        assert opportunity.exploration_block.time_block_size == TimeBlockSize.SPRINT_15

    @pytest.mark.asyncio
    async def test_exploration_block_has_title(
        self, curiosity_compass, test_user_id, sample_bottlenecks
    ):
        """Test: Exploration block has descriptive title"""
        curiosity_compass.growth_scaffold.add_bottleneck(sample_bottlenecks[0])

        opportunity = await curiosity_compass.suggest_exploration(test_user_id)

        title = opportunity.exploration_block.title
        assert "Explore" in title or "explore" in title
        assert len(title) > 0

    @pytest.mark.asyncio
    async def test_exploration_block_preserves_original(
        self, curiosity_compass, test_user_id, sample_bottlenecks
    ):
        """Test: Exploration block preserves original task description"""
        curiosity_compass.growth_scaffold.add_bottleneck(sample_bottlenecks[0])

        opportunity = await curiosity_compass.suggest_exploration(test_user_id)

        assert opportunity.exploration_block.original_description == sample_bottlenecks[0].task_description


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_empty_task_description(self, curiosity_compass, test_user_id):
        """Test: Empty task description handled"""
        bn = BottleneckTask(
            bottleneck_id="bn_empty",
            user_id=test_user_id,
            task_description="",
            bottleneck_reason=BottleneckReason.UNCLEAR,
            avoidance_count=1,
        )
        curiosity_compass.growth_scaffold.add_bottleneck(bn)

        # Should still create opportunity
        opportunity = await curiosity_compass.suggest_exploration(test_user_id)

        assert opportunity is not None

    @pytest.mark.asyncio
    async def test_very_long_task_description(self, curiosity_compass, test_user_id):
        """Test: Very long task descriptions handled"""
        long_task = "A" * 500  # Very long task

        bn = BottleneckTask(
            bottleneck_id="bn_long",
            user_id=test_user_id,
            task_description=long_task,
            bottleneck_reason=BottleneckReason.DIFFICULT,
            avoidance_count=1,
        )
        curiosity_compass.growth_scaffold.add_bottleneck(bn)

        opportunity = await curiosity_compass.suggest_exploration(test_user_id)

        # Should truncate or handle gracefully
        assert opportunity is not None
        # Title should be truncated (max 50 chars + "Explore: ")
        assert len(opportunity.exploration_block.title) < 70

    @pytest.mark.asyncio
    async def test_unknown_bottleneck_reason(self, curiosity_compass, test_user_id):
        """Test: Unknown bottleneck reasons use default framing"""
        # This tests the fallback behavior
        suggestion = await curiosity_compass._create_exploration_suggestion(
            BottleneckTask(
                bottleneck_id="bn_test",
                user_id=test_user_id,
                task_description="Test task",
                bottleneck_reason=BottleneckReason.UNCLEAR,
                avoidance_count=1,
            )
        )

        # Should still have curiosity prompt
        assert "curiosity_prompt" in suggestion
        assert len(suggestion["curiosity_prompt"]) > 0


class TestSafetyMessages:
    """Test safety and reassurance messaging"""

    @pytest.mark.asyncio
    async def test_no_commitment_message(
        self, curiosity_compass, test_user_id, sample_bottlenecks
    ):
        """Test: Every exploration has no-commitment message"""
        curiosity_compass.growth_scaffold.add_bottleneck(sample_bottlenecks[0])

        opportunity = await curiosity_compass.suggest_exploration(test_user_id)

        assert opportunity.no_commitment_message is not None
        assert "15 minutes" in opportunity.no_commitment_message
        assert any(word in opportunity.no_commitment_message.lower() for word in [
            "just", "explore", "no pressure", "no commitment"
        ])

    @pytest.mark.asyncio
    async def test_escape_hatch_message(
        self, curiosity_compass, test_user_id, sample_bottlenecks
    ):
        """Test: Every exploration has escape hatch"""
        curiosity_compass.growth_scaffold.add_bottleneck(sample_bottlenecks[0])

        opportunity = await curiosity_compass.suggest_exploration(test_user_id)

        assert opportunity.escape_hatch is not None
        assert any(word in opportunity.escape_hatch.lower() for word in [
            "stop", "anytime", "leave", "exit"
        ])


class TestIntegration:
    """Test integration between components"""

    @pytest.mark.asyncio
    async def test_full_exploration_workflow(
        self, curiosity_compass, test_user_id, sample_bottlenecks
    ):
        """Test: Complete exploration workflow"""
        # 1. Add bottlenecks
        for bn in sample_bottlenecks:
            curiosity_compass.growth_scaffold.add_bottleneck(bn)

        # 2. Show curiosity map
        curiosity_map = await curiosity_compass.show_curiosity_map(test_user_id)
        assert len(curiosity_map.unexplored_areas) == len(sample_bottlenecks)

        # 3. Suggest exploration
        opportunity = await curiosity_compass.suggest_exploration(test_user_id)
        assert opportunity is not None

        # 4. Record discovery
        result = await curiosity_compass.record_discovery(
            user_id=test_user_id,
            bottleneck_id=opportunity.bottleneck_id,
            discovery="Found it interesting!",
            wants_to_continue=True
        )
        assert result["wants_more"] is True
        assert result["next_exploration"] is not None

        # 5. Get discovery log
        log = await curiosity_compass.get_discovery_log(test_user_id)
        assert isinstance(log, list)

    @pytest.mark.asyncio
    async def test_multiple_explorations_sequence(
        self, curiosity_compass, test_user_id, sample_bottlenecks
    ):
        """Test: Multiple explorations in sequence"""
        # Add multiple bottlenecks
        for bn in sample_bottlenecks[:3]:
            curiosity_compass.growth_scaffold.add_bottleneck(bn)

        # Get three explorations in sequence
        opportunities = []
        for i in range(3):
            opp = await curiosity_compass.suggest_exploration(test_user_id)
            assert opp is not None
            opportunities.append(opp)

        # Should have gotten 3 different bottlenecks
        bottleneck_ids = [opp.bottleneck_id for opp in opportunities]
        assert len(set(bottleneck_ids)) == 3  # All unique

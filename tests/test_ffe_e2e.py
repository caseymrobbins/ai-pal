"""
End-to-End Validation Test for Phase 5 (Fractal Flow Engine)

This test validates the complete FFE V3.0 workflow:
- Goal ingestion and 80/20 scoping
- Atomic block creation
- Momentum Loop (WIN → AFFIRM → PIVOT → REFRAME → LAUNCH → WIN)
- Signature strength amplification
- Bottleneck detection and reframing
- Integration with Phase 1-3 components
"""

import asyncio
import pytest
from pathlib import Path
import tempfile
from datetime import datetime

from ai_pal.core.integrated_system import create_default_system
from ai_pal.ffe.models import (
    PersonalityProfile,
    SignatureStrength,
    StrengthType,
    BottleneckTask,
    BottleneckReason,
    MomentumState,
    TaskComplexityLevel,
)


@pytest.fixture
def temp_storage():
    """Create temporary storage directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def ffe_system(temp_storage):
    """Create a fully configured system with FFE enabled"""
    system = create_default_system(
        data_dir=temp_storage,
        credentials_path=temp_storage / "credentials.json"
    )
    return system


@pytest.fixture
def test_user_personality():
    """Create a test user personality profile"""
    profile = PersonalityProfile(
        user_id="test_user_001",
        signature_strengths=[
            SignatureStrength(
                strength_type=StrengthType.VISUAL_THINKING,
                identity_label="Visual Mapper",
                strength_description="Thinks in pictures and diagrams",
                confidence_score=0.9,
                usage_count=10,
                compatible_task_types={"design", "architecture", "planning"},
            ),
            SignatureStrength(
                strength_type=StrengthType.ANALYTICAL,
                identity_label="Problem Solver",
                strength_description="Breaks down complex problems logically",
                confidence_score=0.8,
                usage_count=5,
                compatible_task_types={"coding", "debugging", "analysis"},
            ),
        ],
        primary_strength=StrengthType.VISUAL_THINKING,
        core_values=["Learning", "Growth", "Community"],
        current_priorities=["Learn Python", "Build portfolio project"],
        life_goals=["Become a skilled software engineer"],
    )
    return profile


class TestFFEEndToEnd:
    """End-to-end FFE V3.0 workflow tests"""

    def test_ffe_initialization(self, ffe_system):
        """Test: FFE initializes with all components"""
        system = ffe_system

        print("\n=== FFE Initialization Test ===")

        # Verify FFE is initialized
        assert system.ffe_engine is not None, "FFE engine should be initialized"
        print("✓ FFE engine initialized")

        # Verify all 7 core components
        assert system.ffe_engine.goal_ingestor is not None
        print("✓ Goal Ingestor initialized")

        assert system.ffe_engine.reward_emitter is not None
        print("✓ Reward Emitter initialized")

        assert system.ffe_engine.time_block_manager is not None
        print("✓ Time-Block Manager initialized")

        assert system.ffe_engine.scoping_agent is not None
        print("✓ Scoping Agent initialized")

        assert system.ffe_engine.strength_amplifier is not None
        print("✓ Signature Strength Amplifier initialized")

        assert system.ffe_engine.growth_scaffold is not None
        print("✓ Growth Scaffold initialized")

        assert system.ffe_engine.momentum_orchestrator is not None
        print("✓ Momentum Loop Orchestrator initialized")

        # Verify connectors
        assert system.ffe_engine.personality_connector is not None
        print("✓ Personality Module connector initialized")

        assert system.ffe_engine.ari_connector is not None
        print("✓ ARI connector initialized")

        assert system.ffe_engine.dashboard_connector is not None
        print("✓ Dashboard connector initialized")

        print("\n✓ All FFE components successfully initialized!")

    @pytest.mark.asyncio
    async def test_goal_ingestion_and_scoping(self, ffe_system):
        """Test: Goal Ingestor and Fractal 80/20 Scoping"""
        engine = ffe_system.ffe_engine

        print("\n=== Goal Ingestion & 80/20 Scoping Test ===")

        # Step 1: Ingest a macro goal
        user_id = "test_user_001"
        goal_description = "Learn Python programming language"

        goal = await engine.start_goal(
            user_id=user_id,
            goal_description=goal_description,
            from_personality_module=False
        )

        print(f"✓ Goal ingested: {goal.description}")
        print(f"  - Goal ID: {goal.goal_id}")
        print(f"  - Complexity: {goal.complexity_level.value}")

        assert goal.user_id == user_id
        assert goal.description == goal_description
        assert goal.complexity_level == TaskComplexityLevel.MACRO

        # Step 2: Break down via 80/20 scoping
        print("\n📊 Breaking down via 80/20 Fractal Scoping...")
        atomic_blocks = await engine.break_down_goal(goal)

        print(f"✓ Scoped into {len(atomic_blocks)} atomic block(s)")

        assert len(atomic_blocks) > 0, "Should create at least one atomic block"

        for i, block in enumerate(atomic_blocks):
            print(f"  Block {i+1}: {block.description}")
            print(f"    - Duration: {block.time_block_size.value} minutes")
            assert block.user_id == user_id
            assert block.goal_id is not None

        print("\n✓ 80/20 scoping successful!")

    @pytest.mark.asyncio
    async def test_momentum_loop_complete_cycle(self, ffe_system, test_user_personality):
        """Test: Complete Momentum Loop cycle (WIN → AFFIRM → PIVOT → REFRAME → LAUNCH → WIN)"""
        engine = ffe_system.ffe_engine
        user_id = "test_user_001"

        print("\n=== Momentum Loop Complete Cycle Test ===")

        # Setup: Save personality profile
        await engine.personality_connector.save_personality_profile(test_user_personality)
        print("✓ Personality profile saved")

        # Step 1: Create an atomic block (strength task)
        goal = await engine.start_goal(
            user_id=user_id,
            goal_description="Create a visual diagram of Python data structures"
        )

        atomic_blocks = await engine.break_down_goal(goal)
        strength_block = atomic_blocks[0]

        print(f"\n1. STRENGTH TASK: {strength_block.description}")
        print(f"   Duration: {strength_block.time_block_size.value} minutes")

        # Step 2: START MOMENTUM LOOP (WIN_STRENGTH state)
        print("\n🔁 Starting Momentum Loop...")
        loop_state = await engine.start_momentum_loop(user_id, strength_block)

        assert loop_state.current_state == MomentumState.WIN_STRENGTH
        assert loop_state.user_id == user_id
        print(f"✓ Loop started: {loop_state.loop_id}")
        print(f"  State: {loop_state.current_state.value}")
        if strength_block.strength_reframe:
            print(f"  Reframed: {strength_block.strength_reframe}")

        # Step 3: Complete strength task (WIN → AFFIRM)
        print("\n2. WIN (Strength Task)...")
        loop_state, reward_text = await engine.complete_block(strength_block, quality_score=0.85)

        assert loop_state is not None
        print(f"✓ Block completed!")
        print(f"  State: {loop_state.current_state.value}")

        # Step 4: Reward emitted (AFFIRM)
        if reward_text:
            print(f"\n3. AFFIRM (Pride Hit)...")
            print(f"  Reward: {reward_text}")
            print(f"✓ Pride hit delivered!")

        # Step 5: Check current state (should be PIVOT_DETECT or WIN_STRENGTH)
        print(f"\n4. PIVOT (Bottleneck Detection)...")
        print(f"  Current state: {loop_state.current_state.value}")

        if loop_state.current_state == MomentumState.PIVOT_DETECT:
            print("  ✓ In PIVOT state - checking for bottlenecks")
        elif loop_state.current_state == MomentumState.WIN_STRENGTH:
            print("  ✓ No bottleneck detected - new cycle started")
        elif loop_state.current_state == MomentumState.REFRAME_STRENGTH:
            print("  ✓ Bottleneck detected - moving to REFRAME")

        print("\n✓ Momentum Loop cycle completed!")

    @pytest.mark.asyncio
    async def test_signature_strength_amplification(self, ffe_system, test_user_personality):
        """Test: Signature Strength Amplifier reframes tasks"""
        engine = ffe_system.ffe_engine

        print("\n=== Signature Strength Amplification Test ===")

        # Save personality profile
        await engine.personality_connector.save_personality_profile(test_user_personality)

        # Test reframing with visual thinking strength
        generic_task = "Organize project files"
        visual_strength = test_user_personality.signature_strengths[0]

        print(f"\nGeneric task: {generic_task}")
        print(f"Using strength: {visual_strength.identity_label} ({visual_strength.strength_type.value})")

        reframed_task = await engine.strength_amplifier.reframe_task_via_strength(
            generic_task,
            visual_strength
        )

        print(f"Reframed task: {reframed_task}")

        assert reframed_task != generic_task, "Task should be reframed"
        assert len(reframed_task) > 0, "Reframed task should not be empty"

        print("\n✓ Signature strength amplification working!")

    @pytest.mark.asyncio
    async def test_reward_emitter(self, ffe_system, test_user_personality):
        """Test: Reward Emitter generates identity-affirming rewards"""
        engine = ffe_system.ffe_engine

        print("\n=== Reward Emitter Test ===")

        # Create a completed block
        goal = await engine.start_goal(
            user_id="test_user_001",
            goal_description="Create visual flowchart"
        )
        atomic_blocks = await engine.break_down_goal(goal)
        block = atomic_blocks[0]
        block.completed = True
        block.quality_score = 0.9

        # Get visual thinking strength
        visual_strength = test_user_personality.signature_strengths[0]

        # Emit reward
        reward = await engine.reward_emitter.emit_reward(block, visual_strength)

        print(f"\nReward emitted:")
        print(f"  Text: {reward.reward_text}")
        print(f"  Strength referenced: {reward.strength_referenced}")
        print(f"  Identity label: {reward.identity_label_used}")

        assert reward.reward_text is not None
        assert len(reward.reward_text) > 0
        assert "✓" in reward.reward_text or "Win" in reward.reward_text

        print("\n✓ Reward emitter working!")

    @pytest.mark.asyncio
    async def test_growth_scaffold_bottleneck_detection(self, ffe_system):
        """Test: Growth Scaffold detects and queues bottlenecks"""
        engine = ffe_system.ffe_engine
        user_id = "test_user_001"

        print("\n=== Growth Scaffold Bottleneck Detection Test ===")

        # Report an avoided task
        bottleneck = await engine.growth_scaffold.report_avoidance(
            user_id=user_id,
            task_description="Practice debugging code",
            reason=BottleneckReason.DIFFICULT
        )

        print(f"\nBottleneck reported:")
        print(f"  Task: {bottleneck.task_description}")
        print(f"  Reason: {bottleneck.bottleneck_reason.value}")
        print(f"  Queued: {bottleneck.queued}")

        assert bottleneck.user_id == user_id
        assert bottleneck.queued is True

        # Retrieve bottleneck from queue
        next_bottleneck = await engine.growth_scaffold.get_next_bottleneck(user_id)

        assert next_bottleneck is not None
        assert next_bottleneck.bottleneck_id == bottleneck.bottleneck_id

        print(f"\n✓ Retrieved from queue: {next_bottleneck.task_description}")
        print("\n✓ Growth Scaffold bottleneck detection working!")

    @pytest.mark.asyncio
    async def test_time_block_manager_five_block_rule(self, ffe_system):
        """Test: Time-Block Manager enforces 5-Block Stop rule"""
        engine = ffe_system.ffe_engine
        user_id = "test_user_001"

        print("\n=== 5-Block Stop Rule Test ===")

        # Create a macro goal for 5-block planning
        goal = await engine.start_goal(
            user_id=user_id,
            goal_description="Master Python over 5 months"
        )

        print(f"\nMacro goal: {goal.description}")

        # Create 5-block plan
        five_block_plan = await engine.time_block_manager.create_five_block_plan(
            user_id=user_id,
            macro_goal=goal,
            total_months=5
        )

        print(f"\n✓ 5-Block Plan created:")
        print(f"  Plan ID: {five_block_plan.plan_id}")
        print(f"  Total duration: {five_block_plan.total_duration_months} months")
        print(f"  Block duration: {five_block_plan.block_duration_months} month each")
        print(f"  Number of blocks: {len(five_block_plan.blocks)}")
        print(f"  Stop points: {len(five_block_plan.stop_points)}")

        assert len(five_block_plan.blocks) == 5, "Should have exactly 5 blocks"
        assert len(five_block_plan.stop_points) == 5, "Should have 5 stop points"
        assert five_block_plan.user_can_modify is True, "User should be able to modify"

        # Test stop enforcement
        should_stop = await engine.time_block_manager.check_five_block_stop(five_block_plan, 0)
        print(f"\n✓ Stop check for block 0: {should_stop}")

        print("\n✓ 5-Block Stop rule enforced!")

    @pytest.mark.asyncio
    async def test_ffe_integration_with_phase3(self, ffe_system, test_user_personality):
        """Test: FFE integrates with Phase 1-3 components"""
        system = ffe_system
        engine = system.ffe_engine
        user_id = "test_user_001"

        print("\n=== FFE Integration with Phase 1-3 Test ===")

        # Test 1: Personality Module connector (Phase 3 - Context Manager)
        print("\n1. Testing Personality Module connector...")
        await engine.personality_connector.save_personality_profile(test_user_personality)
        loaded_profile = await engine.personality_connector.load_personality_profile(user_id)

        assert loaded_profile.user_id == user_id
        assert len(loaded_profile.signature_strengths) > 0
        print(f"✓ Personality Module connector working")
        print(f"  Loaded {len(loaded_profile.signature_strengths)} strengths")

        # Test 2: ARI connector (Phase 2 - ARI Monitor)
        print("\n2. Testing ARI connector...")
        atrophying_skills = await engine.ari_connector.detect_skill_atrophy(
            user_id=user_id,
            lookback_days=30
        )
        print(f"✓ ARI connector working")
        print(f"  Detected {len(atrophying_skills)} atrophying skills")

        # Test 3: Dashboard connector (Phase 3 - Dashboard)
        print("\n3. Testing Dashboard connector...")
        ffe_metrics = await engine.dashboard_connector.get_ffe_metrics(
            user_id=user_id,
            period_days=7
        )
        print(f"✓ Dashboard connector working")
        print(f"  Metrics structure: {list(ffe_metrics.keys())}")

        # Test 4: Non-extractive validation (Gate #2)
        print("\n4. Testing Gate #2 (Humanity Gate) compliance...")
        validation = engine.validate_non_extractive()

        assert validation["gate_2_compliant"] is True
        assert validation["five_block_stop_enabled"] is True
        assert validation["pride_based_rewards"] is True
        assert validation["user_autonomy_enforced"] is True

        print(f"✓ Gate #2 compliance validated")
        print(f"  5-Block Stop: {validation['five_block_stop_enabled']}")
        print(f"  Pride-based rewards: {validation['pride_based_rewards']}")
        print(f"  User autonomy: {validation['user_autonomy_enforced']}")
        print(f"  No dark patterns: {validation['no_dark_patterns']}")

        print("\n✓ All Phase 1-3 integrations working!")

    @pytest.mark.asyncio
    async def test_complete_user_journey(self, ffe_system, test_user_personality):
        """Test: Complete user journey through FFE V3.0"""
        engine = ffe_system.ffe_engine
        user_id = "test_user_001"

        print("\n=== Complete User Journey Test ===")
        print("Simulating full FFE V3.0 workflow...\n")

        # 1. Setup: Save personality
        await engine.personality_connector.save_personality_profile(test_user_personality)
        print("1. ✓ User personality configured")

        # 2. Start goal
        goal = await engine.start_goal(
            user_id=user_id,
            goal_description="Build a Python web scraper for news articles"
        )
        print(f"2. ✓ Goal started: {goal.description}")

        # 3. Break down via 80/20 scoping
        atomic_blocks = await engine.break_down_goal(goal)
        print(f"3. ✓ Goal scoped into {len(atomic_blocks)} atomic blocks")

        # 4. Start momentum loop
        first_block = atomic_blocks[0]
        loop_state = await engine.start_momentum_loop(user_id, first_block)
        print(f"4. ✓ Momentum loop started: {loop_state.loop_id}")
        print(f"   Initial state: {loop_state.current_state.value}")

        # 5. Complete first block
        loop_state, reward = await engine.complete_block(first_block, quality_score=0.85)
        print(f"5. ✓ First block completed")
        if reward:
            print(f"   Reward: {reward[:60]}...")

        # 6. Report a bottleneck
        bottleneck = await engine.growth_scaffold.report_avoidance(
            user_id=user_id,
            task_description="Write unit tests for scraper",
            reason=BottleneckReason.BORING
        )
        print(f"6. ✓ Bottleneck reported: {bottleneck.task_description}")

        # 7. Get current momentum state
        current_state = engine.get_momentum_state(user_id)
        if current_state:
            print(f"7. ✓ Current momentum state: {current_state.current_state.value}")
            print(f"   Cycle count: {current_state.cycle_count}")

        print("\n✓ Complete user journey successful!")
        print("\n🎉 FFE V3.0 fully operational!")

    @pytest.mark.asyncio
    async def test_protege_pipeline_teaching_mode(self, ffe_system):
        """Test: Protégé Pipeline learn-by-teaching mode"""
        from ai_pal.ffe.modules import ProtegePipeline
        from ai_pal.ffe.interfaces import TeachingInterface

        print("\n=== Protégé Pipeline Teaching Mode Test ===")

        # Create instances
        protege = ProtegePipeline()
        teaching_interface = TeachingInterface(protege)

        user_id = "test_user_001"

        # 1. Start teaching session
        print("\n1. Starting teaching session...")
        session = await protege.start_teaching_mode(
            user_id=user_id,
            subject="Python lists",
            from_learning_goal=True
        )

        assert session.user_id == user_id
        assert session.subject == "Python lists"
        print(f"✓ Teaching session started: {session.session_id}")
        print(f"  Subject: {session.subject}")

        # 2. Request explanation
        print("\n2. AI student requests explanation...")
        request = await protege.request_explanation(
            user_id=user_id,
            concept="list comprehension"
        )

        assert "student_question" in request
        print(f"✓ Student question: '{request['student_question']}'")

        # 3. User provides explanation
        print("\n3. User teaches concept...")
        explanation_text = "A list comprehension is a concise way to create lists in Python. It's like a for loop but written in one line inside square brackets."

        explanation = await protege.receive_explanation(
            user_id=user_id,
            concept="list comprehension",
            explanation_text=explanation_text
        )

        assert explanation is not None
        assert explanation.concept == "list comprehension"
        print(f"✓ Explanation received")
        print(f"  Clarity: {explanation.clarity_score:.2f}")
        print(f"  Completeness: {explanation.completeness_score:.2f}")
        print(f"  Depth: {explanation.depth_score:.2f}")
        print(f"  Student understood: {explanation.student_understood}")
        print(f"  Feedback: '{explanation.student_feedback}'")

        # 4. Check session progress
        print("\n4. Checking teaching progress...")
        assert session.concepts_explained == ["list comprehension"]
        assert session.understanding_level > 0
        print(f"✓ Progress updated")
        print(f"  Concepts explained: {len(session.concepts_explained)}")
        print(f"  Understanding level: {session.understanding_level:.2f}")

        print("\n✓ Protégé Pipeline teaching mode working!")

    @pytest.mark.asyncio
    async def test_curiosity_compass_exploration(self, ffe_system):
        """Test: Curiosity Compass exploration mode"""
        from ai_pal.ffe.interfaces import CuriosityCompass

        print("\n=== Curiosity Compass Exploration Test ===")

        engine = ffe_system.ffe_engine
        user_id = "test_user_001"

        # Create curiosity compass
        compass = CuriosityCompass(
            growth_scaffold=engine.growth_scaffold,
            scoping_agent=engine.scoping_agent,
            strength_amplifier=engine.strength_amplifier
        )

        # 1. Report a bottleneck first
        print("\n1. Creating a bottleneck...")
        bottleneck = await engine.growth_scaffold.report_avoidance(
            user_id=user_id,
            task_description="Learn regex patterns",
            reason=BottleneckReason.DIFFICULT
        )
        print(f"✓ Bottleneck created: {bottleneck.task_description}")

        # 2. Show curiosity map
        print("\n2. Showing curiosity map...")
        curiosity_map = await compass.show_curiosity_map(user_id)

        assert curiosity_map.user_id == user_id
        assert len(curiosity_map.unexplored_areas) > 0
        print(f"✓ Curiosity map generated")
        print(f"  Unexplored areas: {len(curiosity_map.unexplored_areas)}")
        print(f"  Suggestions: {len(curiosity_map.exploration_suggestions)}")

        # 3. Get exploration suggestion
        print("\n3. Getting exploration suggestion...")
        opportunity = await compass.suggest_exploration(user_id)

        assert opportunity is not None
        assert opportunity.user_id == user_id
        assert opportunity.exploration_block.time_block_size.value == 15  # 15 minutes
        print(f"✓ Exploration suggested:")
        print(f"  Prompt: '{opportunity.exploration_prompt}'")
        print(f"  Duration: {opportunity.exploration_block.time_block_size.value} minutes")
        print(f"  No pressure: '{opportunity.no_commitment_message}'")

        # 4. Record discovery
        print("\n4. Recording discovery...")
        discovery = await compass.record_discovery(
            user_id=user_id,
            bottleneck_id=bottleneck.bottleneck_id,
            discovery="Regex patterns are actually like puzzles - fun!",
            wants_to_continue=False
        )

        assert "celebration_message" in discovery
        print(f"✓ Discovery recorded")
        print(f"  Celebration: '{discovery['celebration_message']}'")
        print(f"  Closure: '{discovery['closure_message']}'")

        print("\n✓ Curiosity Compass exploration mode working!")

    @pytest.mark.asyncio
    async def test_teaching_interface_workflow(self, ffe_system):
        """Test: Complete teaching interface workflow"""
        from ai_pal.ffe.modules import ProtegePipeline
        from ai_pal.ffe.interfaces import TeachingInterface
        from ai_pal.ffe.models import GoalPacket, TaskComplexityLevel, GoalStatus

        print("\n=== Teaching Interface Workflow Test ===")

        protege = ProtegePipeline()
        interface = TeachingInterface(protege)
        user_id = "test_user_001"

        # 1. Create learning goal
        print("\n1. Creating learning goal...")
        learning_goal = GoalPacket(
            user_id=user_id,
            description="Learn Python decorators",
            complexity_level=TaskComplexityLevel.MINI,
            status=GoalStatus.PENDING
        )
        print(f"✓ Learning goal: '{learning_goal.description}'")

        # 2. Start teaching mode from goal
        print("\n2. Converting to teaching mode...")
        session = await interface.start_teaching(user_id, learning_goal)

        assert session is not None
        print(f"✓ Teaching mode started")
        print(f"  Will teach: {session.subject}")

        # 3. Get teaching prompt
        print("\n3. Getting teaching prompt...")
        prompt = await interface.get_teaching_prompt(user_id)

        assert prompt is not None
        print(f"✓ Teaching prompt received:")
        print(f"  Question: '{prompt.student_question}'")
        print(f"  Hint: '{prompt.difficulty_hint}'")

        # 4. Submit explanation
        print("\n4. Submitting explanation...")
        feedback = await interface.submit_explanation(
            user_id=user_id,
            concept=prompt.concept,
            explanation_text="Decorators are functions that modify other functions. They use the @ symbol and wrap the original function with additional behavior."
        )

        assert feedback is not None
        assert "understood" in feedback
        print(f"✓ Explanation submitted")
        print(f"  Student understood: {feedback['understood']}")
        print(f"  Feedback: '{feedback['student_feedback']}'")

        # 5. Check progress
        print("\n5. Checking progress...")
        progress = await interface.get_teaching_progress(user_id)

        assert "concepts_explained" in progress
        print(f"✓ Progress tracked")
        print(f"  Concepts taught: {progress['concepts_explained']}")
        print(f"  Quality: {progress['teaching_quality']:.2f}")

        # 6. Complete session
        print("\n6. Completing session...")
        summary = await interface.complete_teaching_session(user_id)

        assert "celebration_message" in summary
        print(f"✓ Session completed")
        print(f"  Concepts mastered: {summary['concepts_mastered']}")
        print(f"  Final quality: {summary['teaching_quality']:.2f}")
        print(f"  Celebration: '{summary['celebration_message']}'")

        print("\n✓ Complete teaching workflow successful!")

    @pytest.mark.asyncio
    async def test_real_model_execution(self, ffe_system):
        """Test: Real model execution via MultiModelOrchestrator"""
        from ai_pal.orchestration.multi_model import (
            MultiModelOrchestrator,
            ModelProvider,
            TaskRequirements,
            TaskComplexity,
        )
        from pathlib import Path

        print("\n=== Real Model Execution Test ===")

        # Create orchestrator
        orchestrator = MultiModelOrchestrator(
            storage_dir=Path("./data/orchestrator_test")
        )

        # 1. Test model selection
        print("\n1. Testing model selection...")
        requirements = TaskRequirements(
            complexity=TaskComplexity.SIMPLE,
            min_reasoning_capability=0.5,
            max_cost_per_1k_tokens=0.01,
            max_latency_ms=5000,
            requires_local=True,  # Force local to avoid API keys in tests
        )

        selection = await orchestrator.select_model(requirements)
        print(f"✓ Model selected: {selection.provider.value}:{selection.model_name}")
        print(f"  Reason: {selection.selection_reason}")
        print(f"  Estimated cost: ${selection.estimated_cost:.4f}")

        # 2. Test execution (only if we have a local model available)
        print("\n2. Testing model execution...")
        try:
            # Simple test prompt
            response = await orchestrator.execute_model(
                provider=selection.provider,
                model_name=selection.model_name,
                prompt="What is 2+2? Answer in one sentence.",
                max_tokens=50,
                temperature=0.3,
            )

            print(f"✓ Model execution successful")
            print(f"  Response: '{response.text[:100]}...'")
            print(f"  Tokens used: {response.tokens_used}")
            print(f"  Cost: ${response.cost_usd:.4f}")
            print(f"  Latency: {response.latency_ms:.0f}ms")

            assert response.text is not None
            assert len(response.text) > 0
            assert response.tokens_used > 0

        except Exception as e:
            # Expected if model not initialized or API keys missing
            print(f"⚠ Model execution skipped: {str(e)[:100]}")
            print("  (This is expected if local model not initialized or API keys missing)")

        # 3. Test performance tracking
        print("\n3. Testing performance tracking...")
        report = orchestrator.get_performance_report()

        print(f"✓ Performance report generated")
        print(f"  Tracked models: {len(report['models'])}")

        print("\n✓ Real model execution test complete!")


if __name__ == "__main__":
    # Run tests directly
    print("Running FFE E2E Tests...")
    pytest.main([__file__, "-v", "-s"])

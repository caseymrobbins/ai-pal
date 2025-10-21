"""
Learning Module example demonstrating VARK-based personalization.
"""

import asyncio
from datetime import datetime
from ai_pal.modules.learning import LearningModule, VARKStyle
from ai_pal.modules.base import ModuleRequest


async def main():
    """Run Learning Module example."""
    print("Learning Module - VARK Personalization Example\n")

    # Initialize module
    print("Initializing Learning Module...")
    learning = LearningModule()
    await learning.initialize()
    print("✓ Initialized\n")

    # Test different learning styles
    styles_to_test = [
        VARKStyle.VISUAL,
        VARKStyle.AURAL,
        VARKStyle.READ_WRITE,
        VARKStyle.KINESTHETIC,
    ]

    for style in styles_to_test:
        print(f"\n{'=' * 80}")
        print(f"Testing {style.value.upper()} learning style")
        print('=' * 80)

        # Create request with style preference
        request = ModuleRequest(
            task="Explain how neural networks work",
            context={
                "style_preferences": {
                    "prefers_diagrams": style == VARKStyle.VISUAL,
                    "prefers_audio": style == VARKStyle.AURAL,
                    "prefers_text": style == VARKStyle.READ_WRITE,
                    "prefers_practice": style == VARKStyle.KINESTHETIC,
                },
                "domain": "machine_learning",
            },
            user_id=f"user_{style.value}",
            timestamp=datetime.now(),
            metadata={},
        )

        # Process
        response = await learning.process(request)
        result = response.result

        print(f"\nAdapted for: {result['style']}")
        print(f"Suggestion: {result['suggestion']}")
        print(f"Adaptations: {result['adaptations']}")
        print(f"Challenge level: {result['challenge_level']:.2f}")

        print(f"\nMetadata:")
        print(f"  - Learning style: {response.metadata['learning_style']}")
        print(f"  - Skill level: {response.metadata['skill_level']}")
        print(f"  - Learning velocity: {response.metadata['learning_velocity']:.2f}")

    # Test skill progression
    print(f"\n{'=' * 80}")
    print("Testing Skill Progression")
    print('=' * 80)

    user_id = "progression_test_user"

    for i in range(5):
        print(f"\nSession {i + 1}:")

        request = ModuleRequest(
            task="Practice Python coding",
            context={
                "domain": "python_programming",
                "task_success": True,  # User successfully completed the task
            },
            user_id=user_id,
            timestamp=datetime.now(),
            metadata={},
        )

        response = await learning.process(request)

        # Get profile to see progression
        if user_id in learning.learning_profiles:
            profile = learning.learning_profiles[user_id]
            skill = profile.skill_level.get("python_programming", 0.0)
            velocity = profile.learning_velocity

            print(f"  Skill level: {skill:.3f}")
            print(f"  Learning velocity: {velocity:.3f}")

    # Cleanup
    await learning.shutdown()
    print("\n✓ Example complete!")


if __name__ == "__main__":
    asyncio.run(main())

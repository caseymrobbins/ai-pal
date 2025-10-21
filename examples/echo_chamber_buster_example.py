"""
Echo Chamber Buster example.

Demonstrates multi-perspective analysis of a controversial topic.
"""

import asyncio
from datetime import datetime
from ai_pal.modules.echo_chamber_buster import EchoChamberBuster
from ai_pal.modules.base import ModuleRequest


async def main():
    """Run Echo Chamber Buster example."""
    print("Echo Chamber Buster - Multi-Perspective Analysis Example\n")

    # Initialize module
    print("Initializing Echo Chamber Buster...")
    ecb = EchoChamberBuster()
    await ecb.initialize()
    print("✓ Initialized\n")

    # Topic to analyze
    topic = (
        "Artificial Intelligence will be beneficial for humanity in the long run."
    )

    print(f"Topic: {topic}\n")
    print("Running three-stage deliberation...\n")

    # Create request
    request = ModuleRequest(
        task=topic,
        context={},
        user_id="example_user",
        timestamp=datetime.now(),
        metadata={},
    )

    # Process
    print("Stage 1: The Critic (challenging assumptions)...")
    response = await ecb.process(request)

    result = response.result

    print(f"✓ Complete ({response.processing_time_ms:.0f}ms)\n")

    # Display results
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)

    print("\n[CRITIC'S PERSPECTIVE]")
    print("-" * 80)
    print(result["critic_perspective"])

    print("\n\n[CHALLENGER'S PERSPECTIVE]")
    print("-" * 80)
    print(result["challenger_perspective"])

    print("\n\n[SYNTHESIZED CONCLUSION]")
    print("-" * 80)
    print(result["synthesis"])

    print("\n" + "=" * 80)
    print(f"Stages completed: {result['stages_completed']}")
    print(f"Confidence: {response.confidence:.2f}")
    print("=" * 80)

    # Cleanup
    await ecb.shutdown()
    print("\n✓ Example complete!")


if __name__ == "__main__":
    asyncio.run(main())

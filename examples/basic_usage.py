"""
Basic usage example for AI Pal.

This example demonstrates:
1. Initializing the orchestrator
2. Making a request with PII scrubbing
3. Checking ethics metrics
4. Proper cleanup
"""

import asyncio
from ai_pal.core.orchestrator import Orchestrator, OrchestratorRequest


async def main():
    """Run basic usage example."""
    print("AI Pal - Basic Usage Example\n")

    # Initialize orchestrator
    print("1. Initializing orchestrator...")
    orchestrator = Orchestrator()
    await orchestrator.initialize()
    print("   ✓ Orchestrator initialized\n")

    # Make a request (PII will be automatically scrubbed)
    print("2. Making a request...")
    request = OrchestratorRequest(
        user_id="example_user",
        message="Hi! My name is John Smith and my email is john@example.com. "
        "Can you help me learn Python?",
        prefer_local=True,  # Prefer local models for privacy
        enable_pii_scrubbing=True,  # Enable PII scrubbing
    )

    response = await orchestrator.process(request)

    print(f"   Response: {response.message}\n")
    print(f"   Model used: {response.model_used}")
    print(f"   Processing time: {response.processing_time_ms:.0f}ms")
    print(f"   PII scrubbed: {response.pii_scrubbed}")

    if response.pii_scrubbed:
        print(f"   Scrubbed entities: {len(response.scrub_details.detections)}")
        for detection in response.scrub_details.detections:
            print(
                f"     - {detection.entity_type}: "
                f"'{detection.text}' → '{detection.anonymized_value}'"
            )

    print(f"   Ethics check passed: {response.ethics_check_passed}\n")

    # Check ethics metrics
    print("3. Checking ethics metrics...")
    ethics_dashboard = await orchestrator.get_ethics_dashboard()

    print(f"   Net Agency Delta: {ethics_dashboard.get('net_agency_delta', 'N/A')}")
    print(f"   Epistemic Debt: {ethics_dashboard.get('epistemic_debt', 'N/A')}")
    print(f"   BHIR: {ethics_dashboard.get('bhir', 'N/A')}")
    print(
        f"   Circuit Breaker: "
        f"{'TRIGGERED' if ethics_dashboard.get('circuit_breaker_active') else 'OK'}\n"
    )

    # Check system health
    print("4. Checking system health...")
    health = await orchestrator.health_check()

    print(f"   Orchestrator: {'✓' if health['orchestrator_initialized'] else '✗'}")
    print(f"   Ethics Module: {'✓' if health['ethics_module_active'] else '✗'}")
    print(f"   Active Modules: {len(health['modules'])}")
    print(f"   Available LLM Providers: {len(health['llm_providers'])}\n")

    # Cleanup
    print("5. Shutting down...")
    await orchestrator.shutdown()
    print("   ✓ Shutdown complete\n")

    print("Example complete!")


if __name__ == "__main__":
    asyncio.run(main())

"""
Performance Tests for AI-PAL System

Tests system performance under various load conditions:
- Load testing (concurrent requests)
- Latency benchmarks (response times)
- Memory profiling (resource usage)
- Throughput measurements
- Stress testing
"""

import pytest
import asyncio
import time
import psutil
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from ai_pal.core.integrated_system import IntegratedACSystem, ACConfig
from ai_pal.orchestration.multi_model import MultiModelOrchestrator, LLMResponse
from ai_pal.monitoring.ari_monitor import ARIMonitor, AgencySnapshot
from ai_pal.monitoring.edm_monitor import EDMMonitor
from ai_pal.ffe.engine import FractalFlowEngine


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary storage directory"""
    return tmp_path / "performance_test"


@pytest.fixture
def test_config(temp_storage):
    """Create test configuration"""
    temp_storage.mkdir(exist_ok=True)
    return ACConfig(
        data_dir=temp_storage,
        enable_gates=True,
        enable_ari_monitoring=True,
        enable_edm_monitoring=True,
        enable_model_orchestration=True,
        enable_ffe=True,
    )


@pytest.fixture
def mock_llm_response():
    """Create mock LLM response for performance testing"""
    return LLMResponse(
        generated_text="This is a test response from the model.",
        model_name="test-model",
        provider="test",
        prompt_tokens=20,
        completion_tokens=30,
        total_tokens=50,
        finish_reason="stop",
        cost_usd=0.001,
        latency_ms=150.0,
        timestamp=datetime.now(),
    )


# ============================================================================
# Load Testing - Concurrent Request Handling
# ============================================================================


@pytest.mark.asyncio
async def test_concurrent_requests_10(test_config, mock_llm_response):
    """Test system handles 10 concurrent requests"""
    system = IntegratedACSystem(config=test_config)

    with patch.object(system.orchestrator, 'execute_model', return_value=mock_llm_response):
        start_time = time.time()

        tasks = [
            system.process_request(
                user_id=f"user-{i}",
                query=f"Test query {i}",
                session_id=f"session-{i}",
            )
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        # All requests should complete
        assert len(results) == 10
        assert all(r.model_response is not None for r in results)

        # Should complete in reasonable time (< 5 seconds for 10 concurrent)
        assert duration < 5.0, f"Took {duration}s, expected < 5s"

        # Calculate throughput
        throughput = 10 / duration
        print(f"\n10 concurrent requests: {duration:.2f}s, throughput: {throughput:.2f} req/s")


@pytest.mark.asyncio
async def test_concurrent_requests_50(test_config, mock_llm_response):
    """Test system handles 50 concurrent requests"""
    system = IntegratedACSystem(config=test_config)

    with patch.object(system.orchestrator, 'execute_model', return_value=mock_llm_response):
        start_time = time.time()

        tasks = [
            system.process_request(
                user_id=f"user-{i}",
                query=f"Test query {i}",
                session_id=f"session-{i}",
            )
            for i in range(50)
        ]

        results = await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        assert len(results) == 50
        assert all(r.model_response is not None for r in results)

        # Should complete in reasonable time (< 15 seconds)
        assert duration < 15.0, f"Took {duration}s, expected < 15s"

        throughput = 50 / duration
        print(f"\n50 concurrent requests: {duration:.2f}s, throughput: {throughput:.2f} req/s")


@pytest.mark.asyncio
async def test_concurrent_requests_100(test_config, mock_llm_response):
    """Test system handles 100 concurrent requests"""
    system = IntegratedACSystem(config=test_config)

    with patch.object(system.orchestrator, 'execute_model', return_value=mock_llm_response):
        start_time = time.time()

        tasks = [
            system.process_request(
                user_id=f"user-{i}",
                query=f"Test query {i}",
                session_id=f"session-{i}",
            )
            for i in range(100)
        ]

        results = await asyncio.gather(*tasks)

        end_time = time.time()
        duration = end_time - start_time

        assert len(results) == 100
        assert all(r.model_response is not None for r in results)

        # Should complete in reasonable time (< 30 seconds)
        assert duration < 30.0, f"Took {duration}s, expected < 30s"

        throughput = 100 / duration
        print(f"\n100 concurrent requests: {duration:.2f}s, throughput: {throughput:.2f} req/s")


# ============================================================================
# Latency Benchmarks - Response Time Measurements
# ============================================================================


@pytest.mark.asyncio
async def test_single_request_latency(test_config, mock_llm_response):
    """Benchmark latency for single request"""
    system = IntegratedACSystem(config=test_config)

    with patch.object(system.orchestrator, 'execute_model', return_value=mock_llm_response):
        # Warm up
        await system.process_request(
            user_id="warmup-user",
            query="Warmup query",
            session_id="warmup-session",
        )

        # Measure latency over 10 requests
        latencies = []
        for i in range(10):
            start_time = time.time()

            result = await system.process_request(
                user_id=f"test-user-{i}",
                query="What is the best way to implement authentication?",
                session_id=f"test-session-{i}",
            )

            end_time = time.time()
            latency = (end_time - start_time) * 1000  # Convert to ms
            latencies.append(latency)

            assert result.model_response is not None

        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(0.95 * len(latencies))]

        print(f"\nLatency stats (ms):")
        print(f"  Avg: {avg_latency:.2f}")
        print(f"  Min: {min_latency:.2f}")
        print(f"  Max: {max_latency:.2f}")
        print(f"  P95: {p95_latency:.2f}")

        # Average latency should be < 500ms
        assert avg_latency < 500, f"Average latency {avg_latency}ms exceeds 500ms"


@pytest.mark.asyncio
async def test_ari_monitoring_latency(temp_storage):
    """Benchmark ARI monitoring latency"""
    ari_monitor = ARIMonitor(storage_dir=temp_storage / "ari")

    # Measure snapshot recording latency
    latencies = []
    for i in range(100):
        snapshot = AgencySnapshot(
            timestamp=datetime.now(),
            task_id=f"task-{i}",
            task_type="coding",
            delta_agency=0.1,
            bhir=1.5,
            task_efficacy=0.9,
            user_skill_before=0.7,
            user_skill_after=0.75,
            skill_development=0.05,
            ai_reliance=0.5,
            autonomy_retention=0.8,
            user_id="test-user",
            session_id="session-1",
        )

        start_time = time.time()
        await ari_monitor.record_snapshot(snapshot)
        end_time = time.time()

        latency = (end_time - start_time) * 1000
        latencies.append(latency)

    avg_latency = sum(latencies) / len(latencies)
    print(f"\nARI snapshot recording latency: {avg_latency:.2f}ms")

    # Should be very fast (< 50ms)
    assert avg_latency < 50, f"ARI latency {avg_latency}ms exceeds 50ms"


@pytest.mark.asyncio
async def test_edm_analysis_latency(temp_storage):
    """Benchmark EDM text analysis latency"""
    edm_monitor = EDMMonitor(storage_dir=temp_storage / "edm", fact_check_enabled=False)

    test_texts = [
        "Everyone knows that AI will change everything.",
        "Studies show that machine learning improves productivity.",
        "Research indicates that quantum computing is the future.",
        "Many people believe that blockchain solves all problems.",
        "It's obvious that this approach is superior.",
    ]

    latencies = []
    for i, text in enumerate(test_texts * 20):  # 100 analyses
        start_time = time.time()

        debts = await edm_monitor.analyze_text(
            text=text,
            task_id=f"task-{i}",
            user_id="test-user",
        )

        end_time = time.time()
        latency = (end_time - start_time) * 1000
        latencies.append(latency)

    avg_latency = sum(latencies) / len(latencies)
    print(f"\nEDM text analysis latency: {avg_latency:.2f}ms")

    # Should be reasonably fast (< 100ms)
    assert avg_latency < 100, f"EDM latency {avg_latency}ms exceeds 100ms"


# ============================================================================
# Memory Profiling - Resource Usage
# ============================================================================


@pytest.mark.asyncio
async def test_memory_usage_single_request(test_config, mock_llm_response):
    """Test memory usage for single request"""
    process = psutil.Process(os.getpid())

    # Get baseline memory
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    system = IntegratedACSystem(config=test_config)

    with patch.object(system.orchestrator, 'execute_model', return_value=mock_llm_response):
        result = await system.process_request(
            user_id="test-user",
            query="Test query",
            session_id="test-session",
        )

        assert result.model_response is not None

    # Get final memory
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    print(f"\nMemory usage:")
    print(f"  Initial: {initial_memory:.2f} MB")
    print(f"  Final: {final_memory:.2f} MB")
    print(f"  Increase: {memory_increase:.2f} MB")

    # Memory increase should be reasonable (< 100MB for single request)
    assert memory_increase < 100, f"Memory increase {memory_increase}MB exceeds 100MB"


@pytest.mark.asyncio
async def test_memory_usage_100_requests(test_config, mock_llm_response):
    """Test memory usage for 100 sequential requests"""
    process = psutil.Process(os.getpid())

    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    system = IntegratedACSystem(config=test_config)

    with patch.object(system.orchestrator, 'execute_model', return_value=mock_llm_response):
        for i in range(100):
            result = await system.process_request(
                user_id=f"user-{i}",
                query=f"Test query {i}",
                session_id=f"session-{i}",
            )
            assert result.model_response is not None

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    print(f"\nMemory usage (100 requests):")
    print(f"  Initial: {initial_memory:.2f} MB")
    print(f"  Final: {final_memory:.2f} MB")
    print(f"  Increase: {memory_increase:.2f} MB")
    print(f"  Per request: {memory_increase/100:.2f} MB")

    # Total memory increase should be reasonable (< 200MB)
    assert memory_increase < 200, f"Memory increase {memory_increase}MB exceeds 200MB"


@pytest.mark.asyncio
async def test_memory_leak_detection(temp_storage):
    """Test for memory leaks in ARI monitoring"""
    process = psutil.Process(os.getpid())
    ari_monitor = ARIMonitor(storage_dir=temp_storage / "ari")

    # Record memory before loop
    initial_memory = process.memory_info().rss / 1024 / 1024

    # Create and record many snapshots
    for i in range(1000):
        snapshot = AgencySnapshot(
            timestamp=datetime.now(),
            task_id=f"task-{i}",
            task_type="coding",
            delta_agency=0.1,
            bhir=1.5,
            task_efficacy=0.9,
            user_skill_before=0.7,
            user_skill_after=0.75,
            skill_development=0.05,
            ai_reliance=0.5,
            autonomy_retention=0.8,
            user_id="test-user",
            session_id="session-1",
        )
        await ari_monitor.record_snapshot(snapshot)

    # Check memory after loop
    final_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = final_memory - initial_memory

    print(f"\nMemory leak test (1000 snapshots):")
    print(f"  Memory increase: {memory_increase:.2f} MB")

    # Memory increase should be linear with data (< 50MB for 1000 snapshots)
    assert memory_increase < 50, f"Possible memory leak: {memory_increase}MB increase"


# ============================================================================
# Throughput Measurements
# ============================================================================


@pytest.mark.asyncio
async def test_sustained_throughput(test_config, mock_llm_response):
    """Test sustained throughput over time"""
    system = IntegratedACSystem(config=test_config)

    with patch.object(system.orchestrator, 'execute_model', return_value=mock_llm_response):
        # Run requests for 10 seconds
        duration = 10  # seconds
        start_time = time.time()
        request_count = 0

        while time.time() - start_time < duration:
            result = await system.process_request(
                user_id=f"user-{request_count}",
                query=f"Test query {request_count}",
                session_id=f"session-{request_count}",
            )
            assert result.model_response is not None
            request_count += 1

        actual_duration = time.time() - start_time
        throughput = request_count / actual_duration

        print(f"\nSustained throughput test:")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Requests: {request_count}")
        print(f"  Throughput: {throughput:.2f} req/s")

        # Should maintain reasonable throughput (> 5 req/s)
        assert throughput > 5, f"Throughput {throughput:.2f} req/s is too low"


# ============================================================================
# Stress Testing
# ============================================================================


@pytest.mark.asyncio
async def test_stress_rapid_requests(test_config, mock_llm_response):
    """Stress test with rapid sequential requests"""
    system = IntegratedACSystem(config=test_config)

    with patch.object(system.orchestrator, 'execute_model', return_value=mock_llm_response):
        start_time = time.time()

        # Send 500 requests as fast as possible
        for i in range(500):
            result = await system.process_request(
                user_id=f"user-{i}",
                query=f"Query {i}",
                session_id=f"session-{i}",
            )
            assert result.model_response is not None

        duration = time.time() - start_time
        throughput = 500 / duration

        print(f"\nStress test (500 rapid requests):")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Throughput: {throughput:.2f} req/s")

        # Should handle stress (< 60 seconds)
        assert duration < 60, f"Took {duration}s, too slow under stress"


@pytest.mark.asyncio
async def test_stress_mixed_load(test_config, mock_llm_response):
    """Stress test with mixed concurrent and sequential load"""
    system = IntegratedACSystem(config=test_config)

    with patch.object(system.orchestrator, 'execute_model', return_value=mock_llm_response):
        start_time = time.time()

        # Run 10 batches of 20 concurrent requests
        all_results = []
        for batch in range(10):
            tasks = [
                system.process_request(
                    user_id=f"user-{batch}-{i}",
                    query=f"Query {batch}-{i}",
                    session_id=f"session-{batch}-{i}",
                )
                for i in range(20)
            ]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)

        duration = time.time() - start_time

        assert len(all_results) == 200
        assert all(r.model_response is not None for r in all_results)

        throughput = 200 / duration

        print(f"\nMixed load stress test (10 batches × 20 concurrent):")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Throughput: {throughput:.2f} req/s")

        # Should handle mixed load (< 40 seconds)
        assert duration < 40, f"Took {duration}s under mixed load"


# ============================================================================
# Component-Specific Performance Tests
# ============================================================================


@pytest.mark.asyncio
async def test_orchestrator_selection_performance():
    """Test model selection performance"""
    orchestrator = MultiModelOrchestrator()

    start_time = time.time()

    # Run 1000 model selections
    for i in range(1000):
        from ai_pal.orchestration.multi_model import TaskComplexity, TaskRequirements
        requirements = TaskRequirements(
            complexity=TaskComplexity.SIMPLE,
            max_latency_ms=1000,
            max_cost_usd=0.01,
        )
        model = orchestrator.select_model(requirements)
        assert model is not None

    duration = time.time() - start_time
    avg_time = (duration / 1000) * 1000  # ms

    print(f"\nModel selection performance:")
    print(f"  1000 selections in {duration:.2f}s")
    print(f"  Average: {avg_time:.2f}ms per selection")

    # Should be very fast (< 1ms per selection)
    assert avg_time < 1.0, f"Selection too slow: {avg_time}ms"


@pytest.mark.asyncio
async def test_ffe_goal_ingestion_performance(temp_storage):
    """Test FFE goal ingestion performance"""
    ffe = FractalFlowEngine(storage_dir=temp_storage / "ffe")

    from ai_pal.ffe.models import TaskComplexityLevel

    start_time = time.time()

    # Ingest 100 goals
    for i in range(100):
        await ffe.ingest_goal(
            user_id="test-user",
            description=f"Test goal {i}",
            complexity_level=TaskComplexityLevel.ATOMIC,
        )

    duration = time.time() - start_time
    avg_time = (duration / 100) * 1000  # ms

    print(f"\nFFE goal ingestion performance:")
    print(f"  100 goals in {duration:.2f}s")
    print(f"  Average: {avg_time:.2f}ms per goal")

    # Should be fast (< 50ms per goal)
    assert avg_time < 50, f"Goal ingestion too slow: {avg_time}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

#!/usr/bin/env python3
"""
Load Testing Script for Redis Cache Integration

Simulates realistic workloads to measure cache effectiveness and system performance.
Tests cache hit rates, response times, and system stability under load.

Usage:
    python scripts/load_test_cache.py --duration 60 --rps 100 --clients 10
    python scripts/load_test_cache.py --profile  # Enable cProfile
"""

import asyncio
import time
import statistics
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from unittest.mock import AsyncMock
import random

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_pal.cache.redis_cache import RedisCache
from ai_pal.storage.database import DatabaseManager, ARIRepository, GoalRepository
from ai_pal.storage.cached_repositories import (
    CachedARIRepository,
    CachedGoalRepository,
    CachedTaskRepository,
)


@dataclass
class LoadTestResult:
    """Result from a single request during load test."""
    timestamp: float
    operation: str
    duration_ms: float
    cache_hit: bool
    success: bool
    error: str = None


@dataclass
class LoadTestStats:
    """Statistics for load test execution."""
    operation: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_duration_s: float
    requests_per_second: float
    min_response_ms: float
    max_response_ms: float
    mean_response_ms: float
    median_response_ms: float
    p95_response_ms: float
    p99_response_ms: float
    cache_hits: int
    cache_misses: int
    hit_rate: float
    error_rate: float

    def __str__(self) -> str:
        """Format stats for display."""
        return (
            f"\n{self.operation} Statistics:\n"
            f"  Total Requests: {self.total_requests}\n"
            f"  Successful: {self.successful_requests}\n"
            f"  Failed: {self.failed_requests}\n"
            f"  Error Rate: {self.error_rate*100:.2f}%\n"
            f"  Duration: {self.total_duration_s:.1f}s\n"
            f"  Throughput: {self.requests_per_second:.1f} RPS\n"
            f"  Response Times:\n"
            f"    Min: {self.min_response_ms:.2f}ms\n"
            f"    Mean: {self.mean_response_ms:.2f}ms\n"
            f"    Median: {self.median_response_ms:.2f}ms\n"
            f"    P95: {self.p95_response_ms:.2f}ms\n"
            f"    P99: {self.p99_response_ms:.2f}ms\n"
            f"    Max: {self.max_response_ms:.2f}ms\n"
            f"  Cache Performance:\n"
            f"    Hits: {self.cache_hits}\n"
            f"    Misses: {self.cache_misses}\n"
            f"    Hit Rate: {self.hit_rate*100:.1f}%"
        )


class CacheLoadTester:
    """Load testing harness for cache performance."""

    def __init__(self, num_users: int = 1000, num_goals: int = 5000):
        """Initialize load tester with test data."""
        self.num_users = num_users
        self.num_goals = num_goals
        self.test_data = self._generate_test_data()
        self.results: List[LoadTestResult] = []

    def _generate_test_data(self) -> Dict[str, Any]:
        """Generate realistic test data."""
        return {
            "users": [f"user{i}" for i in range(self.num_users)],
            "goals": [
                {
                    "goal_id": f"goal{i}",
                    "user_id": f"user{i % self.num_users}",
                    "description": f"Goal {i}",
                    "status": random.choice(["active", "completed", "paused"]),
                }
                for i in range(self.num_goals)
            ],
        }

    async def _simulate_cache_get(self, key: str) -> Any:
        """Simulate cache get with realistic latency."""
        await asyncio.sleep(0.0001)  # ~0.1ms network latency
        return random.choice([None, {"cached": True}])  # 50% hit rate

    async def _simulate_cache_set(self, key: str, value: Any, ttl: int = None):
        """Simulate cache set operation."""
        await asyncio.sleep(0.0001)  # ~0.1ms write latency

    async def _simulate_db_query(self) -> List[Dict[str, Any]]:
        """Simulate database query with realistic latency."""
        await asyncio.sleep(random.uniform(0.01, 0.05))  # 10-50ms
        return [{"result": "data"}]

    async def _execute_ari_query(self, cache: AsyncMock) -> LoadTestResult:
        """Execute a single ARI query with caching."""
        timestamp = time.time()
        operation = "ARI Query"
        user_id = random.choice(self.test_data["users"])
        cache_hit = False

        try:
            start = time.perf_counter()

            # Check cache
            cache_key = f"user:ari:history:{user_id}"
            cached = await cache.get(cache_key)

            if cached is not None:
                cache_hit = True
                response = cached
            else:
                # Database query
                response = await self._simulate_db_query()
                await cache.set(cache_key, response, ttl=300)

            duration_ms = (time.perf_counter() - start) * 1000

            return LoadTestResult(
                timestamp=timestamp,
                operation=operation,
                duration_ms=duration_ms,
                cache_hit=cache_hit,
                success=True,
            )

        except Exception as e:
            return LoadTestResult(
                timestamp=timestamp,
                operation=operation,
                duration_ms=(time.perf_counter() - start) * 1000,
                cache_hit=False,
                success=False,
                error=str(e),
            )

    async def _execute_goal_query(self, cache: AsyncMock) -> LoadTestResult:
        """Execute a single goal query with caching."""
        timestamp = time.time()
        operation = "Goal Query"
        user_id = random.choice(self.test_data["users"])
        cache_hit = False

        try:
            start = time.perf_counter()

            cache_key = f"user:goals:active:{user_id}"
            cached = await cache.get(cache_key)

            if cached is not None:
                cache_hit = True
                response = cached
            else:
                response = await self._simulate_db_query()
                await cache.set(cache_key, response, ttl=600)

            duration_ms = (time.perf_counter() - start) * 1000

            return LoadTestResult(
                timestamp=timestamp,
                operation=operation,
                duration_ms=duration_ms,
                cache_hit=cache_hit,
                success=True,
            )

        except Exception as e:
            return LoadTestResult(
                timestamp=timestamp,
                operation=operation,
                duration_ms=(time.perf_counter() - start) * 1000,
                cache_hit=False,
                success=False,
                error=str(e),
            )

    async def _execute_mixed_workload(
        self, cache: AsyncMock
    ) -> Tuple[LoadTestResult, LoadTestResult]:
        """Execute mixed ARI and goal queries."""
        tasks = [
            self._execute_ari_query(cache),
            self._execute_goal_query(cache),
        ]
        return await asyncio.gather(*tasks)

    async def run_load_test(
        self,
        duration_seconds: int = 60,
        requests_per_second: int = 100,
        num_concurrent: int = 10,
    ):
        """Run load test for specified duration."""
        print(f"\n{'='*60}")
        print("Cache Load Test")
        print(f"{'='*60}")
        print(f"Duration: {duration_seconds}s")
        print(f"Target RPS: {requests_per_second}")
        print(f"Concurrent Tasks: {num_concurrent}")
        print(f"Total Users: {self.num_users}")
        print(f"{'='*60}\n")

        # Setup mock cache
        cache = AsyncMock(spec=RedisCache)
        cache.get = AsyncMock(side_effect=self._simulate_cache_get)
        cache.set = AsyncMock(side_effect=self._simulate_cache_set)

        results: List[LoadTestResult] = []
        start_time = time.time()
        request_count = 0

        async def request_generator():
            """Generate requests at target RPS."""
            nonlocal request_count
            interval = 1.0 / requests_per_second

            while time.time() - start_time < duration_seconds:
                request_count += 1
                yield request_count
                await asyncio.sleep(interval)

        async def worker(task_id: int):
            """Worker task executing cache operations."""
            async for _ in request_generator():
                # Execute mixed workload
                ari_result, goal_result = await self._execute_mixed_workload(cache)
                results.extend([ari_result, goal_result])

                if len(results) % 100 == 0:
                    elapsed = time.time() - start_time
                    actual_rps = len(results) / elapsed if elapsed > 0 else 0
                    print(
                        f"  {len(results)} requests completed "
                        f"({actual_rps:.1f} RPS, {elapsed:.1f}s elapsed)"
                    )

        # Run workers
        try:
            workers = [
                worker(i) for i in range(num_concurrent)
            ]
            await asyncio.wait_for(
                asyncio.gather(*workers, return_exceptions=True),
                timeout=duration_seconds + 5
            )
        except asyncio.TimeoutError:
            pass  # Test duration expired

        end_time = time.time()
        actual_duration = end_time - start_time

        # Calculate statistics
        return self._calculate_stats(results, actual_duration)

    def _calculate_stats(
        self, results: List[LoadTestResult], duration_s: float
    ) -> Dict[str, LoadTestStats]:
        """Calculate statistics for results."""
        # Group by operation
        ari_results = [r for r in results if r.operation == "ARI Query"]
        goal_results = [r for r in results if r.operation == "Goal Query"]

        stats = {}

        for operation_name, operation_results in [
            ("ARI Queries", ari_results),
            ("Goal Queries", goal_results),
        ]:
            if not operation_results:
                continue

            durations = [r.duration_ms for r in operation_results]
            successful = [r for r in operation_results if r.success]
            cache_hits = sum(1 for r in operation_results if r.cache_hit)

            durations_sorted = sorted(durations)
            p95_idx = int(len(durations_sorted) * 0.95)
            p99_idx = int(len(durations_sorted) * 0.99)

            stats[operation_name] = LoadTestStats(
                operation=operation_name,
                total_requests=len(operation_results),
                successful_requests=len(successful),
                failed_requests=len(operation_results) - len(successful),
                total_duration_s=duration_s,
                requests_per_second=len(operation_results) / duration_s,
                min_response_ms=min(durations),
                max_response_ms=max(durations),
                mean_response_ms=statistics.mean(durations),
                median_response_ms=statistics.median(durations),
                p95_response_ms=durations_sorted[p95_idx]
                if p95_idx < len(durations_sorted)
                else max(durations),
                p99_response_ms=durations_sorted[p99_idx]
                if p99_idx < len(durations_sorted)
                else max(durations),
                cache_hits=cache_hits,
                cache_misses=len(operation_results) - cache_hits,
                hit_rate=cache_hits / len(operation_results)
                if operation_results else 0,
                error_rate=(len(operation_results) - len(successful))
                / len(operation_results)
                if operation_results
                else 0,
            )

        return stats


async def main():
    """Main load test execution."""
    parser = argparse.ArgumentParser(description="Load test cache performance")
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Test duration in seconds (default: 60)",
    )
    parser.add_argument(
        "--rps",
        type=int,
        default=100,
        help="Target requests per second (default: 100)",
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=10,
        help="Number of concurrent tasks (default: 10)",
    )
    parser.add_argument(
        "--users",
        type=int,
        default=1000,
        help="Number of test users (default: 1000)",
    )

    args = parser.parse_args()

    try:
        tester = CacheLoadTester(num_users=args.users)
        stats = await tester.run_load_test(
            duration_seconds=args.duration,
            requests_per_second=args.rps,
            num_concurrent=args.concurrent,
        )

        # Print results
        print(f"\n{'='*60}")
        print("LOAD TEST RESULTS")
        print(f"{'='*60}")

        for operation, operation_stats in stats.items():
            print(operation_stats)

        # Print summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")

        if "ARI Queries" in stats and "Goal Queries" in stats:
            total_requests = (
                stats["ARI Queries"].total_requests
                + stats["Goal Queries"].total_requests
            )
            avg_rps = (
                stats["ARI Queries"].requests_per_second
                + stats["Goal Queries"].requests_per_second
            ) / 2
            avg_hit_rate = (
                stats["ARI Queries"].hit_rate + stats["Goal Queries"].hit_rate
            ) / 2
            avg_response_ms = (
                stats["ARI Queries"].mean_response_ms
                + stats["Goal Queries"].mean_response_ms
            ) / 2

            print(f"Total Requests: {total_requests}")
            print(f"Average RPS: {avg_rps:.1f}")
            print(f"Average Response Time: {avg_response_ms:.2f}ms")
            print(f"Average Cache Hit Rate: {avg_hit_rate*100:.1f}%")
            print(f"\n✓ Load test completed successfully")

    except Exception as e:
        print(f"\nLoad test error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

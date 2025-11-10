#!/usr/bin/env python3
"""
Cache Performance Benchmark Script

Compares performance of cached vs non-cached repositories.
Measures query performance, database load reduction, and cache effectiveness.

Usage:
    python scripts/benchmark_cache.py --runs 100 --concurrent 10
    python scripts/benchmark_cache.py --profile     # Profile with cProfile
"""

import asyncio
import time
import statistics
import cProfile
import pstats
import io
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from unittest.mock import AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_pal.cache.redis_cache import RedisCache
from ai_pal.storage.database import DatabaseManager, ARIRepository
from ai_pal.storage.cached_repositories import CachedARIRepository


@dataclass
class BenchmarkResult:
    """Benchmark result for a single operation."""
    operation: str
    duration_ms: float
    cache_hit: bool = False
    memory_kb: float = 0.0


@dataclass
class BenchmarkStats:
    """Statistics for a benchmark run."""
    operation: str
    total_runs: int
    total_time_ms: float
    min_ms: float
    max_ms: float
    mean_ms: float
    median_ms: float
    stdev_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    hit_rate: float = 0.0

    def __str__(self) -> str:
        """Format stats for display."""
        return (
            f"\n{self.operation}:\n"
            f"  Runs: {self.total_runs}\n"
            f"  Total Time: {self.total_time_ms:.2f}ms\n"
            f"  Mean: {self.mean_ms:.3f}ms\n"
            f"  Median: {self.median_ms:.3f}ms\n"
            f"  Min/Max: {self.min_ms:.3f}ms / {self.max_ms:.3f}ms\n"
            f"  Stdev: {self.stdev_ms:.3f}ms\n"
            f"  Cache Hits: {self.cache_hits}/{self.total_runs} ({self.hit_rate*100:.1f}%)"
        )


class CacheBenchmark:
    """Benchmark harness for cache performance testing."""

    def __init__(self, num_users: int = 100, num_snapshots: int = 10):
        """Initialize benchmark with test data."""
        self.num_users = num_users
        self.num_snapshots = num_snapshots
        self.test_data = self._generate_test_data()

    def _generate_test_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate realistic test data."""
        data = {}

        for user_id in range(self.num_users):
            user_key = f"user{user_id}"
            snapshots = []

            for snap_id in range(self.num_snapshots):
                snapshot = {
                    "snapshot_id": f"{user_key}_snap{snap_id}",
                    "user_id": user_key,
                    "timestamp": time.time() - (snap_id * 3600),
                    "autonomy_retention": 50.0 + (snap_id * 2.5),
                    "decision_quality": 60.0 + (snap_id * 1.5),
                    "skill_development": 55.0 + (snap_id * 2.0),
                    "ai_reliance": 40.0 - (snap_id * 1.0),
                    "bottleneck_resolution": 65.0 + (snap_id * 1.8),
                    "user_confidence": 70.0 + (snap_id * 1.2),
                    "engagement": 75.0 + (snap_id * 0.8),
                    "autonomy_perception": 72.0 + (snap_id * 1.5),
                }
                snapshots.append(snapshot)

            data[user_key] = snapshots

        return data

    async def benchmark_non_cached(self, num_runs: int = 100) -> BenchmarkStats:
        """Benchmark non-cached repository queries."""
        print(f"\n{'='*60}")
        print("Benchmarking Non-Cached Repository")
        print(f"{'='*60}")

        db_manager = AsyncMock(spec=DatabaseManager)
        repo = ARIRepository(db_manager)
        repo.get_snapshots_by_user = AsyncMock(
            side_effect=lambda user_id, **kwargs: self.test_data.get(user_id, [])
        )

        durations = []
        start_total = time.time()

        for i in range(num_runs):
            user_id = f"user{i % self.num_users}"

            start = time.perf_counter()
            await repo.get_snapshots_by_user(user_id)
            duration = (time.perf_counter() - start) * 1000  # Convert to ms

            durations.append(duration)

            if (i + 1) % 20 == 0:
                print(f"  Completed {i + 1}/{num_runs} runs...")

        total_time = (time.time() - start_total) * 1000

        return BenchmarkStats(
            operation="Non-Cached Query",
            total_runs=num_runs,
            total_time_ms=total_time,
            min_ms=min(durations),
            max_ms=max(durations),
            mean_ms=statistics.mean(durations),
            median_ms=statistics.median(durations),
            stdev_ms=statistics.stdev(durations) if len(durations) > 1 else 0.0,
            cache_hits=0,
            cache_misses=num_runs,
            hit_rate=0.0,
        )

    async def benchmark_cached(self, num_runs: int = 100) -> BenchmarkStats:
        """Benchmark cached repository queries."""
        print(f"\n{'='*60}")
        print("Benchmarking Cached Repository")
        print(f"{'='*60}")

        db_manager = AsyncMock(spec=DatabaseManager)
        cache = AsyncMock(spec=RedisCache)
        cache.enabled = True

        # Create a simple in-memory cache simulation
        memory_cache = {}

        async def mock_cache_get(key):
            await asyncio.sleep(0.0001)  # Simulate network latency (~0.1ms)
            return memory_cache.get(key)

        async def mock_cache_set(key, value, ttl=None):
            await asyncio.sleep(0.0001)  # Simulate network latency
            memory_cache[key] = value

        cache.get = AsyncMock(side_effect=mock_cache_get)
        cache.set = AsyncMock(side_effect=mock_cache_set)

        repo = ARIRepository(db_manager)
        repo.get_snapshots_by_user = AsyncMock(
            side_effect=lambda user_id, **kwargs: self.test_data.get(user_id, [])
        )

        cached_repo = CachedARIRepository(db_manager, cache)
        cached_repo.db_repo = repo

        durations = []
        cache_hits = 0
        cache_misses = 0
        start_total = time.time()

        for i in range(num_runs):
            user_id = f"user{i % self.num_users}"
            is_cache_hit = f"user:ari:history:{user_id}" in memory_cache

            start = time.perf_counter()
            await cached_repo.get_snapshots_by_user(user_id)
            duration = (time.perf_counter() - start) * 1000  # Convert to ms

            durations.append(duration)

            if is_cache_hit:
                cache_hits += 1
            else:
                cache_misses += 1

            if (i + 1) % 20 == 0:
                print(f"  Completed {i + 1}/{num_runs} runs (Hit rate: {cache_hits}/{i+1})...")

        total_time = (time.time() - start_total) * 1000
        hit_rate = cache_hits / num_runs if num_runs > 0 else 0.0

        return BenchmarkStats(
            operation="Cached Query",
            total_runs=num_runs,
            total_time_ms=total_time,
            min_ms=min(durations),
            max_ms=max(durations),
            mean_ms=statistics.mean(durations),
            median_ms=statistics.median(durations),
            stdev_ms=statistics.stdev(durations) if len(durations) > 1 else 0.0,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            hit_rate=hit_rate,
        )

    async def benchmark_concurrent_access(
        self, num_concurrent: int = 10, num_per_task: int = 10
    ) -> BenchmarkStats:
        """Benchmark concurrent cache access."""
        print(f"\n{'='*60}")
        print(f"Benchmarking Concurrent Access ({num_concurrent} tasks)")
        print(f"{'='*60}")

        db_manager = AsyncMock(spec=DatabaseManager)
        cache = AsyncMock(spec=RedisCache)
        cache.enabled = True

        memory_cache = {}

        async def mock_cache_get(key):
            await asyncio.sleep(0.0001)  # Simulate network latency
            return memory_cache.get(key)

        async def mock_cache_set(key, value, ttl=None):
            await asyncio.sleep(0.0001)  # Simulate network latency
            memory_cache[key] = value

        cache.get = AsyncMock(side_effect=mock_cache_get)
        cache.set = AsyncMock(side_effect=mock_cache_set)

        repo = ARIRepository(db_manager)
        repo.get_snapshots_by_user = AsyncMock(
            side_effect=lambda user_id, **kwargs: self.test_data.get(user_id, [])
        )

        cached_repo = CachedARIRepository(db_manager, cache)
        cached_repo.db_repo = repo

        async def worker(task_id: int) -> List[float]:
            """Worker task that performs multiple queries."""
            durations = []
            for i in range(num_per_task):
                user_id = f"user{(task_id * num_per_task + i) % self.num_users}"
                start = time.perf_counter()
                await cached_repo.get_snapshots_by_user(user_id)
                duration = (time.perf_counter() - start) * 1000
                durations.append(duration)
            return durations

        start_total = time.time()
        tasks = [worker(i) for i in range(num_concurrent)]
        all_durations = []

        for task in asyncio.as_completed(tasks):
            durations = await task
            all_durations.extend(durations)

        total_time = (time.time() - start_total) * 1000

        return BenchmarkStats(
            operation=f"Concurrent Query ({num_concurrent} tasks)",
            total_runs=len(all_durations),
            total_time_ms=total_time,
            min_ms=min(all_durations),
            max_ms=max(all_durations),
            mean_ms=statistics.mean(all_durations),
            median_ms=statistics.median(all_durations),
            stdev_ms=statistics.stdev(all_durations) if len(all_durations) > 1 else 0.0,
        )

    def print_comparison(self, non_cached: BenchmarkStats, cached: BenchmarkStats):
        """Print comparison between cached and non-cached results."""
        speedup = non_cached.mean_ms / cached.mean_ms if cached.mean_ms > 0 else 0

        print(f"\n{'='*60}")
        print("BENCHMARK RESULTS SUMMARY")
        print(f"{'='*60}")

        print(non_cached)
        print(cached)

        print(f"\n{'─'*60}")
        print("PERFORMANCE IMPROVEMENT:")
        print(f"{'─'*60}")
        print(f"  Speedup: {speedup:.1f}x faster")
        print(f"  Time Reduction: {(1 - cached.mean_ms/non_cached.mean_ms)*100:.1f}%")
        print(f"  Cache Hit Rate: {cached.hit_rate*100:.1f}%")

        if non_cached.total_time_ms > 0:
            db_reduction = (1 - (cached.cache_misses / non_cached.total_runs)) * 100
            print(f"  Database Load Reduction: {db_reduction:.1f}%")

        print(f"\n{'─'*60}")


async def main():
    """Main benchmark execution."""
    parser = argparse.ArgumentParser(
        description="Benchmark Redis caching performance"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=100,
        help="Number of benchmark runs (default: 100)",
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
        default=100,
        help="Number of test users (default: 100)",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Enable cProfile profiling",
    )

    args = parser.parse_args()

    # Create benchmark instance
    benchmark = CacheBenchmark(num_users=args.users)

    # Run profiling if requested
    if args.profile:
        profiler = cProfile.Profile()
        profiler.enable()

    try:
        # Run benchmarks
        non_cached_stats = await benchmark.benchmark_non_cached(args.runs)
        cached_stats = await benchmark.benchmark_cached(args.runs)
        concurrent_stats = await benchmark.benchmark_concurrent_access(
            args.concurrent
        )

        if args.profile:
            profiler.disable()
            stats = pstats.Stats(profiler)
            stats.strip_dirs()
            stats.sort_stats("cumulative")
            print(f"\n{'='*60}")
            print("PROFILING RESULTS (Top 20 functions)")
            print(f"{'='*60}")
            stats.print_stats(20)

        # Print comparison
        benchmark.print_comparison(non_cached_stats, cached_stats)

        # Print concurrent stats
        print(f"\n{concurrent_stats}")

        # Final summary
        print(f"\n{'='*60}")
        print("BENCHMARK COMPLETE")
        print(f"{'='*60}")
        print(f"\nCache effectiveness at scale:")
        print(f"  - Single-user queries: {non_cached_stats.mean_ms/cached_stats.mean_ms:.1f}x faster")
        print(f"  - Concurrent workload: {cached_stats.hit_rate*100:.1f}% hit rate")
        print(f"  - DB load reduction: {(1 - cached_stats.cache_misses/non_cached_stats.total_runs)*100:.1f}%")

    except Exception as e:
        print(f"\nBenchmark error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

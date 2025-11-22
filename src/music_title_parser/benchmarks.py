# SPDX - License - Identifier: MIT
# Copyright (c) 2025 Perday CatalogLAB™

"""
Benchmarking utilities for music title parser.

This module provides performance benchmarking capabilities for production monitoring.
"""

from __future__ import annotations

import gc
import time
from typing import TYPE_CHECKING

from .models import BenchmarkResult
from .policy_engine import parse_with_policy

if TYPE_CHECKING:
    from .models import PolicyProfile


def run_basic_benchmark(num_titles: int = 1000) -> BenchmarkResult:
    """
    Run basic performance benchmark.

    This function outputs a single line suitable for README badges.
    """
    test_titles = _generate_test_titles(num_titles)

    # Force garbage collection before measurement
    gc.collect()

    start_time = time.perf_counter()

    for title in test_titles:
        parse_with_policy(title, "", "balanced")

    end_time = time.perf_counter()

    time_seconds = end_time - start_time
    rows_per_second = int(num_titles / time_seconds) if time_seconds > 0 else 0

    # Output single line for badges
    print(f"BENCHMARK: {rows_per_second:,} titles / sec, {time_seconds:.3f}s total")

    return BenchmarkResult(
        test_name="basic_benchmark",
        rows_processed=num_titles,
        time_seconds=time_seconds,
        memory_mb=0.0,  # Simplified for basic benchmark
        rows_per_second=rows_per_second,
        accuracy_score=1.0,  # Simplified for basic benchmark
        metadata={
            "profile": "balanced",
            "test_type": "synthetic_titles",
        },
    )


def run_comprehensive_benchmark() -> list[BenchmarkResult]:
    """Run comprehensive benchmark across all profiles."""
    profiles: list[PolicyProfile] = ["strict", "balanced", "aggressive"]
    results = []

    for profile in profiles:
        result = _benchmark_profile(profile)
        results.append(result)

    return results


def _benchmark_profile(
    profile: PolicyProfile, num_titles: int = 100
) -> BenchmarkResult:
    """Benchmark a specific policy profile."""
    test_titles = _generate_test_titles(num_titles)

    gc.collect()
    start_time = time.perf_counter()

    accepted = 0
    rejected = 0
    graylist = 0

    for title in test_titles:
        result = parse_with_policy(title, "", profile)
        if result.decision == "accept":
            accepted += 1
        elif result.decision == "reject":
            rejected += 1
        else:
            graylist += 1

    end_time = time.perf_counter()
    time_seconds = end_time - start_time
    rows_per_second = int(num_titles / time_seconds) if time_seconds > 0 else 0

    return BenchmarkResult(
        test_name=f"profile_{profile}",
        rows_processed=num_titles,
        time_seconds=time_seconds,
        memory_mb=0.0,
        rows_per_second=rows_per_second,
        accuracy_score=accepted / num_titles if num_titles > 0 else 0.0,
        metadata={
            "profile": profile,
            "accepted": accepted,
            "rejected": rejected,
            "graylist": graylist,
        },
    )


def _generate_test_titles(num_titles: int) -> list[str]:
    """Generate synthetic test titles for benchmarking."""
    base_titles = [
        "Artist - Song Title",
        "Song Title (feat. Featured Artist)",
        "Artist & Guest - Collaboration",
        "Song Title (Live Version)",
        "Artist - Song (Acoustic)",
        "Song Title (Official Video)",
        "Artist - Song (Remix)",
        "Song Title",
        "Artist Name - Track Name (Radio Edit)",
        "Song (Extended Mix)",
    ]

    # Repeat base titles to reach desired count
    titles = []
    for i in range(num_titles):
        base_title = base_titles[i % len(base_titles)]
        # Add variation to avoid caching effects
        titles.append(f"{base_title} {i // len(base_titles)}")

    return titles


if __name__ == "__main__":
    # CLI usage for CI / CD
    result = run_basic_benchmark()
    print(f"Processed {result.rows_processed} titles in {result.time_seconds:.3f}s")
    print(f"Rate: {result.rows_per_second:,} titles / second")

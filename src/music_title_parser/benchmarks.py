# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Perday CatalogLAB™

"""Benchmarking utilities for music title parser using sanitized samples."""

from __future__ import annotations

import gc
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

from .models import BenchmarkResult
from .policy_engine import parse_with_policy

if TYPE_CHECKING:
    from .models import PolicyProfile


_SAMPLE_DATA_PATH = Path(__file__).resolve().parent / "config" / "benchmark_sample.jsonl"
_OUTPUT_PATH = Path(__file__).resolve().parent / "benchmark_results.json"


def run_basic_benchmark(num_titles: int = 1000) -> BenchmarkResult:
    """
    Run basic performance benchmark.

    This function outputs a single line suitable for README badges.
    """
    records = _load_benchmark_records(num_titles)

    # Force garbage collection before measurement
    gc.collect()

    start_time = time.perf_counter()

    accepted = 0
    rejected = 0
    graylist = 0

    for record in records:
        title = record["title"]
        channel = record.get("channel", "")
        result = parse_with_policy(title, channel, "balanced")
        if result.decision == "accept":
            accepted += 1
        elif result.decision == "reject":
            rejected += 1
        else:
            graylist += 1

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
            "sample_source": str(_SAMPLE_DATA_PATH.name),
            "accepted": accepted,
            "rejected": rejected,
            "graylist": graylist,
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
    records = _load_benchmark_records(num_titles)

    gc.collect()
    start_time = time.perf_counter()

    accepted = 0
    rejected = 0
    graylist = 0

    for record in records:
        title = record["title"]
        channel = record.get("channel", "")
        result = parse_with_policy(title, channel, profile)
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
            "sample_source": str(_SAMPLE_DATA_PATH.name),
        },
    )


def _load_benchmark_records(limit: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    try:
        with _SAMPLE_DATA_PATH.open() as fh:
            for line in fh:
                if not line.strip():
                    continue
                rows.append(json.loads(line))
    except FileNotFoundError:
        pass

    if not rows:
        rows = _fallback_records()

    if limit <= len(rows):
        return rows[:limit]

    cycled: list[dict[str, str]] = []
    for idx in range(limit):
        cycled.append(rows[idx % len(rows)])
    return cycled


def _fallback_records() -> list[dict[str, str]]:
    return [
        {"title": "Artist - Song Title", "channel": ""},
        {"title": "Song Title (feat. Featured Artist)", "channel": ""},
        {"title": "Artist & Guest - Collaboration", "channel": ""},
        {"title": "Song Title (Live Version)", "channel": ""},
        {"title": "Artist - Song (Acoustic)", "channel": ""},
        {"title": "Song Title (Official Video)", "channel": ""},
        {"title": "Artist - Song (Remix)", "channel": ""},
        {"title": "Song Title", "channel": ""},
        {"title": "Artist Name - Track Name (Radio Edit)", "channel": ""},
        {"title": "Song (Extended Mix)", "channel": ""},
    ]


def _write_benchmark_report(result: BenchmarkResult) -> Path:
    payload = result.model_dump()
    _OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    return _OUTPUT_PATH


if __name__ == "__main__":
    # CLI usage for CI / CD
    result = run_basic_benchmark()
    print(f"Processed {result.rows_processed} titles in {result.time_seconds:.3f}s")
    print(f"Rate: {result.rows_per_second:,} titles / second")
    output_file = _write_benchmark_report(result)
    print(f"Results saved to {output_file}")

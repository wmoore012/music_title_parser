# SPDX-License-Identifier: MIT
# Copyright (c) 2024 MusicScope

"""
Benchmark tests for music title parser using pytest-benchmark.

These benchmarks measure performance and memory usage of parsing operations
across different scenarios and data complexity levels.
"""

import gc
import time
import tracemalloc
from typing import List

import pytest

from music_title_parser.parser import parse_title


@pytest.fixture
def clean_titles() -> List[str]:
    """Generate clean, well-formatted music titles for benchmarking."""
    return [
        "Artist Name - Song Title",
        "The Beatles - Hey Jude",
        "Queen - Bohemian Rhapsody",
        "Led Zeppelin - Stairway to Heaven",
        "Pink Floyd - Comfortably Numb",
        "The Rolling Stones - Paint It Black",
        "Bob Dylan - Like a Rolling Stone",
        "Nirvana - Smells Like Teen Spirit",
        "Radiohead - Creep",
        "The Doors - Light My Fire",
        "Jimi Hendrix - Purple Haze",
        "AC/DC - Back in Black",
        "Metallica - Enter Sandman",
        "Guns N' Roses - Sweet Child O' Mine",
        "U2 - With or Without You",
        "Coldplay - Yellow",
        "Red Hot Chili Peppers - Under the Bridge",
        "Pearl Jam - Alive",
        "Soundgarden - Black Hole Sun",
        "Alice in Chains - Man in the Box"
    ]


@pytest.fixture
def gnarly_titles() -> List[str]:
    """Generate complex, messy music titles for benchmarking."""
    return [
        "Artist Name - Song Title (Official Music Video) [HD]",
        "THE BEATLES - HEY JUDE (REMASTERED 2009) | OFFICIAL VIDEO",
        "Queen - Bohemian Rhapsody [Official Video] (4K Remaster)",
        "Led Zeppelin - Stairway to Heaven (Live at Madison Square Garden 1973)",
        "Pink Floyd - Comfortably Numb (Pulse Live) [HD] 🎵",
        "The Rolling Stones - Paint It Black (Official Lyric Video) 1966",
        "Bob Dylan - Like a Rolling Stone (Audio) | Columbia Records",
        "Nirvana - Smells Like Teen Spirit (Official Music Video) MTV Version",
        "Radiohead - Creep [EXPLICIT] (Official Video) 1992 ♪",
        "The Doors - Light My Fire (Ed Sullivan Show Performance) RARE",
        "Jimi Hendrix - Purple Haze (Live at Woodstock 1969) [Restored Audio]",
        "AC/DC - Back in Black (Official Video) | Atlantic Records ⚡",
        "Metallica - Enter Sandman [Official Music Video] (1991) HD",
        "Guns N' Roses - Sweet Child O' Mine (Official Music Video) 🌹",
        "U2 - With or Without You (360° Live from Rose Bowl) [4K]",
        "Coldplay - Yellow (Official Video) | Parlophone Records 🟡",
        "Red Hot Chili Peppers - Under the Bridge [Official Music Video] 1991",
        "Pearl Jam - Alive (MTV Unplugged) [Live Performance] 1992",
        "Soundgarden - Black Hole Sun (Official Video) | A&M Records ☀️",
        "Alice in Chains - Man in the Box (Official Video) [Remastered] 1990"
    ]


@pytest.fixture
def mixed_complexity_titles() -> List[str]:
    """Generate titles with varying complexity levels."""
    return [
        # Simple
        "Artist - Song",
        "Band - Track Name",

        # Medium complexity
        "Artist Name - Song Title (feat. Guest Artist)",
        "Band Name - Track Title [Remix]",

        # High complexity
        "Artist Name ft. Guest Artist - Song Title (Official Music Video) [HD] 2023",
        "BAND NAME - TRACK TITLE (LIVE AT VENUE) [REMASTERED] | LABEL RECORDS 🎵",

        # Edge cases
        "Artist - Song - Extra Dash",
        "No Dash In This Title At All",
        "- Leading Dash",
        "Trailing Dash -",
        "",  # Empty string
        "   ",  # Whitespace only

        # Unicode and special characters
        "Artíst Ñamé - Sóng Títlé",
        "Artist™ - Song® (Official©)",
        "🎵 Artist - Song 🎵",
        "Artist & Band - Song + Remix",

        # Very long titles
        "Very Long Artist Name That Goes On And On - Very Long Song Title That Also Goes On And On And On (Official Music Video) [HD] [Remastered] [Extended Version] [Director's Cut] [Special Edition]"
    ]


def warmup_parser(titles: List[str]):
    """Warm up the parser to avoid first-call penalty."""
    for title in titles[:3]:
        parse_title(title)


class TestParserBenchmarks:
    """Benchmark tests for music title parsing operations."""

    def test_parse_clean_titles(self, benchmark, clean_titles):
        """Benchmark parsing clean, well-formatted titles."""
        warmup_parser(clean_titles)

        gc.disable()
        try:
            results = benchmark(self._parse_batch, clean_titles)
        finally:
            gc.enable()

        # Verify results
        assert len(results) == len(clean_titles)
        assert all(result.artist and result.title for result in results)

    def test_parse_gnarly_titles(self, benchmark, gnarly_titles):
        """Benchmark parsing complex, messy titles."""
        warmup_parser(gnarly_titles)

        gc.disable()
        try:
            results = benchmark(self._parse_batch, gnarly_titles)
        finally:
            gc.enable()

        # Verify results
        assert len(results) == len(gnarly_titles)
        # Most should parse successfully despite complexity
        successful_parses = sum(1 for r in results if r.artist and r.title)
        assert successful_parses >= len(gnarly_titles) * 0.8  # 80% success rate

    def test_parse_mixed_complexity(self, benchmark, mixed_complexity_titles):
        """Benchmark parsing titles with varying complexity."""
        warmup_parser(mixed_complexity_titles)

        gc.disable()
        try:
            results = benchmark(self._parse_batch, mixed_complexity_titles)
        finally:
            gc.enable()

        # Verify results
        assert len(results) == len(mixed_complexity_titles)

    def test_single_title_parsing(self, benchmark):
        """Benchmark single title parsing for latency measurement."""
        title = "The Beatles - Hey Jude (Official Music Video) [Remastered]"

        # Warm up
        parse_title(title)

        gc.disable()
        try:
            result = benchmark(parse_title, title)
        finally:
            gc.enable()

        assert result.artist == "The Beatles"
        assert result.title == "Hey Jude"

    def test_empty_and_edge_cases(self, benchmark):
        """Benchmark parsing edge cases and malformed input."""
        edge_cases = [
            "",
            "   ",
            "No separator here",
            "- Only separator",
            "Multiple - Separators - Here",
            "🎵🎵🎵",
            "A" * 1000,  # Very long string
        ]

        # Warm up
        for case in edge_cases[:2]:
            parse_title(case)

        gc.disable()
        try:
            results = benchmark(self._parse_batch, edge_cases)
        finally:
            gc.enable()

        # Should handle all cases without crashing
        assert len(results) == len(edge_cases)

    def test_batch_size_scaling(self, benchmark, clean_titles):
        """Benchmark how performance scales with batch size."""
        # Create larger batch by repeating titles
        large_batch = clean_titles * 50  # 1000 titles

        warmup_parser(large_batch[:10])

        gc.disable()
        try:
            results = benchmark(self._parse_batch, large_batch)
        finally:
            gc.enable()

        assert len(results) == len(large_batch)

    @staticmethod
    def _parse_batch(titles: List[str]):
        """Helper method to parse a batch of titles."""
        return [parse_title(title) for title in titles]


class TestMemoryBenchmarks:
    """Memory usage benchmarks using tracemalloc."""

    def test_memory_usage_clean_titles(self, clean_titles):
        """Measure memory usage for clean title parsing."""
        warmup_parser(clean_titles[:3])

        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        # Parse all titles
        results = [parse_title(title) for title in clean_titles]

        snapshot2 = tracemalloc.take_snapshot()

        # Calculate memory difference
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        total_memory_mb = sum(stat.size_diff for stat in top_stats) / 1024 / 1024

        tracemalloc.stop()

        # Memory usage should be reasonable (< 10MB for 20 titles)
        assert total_memory_mb < 10
        assert len(results) == len(clean_titles)

        print(f"Memory usage: {total_memory_mb:.2f} MB for {len(clean_titles)} clean titles")

    def test_memory_usage_gnarly_titles(self, gnarly_titles):
        """Measure memory usage for complex title parsing."""
        warmup_parser(gnarly_titles[:3])

        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        # Parse all titles
        results = [parse_title(title) for title in gnarly_titles]

        snapshot2 = tracemalloc.take_snapshot()

        # Calculate memory difference
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        total_memory_mb = sum(stat.size_diff for stat in top_stats) / 1024 / 1024

        tracemalloc.stop()

        # Complex titles may use more memory but should still be reasonable
        assert total_memory_mb < 20
        assert len(results) == len(gnarly_titles)

        print(f"Memory usage: {total_memory_mb:.2f} MB for {len(gnarly_titles)} complex titles")

    def test_memory_scaling_large_batch(self, clean_titles):
        """Test memory usage with large batches."""
        large_batch = clean_titles * 100  # 2000 titles
        warmup_parser(large_batch[:5])

        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()

        # Process in chunks to simulate real-world usage
        chunk_size = 100
        all_results = []
        for i in range(0, len(large_batch), chunk_size):
            chunk = large_batch[i:i + chunk_size]
            chunk_results = [parse_title(title) for title in chunk]
            all_results.extend(chunk_results)

        snapshot2 = tracemalloc.take_snapshot()

        # Calculate memory difference
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        total_memory_mb = sum(stat.size_diff for stat in top_stats) / 1024 / 1024

        tracemalloc.stop()

        # Memory should scale reasonably (< 100MB for 2000 titles)
        assert total_memory_mb < 100
        assert len(all_results) == len(large_batch)

        print(f"Memory usage: {total_memory_mb:.2f} MB for {len(large_batch)} titles (chunked)")


def test_performance_regression_guard(clean_titles):
    """Guard against performance regressions with timing assertions."""
    warmup_parser(clean_titles)

    # Time the operation
    start_time = time.perf_counter_ns()
    results = [parse_title(title) for title in clean_titles]
    end_time = time.perf_counter_ns()

    duration_ms = (end_time - start_time) / 1_000_000
    ops_per_second = len(clean_titles) / (duration_ms / 1000)

    # Should process at least 1000 titles/second (adjust based on requirements)
    assert ops_per_second > 1000, f"Performance regression: {ops_per_second:.0f} ops/sec"
    assert len(results) == len(clean_titles)

    print(f"Performance: {ops_per_second:.0f} titles/sec, {duration_ms:.1f}ms total")


def test_accuracy_vs_performance_tradeoff(gnarly_titles):
    """Test that performance optimizations don't hurt accuracy."""
    # Parse with full processing
    start_time = time.perf_counter_ns()
    detailed_results = [parse_title(title) for title in gnarly_titles]
    detailed_time = time.perf_counter_ns() - start_time

    # Count successful parses
    successful_detailed = sum(1 for r in detailed_results if r.artist and r.title)

    # Performance should be reasonable and accuracy should be high
    detailed_ops_per_sec = len(gnarly_titles) / (detailed_time / 1_000_000_000)
    accuracy_rate = successful_detailed / len(gnarly_titles)

    assert detailed_ops_per_sec > 100, "Performance too slow for complex titles"
    assert accuracy_rate > 0.7, "Accuracy too low for complex titles"

    print(f"Complex titles: {detailed_ops_per_sec:.0f} ops/sec, {accuracy_rate:.1%} accuracy")

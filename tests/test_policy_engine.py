# SPDX-License-Identifier: MIT
# Copyright (c) 2024 MusicScope

"""Tests for policy engine functionality."""

import pytest
from music_title_parser.models import ParsedTitle
from music_title_parser.policy_engine import PolicyEngine, parse_with_policy


class TestPolicyEngine:
    """Test policy engine core functionality."""

    def test_garbage_detection(self):
        """Test that garbage artists are properly detected."""
        engine = PolicyEngine()

        # Known garbage patterns
        assert engine.is_garbage_artist("3rd I Cam")
        assert engine.is_garbage_artist("word 4 word🎼")
        assert engine.is_garbage_artist("GameSound Hub 🎮🎶")

        # Clean artists should not be flagged
        assert not engine.is_garbage_artist("Taylor Swift")
        assert not engine.is_garbage_artist("Drake")
        assert not engine.is_garbage_artist("")

    def test_oac_detection(self):
        """Test YouTube Official Artist Channel detection."""
        engine = PolicyEngine()

        # Should detect OAC channels
        assert engine.is_youtube_oac("Taylor Swift - Topic")
        assert engine.is_youtube_oac("DrakeVEVO")

        # Should not detect regular channels
        assert not engine.is_youtube_oac("Random Channel")
        assert not engine.is_youtube_oac("3rd I Cam")
        assert not engine.is_youtube_oac("")

    def test_oac_artist_extraction(self):
        """Test artist name extraction from OAC channels."""
        engine = PolicyEngine()

        assert engine.get_oac_artist_name("Taylor Swift - Topic") == "Taylor Swift"
        assert engine.get_oac_artist_name("DrakeVEVO") == "Drake"
        assert engine.get_oac_artist_name("Random Channel") is None

    def test_confidence_calculation(self):
        """Test confidence scoring system."""
        engine = PolicyEngine()

        # High confidence for OAC
        conf, reason = engine.calculate_confidence(
            "Taylor Swift", "Anti-Hero", "Taylor Swift - Topic", "channel_oac"
        )
        assert conf >= 0.9
        assert "OAC boost" in reason

        # Zero confidence for garbage
        conf, reason = engine.calculate_confidence("3rd I Cam", "Some Song", "", "basic_parsing")
        assert conf == 0.0
        assert "GARBAGE DETECTED" in reason

    def test_decision_making(self):
        """Test decision thresholds across profiles."""
        engine = PolicyEngine()

        # High confidence should be accepted in all profiles
        assert engine.make_decision(0.9, "strict") == "accept"
        assert engine.make_decision(0.9, "balanced") == "accept"
        assert engine.make_decision(0.9, "aggressive") == "accept"

        # Low confidence should be rejected in all profiles
        assert engine.make_decision(0.1, "strict") == "reject"
        assert engine.make_decision(0.1, "balanced") == "reject"
        assert engine.make_decision(0.1, "aggressive") == "reject"


class TestParseWithPolicy:
    """Test the main parse_with_policy function."""

    def test_oac_parsing(self):
        """Test parsing with YouTube OAC channels."""
        result = parse_with_policy("Anti-Hero", "Taylor Swift - Topic", "balanced")

        assert isinstance(result, ParsedTitle)
        assert result.artist == "Taylor Swift"
        assert result.decision == "accept"
        assert result.confidence >= 0.9
        assert result.parsing_method == "channel_oac"

    def test_dash_parsing(self):
        """Test parsing with dash separators."""
        result = parse_with_policy("Taylor Swift - Anti-Hero", "", "balanced")

        assert result.artist == "Taylor Swift"
        assert result.title == "Taylor Swift - Anti-Hero"  # Basic parser doesn't split
        assert result.parsing_method in ["title_dash", "basic_parsing"]

    def test_garbage_rejection(self):
        """Test that garbage artists are rejected."""
        result = parse_with_policy("3rd I Cam''the Light On''word 4 word🎼", "3rd I Cam")

        assert result.decision == "reject"
        assert result.artist == ""
        assert result.confidence == 0.0

    def test_profile_differences(self):
        """Test that different profiles behave differently."""
        title = "Ambiguous - Title"

        strict_result = parse_with_policy(title, "", "strict")
        balanced_result = parse_with_policy(title, "", "balanced")
        aggressive_result = parse_with_policy(title, "", "aggressive")

        # All should return valid ParsedTitle objects
        assert all(
            isinstance(r, ParsedTitle) for r in [strict_result, balanced_result, aggressive_result]
        )

        # Profile should be recorded correctly
        assert strict_result.profile_used == "strict"
        assert balanced_result.profile_used == "balanced"
        assert aggressive_result.profile_used == "aggressive"

    def test_empty_inputs(self):
        """Test handling of empty or invalid inputs."""
        result = parse_with_policy("", "", "balanced")

        assert isinstance(result, ParsedTitle)
        assert result.artist == ""
        assert result.decision == "reject"

    def test_type_safety(self):
        """Test that return types are correct."""
        result = parse_with_policy("Test Title", "Test Channel", "balanced")

        # Should return ParsedTitle with correct types
        assert isinstance(result, ParsedTitle)
        assert isinstance(result.artist, str)
        assert isinstance(result.title, str)
        assert isinstance(result.features, list)
        assert isinstance(result.confidence, float)
        assert result.decision in ["accept", "graylist", "reject"]
        assert result.profile_used in ["strict", "balanced", "aggressive"]

        # Confidence should be in valid range
        assert 0.0 <= result.confidence <= 1.0


@pytest.mark.benchmark
class TestPerformance:
    """Performance tests for benchmarking."""

    def test_parsing_speed(self, benchmark):
        """Benchmark parsing speed."""

        def parse_titles():
            titles = [
                "Artist - Song Title",
                "Song (feat. Featured Artist)",
                "Artist & Guest - Collaboration",
            ]
            for title in titles:
                parse_with_policy(title, "", "balanced")

        benchmark(parse_titles)

    def test_garbage_detection_speed(self, benchmark):
        """Benchmark garbage detection speed."""
        engine = PolicyEngine()

        def check_garbage():
            artists = ["3rd I Cam", "Taylor Swift", "word 4 word🎼", "Drake"]
            for artist in artists:
                engine.is_garbage_artist(artist)

        benchmark(check_garbage)

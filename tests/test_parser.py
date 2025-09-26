# SPDX-License-Identifier: MIT
# Copyright (c) 2024 MusicScope

"""
Tests for music title parser functionality.

These tests verify title parsing, artist extraction, feature detection,
and version identification capabilities.
"""

import pytest
from music_title_parser.parser import parse_title, split_artist_title


class TestBasicTitleParsing:
    """Test basic title parsing functionality."""

    def test_basic_title_no_features_no_version(self):
        """Test parsing simple title with no features or version."""
        title = "My Awesome Song"
        expected = {
            "artist": "",
            "title": "My Awesome Song",
            "features": [],
            "version": "Original",
        }
        assert parse_title(title) == expected

    def test_empty_title_raises_error(self):
        """Test that empty title raises ValueError."""
        with pytest.raises(ValueError, match="title must be a non-empty string"):
            parse_title("")

    def test_none_title_raises_error(self):
        """Test that None title raises ValueError."""
        with pytest.raises(ValueError, match="title must be a non-empty string"):
            parse_title(None)

    def test_whitespace_only_title_raises_error(self):
        """Test that whitespace-only title raises ValueError."""
        with pytest.raises(ValueError, match="title must be a non-empty string"):
            parse_title("   ")


class TestFeatureDetection:
    """Test feature artist detection."""

    def test_title_with_feat_parentheses(self):
        """Test title with 'feat.' in parentheses."""
        title = "Song Title (feat. Featured Artist)"
        expected = {
            "artist": "",
            "title": "Song Title",
            "features": ["Featured Artist"],
            "version": "Original",
        }
        assert parse_title(title) == expected

    def test_title_with_ft_parentheses(self):
        """Test title with 'ft.' in parentheses."""
        title = "Another Song (ft. Another Artist)"
        expected = {
            "artist": "",
            "title": "Another Song",
            "features": ["Another Artist"],
            "version": "Original",
        }
        assert parse_title(title) == expected

    def test_title_with_featuring_parentheses(self):
        """Test title with 'featuring' in parentheses."""
        title = "Third Song (featuring Third Artist)"
        expected = {
            "artist": "",
            "title": "Third Song",
            "features": ["Third Artist"],
            "version": "Original",
        }
        assert parse_title(title) == expected

    def test_title_with_multiple_features(self):
        """Test title with multiple featured artists."""
        title = "Song Title (feat. Artist A & Artist B)"
        expected = {
            "artist": "",
            "title": "Song Title",
            "features": ["Artist A", "Artist B"],
            "version": "Original",
        }
        assert parse_title(title) == expected

    def test_title_with_features_and_commas(self):
        """Test title with comma-separated featured artists."""
        title = "Song Title (feat. Artist A, Artist B, Artist C)"
        expected = {
            "artist": "",
            "title": "Song Title",
            "features": ["Artist A", "Artist B", "Artist C"],
            "version": "Original",
        }
        assert parse_title(title) == expected

    def test_title_with_features_dash_format(self):
        """Test title with features in dash format."""
        title = "Song Title - feat. Featured Artist"
        expected = {
            "artist": "",
            "title": "Song Title",
            "features": ["Featured Artist"],
            "version": "Original",
        }
        assert parse_title(title) == expected


class TestVersionDetection:
    """Test version identification."""

    def test_title_with_live_version(self):
        """Test title with live version."""
        title = "Song Title (Live)"
        expected = {
            "artist": "",
            "title": "Song Title",
            "features": [],
            "version": "Live",
        }
        assert parse_title(title) == expected

    def test_title_with_acoustic_version(self):
        """Test title with acoustic version."""
        title = "Song Title (Acoustic)"
        expected = {
            "artist": "",
            "title": "Song Title",
            "features": [],
            "version": "Acoustic",
        }
        assert parse_title(title) == expected

    def test_title_with_remix_version(self):
        """Test title with remix version."""
        title = "Song Title (Remix)"
        expected = {
            "artist": "",
            "title": "Song Title",
            "features": [],
            "version": "Remix",
        }
        assert parse_title(title) == expected

    def test_title_with_slowed_reverb(self):
        """Test title with slowed and reverb version."""
        title = "Song Title (Slowed + Reverb)"
        expected = {
            "artist": "",
            "title": "Song Title",
            "features": [],
            "version": "Slowed and Reverbed",
        }
        assert parse_title(title) == expected

    def test_title_with_radio_edit(self):
        """Test title with radio edit version."""
        title = "Song Title (Radio Edit)"
        expected = {
            "artist": "",
            "title": "Song Title",
            "features": [],
            "version": "Radio Edit",
        }
        assert parse_title(title) == expected


class TestComplexTitleParsing:
    """Test complex title parsing scenarios."""

    def test_title_with_features_and_version(self):
        """Test title with both features and version."""
        title = "Song Title (feat. Featured Artist) (Live Version)"
        expected = {
            "artist": "",
            "title": "Song Title",
            "features": ["Featured Artist"],
            "version": "Live Version",
        }
        assert parse_title(title) == expected

    def test_title_with_multiple_features_and_version(self):
        """Test title with multiple features and version."""
        title = "Song Title (feat. Artist A & Artist B) (Acoustic)"
        expected = {
            "artist": "",
            "title": "Song Title",
            "features": ["Artist A", "Artist B"],
            "version": "Acoustic",
        }
        assert parse_title(title) == expected

    def test_title_with_mixed_brackets(self):
        """Test title with mixed bracket types."""
        title = "Song Title [feat. Featured Artist] (Live) {Remastered}"
        result = parse_title(title)

        assert result["title"] == "Song Title"
        assert "Featured Artist" in result["features"]
        # Should pick up first version-like content
        assert result["version"] in ["Live", "Remastered"]

    def test_title_with_youtube_noise(self):
        """Test title with YouTube presentation labels."""
        title = "Song Title (Official Music Video)"
        expected = {
            "artist": "",
            "title": "Song Title",
            "features": [],
            "version": "Original",  # Should ignore YouTube noise by default
        }
        assert parse_title(title) == expected

    def test_title_with_youtube_noise_normalized(self):
        """Test title with YouTube noise filtering enabled."""
        title = "Song Title (Official Music Video)"
        expected = {
            "artist": "",
            "title": "Song Title",
            "features": [],
            "version": "Original",
        }
        assert parse_title(title, normalize_youtube_noise=True) == expected


class TestArtistTitleSplitting:
    """Test artist and title splitting functionality."""

    def test_split_artist_title_basic(self):
        """Test basic artist-title splitting."""
        full = "Artist Name - Song Title"
        artists, title = split_artist_title(full)

        assert artists == ["Artist Name"]
        assert title == "Song Title"

    def test_split_artist_title_multiple_artists(self):
        """Test splitting with multiple artists."""
        full = "Artist A & Artist B - Song Title"
        artists, title = split_artist_title(full)

        assert artists == ["Artist A", "Artist B"]
        assert title == "Song Title"

    def test_split_artist_title_no_dash(self):
        """Test splitting when no dash is present."""
        full = "Just a Song Title"
        artists, title = split_artist_title(full)

        assert artists == []
        assert title == "Just a Song Title"

    def test_split_artist_title_with_features(self):
        """Test splitting preserves features in title."""
        full = "Artist A & Artist B - Song Title (feat. Featured Artist)"
        artists, title = split_artist_title(full)

        assert artists == ["Artist A", "Artist B"]
        assert title == "Song Title (feat. Featured Artist)"

    def test_split_artist_title_collaboration_separators(self):
        """Test various collaboration separators."""
        test_cases = [
            ("A & B - Title", ["A", "B"]),
            ("A and B - Title", ["A", "B"]),
            ("A x B - Title", ["A", "B"]),
            ("A × B - Title", ["A", "B"]),
            ("A + B - Title", ["A", "B"]),
            ("A, B - Title", ["A", "B"]),
        ]

        for full, expected_artists in test_cases:
            artists, title = split_artist_title(full)
            assert artists == expected_artists
            assert title == "Title"

    def test_split_artist_title_deduplication(self):
        """Test artist deduplication."""
        full = "Artist A & Artist A & Artist B - Song Title"
        artists, title = split_artist_title(full)

        assert artists == ["Artist A", "Artist B"]  # Deduplicated
        assert title == "Song Title"

    def test_split_artist_title_type_error(self):
        """Test that non-string input raises TypeError."""
        with pytest.raises(TypeError, match="full must be a string"):
            split_artist_title(123)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_title_with_nested_parentheses(self):
        """Test title with nested parentheses (should handle gracefully)."""
        title = "Song Title (feat. Artist (The Great))"
        result = parse_title(title)

        # Should still parse successfully
        assert result["title"] == "Song Title"
        assert isinstance(result["features"], list)

    def test_title_with_unmatched_brackets(self):
        """Test title with unmatched brackets."""
        title = "Song Title (feat. Artist"
        result = parse_title(title)

        # Should handle gracefully
        assert result["title"] is not None
        assert isinstance(result["features"], list)

    def test_title_with_unicode_characters(self):
        """Test title with unicode characters."""
        title = "Sóng Títle (feat. Artíst Ñame)"
        result = parse_title(title)

        assert "Sóng Títle" in result["title"]
        assert len(result["features"]) > 0

    def test_very_long_title(self):
        """Test with very long title."""
        long_title = "Very " * 100 + "Long Song Title"
        result = parse_title(long_title)

        assert result["title"] is not None
        assert len(result["title"]) > 0

    def test_title_with_numbers_and_symbols(self):
        """Test title with numbers and symbols."""
        title = "Song #1 (feat. Artist 2.0) [2024 Remix]"
        result = parse_title(title)

        assert "Song #1" in result["title"]
        assert len(result["features"]) > 0


class TestIntegration:
    """Integration tests with realistic scenarios."""

    def test_youtube_title_parsing(self):
        """Test parsing typical YouTube titles."""
        test_cases = [
            {
                "title": "Artist - Song Title (Official Music Video)",
                "expected_title": "Song Title",
                "expected_version": "Original",
            },
            {
                "title": "Song Title (feat. Artist A & Artist B) (Live Performance)",
                "expected_title": "Song Title",
                "expected_features": ["Artist A", "Artist B"],
                "expected_version": "Live Performance",
            },
            {
                "title": "Artist - Song Title (Slowed + Reverb)",
                "expected_title": "Song Title",
                "expected_version": "Slowed and Reverbed",
            },
        ]

        for case in test_cases:
            result = parse_title(case["title"])

            if "expected_title" in case:
                assert case["expected_title"] in result["title"]
            if "expected_features" in case:
                assert set(case["expected_features"]).issubset(set(result["features"]))
            if "expected_version" in case:
                assert result["version"] == case["expected_version"]

    def test_spotify_title_parsing(self):
        """Test parsing typical Spotify titles."""
        test_cases = [
            "Song Title",
            "Song Title (feat. Featured Artist)",
            "Song Title - Acoustic Version",
            "Song Title (Live from Studio)",
        ]

        for title in test_cases:
            result = parse_title(title)

            # Should parse without errors
            assert result["title"] is not None
            assert isinstance(result["features"], list)
            assert result["version"] is not None

    def test_combined_artist_splitting_and_parsing(self):
        """Test combined artist splitting and title parsing."""
        full = "Artist A & Artist B - Song Title (feat. Featured Artist) (Live)"

        # First split artists
        artists, title_part = split_artist_title(full)
        assert artists == ["Artist A", "Artist B"]

        # Then parse the title part
        result = parse_title(title_part)
        assert result["title"] == "Song Title"
        assert result["features"] == ["Featured Artist"]
        assert result["version"] == "Live"

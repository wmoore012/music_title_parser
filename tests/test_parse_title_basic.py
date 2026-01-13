# SPDX-License-Identifier: MIT

"""Unit tests for standalone parsing helpers."""

from __future__ import annotations

import pytest
from music_title_parser.parser import (
    normalize_channel_title_for_artist,
    parse_title,
    split_artist_title,
)


@pytest.mark.parametrize(
    "title,expected",
    [
        (
            "My Awesome Song",
            {
                "artist": "",
                "title": "My Awesome Song",
                "features": [],
                "version": "Original",
            },
        ),
        (
            "Song Title (feat. Artist A & Artist B)",
            {
                "artist": "",
                "title": "Song Title",
                "features": ["Artist A", "Artist B"],
                "version": "Original",
            },
        ),
        (
            "Track Name (Live Version)",
            {
                "artist": "",
                "title": "Track Name",
                "features": [],
                "version": "Live Version",
            },
        ),
    ],
)
def test_parse_title_various_cases(title: str, expected: dict[str, object]) -> None:
    """Ensure parse_title handles core scenarios."""

    assert parse_title(title) == expected


def test_split_artist_title_multiple_artists() -> None:
    artists, remainder = split_artist_title("Artist A & Artist B - Song Title")
    assert artists == ["Artist A", "Artist B"]
    assert remainder == "Song Title"


def test_parse_title_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="non - empty"):
        parse_title("   ")


def test_normalize_channel_title_strips_topic_suffix() -> None:
    assert normalize_channel_title_for_artist("Taylor Swift - Topic") == "Taylor Swift"
    assert normalize_channel_title_for_artist("  Artist Name  ") == "Artist Name"

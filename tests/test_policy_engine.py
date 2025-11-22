# SPDX-License-Identifier: MIT

"""Tests covering policy-driven parsing logic."""

from __future__ import annotations

import pytest

from music_title_parser.exceptions import ValidationError
from music_title_parser.policy_engine import PolicyEngine, parse_with_policy


def test_parse_with_policy_uses_allowlist_oac_channel() -> None:
    result = parse_with_policy("Anti-Hero", "Taylor Swift - Topic", "balanced")

    assert result.artist == "Taylor Swift"
    assert result.decision == "accept"
    assert result.parsing_method == "channel_oac"
    assert result.confidence >= 0.9


def test_parse_with_policy_rejects_denylisted_channel() -> None:
    result = parse_with_policy("Any Song", "word 4 word🎼", "balanced")

    assert result.decision == "reject"
    assert result.confidence == 0.0
    assert "Denylist" in result.reason


def test_profile_thresholds_affect_decision() -> None:
    engine = PolicyEngine()
    title = "Phoenix-Run"  # Lacks spaced dash so needs Stage-B recovery

    strict_result = engine.parse(title, profile="strict")
    balanced_result = engine.parse(title, profile="balanced")

    assert strict_result.decision == "reject"  # Stage B disabled → low confidence
    assert balanced_result.decision == "graylist"
    assert balanced_result.parsing_method == "stage_b_recovery"
    assert balanced_result.confidence > strict_result.confidence


def test_stage_a_dash_split_remains_accept() -> None:
    result = parse_with_policy("Artist X - Midnight", "", "balanced")

    assert result.artist == "Artist X"
    assert result.decision == "accept"
    assert result.parsing_method == "title_dash"


def test_parse_with_policy_validates_title_input() -> None:
    engine = PolicyEngine()
    with pytest.raises(ValidationError):
        engine.parse("", profile="balanced")

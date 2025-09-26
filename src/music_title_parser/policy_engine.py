# SPDX-License-Identifier: MIT
# Copyright (c) 2024 MusicScope

"""
Policy Engine for Music Title Parsing

This module implements the three-tier parsing system with confidence scoring,
garbage detection, and YouTube Official Artist Channel (OAC) support.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from .exceptions import ConfigLoadError, InvalidPatternError
from .models import ParsedTitle, ParsingMethod, PolicyProfile

if TYPE_CHECKING:
    from typing import Any


class PolicyEngine:
    """Policy-aware parsing engine with three-tier system."""

    def __init__(self, policy_path: str | None = None) -> None:
        """Initialize policy engine."""
        self.policy = self._load_policy(policy_path)
        self.allowlist = self._load_allowlist()
        self.denylist = self._load_denylist()

    def _load_policy(self, policy_path: str | None = None) -> dict[str, Any]:
        """Load policy configuration."""
        if policy_path is None:
            current_dir = Path(__file__).parent
            policy_path = str(current_dir / "config" / "perday_parser_policy.yaml")

        try:
            with open(policy_path) as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ConfigLoadError(policy_path, str(e)) from e

    def _load_allowlist(self) -> dict[str, Any]:
        """Load allowlist configuration."""
        try:
            current_dir = Path(__file__).parent
            allowlist_path = current_dir / "config" / "allowlist.json"
            with open(allowlist_path) as f:
                return json.load(f)
        except Exception:
            return {"entries": []}

    def _load_denylist(self) -> dict[str, Any]:
        """Load denylist configuration."""
        try:
            current_dir = Path(__file__).parent
            denylist_path = current_dir / "config" / "denylist.json"
            with open(denylist_path) as f:
                return json.load(f)
        except Exception:
            return {"entries": []}

    def is_garbage_artist(self, artist_name: str) -> bool:
        """Check if artist name matches garbage patterns."""
        if not artist_name:
            return False

        for entry in self.denylist.get("entries", []):
            if self._matches_denylist_entry(artist_name, entry):
                return True

        return False

    def _matches_denylist_entry(self, artist_name: str, entry: dict[str, Any]) -> bool:
        """Check if artist matches a single denylist entry."""
        pattern_mapping = entry.get("pattern_or_mapping", {})

        # Check regex patterns
        if "regex" in pattern_mapping:
            try:
                if re.search(pattern_mapping["regex"], artist_name, re.IGNORECASE):
                    return True
            except re.error as e:
                raise InvalidPatternError(pattern_mapping["regex"], str(e)) from e

        # Check exact matches
        if "exact_match" in pattern_mapping:
            if artist_name == pattern_mapping["exact_match"]:
                return True

        return False

    def is_youtube_oac(self, channel_title: str) -> bool:
        """Check if channel is a YouTube Official Artist Channel."""
        if not channel_title:
            return False

        # Check allowlist for OAC entries
        for entry in self.allowlist.get("entries", []):
            if self._is_oac_entry(channel_title, entry):
                return True

        # Check common OAC patterns
        return self._matches_oac_patterns(channel_title)

    def _is_oac_entry(self, channel_title: str, entry: dict[str, Any]) -> bool:
        """Check if channel matches an allowlist OAC entry."""
        if entry.get("type") != "youtube_oac":
            return False

        pattern = entry.get("pattern_or_mapping", {})
        return pattern.get("channel_name") == channel_title

    def _matches_oac_patterns(self, channel_title: str) -> bool:
        """Check if channel matches common OAC patterns."""
        oac_patterns = [
            r".*\s-\sTopic$",  # "Artist - Topic"
            r".*VEVO$",  # "ArtistVEVO"
        ]

        return any(re.search(pattern, channel_title, re.IGNORECASE) for pattern in oac_patterns)

    def get_oac_artist_name(self, channel_title: str) -> str | None:
        """Extract artist name from OAC channel title."""
        if not self.is_youtube_oac(channel_title):
            return None

        # Check allowlist for explicit mapping
        for entry in self.allowlist.get("entries", []):
            artist_name = self._get_oac_artist_from_entry(channel_title, entry)
            if artist_name:
                return artist_name

        # Extract from common patterns
        return self._extract_artist_from_oac_pattern(channel_title)

    def _get_oac_artist_from_entry(self, channel_title: str, entry: dict[str, Any]) -> str | None:
        """Get artist name from allowlist entry."""
        if entry.get("type") != "youtube_oac":
            return None

        pattern = entry.get("pattern_or_mapping", {})
        if pattern.get("channel_name") == channel_title:
            return pattern.get("artist_name")

        return None

    def _extract_artist_from_oac_pattern(self, channel_title: str) -> str | None:
        """Extract artist name from common OAC patterns."""
        if channel_title.endswith(" - Topic"):
            return channel_title[:-8].strip()
        elif channel_title.endswith("VEVO"):
            return channel_title[:-4].strip()

        return None

    def calculate_confidence(
        self,
        artist: str,
        title: str,
        channel_title: str = "",
        parsing_method: ParsingMethod = "basic_parsing",
    ) -> tuple[float, str]:
        """Calculate confidence score for parsed result."""
        confidence = self._get_base_confidence(parsing_method)
        reasons = [self._get_method_reason(parsing_method)]

        # Apply penalties and boosts
        confidence, penalty_reason = self._apply_penalties(confidence, artist)
        if penalty_reason:
            reasons.append(penalty_reason)

        confidence, boost_reason = self._apply_boosts(confidence, channel_title)
        if boost_reason:
            reasons.append(boost_reason)

        return confidence, "; ".join(reasons)

    def _get_base_confidence(self, parsing_method: ParsingMethod) -> float:
        """Get base confidence by parsing method."""
        confidence_map = {
            "title_dash": 0.8,
            "title_features": 0.75,
            "channel_oac": 0.9,
            "channel_fuzzy": 0.6,
            "stage_b_recovery": 0.65,
            "basic_parsing": 0.5,
        }
        return confidence_map.get(parsing_method, 0.5)

    def _get_method_reason(self, parsing_method: ParsingMethod) -> str:
        """Get human-readable reason for parsing method."""
        reason_map = {
            "title_dash": "clean dash separator",
            "title_features": "feature extraction",
            "channel_oac": "YouTube OAC",
            "channel_fuzzy": "channel matching",
            "stage_b_recovery": "stage B recovery",
            "basic_parsing": "basic parsing",
        }
        return reason_map.get(parsing_method, "unknown method")

    def _apply_penalties(self, confidence: float, artist: str) -> tuple[float, str]:
        """Apply confidence penalties."""
        if self.is_garbage_artist(artist):
            return 0.0, "GARBAGE DETECTED"

        if not artist:
            return 0.0, "no artist extracted"

        return confidence, ""

    def _apply_boosts(self, confidence: float, channel_title: str) -> tuple[float, str]:
        """Apply confidence boosts."""
        if self.is_youtube_oac(channel_title):
            oac_boost = self._get_oac_boost()
            new_confidence = min(1.0, confidence + oac_boost)
            return new_confidence, f"OAC boost (+{oac_boost})"

        return confidence, ""

    def _get_oac_boost(self) -> float:
        """Get OAC boost value from policy."""
        return self.policy.get("profiles", {}).get("balanced", {}).get("oac_boost", 0.15)

    def make_decision(self, confidence: float, profile_name: PolicyProfile) -> str:
        """Make accept/graylist/reject decision based on confidence and profile."""
        profile = self.policy.get("profiles", {}).get(profile_name, {})

        accept_min = profile.get("accept_min", 0.7)
        gray_min = profile.get("gray_min", 0.4)

        if confidence >= accept_min:
            return "accept"
        elif confidence >= gray_min:
            return "graylist"
        else:
            return "reject"

    def parse_with_policy(
        self,
        title: str,
        channel_title: str = "",
        profile: PolicyProfile = "balanced",
    ) -> ParsedTitle:
        """Parse title using specified policy profile."""
        # Stage A: Standards-first parsing (high precision)
        result = self._stage_a_parsing(title, channel_title)

        # Stage B: Recovery parsing (if enabled for profile)
        if not result.artist and self._should_use_stage_b(profile):
            result = self._stage_b_parsing(title, channel_title)

        # Calculate confidence and make decision
        confidence, reason = self.calculate_confidence(
            result.artist, result.title, channel_title, result.parsing_method
        )

        decision = self.make_decision(confidence, profile)

        return ParsedTitle(
            artist=result.artist,
            title=result.title,
            features=result.features,
            version=result.version,
            confidence=confidence,
            decision=decision,  # type: ignore[arg-type]
            reason=reason,
            profile_used=profile,
            parsing_method=result.parsing_method,
        )

    def _should_use_stage_b(self, profile: PolicyProfile) -> bool:
        """Check if Stage B parsing should be used for this profile."""
        profile_config = self.policy.get("profiles", {}).get(profile, {})
        return profile_config.get("allow_stage_b", False)

    def _stage_a_parsing(self, title: str, channel_title: str = "") -> _ParseResult:
        """Stage A: Standards-first parsing with high precision."""
        # Try YouTube OAC first (highest confidence)
        oac_result = self._try_oac_parsing(title, channel_title)
        if oac_result:
            return oac_result

        # Try standard dash parsing
        dash_result = self._try_dash_parsing(title)
        if dash_result:
            return dash_result

        # Fallback to basic parsing
        return self._basic_parsing(title)

    def _try_oac_parsing(self, title: str, channel_title: str) -> _ParseResult | None:
        """Try parsing using YouTube OAC channel information."""
        if not channel_title or not self.is_youtube_oac(channel_title):
            return None

        oac_artist = self.get_oac_artist_name(channel_title)
        if not oac_artist or self.is_garbage_artist(oac_artist):
            return None

        basic_result = self._parse_title_basic(title)
        return _ParseResult(
            artist=oac_artist,
            title=basic_result["title"],
            features=basic_result["features"],
            version=basic_result["version"],
            parsing_method="channel_oac",
        )

    def _try_dash_parsing(self, title: str) -> _ParseResult | None:
        """Try parsing using dash separators."""
        if " - " not in title and " – " not in title:
            return None

        parts = re.split(r" [-–] ", title, 1)
        if len(parts) != 2:
            return None

        potential_artist = parts[0].strip()
        if self.is_garbage_artist(potential_artist):
            return None

        remaining_title = parts[1].strip()
        basic_result = self._parse_title_basic(remaining_title)

        return _ParseResult(
            artist=potential_artist,
            title=basic_result["title"],
            features=basic_result["features"],
            version=basic_result["version"],
            parsing_method="title_dash",
        )

    def _basic_parsing(self, title: str) -> _ParseResult:
        """Fallback to basic parsing."""
        basic_result = self._parse_title_basic(title)
        return _ParseResult(
            artist="",
            title=basic_result["title"],
            features=basic_result["features"],
            version=basic_result["version"],
            parsing_method="basic_parsing",
        )

    def _stage_b_parsing(self, title: str, channel_title: str = "") -> _ParseResult:
        """Stage B: Recovery parsing with looser rules."""
        loose_separators = [" & ", " x ", " / ", ", "]

        for sep in loose_separators:
            result = self._try_separator_parsing(title, sep)
            if result:
                return result

        # If no recovery possible, return stage A result
        return self._stage_a_parsing(title, channel_title)

    def _try_separator_parsing(self, title: str, separator: str) -> _ParseResult | None:
        """Try parsing with a specific separator."""
        if separator not in title:
            return None

        parts = title.split(separator, 1)
        if len(parts) != 2:
            return None

        potential_artist = parts[0].strip()
        if not potential_artist or self.is_garbage_artist(potential_artist):
            return None

        remaining_title = parts[1].strip()
        basic_result = self._parse_title_basic(remaining_title)

        return _ParseResult(
            artist=potential_artist,
            title=basic_result["title"],
            features=basic_result["features"],
            version=basic_result["version"],
            parsing_method="stage_b_recovery",
        )

    def _parse_title_basic(self, title: str) -> dict[str, Any]:
        """Parse title using basic parser."""
        from .parser import parse_title

        return parse_title(title)


class _ParseResult:
    """Internal parsing result before confidence calculation."""

    def __init__(
        self,
        artist: str,
        title: str,
        features: list[str],
        version: str,
        parsing_method: ParsingMethod,
    ) -> None:
        self.artist = artist
        self.title = title
        self.features = features
        self.version = version
        self.parsing_method = parsing_method


# Global policy engine instance
_policy_engine: PolicyEngine | None = None


def get_policy_engine() -> PolicyEngine:
    """Get global policy engine instance."""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine


def parse_with_policy(
    title: str,
    channel_title: str = "",
    profile: PolicyProfile = "balanced",
) -> ParsedTitle:
    """Parse title using policy engine."""
    engine = get_policy_engine()
    return engine.parse_with_policy(title, channel_title, profile)

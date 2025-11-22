# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Perday CatalogLAB™

"""Policy-aware parsing utilities."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .exceptions import ConfigLoadError, InvalidPatternError, PolicyError, ValidationError
from .models import (
    AllowlistEntry,
    Decision,
    DenylistEntry,
    ParsedTitle,
    ParserPolicy,
    ParsingMethod,
    PolicyProfile,
    DEFAULT_POLICY_PROFILE,
)
from .parser import (
    normalize_channel_title_for_artist,
    parse_title,
    split_artist_title,
)

__all__ = ["PolicyEngine", "get_policy_engine", "parse_with_policy"]


@dataclass(frozen=True)
class _DenylistHit:
    entry: DenylistEntry
    source_value: str


class PolicyEngine:
    """Loads parser policy + allow/deny lists and evaluates parse decisions."""

    _BASE_CONFIDENCE = {
        "channel_oac": 0.90,
        "title_dash": 0.80,
        "title_features": 0.75,
        "stage_b_recovery": 0.65,
        "channel_fuzzy": 0.60,
        "basic_parsing": 0.50,
    }

    def __init__(self, config_dir: str | Path | None = None) -> None:
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).resolve().parent / "config"
        if not self.config_dir.exists():
            raise ConfigLoadError(str(self.config_dir), "config directory not found")

        self.policy = self._load_policy(self.config_dir / "perday_parser_policy.json")
        self.allowlist, self._allow_exact, self._allow_regex = self._load_allowlist(
            self.config_dir / "allowlist.json"
        )
        self.denylist, self._deny_exact, self._deny_regex = self._load_denylist(
            self.config_dir / "denylist.json"
        )

    def parse(
        self,
        title: str,
        channel_title: str = "",
        profile: PolicyProfile = DEFAULT_POLICY_PROFILE,
    ) -> ParsedTitle:
        """Parse a title and apply policy decisions."""

        if not isinstance(title, str) or not title.strip():
            raise ValidationError("title", str(title), "must be a non-empty string")

        channel_title = channel_title or ""
        normalized_channel = normalize_channel_title_for_artist(channel_title)
        profile_config = self.policy.get_profile(profile)

        stage_a_artists, candidate_title = split_artist_title(title)
        parsing_method: ParsingMethod = "basic_parsing"
        base_confidence = self._BASE_CONFIDENCE[parsing_method]
        reason_parts: list[str] = []
        artist = ""

        if stage_a_artists:
            artist = stage_a_artists[0]
            parsing_method = "title_dash"
            base_confidence = self._BASE_CONFIDENCE[parsing_method]
            reason_parts.append("Stage-A dash split")
        else:
            candidate_title = title.strip()

        stage_b_artist, stage_b_title = self._stage_b_artist_guess(title)
        if not artist and profile_config.allow_stage_b and stage_b_artist:
            artist = stage_b_artist
            candidate_title = stage_b_title
            parsing_method = "stage_b_recovery"
            base_confidence = self._BASE_CONFIDENCE[parsing_method]
            reason_parts.append("Stage-B dash recovery")

        parsed_components = parse_title(candidate_title, normalize_youtube_noise=True)
        song_title = parsed_components.get("title", candidate_title)
        features = parsed_components.get("features", [])
        version = parsed_components.get("version", "Original")

        raw_channel = channel_title.strip()
        allow_hit = self._match_allowlist(raw_channel) or (
            normalized_channel != raw_channel and self._match_allowlist(normalized_channel)
        )
        channel_boost = 0.0
        if allow_hit:
            channel_boost = allow_hit.confidence_boost or profile_config.oac_boost
            if not artist or parsing_method == "stage_b_recovery":
                mapping = allow_hit.pattern_or_mapping
                artist = mapping.get("artist_name", artist)
                parsing_method = "channel_oac"
                base_confidence = self._BASE_CONFIDENCE[parsing_method]
            reason_parts.append("OAC channel match")

        garbage_hit = self._match_denylist(artist) or self._match_denylist(raw_channel)

        confidence = self._clamp_confidence(base_confidence + channel_boost)

        if garbage_hit:
            decision: Decision = "reject"
            reason = f"Denylist: {self._describe_entry(garbage_hit.entry)}"
            confidence = 0.0
        else:
            decision = self._decide(confidence, profile_config)
            if not reason_parts:
                reason_parts.append("basic parsing")
            reason_parts.append(f"profile '{profile}' thresholds")
            if channel_boost:
                reason_parts.append(f"OAC boost +{channel_boost:.2f}")
            reason = "; ".join(reason_parts)

        return ParsedTitle(
            artist=artist,
            title=song_title,
            features=features,
            version=version,
            confidence=confidence,
            decision=decision,
            reason=reason,
            profile_used=profile,
            parsing_method=parsing_method,
        )

    # ------------------------------------------------------------------
    # Loading helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _load_json(path: Path) -> Any:
        try:
            return json.loads(path.read_text())
        except FileNotFoundError as exc:
            raise ConfigLoadError(str(path), "file missing") from exc
        except json.JSONDecodeError as exc:
            raise ConfigLoadError(str(path), f"invalid json: {exc}") from exc

    def _load_policy(self, path: Path) -> ParserPolicy:
        data = self._load_json(path)
        try:
            return ParserPolicy(**data)
        except Exception as exc:  # pragma: no cover - delegated to pydantic
            raise PolicyError(f"invalid policy file '{path}': {exc}") from exc

    def _load_allowlist(
        self, path: Path
    ) -> tuple[list[AllowlistEntry], dict[str, AllowlistEntry], list[tuple[re.Pattern[str], AllowlistEntry]]]:
        data = self._load_json(path)
        entries = [AllowlistEntry(**raw) for raw in data.get("entries", [])]
        exact: dict[str, AllowlistEntry] = {}
        regex_entries: list[tuple[re.Pattern[str], AllowlistEntry]] = []
        for entry in entries:
            mapping = entry.pattern_or_mapping
            channel_name = mapping.get("channel_name")
            if channel_name:
                exact[channel_name.casefold()] = entry
            pattern = mapping.get("regex")
            if pattern:
                regex_entries.append((self._compile_pattern(pattern), entry))
        return entries, exact, regex_entries

    def _load_denylist(
        self, path: Path
    ) -> tuple[list[DenylistEntry], dict[str, DenylistEntry], list[tuple[re.Pattern[str], DenylistEntry]]]:
        data = self._load_json(path)
        entries = [DenylistEntry(**raw) for raw in data.get("entries", [])]
        exact: dict[str, DenylistEntry] = {}
        regex_entries: list[tuple[re.Pattern[str], DenylistEntry]] = []
        for entry in entries:
            mapping = entry.pattern_or_mapping
            if "exact_match" in mapping:
                exact[mapping["exact_match"].casefold()] = entry
            pattern = mapping.get("regex")
            if pattern:
                regex_entries.append((self._compile_pattern(pattern), entry))
        return entries, exact, regex_entries

    @staticmethod
    def _compile_pattern(pattern: str) -> re.Pattern[str]:
        try:
            return re.compile(pattern, re.IGNORECASE)
        except re.error as exc:  # pragma: no cover - defensive
            raise InvalidPatternError(pattern, str(exc)) from exc

    # ------------------------------------------------------------------
    # Matching helpers
    # ------------------------------------------------------------------
    def _match_allowlist(self, channel_title: str) -> AllowlistEntry | None:
        if not channel_title:
            return None
        normalized = channel_title.casefold()
        if normalized in self._allow_exact:
            return self._allow_exact[normalized]
        for pattern, entry in self._allow_regex:
            if pattern.search(channel_title):
                return entry
        return None

    def _match_denylist(self, value: str) -> _DenylistHit | None:
        value = (value or "").strip()
        if not value:
            return None
        key = value.casefold()
        entry = self._deny_exact.get(key)
        if entry:
            return _DenylistHit(entry=entry, source_value=value)
        for pattern, candidate in self._deny_regex:
            if pattern.search(value):
                return _DenylistHit(entry=candidate, source_value=value)
        return None

    # ------------------------------------------------------------------
    # Decision helpers
    # ------------------------------------------------------------------
    def _decide(self, confidence: float, profile: Any) -> Decision:
        if confidence >= profile.accept_min:
            return "accept"
        if confidence >= profile.gray_min:
            return "graylist"
        return "reject"

    @staticmethod
    def _clamp_confidence(value: float) -> float:
        return max(0.0, min(1.0, round(value, 4)))

    @staticmethod
    def _describe_entry(entry: DenylistEntry) -> str:
        details = entry.pattern_or_mapping
        if "description" in details:
            return details["description"]
        if "regex" in details:
            return f"regex: {details['regex']}"
        if "exact_match" in details:
            return f"exact: {details['exact_match']}"
        return entry.type

    @staticmethod
    def _stage_b_artist_guess(full_title: str) -> tuple[str, str]:
        if not isinstance(full_title, str):
            return "", ""
        for token in ("-", "–", "—"):
            if token in full_title and f" {token} " not in full_title:
                left, right = full_title.split(token, 1)
                left = left.strip()
                right = right.strip()
                if left and right:
                    return left, right
        return "", full_title.strip()


_ENGINE_INSTANCE: PolicyEngine | None = None


def get_policy_engine() -> PolicyEngine:
    """Return the singleton policy engine instance."""

    global _ENGINE_INSTANCE
    if _ENGINE_INSTANCE is None:
        _ENGINE_INSTANCE = PolicyEngine()
    return _ENGINE_INSTANCE


def parse_with_policy(
    title: str,
    channel_title: str = "",
    profile: PolicyProfile = DEFAULT_POLICY_PROFILE,
) -> ParsedTitle:
    """Helper that proxies to the singleton policy engine."""

    engine = get_policy_engine()
    return engine.parse(title=title, channel_title=channel_title, profile=profile)

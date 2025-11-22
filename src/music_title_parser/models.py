# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Perday CatalogLAB™

"""
Typed models for music title parsing.

This module provides Pydantic models for type - safe parsing results and configuration.
"""

from __future__ import annotations

from typing import Final, Literal, NewType

from pydantic import BaseModel, ConfigDict, Field

# Type aliases for better type safety
VideoId = NewType("VideoId", str)
ArtistId = NewType("ArtistId", str)
ISRC = NewType("ISRC", str)

# Literal types for policy profiles
PolicyProfile = Literal["strict", "balanced", "aggressive"]
Decision = Literal["accept", "graylist", "reject"]
ParsingMethod = Literal[
    "title_dash",
    "title_features",
    "channel_oac",
    "channel_fuzzy",
    "basic_parsing",
    "stage_b_recovery",
]

# Constants
DEFAULT_CONFIDENCE_THRESHOLD: Final[float] = 0.7
MAX_COMPLEXITY_THRESHOLD: Final[int] = 10
DEFAULT_POLICY_PROFILE: Final[PolicyProfile] = "balanced"


class ParsedTitle(BaseModel):
    """
    Typed result from music title parsing.

    This is the main output model that replaces raw dictionaries.
    """

    model_config = ConfigDict(
        frozen=True,  # Immutable result
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    artist: str = Field(
        default="",
        description="Primary artist name (empty if not detected)",
        examples=["Taylor Swift", "Drake", ""],
    )
    title: str = Field(
        description="Clean song title",
        examples=["Anti - Hero", "God's Plan", "Song Title"],
    )
    features: list[str] = Field(
        default_factory=list,
        description="List of featured artists",
        examples=[["Kendrick Lamar"], ["Artist A", "Artist B"], []],
    )
    version: str = Field(
        default="Original",
        description="Version identifier (e.g., Live, Remix, Acoustic)",
        examples=["Original", "Live", "Acoustic", "Remix"],
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for the parsing result",
        examples=[0.95, 0.7, 0.4],
    )
    decision: Decision = Field(
        description="Policy decision for this result",
        examples=["accept", "graylist", "reject"],
    )
    reason: str = Field(
        description="Human - readable explanation for the decision",
        examples=[
            "YouTube OAC; OAC boost (+0.15)",
            "GARBAGE DETECTED",
            "basic parsing; no artist extracted",
        ],
    )
    profile_used: PolicyProfile = Field(
        description="Policy profile used for parsing",
        examples=["balanced", "strict", "aggressive"],
    )
    parsing_method: ParsingMethod = Field(
        description="Method used to extract the artist",
        examples=["channel_oac", "title_dash", "basic_parsing"],
    )


class PolicyConfig(BaseModel):
    """Configuration for a policy profile."""

    model_config = ConfigDict(validate_assignment=True)

    accept_min: float = Field(
        ge=0.0,
        le=1.0,
        description="Minimum confidence to accept result",
    )
    gray_min: float = Field(
        ge=0.0,
        le=1.0,
        description="Minimum confidence for graylist (below this = reject)",
    )
    reject_below: float = Field(
        ge=0.0,
        le=1.0,
        description="Explicit reject threshold (same as gray_min)",
    )
    oac_boost: float = Field(
        default=0.15,
        ge=0.0,
        le=0.5,
        description="Confidence boost for YouTube Official Artist Channels",
    )
    use_channel_for_artist: bool = Field(
        default=False,
        description="Whether to use channel name as artist (only for OAC)",
    )
    allow_stage_b: bool = Field(
        default=True,
        description="Whether to enable Stage B recovery parsing",
    )
    shadow_only: bool = Field(
        default=False,
        description="Whether this profile only runs in shadow mode",
    )


class AllowlistEntry(BaseModel):
    """Entry in the allowlist for trusted mappings."""

    model_config = ConfigDict(validate_assignment=True)

    pattern_or_mapping: dict[str, str] = Field(
        description="Channel to artist mapping or pattern",
        examples=[{"channel_name": "Taylor Swift - Topic", "artist_name": "Taylor Swift"}],
    )
    type: str = Field(
        description="Type of allowlist entry",
        examples=["youtube_oac", "trusted_channel"],
    )
    confidence_boost: float = Field(
        default=0.15,
        ge=0.0,
        le=0.5,
        description="Confidence boost to apply",
    )
    owner: str = Field(
        description="Who created this entry",
        examples=["system", "data_team", "migration_cleanup"],
    )
    created_at: str = Field(
        description="When this entry was created (ISO format)",
        examples=["2025 - 09 - 23"],
    )
    expires_at: str = Field(
        description="When this entry expires (ISO format)",
        examples=["2025 - 12 - 22"],
    )
    notes: str = Field(
        default="",
        description="Additional notes about this entry",
        examples=["YouTube Official Artist Channel", "Verified mapping"],
    )


class DenylistEntry(BaseModel):
    """Entry in the denylist for garbage patterns."""

    model_config = ConfigDict(validate_assignment=True)

    pattern_or_mapping: dict[str, str] = Field(
        description="Pattern to match or exact string to block",
        examples=[
            {
                "regex": "[0 - 9]+(rd|th|st|nd)\\s + I\\s + Cam",
                "description": "Patterns like '3rd I Cam'",
            },
            {"exact_match": "word 4 word🎼"},
        ],
    )
    type: str = Field(
        description="Type of denylist entry",
        examples=["garbage_pattern", "known_garbage", "spam_channel"],
    )
    action: str = Field(
        default="reject",
        description="Action to take when pattern matches",
        examples=["reject", "flag", "review"],
    )
    owner: str = Field(
        description="Who created this entry",
        examples=["data_quality_team", "migration_cleanup", "system"],
    )
    created_at: str = Field(
        description="When this entry was created (ISO format)",
        examples=["2025 - 09 - 23"],
    )
    expires_at: str = Field(
        description="When this entry expires (ISO format)",
        examples=["2025 - 12 - 22"],
    )
    notes: str = Field(
        default="",
        description="Additional notes about this entry",
        examples=["Known garbage artist pattern from YouTube channel names"],
    )


class ParserPolicy(BaseModel):
    """Complete parser policy configuration."""

    model_config = ConfigDict(validate_assignment=True)

    policy_name: str = Field(
        description="Name of this policy",
        examples=["Perday Catalog — Parser & ETL Policy"],
    )
    policy_version: str = Field(
        description="Version of this policy",
        examples=["2025 - 09 - 23", "1.0.0"],
    )
    one_line_policy: str = Field(
        description="One - line summary of the policy approach",
    )
    profiles: dict[PolicyProfile, PolicyConfig] = Field(
        description="Available policy profiles",
    )

    def get_profile(self, profile_name: PolicyProfile) -> PolicyConfig:
        """Get a specific policy profile configuration."""
        if profile_name not in self.profiles:
            msg = f"Unknown profile: {profile_name}. Available: {list(self.profiles.keys())}"
            raise ValueError(msg)
        return self.profiles[profile_name]


class BenchmarkResult(BaseModel):
    """Result from benchmark testing."""

    model_config = ConfigDict(validate_assignment=True)

    test_name: str = Field(description="Name of the benchmark test")
    rows_processed: int = Field(ge=0, description="Number of rows processed")
    time_seconds: float = Field(ge=0.0, description="Execution time in seconds")
    memory_mb: float = Field(ge=0.0, description="Memory usage in MB")
    rows_per_second: int = Field(ge=0, description="Processing rate")
    accuracy_score: float = Field(ge=0.0, le=1.0, description="Accuracy score")
    metadata: dict[str, str | int | float] = Field(
        default_factory=dict,
        description="Additional benchmark metadata",
    )


class ValidationResult(BaseModel):
    """Result from policy validation."""

    model_config = ConfigDict(validate_assignment=True)

    is_valid: bool = Field(description="Whether validation passed")
    errors: list[str] = Field(default_factory=list, description="Validation errors found")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    summary: dict[str, str | int | float] = Field(
        default_factory=dict,
        description="Validation summary statistics",
    )

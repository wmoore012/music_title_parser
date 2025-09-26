# SPDX-License-Identifier: MIT
# Copyright (c) 2024 MusicScope

"""
Specific exception types for music title parsing.

This module defines typed exceptions for better error handling and debugging.
"""

from __future__ import annotations


class MusicTitleParserError(Exception):
    """Base exception for all music title parser errors."""


class PolicyError(MusicTitleParserError):
    """Raised when policy configuration or execution fails."""


class InvalidPatternError(PolicyError):
    """Raised when a regex pattern in allowlist/denylist is invalid."""

    def __init__(self, pattern: str, reason: str) -> None:
        self.pattern = pattern
        self.reason = reason
        super().__init__(f"Invalid pattern '{pattern}': {reason}")


class ConfigLoadError(PolicyError):
    """Raised when policy configuration files cannot be loaded."""

    def __init__(self, file_path: str, reason: str) -> None:
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"Failed to load config '{file_path}': {reason}")


class ValidationError(MusicTitleParserError):
    """Raised when input validation fails."""

    def __init__(self, field: str, value: str, reason: str) -> None:
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for {field}='{value}': {reason}")


class ParsingError(MusicTitleParserError):
    """Raised when title parsing encounters an unrecoverable error."""

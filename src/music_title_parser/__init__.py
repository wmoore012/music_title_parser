# SPDX-License-Identifier: MIT
# Copyright (c) 2024 MusicScope

"""
Music Title Parser

Production-grade music title parsing with policy-based validation and garbage prevention.

This package provides:
- Three-tier parsing system (strict/balanced/aggressive)
- YouTube Official Artist Channel (OAC) support
- Garbage artist detection and prevention
- Policy-based confidence scoring
- Type-safe parsing results

Example:
    >>> from music_title_parser import parse_with_policy
    >>> result = parse_with_policy("Taylor Swift - Anti-Hero", "TaylorSwiftVEVO")
    >>> print(f"Artist: {result.artist}, Decision: {result.decision}")
    Artist: TaylorSwift, Decision: accept
"""

from __future__ import annotations

from .models import ParsedTitle, PolicyProfile
from .parser import parse_title, split_artist_title
from .policy_engine import parse_with_policy

__version__ = "0.1.0"
__all__ = [
    "parse_title",
    "parse_with_policy",
    "split_artist_title",
    "ParsedTitle",
    "PolicyProfile",
]

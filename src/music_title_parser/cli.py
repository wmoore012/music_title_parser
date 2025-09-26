# SPDX-License-Identifier: MIT
# Copyright (c) 2024 MusicScope

"""
Command-line interface for music title parser.

This module provides CLI tools for parsing titles and validating policies.
"""

from __future__ import annotations

import sys
from typing import NoReturn

from .models import ParsedTitle
from .policy_engine import PolicyEngine, parse_with_policy


def main() -> NoReturn:
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        _show_help()
        sys.exit(1)

    command = sys.argv[1]

    if command == "parse":
        _parse_command()
    elif command == "validate":
        _validate_command()
    elif command == "benchmark":
        _benchmark_command()
    elif command == "--help" or command == "-h":
        _show_help()
        sys.exit(0)
    else:
        print(f"Unknown command: {command}")
        _show_help()
        sys.exit(1)


def validate_policy() -> NoReturn:
    """CLI entry point for policy validation."""
    try:
        result = _validate_policy_files()
        if result:
            print("✅ Policy validation passed")
            sys.exit(0)
        else:
            print("❌ Policy validation failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Validation error: {e}")
        sys.exit(1)


def _parse_command() -> None:
    """Handle parse command."""
    if len(sys.argv) < 3:
        print("Usage: music-title-parser parse <title> [channel] [profile]")
        sys.exit(1)

    title = sys.argv[2]
    channel = sys.argv[3] if len(sys.argv) > 3 else ""
    profile = sys.argv[4] if len(sys.argv) > 4 else "balanced"

    if profile not in ["strict", "balanced", "aggressive"]:
        print(f"Invalid profile: {profile}. Use: strict, balanced, aggressive")
        sys.exit(1)

    try:
        result = parse_with_policy(title, channel, profile)  # type: ignore[arg-type]
        _print_result(result)
    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        sys.exit(1)


def _validate_command() -> None:
    """Handle validate command."""
    try:
        if _validate_policy_files():
            print("✅ All policy files are valid")
        else:
            print("❌ Policy validation failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Validation error: {e}")
        sys.exit(1)


def _benchmark_command() -> None:
    """Handle benchmark command."""
    try:
        from .benchmarks import run_basic_benchmark

        print("🚀 Running benchmark...")
        result = run_basic_benchmark()
        print(f"✅ Processed {result.rows_processed} titles in {result.time_seconds:.3f}s")
        print(f"📊 Rate: {result.rows_per_second:,} titles/second")
        print(f"💾 Memory: {result.memory_mb:.1f} MB")
    except ImportError:
        print("❌ Benchmark module not available")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        sys.exit(1)


def _validate_policy_files() -> bool:
    """Validate policy configuration files."""
    try:
        engine = PolicyEngine()

        # Test that policy loads
        policy = engine.policy
        if not policy:
            return False

        # Test that profiles exist
        required_profiles = ["strict", "balanced", "aggressive"]
        for profile in required_profiles:
            if profile not in policy.get("profiles", {}):
                print(f"❌ Missing profile: {profile}")
                return False

        # Test allowlist/denylist load
        allowlist = engine.allowlist
        denylist = engine.denylist

        if not isinstance(allowlist, dict) or not isinstance(denylist, dict):
            return False

        print(f"✅ Policy loaded: {len(policy.get('profiles', {}))} profiles")
        print(f"✅ Allowlist: {len(allowlist.get('entries', []))} entries")
        print(f"✅ Denylist: {len(denylist.get('entries', []))} entries")

        return True

    except Exception as e:
        print(f"❌ Policy validation failed: {e}")
        return False


def _print_result(result: ParsedTitle) -> None:
    """Print parsing result in a nice format."""
    print(f"🎵 Title: '{result.title}'")
    print(f"🎤 Artist: '{result.artist}'")
    if result.features:
        print(f"🤝 Features: {', '.join(result.features)}")
    if result.version != "Original":
        print(f"🎛️  Version: {result.version}")
    print(f"📊 Confidence: {result.confidence:.2f}")
    print(f"⚖️  Decision: {result.decision}")
    print(f"🔍 Profile: {result.profile_used}")
    print(f"💭 Reason: {result.reason}")


def _show_help() -> None:
    """Show CLI help."""
    print(
        """
Music Title Parser CLI

Usage:
  music-title-parser parse <title> [channel] [profile]
  music-title-parser validate
  music-title-parser benchmark
  music-title-parser --help

Commands:
  parse      Parse a music title with optional channel and profile
  validate   Validate policy configuration files
  benchmark  Run performance benchmark
  --help     Show this help message

Examples:
  music-title-parser parse "Taylor Swift - Anti-Hero"
  music-title-parser parse "Anti-Hero" "Taylor Swift - Topic" balanced
  music-title-parser validate
  music-title-parser benchmark

Profiles:
  strict     Highest precision, conservative parsing
  balanced   Production default with good precision/recall balance
  aggressive Shadow mode for candidate generation

Install with pipx:
  pipx install music-title-parser
"""
    )


if __name__ == "__main__":
    main()

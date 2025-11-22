#!/usr / bin / env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Perday CatalogLAB™

"""
Validate Parser Policy Configuration

This script validates the parser policy files for correctness and completeness.
"""

import json
import os

import yaml


def validate_policy_files():
    """Validate both YAML and JSON policy files."""

    print("🔍 Validating Parser Policy Configuration")
    print("=" * 50)

    issues = []

    # Check if files exist
    yaml_path = "perday_parser_policy.yaml"
    json_path = "perday_parser_policy.json"
    allowlist_path = "allowlist.json"
    denylist_path = "denylist.json"

    for path in [yaml_path, json_path, allowlist_path, denylist_path]:
        if not os.path.exists(path):
            issues.append(f"❌ Missing file: {path}")

    if issues:
        print("\n".join(issues))
        return False

    # Load and validate YAML
    try:
        with open(yaml_path) as f:
            yaml_config = yaml.safe_load(f)
        print("✅ YAML file loads successfully")
    except Exception as e:
        issues.append(f"❌ YAML parsing error: {e}")
        return False

    # Load and validate JSON
    try:
        with open(json_path) as f:
            json_config = json.load(f)
        print("✅ JSON file loads successfully")
    except Exception as e:
        issues.append(f"❌ JSON parsing error: {e}")
        return False

    # Validate structure
    required_sections = [
        "policy_name",
        "policy_version",
        "one_line_policy",
        "profiles",
        "parsing",
        "storage",
        "validation",
        "metrics_targets",
    ]

    for section in required_sections:
        if section not in yaml_config:
            issues.append(f"❌ Missing section in YAML: {section}")
        if section not in json_config:
            issues.append(f"❌ Missing section in JSON: {section}")

    # Validate profiles
    required_profiles = ["strict", "balanced", "aggressive"]
    for profile in required_profiles:
        if profile not in yaml_config.get("profiles", {}):
            issues.append(f"❌ Missing profile: {profile}")

    # Validate thresholds make sense
    for profile_name, profile in yaml_config.get("profiles", {}).items():
        accept_min = profile.get("accept_min", 0)
        gray_min = profile.get("gray_min", 0)
        reject_below = profile.get("reject_below", 0)

        if not (0 <= reject_below <= gray_min <= accept_min <= 1.0):
            issues.append(
                f"❌ Invalid thresholds in {profile_name}: reject({reject_below}) <= gray({gray_min}) <= accept({accept_min})"
            )

    # Validate storage configuration
    storage = yaml_config.get("storage", {})
    required_layers = ["bronze", "silver", "gold"]
    if storage.get("layers") != required_layers:
        issues.append(f"❌ Storage layers should be {required_layers}")

    # Validate metrics targets
    metrics = yaml_config.get("metrics_targets", {})
    if metrics.get("p_at_1_primary_artist_min", 0) < 0.9:
        issues.append("⚠️  P@1 target < 90% - consider raising for production")
    if metrics.get("garbage_rate_max", 1) > 0.01:
        issues.append("⚠️  Garbage rate target > 1% - consider lowering for production")

    # Validate allowlist / denylist files
    try:
        with open(allowlist_path) as f:
            allowlist = json.load(f)
        print("✅ Allowlist file loads successfully")

        # Check allowlist structure
        if "entries" not in allowlist:
            issues.append("❌ Allowlist missing 'entries' field")
        else:
            for i, entry in enumerate(allowlist["entries"]):
                required_fields = [
                    "pattern_or_mapping",
                    "owner",
                    "created_at",
                    "expires_at",
                ]
                for field in required_fields:
                    if field not in entry:
                        issues.append(f"❌ Allowlist entry {i} missing field: {field}")

    except Exception as e:
        issues.append(f"❌ Allowlist error: {e}")

    try:
        with open(denylist_path) as f:
            denylist = json.load(f)
        print("✅ Denylist file loads successfully")

        # Check denylist structure
        if "entries" not in denylist:
            issues.append("❌ Denylist missing 'entries' field")
        else:
            for i, entry in enumerate(denylist["entries"]):
                required_fields = [
                    "pattern_or_mapping",
                    "owner",
                    "created_at",
                    "expires_at",
                ]
                for field in required_fields:
                    if field not in entry:
                        issues.append(f"❌ Denylist entry {i} missing field: {field}")

    except Exception as e:
        issues.append(f"❌ Denylist error: {e}")

    # Check for consistency between YAML and JSON
    key_fields = ["policy_name", "policy_version", "one_line_policy"]
    for field in key_fields:
        if yaml_config.get(field) != json_config.get(field):
            issues.append(f"❌ Mismatch between YAML and JSON for field: {field}")

    # Print results
    if issues:
        print(f"\n❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("\n✅ All validation checks passed!")
        print("\n📋 Policy Summary:")
        print(f"  Policy: {yaml_config['policy_name']}")
        print(f"  Version: {yaml_config['policy_version']}")
        print(f"  Profiles: {', '.join(yaml_config['profiles'].keys())}")
        print(f"  Storage: {' → '.join(yaml_config['storage']['layers'])}")
        print(
            f"  P@1 Target: {yaml_config['metrics_targets']['p_at_1_primary_artist_min']*100}%"
        )
        print(
            f"  Garbage Target: <{yaml_config['metrics_targets']['garbage_rate_max']*100}%"
        )

        return True


def show_policy_usage():
    """Show how to use the policy files."""

    print("\n📖 Usage Examples:")
    print("=" * 20)

    print("\n1. Load policy in Python:")
    print(
        """
import yaml
with open('perday_parser_policy.yaml', 'r') as f:
    policy = yaml.safe_load(f)

# Use balanced profile for production
profile = policy['profiles']['balanced']
accept_threshold = profile['accept_min']  # 0.7
"""
    )

    print("\n2. Check if artist should be rejected:")
    print(
        """
import json
with open('denylist.json', 'r') as f:
    denylist = json.load(f)

def is_garbage_artist(artist_name):
    for entry in denylist['entries']:
        pattern = entry['pattern_or_mapping']
        if 'regex' in pattern:
            if re.search(pattern['regex'], artist_name):
                return True
        elif 'exact_match' in pattern:
            if artist_name == pattern['exact_match']:
                return True
    return False
"""
    )

    print("\n3. Apply confidence boost for OAC:")
    print(
        """
def apply_oac_boost(confidence, channel_title, policy):
    # Check if channel is in allowlist as OAC
    if is_youtube_oac(channel_title):
        boost = policy['profiles']['balanced']['oac_boost']
        return min(1.0, confidence + boost)
    return confidence
"""
    )


if __name__ == "__main__":
    success = validate_policy_files()
    if success:
        show_policy_usage()
    else:
        print("\n🚨 Please fix the issues above before using the policy files.")
        exit(1)

<!-- SPDX-License-Identifier: MIT
Copyright (c) 2024 MusicScope -->

# Parser Policy Configuration

This directory contains production-grade policy files for implementing a robust YouTube title parsing system with garbage artist prevention.

## 📋 Files Overview

- **`perday_parser_policy.yaml`** - Main policy configuration (human-readable)
- **`perday_parser_policy.json`** - Same policy in JSON format (machine-readable)
- **`allowlist.json`** - Trusted channel-to-artist mappings (YouTube Official Artist Channels)
- **`denylist.json`** - Garbage patterns to reject (prevents fake artists)
- **`validate_parser_policy.py`** - Validation script to check policy correctness

## 🎯 Policy Philosophy

**"Precision first. Conservative parser writes canonical tables; aggressive parser runs in shadow."**

### Three-Tier Approach:
1. **Conservative Parser** → Writes to production (high precision, no garbage)
2. **Aggressive Parser** → Runs in shadow mode (generates candidates for review)
3. **Medallion Architecture** → Bronze (raw) → Silver (parsed) → Gold (published)

## 🔧 Quick Start

### 1. Validate Configuration
```bash
python validate_parser_policy.py
```

### 2. Load Policy in Your Code
```python
import yaml

# Load main policy
with open('perday_parser_policy.yaml', 'r') as f:
    policy = yaml.safe_load(f)

# Use balanced profile for production
profile = policy['profiles']['balanced']
accept_threshold = profile['accept_min']  # 0.7
gray_threshold = profile['gray_min']      # 0.4
```

### 3. Check for Garbage Artists
```python
import json
import re

with open('denylist.json', 'r') as f:
    denylist = json.load(f)

def is_garbage_artist(artist_name):
    for entry in denylist['entries']:
        pattern = entry['pattern_or_mapping']
        if 'regex' in pattern:
            if re.search(pattern['regex'], artist_name, re.IGNORECASE):
                return True
        elif 'exact_match' in pattern:
            if artist_name == pattern['exact_match']:
                return True
    return False

# Test
print(is_garbage_artist("3rd I Cam"))      # True
print(is_garbage_artist("word 4 word🎼"))  # True
print(is_garbage_artist("Taylor Swift"))   # False
```

## 📊 Parsing Profiles

### Strict Profile
- **Use case**: Maximum precision, minimal false positives
- **Accept threshold**: 75%
- **Stage B rules**: Disabled
- **Channel as artist**: Never (except OAC)

### Balanced Profile (Production Default)
- **Use case**: Production parsing with safety nets
- **Accept threshold**: 70%
- **Stage B rules**: Enabled with safeguards
- **Channel as artist**: Only YouTube Official Artist Channels

### Aggressive Profile (Shadow Only)
- **Use case**: Candidate generation for human review
- **Accept threshold**: 60%
- **Stage B rules**: Full recovery mode
- **Output**: Never writes directly to Gold tables

## 🏗️ Storage Architecture

### Bronze Layer (Raw Data)
```sql
CREATE TABLE bronze_youtube_playlist_items (
    video_id VARCHAR(20) PRIMARY KEY,
    playlist_item_id VARCHAR(50),
    channel_id VARCHAR(50),
    channel_title TEXT,
    title_raw TEXT NOT NULL,
    published_at TIMESTAMP,
    first_seen_at TIMESTAMP,
    last_seen_at TIMESTAMP
);
```

### Silver Layer (Parsed Results)
```sql
CREATE TABLE silver_parsed_titles (
    video_id VARCHAR(20) PRIMARY KEY,
    parser_version VARCHAR(20),
    artist_primary TEXT,
    features_json JSON,
    title_clean TEXT,
    version_tag TEXT,
    confidence DECIMAL(3,2),
    decision ENUM('accept', 'graylist', 'reject'),
    reason TEXT
);
```

### Gold Layer (Published Data)
- Only `accept` decisions from Silver
- Enforces style rules (features in credits, versions in parentheses)
- Feeds production artist/track tables

## 🎯 Quality Targets

- **P@1 (Primary Artist)**: ≥ 98%
- **Recall (Any Artist)**: ≥ 85%
- **Garbage Rate**: ≤ 0.1%

## 🔄 Re-parsing Strategy

The system supports safe re-parsing when rules improve:

1. **Parser version bumps** trigger automatic re-parse
2. **Bronze data preserved** for historical re-processing
3. **Idempotent upserts** ensure consistent results
4. **Rollback capability** via parser version management

## 🛡️ Garbage Prevention

### Current Denylist Patterns:
- `[0-9]+(rd|th|st|nd)\s+I\s+Cam` → Blocks "3rd I Cam"
- `word\s+[0-9]+\s+word` → Blocks "word 4 word"
- `[🎼🎮🎶]` → Blocks emoji-containing names
- `''` → Blocks double-quote artifacts

### YouTube Official Artist Channel (OAC) Boost:
- Only OAC channels get confidence boost for channel→artist mapping
- Prevents random channels from being treated as artists
- Maintains high precision while allowing legitimate artist channels

## 📈 Monitoring & Metrics

### Daily Metrics:
- Parse success rate by profile
- Garbage detection rate
- Graylist queue size
- P@1/Recall against golden test set

### Alerting:
- Garbage rate > 0.1%
- P@1 drops below 98%
- Graylist queue exceeds threshold

## 🔧 Maintenance

### Allowlist/Denylist Updates:
- All entries have TTL (90 days default)
- Require owner and expiration date
- Version controlled for audit trail

### Policy Updates:
- Bump parser version on rule changes
- Trigger re-parse of Bronze data
- Validate with test suite before deployment

## 🚀 Implementation Notes

This policy was designed based on production experience with YouTube title parsing at scale. It solves real problems:

- **Eliminates garbage artists** like "3rd I Cam" and "word 4 word🎼"
- **Maintains high precision** while improving recall
- **Enables safe experimentation** via shadow parsing
- **Provides rollback capability** for production safety

The medallion architecture ensures you never lose raw data and can always improve parsing rules as your understanding evolves.

## 📞 Support

For questions about implementing this policy:
1. Run `validate_parser_policy.py` to check configuration
2. Review the examples in this README
3. Check the policy files for detailed configuration options

The policy is designed to be self-documenting and includes extensive validation to catch configuration errors early.

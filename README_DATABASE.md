# Music Title Parser Module - Database Setup

This module uses both shared infrastructure tables and module-specific tables.

## Quick Setup

```bash
# Option 1: Use the module setup script
cd oss/music-title-parser/sql
python setup_module.py "mysql://user:pass@host:port/icatalog_public"

# Option 2: Run SQL directly
mysql -u user -p icatalog_public < sql/create_tables.sql
```

## Tables Created

### Module-Specific Tables

- **`parser_version_mappings`** - Version normalization rules (replaces complex logic)
- **`parser_policy_configs`** - Policy profiles (strict/balanced/aggressive)
- **`parser_allowlist`** - Trusted channel→artist mappings
- **`parser_denylist`** - Garbage patterns and blocked content

### Shared Infrastructure Tables

- **`oss_module_benchmarks`** - Performance benchmarking (shared)

## Usage Examples

```python
from music_title_parser import parse_title

# Parser automatically loads mappings from database
result = parse_title("Song (Slowed) (Visualizer)")
# Uses parser_version_mappings table: slowed+visualizer → slowed

# Policy engine uses parser_policy_configs table
result = parse_title("Song", policy_profile="strict")
```

## Adding Custom Mappings

```sql
-- Add new version mapping
INSERT INTO parser_version_mappings (
    mapping_id, input_pattern, output_version, mapping_type
) VALUES (
    'custom_001', 'nightcore+visualizer', 'nightcore', 'combination'
);

-- Add trusted channel mapping
INSERT INTO parser_allowlist (
    entry_id, channel_name, artist_name, confidence_boost
) VALUES (
    'allow_001', 'Taylor Swift - Topic', 'Taylor Swift', 0.20
);
```

## Simple Table-Based Approach

Instead of complex rule engines, this uses simple key-value mappings:
- ✅ Easy to understand and maintain
- ✅ No complex priority logic to debug
- ✅ Database-driven configuration
- ✅ Perfect for OSS distribution

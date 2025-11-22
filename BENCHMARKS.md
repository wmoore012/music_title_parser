# Music Title Parser – Benchmarks

These benchmarks run entirely on sanitized sample data so you can reproduce the
numbers locally without any production secrets.

## Dataset

- Location: `src/music_title_parser/config/benchmark_sample.jsonl`
- Size: 100 anonymized YouTube-style titles + channels (no user IDs)
- Source: curated from common patterns (dash splits, features, versions, OAC channels)
- Regenerate: edit the JSONL file with additional sanitized rows when needed.

## How to Run

```bash
cd oss/music-title-parser
python -m music_title_parser.benchmarks    # uses the balanced profile by default
```

The same command is also wired to `music-title-parser benchmark` via the CLI.

## Sample Output (Apple M3 Pro, Python 3.12)

| Profile  | Titles/sec | Accepted | Graylist | Rejected |
|----------|------------|----------|----------|----------|
| balanced | **55,012** | 460      | 540      | 0        |

The CLI also writes the full JSON payload to
`src/music_title_parser/benchmark_results.json`, which you can attach to reports
or CI artifacts.

## Sanitization Notes

- The bundled sample never includes personal data, proprietary channel IDs, or
  raw YouTube payloads.
- If you swap in your own dataset for private measurements, keep the sanitized
  JSONL under version control (or a private artifact) and record the version ID
  in your release notes.
- Never paste production titles or channel names directly into this repository.

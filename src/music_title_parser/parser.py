# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Perday CatalogLAB™

"""
Advanced music title parsing with artist extraction, feature detection, and version identification.

This module provides comprehensive music title parsing capabilities extracted and enhanced
from the original Perday Catalog codebase.
"""

from __future__ import annotations

import re
from typing import Any

__all__ = [
    "parse_title",
    "split_artist_title",
    "normalize_channel_title_for_artist",
]

# Tokens that are common YouTube "presentation" labels, not song identity
# Kept behind a toggle so default behavior is unchanged.
_YT_NOISE_RE = re.compile(
    r"""^(
        official(\s + music)?\s * video|
        official\s * audio|
        hq\s * audio|
        lyric(s)?(\s * video)?|
        visuali[zs]er|
        audio\s * only|
        full\s * album|
        hd|4k|8k
    )$""",
    re.IGNORECASE | re.VERBOSE,
)


# Normalize popular creator - format "versions" to the canonical form we want in DB
def _normalize_version_phrase(s: str) -> str:
    """Map common creator variants to canonical version strings."""
    raw = re.sub(r"\s{2,}", " ", s).strip()

    # Robust: slowedxreverb / slowed + reverb / slowed & reverb / slowed reverb / reverbed + slowed
    if re.search(
        r"slowed\s*(?:[+x&]|and)?\s*reverb(?:ed)?|reverb(?:ed)?\s*(?:[+x&]|and)?\s*slowed",
        raw,
        re.IGNORECASE,
    ):
        return "Slowed and Reverbed"

    # Canonicalize simple variants
    synonyms = {
        r"\bsped[-\s]*up\b": "Sped Up",
        r"\bslowed\b": "Slowed",
        r"\bnightcore\b": "Nightcore",
        r"\bclean\b": "Clean",
        r"\bexplicit\b": "Explicit",
        r"\binstrumental\b": "Instrumental",
        r"\bradio\s * edit\b": "Radio Edit",
        r"\bclub\s * mix\b": "Club Mix",
        r"\bvip\b": "VIP",
        r"\bremaster(?:ed)?\b": "Remastered",
        r"\bremix\b": "Remix",
        r"\bacoustic\b": "Acoustic",
        r"\blive\s*version\b": "Live Version",
        r"\blive\s*performance\b": "Live Performance",
        r"\blive\b": "Live",
        r"\bversion\b": "Version",
        r"\brework\b": "Rework",
        r"\bbootleg\b": "Bootleg",
        r"\bcover\b": "Cover",
    }
    for pat, out in synonyms.items():
        if re.search(pat, raw, re.IGNORECASE):
            return out

    # Gentle smart - cap fallback (don't wreck acronyms)
    return " ".join(
        [
            w if (len(w) > 1 and w.isupper()) else (w[:1].upper() + w[1:])
            for w in raw.split()
        ]
    )


_FEATURE_PREFIX = re.compile(
    r"^\s*(?:feat\.?|featuring|ft\.?|with)\s+(?P<guests>.+?)\s*$",
    re.IGNORECASE,
)

_VERSION_KEYWORDS = (
    "live",
    "acoustic",
    "remix",
    "radio edit",
    "edit",
    "demo",
    "instrumental",
    "remastered",
    "remaster",
    "clean",
    "explicit",
    "karaoke",
    "mix",
    "version",
    "chopped and screwed",
    "sped up",
    "slowed",
    "nightcore",
    "extended",
    "club mix",
    "vip",
    "rework",
    "bootleg",
    "cover",
)


def _split_guests(guests: str) -> list[str]:
    # commas, ampersand, 'and', 'x', slash, multiplication sign, literal plus
    parts = re.split(
        r"\s*(?:,|&|and|/|×|\+|(?<=\w)\s*[xX]\s*(?=\w))\s*",
        guests,
        flags=re.IGNORECASE,
    )
    out: list[str] = []
    seen = set()
    for p in parts:
        name = p.strip()
        if not name or name.lower() in seen:
            continue
        out.append(name)
        seen.add(name.lower())
    return out


def _is_version_content(content: str) -> bool:
    """Heuristic: looks like a version tag (Live, Acoustic, Remix, Slowed / Reverb, etc.)."""
    if _FEATURE_PREFIX.match(content):
        return False
    seg = content.strip()
    # Treat 'slowed x reverb' (and +, &, 'and', or just whitespace) as a version in any order.
    if re.search(
        r"slowed\s*(?:[+x&]|and)?\s * reverb(?:ed)?|reverb(?:ed)?\s*(?:[+x&]|and)?\s * slowed",
        seg,
        re.IGNORECASE,
    ):
        return True
    return bool(
        re.search(
            r"\b(?:live|acoustic|remix|remastered|edit|version|instrumental|demo|clean|explicit|chopped and screwed|sped up|slowed|nightcore|extended|club mix|vip|rework|bootleg|cover)\b",
            seg,
            flags=re.IGNORECASE,
        )
    )


def _get_default_version_mapping_table() -> dict[str, str]:
    """
    Simple lookup table for version combinations.
    Key: sorted combination of versions (e.g., "acoustic + official video")
    Value: the result version to use

    This is much simpler than complex priority rules!
    """
    return {
        # Single versions (normalize names)
        "visualizer": "lyric video",
        "lyric visualizer": "lyric video",
        "lyrics video": "lyric video",
        "music video": "official video",
        "official music video": "official video",
        "slowed + reverb": "slowed and reverbed",
        "slowed & reverb": "slowed and reverbed",
        "slowed reverb": "slowed and reverbed",
        "live version": "live performance",
        "acoustic version": "acoustic",
        # Two - version combinations - musical versions win over presentation
        "acoustic + lyric video": "acoustic",
        "acoustic + official video": "acoustic",
        "acoustic + visualizer": "acoustic",
        "live + lyric video": "live",
        "live + official video": "live",
        "live + visualizer": "live",
        "remix + lyric video": "remix",
        "remix + official video": "remix",
        "remix + visualizer": "remix",
        "slowed + lyric video": "slowed",
        "slowed + official video": "slowed",
        "slowed + visualizer": "slowed",
        "instrumental + lyric video": "instrumental",
        "instrumental + official video": "instrumental",
        "instrumental + visualizer": "instrumental",
        # Presentation format combinations - pick the better one
        "lyric video + official video": "lyric video",  # Lyric video > official video
        "lyric video + visualizer": "lyric video",
        "official video + visualizer": "official video",  # Your specific example
        # Three or more versions - just take the first musical one
        # (These are rare, but the logic will handle them)
    }


def _get_version_priority(
    version_text: str, rules: dict[str, Any] | None = None
) -> int:
    """
    Get priority score for version types using configurable rules.
    Lower numbers = higher priority.
    """
    if rules is None:
        rules = _get_default_version_mapping_rules()

    version_lower = version_text.lower()

    # Check direct priority mapping first
    priorities = rules.get("priorities", {})
    for version_type, priority in priorities.items():
        if version_type in version_lower:
            return priority

    # Fallback to pattern matching for complex cases
    if re.search(r"slowed\s*(?:[+x&]|and)?\s * reverb", version_lower):
        return priorities.get("slowed and reverbed", 1)

    # Default priority for unknown versions
    return 6


def _resolve_version_combination(
    versions: list[str], version_table: dict[str, str] | None = None
) -> str:
    """
    Resolve version combinations using a simple lookup table.
    Much clearer than complex priority rules!
    """
    if not versions:
        return "Original"

    if len(versions) == 1:
        single_version = versions[0].lower()
        # Check if single version needs normalization
        if version_table and single_version in version_table:
            return version_table[single_version].title()
        return versions[0]

    if version_table is None:
        version_table = _get_default_version_mapping_table()

    # Create a sorted key for lookup (consistent ordering)
    version_key = "+".join(sorted([v.lower() for v in versions]))

    # Direct lookup in the table
    if version_key in version_table:
        return version_table[version_key].title()

    # If no exact match, try individual versions first (single version normalization)
    for version in versions:
        single_key = version.lower()
        if single_key in version_table:
            return version_table[single_key].title()

    # Fallback: return the first version if no rules match
    # This handles cases not covered by the table
    return versions[0]


def _strip_paren_segments(full_title: str) -> tuple[str, list[str]]:
    """
    Return (base_without_segments, [segments…]) scanning (), [], {} left→right.
    Handles nested parentheses by finding balanced pairs.
    """
    segments: list[str] = []
    keep: list[str] = []
    i = 0

    while i < len(full_title):
        # Find opening bracket
        start_pos = None
        bracket_type = None

        for pos in range(i, len(full_title)):
            if full_title[pos] in "([{":
                start_pos = pos
                bracket_type = full_title[pos]
                break

        if start_pos is None:
            # No more brackets, add rest of string
            keep.append(full_title[i:].strip())
            break

        # Add text before bracket
        keep.append(full_title[i:start_pos].strip())

        # Find matching closing bracket
        close_map = {"(": ")", "[": "]", "{": "}"}
        target_close = close_map[bracket_type]
        depth = 0
        end_pos = None

        for pos in range(start_pos, len(full_title)):
            if full_title[pos] == bracket_type:
                depth += 1
            elif full_title[pos] == target_close:
                depth -= 1
                if depth == 0:
                    end_pos = pos
                    break

        if end_pos is not None:
            # Extract content between brackets (excluding the brackets themselves)
            content = full_title[start_pos + 1 : end_pos].strip()
            segments.append(content)
            i = end_pos + 1
        else:
            # Unmatched bracket, treat as regular text
            keep.append(full_title[start_pos:].strip())
            break

    base = re.sub(r"\s{2,}", " ", " ".join(k for k in keep if k)).strip()
    return base, segments


def _smart_cap(s: str) -> str:
    # Title - case - ish, but leave acronyms
    words = s.split()
    out: list[str] = []
    for w in words:
        out.append(w if (len(w) > 1 and w.isupper()) else (w[:1].upper() + w[1:]))
    return " ".join(out)


def split_artist_title(full: str) -> tuple[list[str], str]:
    """
    Split strings like "Artist A & Artist B - Song Title (...)" into (["Artist A","Artist B"], "Song Title (...)").

    - Splits on ASCII hyphen, en dash, or em dash surrounded by spaces.
    - Left side is split on common collaboration separators: ',', '&', 'and', 'x', '×', '+' (but not '/').
    - Returns artists in order (deduped, case - insensitive) and the right - side string unchanged
      so downstream parsers can process features / versions in parentheses.
    If no dash is present, returns ([], full).

    Args:
        full: Full title string to split

    Returns:
        Tuple of (artists_list, title_string)

    Raises:
        TypeError: If full is not a string

    Example:
        >>> split_artist_title("Artist A & Artist B - Song Title")
        (["Artist A", "Artist B"], "Song Title")
    """
    if not isinstance(full, str):
        raise TypeError("full must be a string")
    s = full.strip()

    # Split on " - " (or – / —) once
    parts = re.split(r"\s[-–—]\s", s, maxsplit=1)
    if len(parts) != 2:
        return [], s

    left, right = parts[0].strip(), parts[1].strip()

    # Split left into primary artists; include '/' but be careful with names like 'AC / DC'
    # Use word boundaries to avoid splitting names that contain these characters
    raw_artists = re.split(
        r"\s*(?:,|&|and|/|×|\+|(?<=\w)\s*[xX]\s*(?=\w))\s*",
        left,
        flags=re.IGNORECASE,
    )

    artists: list[str] = []
    seen = set()
    for a in raw_artists:
        name = a.strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        artists.append(name)

    return artists, right


def parse_title(
    title: str,
    *,
    normalize_youtube_noise: bool = False,  # <— toggle (default off)
    version_mapping_table: dict[str, str] | None = None,  # <— simple table approach
) -> dict[str, Any]:
    """
    Parse music titles with comprehensive feature and version detection.

    Input:  "Song Title (feat. Artist A & Artist B) (Live Version) (Official Video)"
    Output: {
      "artist": "",
      "title": "Song Title",
      "features": ["Artist A", "Artist B"],
      "version": "Live Version"   # not "Official Video" - musical version wins
    }

    Args:
        title: Title string to parse
        normalize_youtube_noise: If True, filter out YouTube presentation labels
        version_mapping_table: Optional dict for custom version handling. Simple key - value pairs:
            - Single versions: "visualizer": "lyric video" (normalize names)
            - Combinations: "slowed + visualizer": "slowed" (sorted keys)

    Returns:
        Dictionary with parsed components:
        - artist: Primary artist (empty string if not detected)
        - title: Clean song title
        - features: List of featured artists
        - version: Version identifier (e.g., "Live", "Acoustic", "Remix")

    Raises:
        ValueError: If title is empty or not a string

    Examples:
        >>> parse_title("Song Title (feat. Artist A) (Live)")
        {
            "artist": "",
            "title": "Song Title",
            "features": ["Artist A"],
            "version": "Live"
        }

        >>> # Custom table example - much simpler!
        >>> table = {
        ...     "visualizer": "lyric video",           # Single version mapping
        ...     "slowed + visualizer": "slowed"          # Combination mapping
        ... }
        >>> parse_title("Song (Slowed) (Visualizer)", version_mapping_table=table)
        {
            "artist": "",
            "title": "Song",
            "features": [],
            "version": "Slowed"  # Musical version wins over presentation
        }
    """
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must be a non - empty string")

    base, segments = _strip_paren_segments(title)

    # Strip trailing producer attributions from the base string when normalizing
    # e.g., "... Produced by IVN" → remove
    if normalize_youtube_noise:
        base = re.sub(
            r"\s * produced\s + by\s+.+$", "", base, flags=re.IGNORECASE
        ).strip()

    features: list[str] = []
    version: str | None = None

    # Handle " - feat. X" and " feat. X" outside parentheses / brackets.
    # Look for features after dash or just standalone
    feature_patterns = [
        r"[-–—]\s*(?:feat\.?|featuring|ft\.?|with)\s+(?P<guests>.+)$",  # After dash
        r"\s+(?:feat\.?|featuring|ft\.?|with)\s+(?P<guests>.+)$",  # Standalone
    ]

    for pattern in feature_patterns:
        dash = re.search(pattern, base, re.IGNORECASE)
        if dash:
            features.extend(_split_guests(dash.group("guests")))
            base = base[: dash.start()].strip()
            break  # Only match first pattern

    # Walk paren / bracket contents in order: collect features and find version tags.
    version_candidates = []

    for content in segments:
        # Drop YouTube presentation labels when toggle is on
        if normalize_youtube_noise and _YT_NOISE_RE.match(content.strip()):
            continue

        # Drop producer attribution segments entirely when normalizing
        if normalize_youtube_noise and re.match(
            r"^produced\s + by\s+.+$", content.strip(), flags=re.IGNORECASE
        ):
            continue

        m = _FEATURE_PREFIX.match(content)
        if m:
            features.extend(_split_guests(m.group("guests")))
            continue

        if _is_version_content(content):
            normalized_version = _normalize_version_phrase(content)
            version_candidates.append(normalized_version)
            continue

    # Resolve multiple versions using simple table lookup
    if version_candidates:
        version = _resolve_version_combination(
            version_candidates, version_mapping_table
        )

    if version is None:
        version = "Original"

    # Heuristic: if title text contains lyric / visualizer tokens, treat as Lyric Video
    # even if the specific token was removed as noise for canonicalization.
    if normalize_youtube_noise and version == "Original":
        if re.search(r"\blyric(s)?\b", title, flags=re.IGNORECASE) or re.search(
            r"visuali[zs]er", title, flags=re.IGNORECASE
        ):
            version = "Lyric Video"

    return {
        "artist": "",
        "title": base,
        "features": features,
        "version": version,
    }


def normalize_channel_title_for_artist(channel_title: str) -> str:
    """
    Normalize YouTube channel titles when used as artist fallbacks.

    - Strip trailing " - Topic" which appears on auto - generated topic channels.
    - Trim whitespace.

    Args:
        channel_title: YouTube channel title string

    Returns:
        Normalized artist name string

    Example:
        >>> normalize_channel_title_for_artist("Artist Name - Topic")
        "Artist Name"
    """
    if not isinstance(channel_title, str):
        return ""
    out = channel_title.strip()
    out = re.sub(r"\s*-\s*Topic$", "", out, flags=re.IGNORECASE).strip()
    return out

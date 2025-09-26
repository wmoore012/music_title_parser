# SPDX-License-Identifier: MIT
# Copyright (c) 2024 MusicScope

"""
Examples of configurable version mapping for music title parser.

This demonstrates how users can customize version handling rules to match
their specific needs and handle edge cases they encounter.
"""

from music_title_parser.parser import parse_title, split_artist_title


def example_default_behavior():
    """Show default version handling behavior."""
    print("🎵 Default Version Handling")
    print("=" * 40)

    test_cases = [
        "Song Title (Slowed) (Visualizer)",
        "Song Title (Lyric Visualizer)",
        "Song Title (Acoustic) (Official Video)",
        "Song Title (Live Performance) (Lyric Video)",
    ]

    for title in test_cases:
        result = parse_title(title, normalize_youtube_noise=True)
        print(f"'{result['title']}' → {result['version']}")


def example_custom_equivalencies():
    """Show how to define version equivalencies."""
    print("\n🔧 Custom Equivalencies")
    print("=" * 40)

    # Define custom equivalencies
    custom_rules = {
        "equivalencies": {
            "lyric video": ["visualizer", "lyric visualizer", "lyrics video", "visiualizer"],
            "official video": ["music video", "official music video", "official mv"],
            "live": ["live performance", "live version", "live recording"],
            "acoustic": ["acoustic version", "acoustic performance", "unplugged"],
        }
    }

    test_cases = [
        "Song Title (Lyric Visualizer)",  # Should become "Lyric Video"
        "Song Title (Visiualizer)",  # Typo handling
        "Song Title (Official MV)",  # Abbreviation handling
        "Song Title (Live Performance)",  # Variation handling
    ]

    for title in test_cases:
        result = parse_title(title, version_mapping_rules=custom_rules)
        print(f"'{result['title']}' → {result['version']}")


def example_priority_system():
    """Show how to customize version priorities."""
    print("\n📊 Custom Priority System")
    print("=" * 40)

    # Define custom priorities (lower number = higher priority)
    custom_rules = {
        "priorities": {
            # Musical transformations (highest priority)
            "slowed and reverbed": 1,
            "slowed": 2,
            "sped up": 2,
            "nightcore": 2,
            # Performance versions
            "live": 3,
            "acoustic": 3,
            "instrumental": 3,
            # Production versions
            "remix": 4,
            "radio edit": 5,
            "clean": 6,
            "explicit": 6,
            # Presentation formats (lowest priority)
            "lyric video": 10,
            "official video": 11,
            "visualizer": 12,
        }
    }

    # Test multiple versions in one title
    test_cases = [
        "Song Title (Official Video) (Slowed)",  # Slowed wins
        "Song Title (Lyric Video) (Acoustic)",  # Acoustic wins
        "Song Title (Visualizer) (Remix)",  # Remix wins
        "Song Title (Official Video) (Lyric Video)",  # Lyric Video wins
    ]

    for title in test_cases:
        result = parse_title(title, version_mapping_rules=custom_rules)
        print(f"'{result['title']}' → {result['version']}")


def example_combination_rules():
    """Show how to define specific combination rules."""
    print("\n🎯 Combination Rules")
    print("=" * 40)

    # Define specific rules for version combinations
    custom_rules = {
        "combinations": {
            # Musical + Presentation = Musical
            "slowed+visualizer": "slowed",
            "slowed+lyric video": "slowed",
            "acoustic+official video": "acoustic",
            "remix+visualizer": "remix",
            "live+lyric video": "live",
            # Special cases
            "slowed+reverb": "slowed and reverbed",
            "clean+radio edit": "radio edit",
            "explicit+uncensored": "explicit",
        },
        "equivalencies": {
            "lyric video": ["visualizer", "lyric visualizer"],
        },
    }

    test_cases = [
        "Song Title (Slowed) (Visualizer)",
        "Song Title (Acoustic) (Official Video)",
        "Song Title (Remix) (Lyric Video)",
        "Song Title (Clean) (Radio Edit)",
    ]

    for title in test_cases:
        result = parse_title(title, version_mapping_rules=custom_rules)
        print(f"'{result['title']}' → {result['version']}")


def example_real_world_youtube():
    """Show handling of real YouTube titles with custom rules."""
    print("\n🎬 Real YouTube Title Handling")
    print("=" * 40)

    # Rules optimized for YouTube content
    youtube_rules = {
        "equivalencies": {
            "lyric video": ["visualizer", "lyric visualizer", "lyrics video", "visiualizer"],
            "official video": ["music video", "official music video", "official audio"],
            "slowed and reverbed": ["slowed + reverb", "slowed & reverb", "slowed reverb"],
        },
        "priorities": {
            "slowed and reverbed": 1,
            "slowed": 2,
            "sped up": 2,
            "nightcore": 2,
            "remix": 3,
            "acoustic": 3,
            "live": 3,
            "instrumental": 4,
            "radio edit": 5,
            "lyric video": 10,
            "official video": 11,
        },
        "combinations": {
            "slowed+visualizer": "slowed",
            "slowed+lyric video": "slowed",
            "acoustic+official video": "acoustic",
            "remix+visualizer": "remix",
            "live+lyric video": "live",
        },
    }

    # Real YouTube titles from the database
    youtube_titles = [
        "Lute / Cozz - Eye To Eye ( Slowed To Perfection ) Visiualizer",
        "Emanny - B.D.E. (Lyric Visualizer)",
        "Eric Bellinger - Backwards (Visualizer)",
        "Ryan Destiny - Do You (Quarantine Video)",
    ]

    for title in youtube_titles:
        artists, title_part = split_artist_title(title)
        result = parse_title(
            title_part if artists else title,
            normalize_youtube_noise=True,
            version_mapping_rules=youtube_rules,
        )

        print(f"Artists: {artists}")
        print(f"Title: '{result['title']}' → Version: {result['version']}")
        print()


def example_user_customization_guide():
    """Show how users can customize for their specific needs."""
    print("\n📚 User Customization Guide")
    print("=" * 40)

    print("To customize version handling, create a rules dictionary with:")
    print()
    print("1. 'equivalencies' - Treat different terms as the same:")
    print("   'lyric video': ['visualizer', 'lyric visualizer']")
    print()
    print("2. 'priorities' - Set importance (lower = higher priority):")
    print("   'slowed': 1, 'remix': 3, 'lyric video': 10")
    print()
    print("3. 'combinations' - Handle multiple versions:")
    print("   'slowed+visualizer': 'slowed'")
    print()
    print("Example usage:")
    print("   rules = {'equivalencies': {...}, 'priorities': {...}}")
    print("   result = parse_title(title, version_mapping_rules=rules)")
    print()
    print("✅ No database changes needed!")
    print("✅ Easy to add new rules as issues arise!")
    print("✅ Backward compatible - rules are optional!")


if __name__ == "__main__":
    example_default_behavior()
    example_custom_equivalencies()
    example_priority_system()
    example_combination_rules()
    example_real_world_youtube()
    example_user_customization_guide()

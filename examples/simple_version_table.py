# SPDX-License-Identifier: MIT
# Copyright (c) 2024 MusicScope

"""
Simple Version Mapping Table Examples

This shows the much simpler table-based approach for handling version combinations.
No complex rules - just straightforward key-value mappings!
"""

from music_title_parser.parser import parse_title, split_artist_title


def show_default_table():
    """Show what the default table handles."""
    print("🎵 Default Version Mapping Table")
    print("=" * 40)

    # These are handled by the built-in table
    test_cases = [
        "Song (Visualizer)",  # → Lyric Video
        "Song (Lyric Visualizer)",  # → Lyric Video
        "Song (Slowed) (Visualizer)",  # → Slowed
        "Song (Acoustic) (Official Video)",  # → Acoustic
        "Song (Live) (Lyric Video)",  # → Live
    ]

    for title in test_cases:
        result = parse_title(title)
        print(f"'{title}' → {result['version']}")


def show_custom_table():
    """Show how to create your own simple mapping table."""
    print("\n🔧 Custom Version Mapping Table")
    print("=" * 40)

    # Your custom table - dead simple!
    my_table = {
        # Single version mappings (normalize names)
        "visualizer": "lyric video",
        "lyric visualizer": "lyric video",
        "visiualizer": "lyric video",  # Handle typos
        "official mv": "official video",  # Handle abbreviations
        # Combination mappings (key = sorted versions joined with +)
        "slowed+visualizer": "slowed",  # Your specific case
        "acoustic+official video": "acoustic",  # Musical wins over presentation
        "remix+lyric video": "remix",  # Musical wins over presentation
        # Special combinations you want to handle differently
        "live+lyric video": "live performance",  # Custom result
        "acoustic+live": "acoustic live",  # Custom combination
    }

    test_cases = [
        "Song (Slowed) (Visualizer)",  # Should use combination rule
        "Song (Visiualizer)",  # Should handle typo
        "Song (Official MV)",  # Should handle abbreviation
        "Song (Live) (Lyric Video)",  # Should use custom combination
        "Song (Acoustic) (Live)",  # Should use custom combination
    ]

    for title in test_cases:
        result = parse_title(title, version_mapping_table=my_table)
        print(f"'{title}' → {result['version']}")


def show_real_youtube_examples():
    """Show with real YouTube titles from your database."""
    print("\n🎬 Real YouTube Examples")
    print("=" * 40)

    # Table optimized for your YouTube data
    youtube_table = {
        "visualizer": "lyric video",
        "lyric visualizer": "lyric video",
        "visiualizer": "lyric video",  # Handle the typo in your data
        "slowed+visualizer": "slowed",
        "slowed+visiualizer": "slowed",  # Handle typo in combination too
    }

    # Real titles from your database
    youtube_titles = [
        "Lute / Cozz - Eye To Eye ( Slowed To Perfection ) Visiualizer",
        "Emanny - B.D.E. (Lyric Visualizer)",
        "Eric Bellinger - Backwards (Visualizer)",
    ]

    for title in youtube_titles:
        artists, title_part = split_artist_title(title)
        result = parse_title(title_part, version_mapping_table=youtube_table)

        print(f"Artists: {artists}")
        print(f"Title: '{result['title']}' → Version: {result['version']}")
        print()


def show_how_to_add_new_cases():
    """Show how easy it is to add new cases as you encounter them."""
    print("📚 How to Add New Cases")
    print("=" * 40)

    print("When you encounter a new combination like 'Nightcore + Visualizer':")
    print()
    print("1. Just add it to your table:")
    print("   my_table['nightcore+visualizer'] = 'nightcore'")
    print()
    print("2. Or for single version normalization:")
    print("   my_table['visualiser'] = 'lyric video'  # British spelling")
    print()
    print("3. That's it! No complex priority rules to figure out.")
    print()
    print("✅ Dead simple")
    print("✅ Easy to understand")
    print("✅ Easy to maintain")
    print("✅ Easy to debug")
    print("✅ No surprises")


if __name__ == "__main__":
    show_default_table()
    show_custom_table()
    show_real_youtube_examples()
    show_how_to_add_new_cases()

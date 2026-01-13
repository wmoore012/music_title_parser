# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Perday CatalogLAB™

"""
Interactive Version Rule Manager

Beautiful CLI for managing version mapping rules based on real database examples.
Shows actual problematic cases and lets users create rules visually.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from rich import box
    from rich.align import Align
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print("❌ Rich library required. Install with: pip install rich")
    raise

from .parser import parse_title, split_artist_title


class VersionRuleManager:
    """Interactive manager for version mapping rules."""

    def __init__(self, rules_file: str = "version_rules.json"):
        self.console = Console()
        self.rules_file = Path(rules_file)
        self.rules = self._load_rules()

    def _load_rules(self) -> dict[str, str]:
        """Load existing rules from JSON file."""
        if self.rules_file.exists():
            try:
                with open(self.rules_file) as f:
                    return json.load(f)
            except Exception as e:
                self.console.print(f"⚠️  Error loading rules: {e}", style="yellow")
        return {}

    def _save_rules(self) -> None:
        """Save rules to JSON file."""
        try:
            with open(self.rules_file, "w") as f:
                json.dump(self.rules, f, indent=2, sort_keys=True)
            self.console.print(f"✅ Rules saved to {self.rules_file}", style="green")
        except Exception as e:
            self.console.print(f"❌ Error saving rules: {e}", style="red")

    def show_banner(self):
        """Display the application banner."""
        banner = Text.assemble(
            ("🎵 ", "bright_magenta"),
            ("Version Rule Manager", "bright_cyan bold"),
            (" 🎛️", "bright_yellow"),
        )

        panel = Panel(
            Align.center(banner),
            box=box.DOUBLE,
            border_style="bright_magenta",
            padding=(1, 2),
        )

        self.console.print()
        self.console.print(panel)
        self.console.print()

    def analyze_database_examples(self, database_url: str) -> list[dict[str, Any]]:
        """
        Analyze database to find problematic version combinations.
        Queries your actual YouTube titles table to find real issues.
        """
        if not database_url:
            # Mock data for demo
            return self._get_mock_examples()

        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(database_url)

            # Query your actual YouTube titles
            with engine.begin() as conn:
                result = conn.execute(
                    text(
                        """
                    SELECT title, COUNT(*) as count
                    FROM youtube_videos
                    WHERE title IS NOT NULL
                    AND title != ''
                    GROUP BY title
                    HAVING COUNT(*) >= 1
                    ORDER BY COUNT(*) DESC
                    LIMIT 50
                """
                    )
                )

                examples = []
                for row in result:
                    title = row[0]
                    count = row[1]

                    # Parse the title to see what versions are detected
                    try:
                        artists, title_part = split_artist_title(title)
                        parsed = parse_title(
                            title_part if artists else title,
                            normalize_youtube_noise=True,
                        )

                        # Check if this looks like a multi - version case
                        # Look for multiple parentheses / brackets that might contain versions
                        import re

                        segments = re.findall(r"[(\[{]([^)\]}]*)[)\]}]", title)

                        potential_versions = []
                        for segment in segments:
                            # Simple check if segment looks like a version
                            if any(
                                keyword in segment.lower()
                                for keyword in [
                                    "slowed",
                                    "acoustic",
                                    "live",
                                    "remix",
                                    "visual",
                                    "official",
                                    "lyric",
                                ]
                            ):
                                potential_versions.append(segment.strip())

                        is_problematic = len(potential_versions) > 1

                        examples.append(
                            {
                                "title": title,
                                "versions_found": potential_versions
                                or [parsed["version"]],
                                "current_result": parsed["version"],
                                "count": count,
                                "is_problematic": is_problematic,
                            }
                        )

                    except Exception:
                        # Skip titles that can't be parsed
                        continue

                return examples[:20]  # Return top 20 examples

        except Exception as e:
            self.console.print(f"⚠️  Database error: {e}", style="yellow")
            return self._get_mock_examples()

    def _get_mock_examples(self) -> list[dict[str, Any]]:
        """Get mock examples for demo purposes."""
        problematic_examples = [
            {
                "title": "Lute / Cozz - Eye To Eye ( Slowed To Perfection ) Visiualizer",
                "versions_found": ["Slowed", "Visualizer"],
                "current_result": "Slowed",
                "count": 15,
                "is_problematic": True,
            },
            {
                "title": "Song Title (Acoustic) (Official Video)",
                "versions_found": ["Acoustic", "Official Video"],
                "current_result": "Acoustic",
                "count": 8,
                "is_problematic": False,
            },
            {
                "title": "Artist - Track (Remix) (Lyric Video)",
                "versions_found": ["Remix", "Lyric Video"],
                "current_result": "Remix",
                "count": 23,
                "is_problematic": False,
            },
            {
                "title": "Song (Live Performance) (Visualizer)",
                "versions_found": ["Live", "Visualizer"],
                "current_result": "Live",
                "count": 5,
                "is_problematic": True,
            },
            {
                "title": "Track (Nightcore) (Official Music Video)",
                "versions_found": ["Nightcore", "Official Video"],
                "current_result": "Nightcore",
                "count": 12,
                "is_problematic": True,
            },
        ]

        return problematic_examples

    def show_database_analysis(self, examples: list[dict[str, Any]]) -> None:
        """Show analysis of database examples with current parsing results."""

        # Separate problematic and good examples
        problematic = [ex for ex in examples if ex.get("is_problematic", False)]
        good_examples = [ex for ex in examples if not ex.get("is_problematic", False)]

        if problematic:
            self.console.print(
                Panel(
                    "🚨 Problematic Version Combinations Found",
                    style="red bold",
                    border_style="red",
                )
            )

            prob_table = Table(box=box.ROUNDED, border_style="red")
            prob_table.add_column("Example Title", style="white", width=40)
            prob_table.add_column("Versions Found", style="yellow", width=20)
            prob_table.add_column("Current Result", style="cyan", width=15)
            prob_table.add_column("Count", justify="right", style="red", width=8)

            for ex in problematic:
                prob_table.add_row(
                    ex["title"][:37] + "..." if len(ex["title"]) > 40 else ex["title"],
                    " + ".join(ex["versions_found"]),
                    ex["current_result"],
                    str(ex["count"]),
                )

            self.console.print(prob_table)
            self.console.print()

        if good_examples:
            self.console.print(
                Panel(
                    "✅ Well - Handled Version Combinations",
                    style="green bold",
                    border_style="green",
                )
            )

            good_table = Table(box=box.ROUNDED, border_style="green")
            good_table.add_column("Example Title", style="white", width=40)
            good_table.add_column("Versions Found", style="yellow", width=20)
            good_table.add_column("Current Result", style="cyan", width=15)
            good_table.add_column("Count", justify="right", style="green", width=8)

            for ex in good_examples:
                good_table.add_row(
                    ex["title"][:37] + "..." if len(ex["title"]) > 40 else ex["title"],
                    " + ".join(ex["versions_found"]),
                    ex["current_result"],
                    str(ex["count"]),
                )

            self.console.print(good_table)
            self.console.print()

    def show_current_rules(self) -> None:
        """Display current version mapping rules."""
        if not self.rules:
            self.console.print(
                Panel(
                    "No custom rules defined yet.",
                    title="Current Rules",
                    border_style="blue",
                )
            )
            return

        rules_table = Table(
            title="🎛️ Current Version Rules", box=box.ROUNDED, border_style="blue"
        )

        rules_table.add_column("Version Combination", style="yellow", width=30)
        rules_table.add_column("→", justify="center", style="white", width=3)
        rules_table.add_column("Result", style="green", width=20)

        for combo, result in sorted(self.rules.items()):
            rules_table.add_row(combo, "→", result)

        self.console.print(rules_table)
        self.console.print()

    def create_rule_interactively(self, examples: list[dict[str, Any]]) -> None:
        """Interactive rule creation based on database examples."""

        self.console.print(
            Panel(
                "🎯 Create Version Priority Rule",
                style="bright_blue bold",
                border_style="blue",
            )
        )

        # Show problematic examples for selection
        problematic = [ex for ex in examples if ex.get("is_problematic", False)]

        if not problematic:
            self.console.print("✅ No problematic combinations found!")
            return

        self.console.print("Select a problematic combination to create a rule for:")
        self.console.print()

        for i, ex in enumerate(problematic, 1):
            status = "🚨" if ex["is_problematic"] else "✅"
            self.console.print(
                f"{i}. {status} [yellow]{' + '.join(ex['versions_found'])}[/yellow] → [cyan]{ex['current_result']}[/cyan] ([red]{ex['count']} cases[/red])"
            )
            self.console.print(f"   Example: [dim]{ex['title'][:60]}...[/dim]")
            self.console.print()

        try:
            choice = int(Prompt.ask("Choose a combination (number)", default="1"))
            if 1 <= choice <= len(problematic):
                selected = problematic[choice - 1]
                self._create_rule_for_combination(selected)
            else:
                self.console.print("❌ Invalid choice", style="red")
        except ValueError:
            self.console.print("❌ Please enter a valid number", style="red")

    def _create_rule_for_combination(self, example: dict[str, Any]) -> None:
        """Create a rule for a specific version combination."""
        versions = example["versions_found"]
        current_result = example["current_result"]

        self.console.print(
            Panel(
                f"Creating rule for: [yellow]{' + '.join(versions)}[/yellow]",
                border_style="blue",
            )
        )

        self.console.print(f"Current result: [cyan]{current_result}[/cyan]")
        self.console.print(f"Example title: [dim]{example['title']}[/dim]")
        self.console.print()

        # Show version options
        self.console.print("Which version should win? Choose:")
        for i, version in enumerate(versions, 1):
            marker = "👑" if version == current_result else "  "
            self.console.print(f"{i}. {marker} [yellow]{version}[/yellow]")

        self.console.print(f"{len(versions) + 1}.   [green]Custom result[/green]")
        self.console.print()

        try:
            choice = int(Prompt.ask("Your choice", default="1"))

            if 1 <= choice <= len(versions):
                chosen_result = versions[choice - 1]
            elif choice == len(versions) + 1:
                chosen_result = Prompt.ask("Enter custom result")
            else:
                self.console.print("❌ Invalid choice", style="red")
                return

            # Create the rule key (sorted combination)
            rule_key = "+".join(sorted([v.lower() for v in versions]))

            # Confirm the rule
            self.console.print()
            self.console.print(
                Panel(
                    f"[yellow]{rule_key}[/yellow] → [green]{chosen_result}[/green]",
                    title="New Rule",
                    border_style="green",
                )
            )

            if Confirm.ask("Save this rule?", default=True):
                self.rules[rule_key] = chosen_result.lower()
                self._save_rules()

                # Test the rule
                self._test_rule_on_example(example, rule_key, chosen_result)

        except ValueError:
            self.console.print("❌ Please enter a valid number", style="red")

    def _test_rule_on_example(
        self, example: dict[str, Any], rule_key: str, expected_result: str
    ) -> None:
        """Test the new rule on the example."""
        self.console.print()
        self.console.print("🧪 Testing new rule...")

        # Parse the example title with the new rules
        title = example["title"]
        artists, title_part = split_artist_title(title)
        result = parse_title(
            title_part if artists else title, version_mapping_table=self.rules
        )

        if result["version"].lower() == expected_result.lower():
            self.console.print(
                f"✅ Rule works! [green]{result['version']}[/green]", style="green"
            )
        else:
            self.console.print(
                f"⚠️  Unexpected result: [red]{result['version']}[/red] (expected [green]{expected_result}[/green])",
                style="yellow",
            )

    def run_interactive_session(self, database_url: str | None = None) -> None:
        """Run the interactive version rule management session."""
        self.console.clear()
        self.show_banner()

        # Analyze database examples
        if database_url:
            self.console.print("🔍 Analyzing your database for version combinations...")
            examples = self.analyze_database_examples(database_url)
        else:
            self.console.print(
                "📊 Using sample data (connect database for real analysis)"
            )
            examples = self.analyze_database_examples("")

        while True:
            self.console.print()
            self.show_database_analysis(examples)
            self.show_current_rules()

            # Main menu
            menu_table = Table(box=box.ROUNDED, border_style="cyan")
            menu_table.add_column("Option", style="bright_yellow bold", width=8)
            menu_table.add_column("Action", style="bright_white bold", width=30)

            menu_table.add_row("1", "🎯 Create New Rule")
            menu_table.add_row("2", "📝 Edit Existing Rule")
            menu_table.add_row("3", "🗑️  Delete Rule")
            menu_table.add_row("4", "🔄 Refresh Database Analysis")
            menu_table.add_row("5", "💾 Export Rules")
            menu_table.add_row("q", "🚪 Quit")

            self.console.print(menu_table)
            self.console.print()

            choice = Prompt.ask(
                "Select an option", choices=["1", "2", "3", "4", "5", "q"], default="1"
            )

            if choice == "1":
                self.create_rule_interactively(examples)
            elif choice == "2":
                self._edit_rule()
            elif choice == "3":
                self._delete_rule()
            elif choice == "4":
                examples = self.analyze_database_examples(database_url or "")
            elif choice == "5":
                self._export_rules()
            elif choice == "q":
                self.console.print(
                    "\n👋 [bright_cyan]Thanks for using Version Rule Manager![/bright_cyan]"
                )
                break

            self.console.clear()
            self.show_banner()

    def _edit_rule(self) -> None:
        """Edit an existing rule."""
        if not self.rules:
            self.console.print("❌ No rules to edit", style="red")
            return

        # Show rules for selection
        rule_list = list(self.rules.items())
        for i, (combo, result) in enumerate(rule_list, 1):
            self.console.print(
                f"{i}. [yellow]{combo}[/yellow] → [green]{result}[/green]"
            )

        try:
            choice = int(Prompt.ask("Which rule to edit?", default="1"))
            if 1 <= choice <= len(rule_list):
                combo, old_result = rule_list[choice - 1]
                new_result = Prompt.ask(f"New result for '{combo}'", default=old_result)
                self.rules[combo] = new_result
                self._save_rules()
                self.console.print(
                    f"✅ Updated rule: [yellow]{combo}[/yellow] → [green]{new_result}[/green]"
                )
        except ValueError:
            self.console.print("❌ Invalid choice", style="red")

    def _delete_rule(self) -> None:
        """Delete an existing rule."""
        if not self.rules:
            self.console.print("❌ No rules to delete", style="red")
            return

        rule_list = list(self.rules.keys())
        for i, combo in enumerate(rule_list, 1):
            self.console.print(
                f"{i}. [yellow]{combo}[/yellow] → [green]{self.rules[combo]}[/green]"
            )

        try:
            choice = int(Prompt.ask("Which rule to delete?"))
            if 1 <= choice <= len(rule_list):
                combo = rule_list[choice - 1]
                if Confirm.ask(f"Delete rule for '{combo}'?"):
                    del self.rules[combo]
                    self._save_rules()
                    self.console.print(f"✅ Deleted rule for [yellow]{combo}[/yellow]")
        except ValueError:
            self.console.print("❌ Invalid choice", style="red")

    def _export_rules(self) -> None:
        """Export rules in different formats."""
        if not self.rules:
            self.console.print("❌ No rules to export", style="red")
            return

        self.console.print("📤 Rules exported to:")
        self.console.print(f"   JSON: {self.rules_file}")

        # Also show Python code format
        python_code = "version_mapping_table = {\n"
        for combo, result in sorted(self.rules.items()):
            python_code += f'    "{combo}": "{result}",\n'
        python_code += "}"

        self.console.print("\n📋 Python code format:")
        self.console.print(Panel(python_code, border_style="blue"))


def main():
    """Entry point for the version rule manager."""
    manager = VersionRuleManager()
    manager.run_interactive_session()


if __name__ == "__main__":
    main()

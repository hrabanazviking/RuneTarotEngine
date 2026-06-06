#!/usr/bin/env python3
# RuneTarot — Entry Point
# Golden Dawn Divination Engine — TUI Application
#
# Usage:
#   python runetarot.py           # Launch the TUI
#   python runetarot.py --cli     # CLI mode (basic reading)
#   python runetarot.py --help    # Show help

"""
RuneTarot — A Golden Dawn / Book T Tarot Divination TUI Application.

Launch the beautiful Textual TUI, or use --cli for a simple
command-line reading without the TUI.
"""

from __future__ import annotations

import sys
import argparse
import random
import time

# Ensure the project root is in the Python path
from pathlib import Path

project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))


def run_tui() -> None:
    """Launch the Textual TUI application."""
    from tui.app import RuneTarotApp
    
    app = RuneTarotApp()
    app.run()


def run_cli(args: argparse.Namespace) -> None:
    """
    Run a basic CLI tarot reading (no TUI).
    Useful for quick readings, scripting, or when the terminal
    doesn't support the full TUI.
    """
    from src.engine import RuneTarotEngine
    from src.renderer import CardRenderer
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    
    console = Console()
    
    # Initialize engine
    console.print("[bold medium_purple4]✦ RuneTarot ✦ Golden Dawn Divination Engine[/bold medium_purple4]")
    console.print("[dim]Initializing...[/dim]")
    
    engine = RuneTarotEngine()
    if not engine.initialize_subsystems():
        console.print("[bold red]Engine initialization failed![/bold red]")
        sys.exit(1)
    
    console.print(f"[green]✓[/green] Loaded {engine.deck.count()} cards")
    console.print(f"[green]✓[/green] Loaded {len(engine.spread_manager.list_spreads())} spreads")
    console.print(f"[green]✓[/green] AI: {'enabled' if engine.is_ai_available() else 'disabled (no API key)'}")
    console.print()
    
    # Select spread
    spread_name = args.spread or "celtic_cross"
    spread = engine.spread_manager.get_spread(spread_name)
    
    if not spread:
        console.print(f"[red]Spread '{spread_name}' not found![/red]")
        console.print("Available spreads:")
        for info in engine.spread_manager.list_spreads():
            console.print(f"  • {info['name']} ({info['card_count']} cards)")
        sys.exit(1)
    
    console.print(f"[bold]Spread:[/bold] {spread.name}")
    console.print(f"[dim]{spread.description}[/dim]")
    console.print()
    
    # Get question
    question = args.question or ""
    if not question:
        try:
            question = input("Your question (press Enter to skip): ").strip()
        except (EOFError, KeyboardInterrupt):
            question = ""
    
    if question:
        console.print(f"[bold]Question:[/bold] {question}")
    
    console.print()
    console.print("[bold]Shuffling and drawing cards...[/bold]")
    time.sleep(0.5)
    
    # Generate reading
    seed = args.seed or int(time.time() * 1000) % (2**31)
    
    try:
        result = engine.generate_reading(
            spread_name=spread_name,
            question=question,
            seed=seed,
        )
        
        placed_cards = result.get("placed_cards", [])
        reading_text = result.get("reading_text", "")
        ai_interpretation = result.get("ai_interpretation", "")
        reading_id = result.get("reading_id", "")
        
        # Display cards
        console.print()
        console.print(Panel(
            "Cards Drawn",
            style="bold medium_purple4",
            title="✦ The Spread ✦",
        ))
        
        renderer = CardRenderer(engine.gd_engine)
        
        for pc in placed_cards:
            card = pc.card
            elem = renderer._get_card_element(card)
            rev = " ↕ REVERSED" if card.is_reversed else ""
            color = {"fire": "red3", "water": "dodger_blue1", "air": "gold1", "earth": "green4", "major": "medium_purple4"}.get(elem, "white")
            
            console.print(f"  [{color}]{pc.position.name}[/{color}]: [{color}]{card.display_name}{rev}[/{color}]")
            console.print(f"    [dim]{pc.position.meaning}[/dim]")
        
        console.print()
        
        # Display reading text
        console.print(Panel(
            Markdown(reading_text),
            title="✦ Interpretation ✦",
            style="medium_purple4",
        ))
        
        # AI interpretation
        if ai_interpretation and not ai_interpretation.startswith("⚠"):
            console.print()
            console.print(Panel(
                Markdown(ai_interpretation),
                title="✦ AI Deep Interpretation ✦",
                style="dodger_blue1",
            ))
        elif engine.is_ai_available():
            console.print()
            console.print("[dim italic]Use --ai flag to request an AI deep interpretation.[/dim italic]")
        
        console.print()
        console.print(f"[dim]Reading ID: {reading_id}[/dim]")
        console.print(f"[dim]Seed: {seed}[/dim]")
        
    except Exception as e:
        console.print(f"[bold red]Reading failed: {e}[/bold red]")
        sys.exit(1)


def main() -> None:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="RuneTarot — Golden Dawn Divination Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runetarot.py                    # Launch TUI
  python runetarot.py --cli               # CLI reading (Celtic Cross)
  python runetarot.py --cli --spread three_card   # Three card reading
  python runetarot.py --cli --question "Will I find love?"  # With question
  python runetarot.py --cli --seed 12345  # Reproducible reading
        """,
    )
    
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in CLI mode (no TUI)",
    )
    parser.add_argument(
        "--spread",
        type=str,
        default=None,
        help="Spread name for CLI mode (default: celtic_cross)",
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        default=None,
        help="The querent's question",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible readings",
    )
    
    args = parser.parse_args()
    
    if args.cli:
        run_cli(args)
    else:
        run_tui()


if __name__ == "__main__":
    main()

# RuneTarot — Utility Functions
# Shared helpers used across the codebase

"""
Utility functions for RuneTarot.
File-location agnostic, robust, and fault-tolerant.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional
import logging

logger = logging.getLogger("runetarot")


def get_project_root() -> Path:
    """
    Locate the project root directory by searching upward for a marker file.
    This makes the codebase file-location agnostic — no hardcoded paths.
    """
    current = Path(__file__).resolve().parent
    markers = ["ARCHITECTURE.md", "data", "src"]
    
    # Search upward from this file's location
    for _ in range(10):  # Prevent infinite loop
        if all((current / m).exists() for m in markers):
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    
    # Fallback: assume we are in src/ and project root is one level up
    fallback = Path(__file__).resolve().parent.parent
    logger.warning(f"Could not find project root via markers, using fallback: {fallback}")
    return fallback


def get_data_dir() -> Path:
    """Return the path to the data/ directory."""
    return get_project_root() / "data"


def get_session_dir() -> Path:
    """Return the path to the session/ directory, creating it if needed."""
    session_dir = get_project_root() / "session"
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def get_exports_dir() -> Path:
    """Return the path to the exports/ directory, creating it if needed."""
    exports_dir = get_project_root() / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    return exports_dir


def safe_get(data: dict, key: str, default: Any = None) -> Any:
    """
    Safely retrieve a value from a dictionary.
    Returns the default if the key is missing or the value is None.
    """
    if not isinstance(data, dict):
        return default
    return data.get(key, default)


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length, adding a suffix if truncated.
    Used for display purposes where space is limited.
    """
    if not isinstance(text, str):
        text = str(text)
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_card_id(suit: str, number_or_court: str) -> str:
    """
    Generate a canonical card ID from suit and number/court type.
    Examples: 'major_0', 'wands_2', 'cups_queen', 'pentacles_prince'
    """
    suit_lower = suit.lower()
    num_str = str(number_or_court).lower()
    return f"{suit_lower}_{num_str}"


def elemental_color(element: str) -> str:
    """
    Return a Rich-compatible color string for the given element.
    Used for card rendering and TUI theming.
    """
    color_map = {
        "fire": "red3",
        "water": "dodger_blue1",
        "air": "gold1",
        "earth": "green4",
    }
    return color_map.get(element.lower(), "white")


def suit_symbol(suit: str) -> str:
    """Return the Unicode symbol for a tarot suit."""
    symbols = {
        "wands": "🜂",      # Fire triangle
        "cups": "🜄",       # Water triangle
        "swords": "🜁",     # Air triangle
        "pentacles": "🜃",   # Earth triangle
        "major": "✦",       # Star for Major Arcana
    }
    return symbols.get(suit.lower(), "✦")


def suit_emoji(suit: str) -> str:
    """Return an emoji for a tarot suit (fallback when Unicode symbols don't render)."""
    emojis = {
        "wands": "🔥",
        "cups": "🌊",
        "swords": "🌬️",
        "pentacles": "🌍",
        "major": "✨",
    }
    return emojis.get(suit.lower(), "✦")


def suit_display_name(suit: str) -> str:
    """Return the display name for a suit."""
    names = {
        "wands": "Wands",
        "cups": "Cups",
        "swords": "Swords",
        "pentacles": "Pentacles",
        "major": "Major Arcana",
    }
    return names.get(suit.lower(), suit.title())


def court_display_name(court_type: str) -> str:
    """Return the display name for a court card type (GD naming)."""
    names = {
        "knight": "Knight",
        "queen": "Queen",
        "prince": "Prince",
        "princess": "Princess",
    }
    return names.get(court_type.lower(), court_type.title())


def is_reversed_check(card_data: dict) -> bool:
    """
    Check if a card is reversed based on its internal data.
    Cards carry their own reversal state after drawing.
    """
    return bool(safe_get(card_data, "_reversed", False))


def format_hebrew(letter: str) -> str:
    """Format a Hebrew letter for display, with RTL handling."""
    if not letter:
        return ""
    return letter

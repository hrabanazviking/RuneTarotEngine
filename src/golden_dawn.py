# RuneTarot — Golden Dawn Correspondence Engine
# Master correspondence lookup and cross-referencing system

"""
Golden Dawn correspondence engine for RuneTarot.
Provides lookups for Hebrew letters, astrological correspondences,
Tree of Life paths, elemental dignities, and GD color scales.
All data loaded from data/gd_correspondences.yaml.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml

from src.deck import TarotCard
from src.utils import get_data_dir, safe_get
from src.comprehensive_logging import get_logger

logger = get_logger("golden_dawn")


class GoldenDawnEngine:
    """
    The Mystery Keeper — handles all Golden Dawn correspondence lookups.
    
    Loads master correspondence tables from gd_correspondences.yaml
    and provides methods to cross-reference cards, elements, paths, and dignities.
    """

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self._data_dir = data_dir or get_data_dir()
        self._data: dict = {}
        self._loaded: bool = False

    def load(self) -> bool:
        """Load the GD correspondence tables from YAML."""
        filepath = self._data_dir / "gd_correspondences.yaml"
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}
            self._loaded = True
            logger.info("Golden Dawn correspondence tables loaded")
            return True
        except Exception as e:
            logger.error(f"Error loading GD correspondences: {e}")
            self._data = {}
            return False

    # ═══════════════════════════════════════
    # Hebrew Letter Lookups
    # ═══════════════════════════════════════

    def get_hebrew_correspondence(self, letter_name: str) -> dict:
        """
        Get all correspondences for a Hebrew letter by name.
        
        Args:
            letter_name: Name of the Hebrew letter (e.g., "aleph", "beth")
        
        Returns:
            Dictionary with all correspondence data for that letter.
        """
        if not self._loaded:
            self.load()
        
        letters = self._data.get("hebrew_letters", {})
        key = letter_name.lower()
        
        if key in letters:
            result = letters[key]
            if isinstance(result, dict):
                return result
        
        # Try matching by the letter field
        for letter_data in letters.values():
            if isinstance(letter_data, dict):
                name = str(safe_get(letter_data, "name", "")).lower()
                if name == key:
                    return letter_data
        
        return {}

    def get_hebrew_for_card(self, card: TarotCard) -> dict:
        """Get the Hebrew letter correspondence for a Major Arcana card."""
        hebrew = card.hebrew_letter
        if hebrew:
            # Try to find by the Hebrew character
            letters = self._data.get("hebrew_letters", {})
            for letter_data in letters.values():
                if isinstance(letter_data, dict):
                    if safe_get(letter_data, "letter") == hebrew:
                        return letter_data
                    if safe_get(letter_data, "tarot", "").lower() in card.display_name.lower():
                        return letter_data
            
            # Try by letter name
            letter_names = {
                "א": "aleph", "ב": "beth", "ג": "gimel", "ד": "daleth",
                "ה": "he", "ו": "vav", "ז": "zayin", "ח": "chet",
                "ט": "tet", "י": "yod", "כ": "kaf", "ל": "lamed",
                "מ": "mem", "נ": "nun", "ס": "samekh", "ע": "ayin",
                "פ": "pe", "צ": "tzaddi", "ק": "qof", "ר": "resh",
                "ש": "shin", "ת": "tav",
            }
            name = letter_names.get(hebrew, "")
            if name:
                return self.get_hebrew_correspondence(name)
        
        return {}

    # ═══════════════════════════════════════
    # Astrological Lookups
    # ═══════════════════════════════════════

    def get_astrological_correspondence(self, card: TarotCard) -> dict:
        """
        Get astrological correspondence for a card.
        Returns planetary or zodiacal data depending on card type.
        """
        if not self._loaded:
            self.load()
        
        astro = card.astrological
        if not astro:
            return {}
        
        result: dict[str, Any] = {"raw": astro}
        
        # Check if it's a planetary correspondence
        planets = self._data.get("planets", {})
        if isinstance(planets, dict):
            for planet_name, planet_data in planets.items():
                if isinstance(planet_data, dict):
                    planet_tarot = str(safe_get(planet_data, "tarot", ""))
                    if planet_tarot and planet_tarot.lower() in card.display_name.lower():
                        result["planet"] = planet_data
                        break
        
        return result

    # ═══════════════════════════════════════
    # Tree of Life Path Lookups
    # ═══════════════════════════════════════

    def get_tree_path(self, path_number: int) -> dict:
        """
        Get Tree of Life path data by path number (11-32).
        
        Args:
            path_number: Path number on the Tree of Life.
        
        Returns:
            Dictionary with path data (hebrew letter, connecting sephiroth, tarot card).
        """
        if not self._loaded:
            self.load()
        
        paths = self._data.get("tree_paths", {})
        key = str(path_number)
        
        if key in paths and isinstance(paths[key], dict):
            return paths[key]
        
        return {}

    def get_tree_path_for_card(self, card: TarotCard) -> dict:
        """Get the Tree of Life path for a Major Arcana card."""
        path_num = card.tree_path
        if path_num:
            return self.get_tree_path(path_num)
        return {}

    # ═══════════════════════════════════════
    # Decanate Ruler Lookups
    # ═══════════════════════════════════════

    def get_decan_ruler(self, sign: str, decan: int) -> str:
        """
        Get the planetary ruler of a specific decan.
        
        Args:
            sign: Zodiac sign name (e.g., "Aries")
            decan: Decan number (1, 2, or 3)
        
        Returns:
            Planet name that rules this decan, or empty string.
        """
        if not self._loaded:
            self.load()
        
        decans = self._data.get("decanate_rulers", {})
        key = f"{sign.lower()}_{decan}"
        
        if key in decans and isinstance(decans[key], dict):
            return str(safe_get(decans[key], "ruler", ""))
        
        return ""

    # ═══════════════════════════════════════
    # Elemental Correspondence Lookups
    # ═══════════════════════════════════════

    def get_elemental_correspondence(self, element: str) -> dict:
        """
        Get all elemental correspondences for an element.
        
        Args:
            element: Element name (fire, water, air, earth)
        
        Returns:
            Dictionary with direction, season, archangel, etc.
        """
        if not self._loaded:
            self.load()
        
        elements = self._data.get("elements", {})
        key = element.lower()
        
        if key in elements and isinstance(elements[key], dict):
            return elements[key]
        
        return {}

    # ═══════════════════════════════════════
    # Elemental Dignities
    # ═══════════════════════════════════════

    def assess_elemental_dignities(
        self, cards: list[TarotCard]
    ) -> list[dict[str, Any]]:
        """
        Assess elemental dignities between adjacent cards.
        
        The Golden Dawn system of card interaction:
        - Fire + Air = Friendly
        - Water + Earth = Friendly
        - Fire + Water = Hostile
        - Air + Earth = Hostile
        - Same element = Excessively strong (amplified)
        - Fire + Earth = Neutral
        - Water + Air = Neutral
        
        Args:
            cards: List of cards to assess (in positional order).
        
        Returns:
            List of dicts describing each adjacent pair's relationship.
        """
        if not self._loaded:
            self.load()
        
        dignities_data = self._data.get("elemental_dignities", {})
        results: list[dict[str, Any]] = []
        
        for i in range(len(cards) - 1):
            card_a = cards[i]
            card_b = cards[i + 1]
            
            elem_a = card_a.element.lower() if card_a.element else "unknown"
            elem_b = card_b.element.lower() if card_b.element else "unknown"
            
            # Normalize: extract base element from compound like "Fire of Water"
            base_a = self._extract_base_element(elem_a)
            base_b = self._extract_base_element(elem_b)
            
            # Look up the dignity
            dignity = self._lookup_dignity(base_a, base_b, dignities_data)
            
            results.append({
                "card_a": card_a.display_name,
                "card_a_reversed": card_a.is_reversed,
                "element_a": base_a,
                "card_b": card_b.display_name,
                "card_b_reversed": card_b.is_reversed,
                "element_b": base_b,
                "relationship": dignity.get("relationship", "unknown"),
                "description": dignity.get("description", "No data available."),
            })
        
        return results

    def get_elemental_balance(self, cards: list[TarotCard]) -> dict[str, int]:
        """
        Count the elemental distribution in a reading.
        
        Returns:
            Dictionary mapping element name to count.
        """
        balance: dict[str, int] = {"fire": 0, "water": 0, "air": 0, "earth": 0}
        
        for card in cards:
            base = self._extract_base_element(card.element.lower() if card.element else "")
            if base in balance:
                balance[base] += 1
        
        return balance

    def _lookup_dignity(
        self, elem_a: str, elem_b: str, dignities_data: dict
    ) -> dict:
        """Look up elemental dignity between two elements."""
        if not elem_a or not elem_b or elem_a == "unknown" or elem_b == "unknown":
            return {"relationship": "unknown", "description": "Element unknown."}
        
        # Try both orderings
        key1 = f"{elem_a}_{elem_b}"
        key2 = f"{elem_b}_{elem_a}"
        
        if key1 in dignities_data and isinstance(dignities_data[key1], dict):
            return dignities_data[key1]
        if key2 in dignities_data and isinstance(dignities_data[key2], dict):
            return dignities_data[key2]
        
        # Same element check
        if elem_a == elem_b:
            same_key = f"{elem_a}_{elem_b}"
            if same_key in dignities_data:
                return dignities_data[same_key]
            return {
                "relationship": "friendly_excess",
                "description": f"{elem_a.title()} with {elem_b.title()} — same element, excessively strong.",
            }
        
        return {"relationship": "unknown", "description": "No dignity data available."}

    @staticmethod
    def _extract_base_element(element_str: str) -> str:
        """
        Extract the base element from a potentially compound string.
        'Fire of Water' → 'fire' (the suit's primary element is the first word in GD system)
        For Minor Arcana suit cards, the suit element takes precedence.
        """
        if not element_str:
            return "unknown"
        
        # Known compound patterns from data files
        # "Fire of Mars in Aries" → fire (Wands = Fire)
        # "Water of Venus in Cancer" → water (Cups = Water)
        # "Air of Moon in Libra" → air (Swords = Air)
        # "Earth of Jupiter in Capricorn" → earth (Pentacles = Earth)
        
        first_word = element_str.split()[0].lower()
        if first_word in ("fire", "water", "air", "earth"):
            return first_word
        
        # "Pure Fire" → fire
        if "pure" in element_str.lower():
            for elem in ("fire", "water", "air", "earth"):
                if elem in element_str.lower():
                    return elem
        
        # "Elemental Air" → air
        if "elemental" in element_str.lower():
            for elem in ("fire", "water", "air", "earth"):
                if elem in element_str.lower():
                    return elem
        
        # Fallback: scan for known elements
        for elem in ("fire", "water", "air", "earth"):
            if elem in element_str.lower():
                return elem
        
        return "unknown"

    # ═══════════════════════════════════════
    # Tetragrammaton Lookups
    # ═══════════════════════════════════════

    def get_tetragrammaton(self) -> dict:
        """Get the full Tetragrammaton correspondence data."""
        if not self._loaded:
            self.load()
        return self._data.get("tetragrammaton", {})

    # ═══════════════════════════════════════
    # Color Scale Lookups
    # ═══════════════════════════════════════

    def get_color_scale_info(self) -> dict:
        """Get the GD color scale descriptions."""
        if not self._loaded:
            self.load()
        return self._data.get("color_scales", {})

    # ═══════════════════════════════════════
    # Full Correspondence Report
    # ═══════════════════════════════════════

    def generate_correspondence_report(self, card: TarotCard) -> str:
        """
        Generate a comprehensive correspondence report for a single card.
        
        Includes Hebrew letter, astrological, Tree of Life, and elemental data.
        Returns a formatted string suitable for display.
        """
        lines: list[str] = []
        lines.append(f"═══ Correspondence Report: {card.display_name} ═══")
        
        # Golden Dawn title
        gd_title = card.gd_title
        if gd_title:
            lines.append(f"GD Title: {gd_title}")
        
        # Element
        elem = card.element
        if elem:
            lines.append(f"Element: {elem}")
            elem_data = self.get_elemental_correspondence(elem.split()[0].lower())
            if elem_data:
                direction = safe_get(elem_data, "direction", "")
                archangel = safe_get(elem_data, "archangel", "")
                if direction:
                    lines.append(f"  Direction: {direction}")
                if archangel:
                    lines.append(f"  Archangel: {archangel}")
        
        # Hebrew letter (Major Arcana only)
        hebrew = card.hebrew_letter
        if hebrew:
            hebrew_data = self.get_hebrew_for_card(card)
            if hebrew_data:
                lines.append(f"Hebrew Letter: {hebrew} ({safe_get(hebrew_data, 'name', '')})")
                lines.append(f"  Meaning: {safe_get(hebrew_data, 'meaning', '')}")
                lines.append(f"  Type: {safe_get(hebrew_data, 'type', '')}")
                planet = safe_get(hebrew_data, "planet", "")
                zodiac = safe_get(hebrew_data, "zodiac", "")
                if planet:
                    lines.append(f"  Planet: {planet}")
                if zodiac:
                    lines.append(f"  Zodiac: {zodiac}")
        
        # Astrological
        astro = card.astrological
        if astro:
            lines.append(f"Astrological: {astro}")
        
        # Tree of Life (Major Arcana only)
        path_num = card.tree_path
        if path_num:
            path_data = self.get_tree_path(path_num)
            if path_data:
                lines.append(f"Tree of Life Path: {path_num}")
                lines.append(f"  Connects: {safe_get(path_data, 'connects', '')}")
        
        # GD Meaning
        gd_meaning = card.gd_meaning
        if gd_meaning:
            lines.append(f"GD Meaning: {gd_meaning}")
        
        return "\n".join(lines)

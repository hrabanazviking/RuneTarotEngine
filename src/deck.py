# RuneTarot — Deck Module
# Card and Deck classes with full 78-card Golden Dawn deck

"""
Deck management for RuneTarot.
Loads all 78 cards from YAML data files, handles shuffling and drawing.
Cards carry their own reversal state after being drawn.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from src.utils import (
    get_data_dir, safe_get, format_card_id, suit_display_name,
    court_display_name
)
from src.comprehensive_logging import get_logger

logger = get_logger("deck")


@dataclass
class TarotCard:
    """
    A single tarot card with all its data loaded from YAML.
    Cards are immutable after creation except for the _reversed flag
    which is set during drawing.
    """
    card_id: str
    suit: str
    name: str
    data: dict
    _reversed: bool = field(default=False, repr=False)

    @property
    def is_reversed(self) -> bool:
        """Whether this card was drawn reversed."""
        return self._reversed

    @property
    def display_name(self) -> str:
        """Human-readable card name."""
        return self.name

    @property
    def element(self) -> str:
        """Elemental association of this card."""
        elem = safe_get(self.data, "element", "")
        if isinstance(elem, str) and elem:
            return elem.split()[0].lower()
        return ""

    @property
    def keywords(self) -> list[str]:
        """Keywords associated with this card."""
        kw = safe_get(self.data, "keywords", [])
        if isinstance(kw, list):
            return kw
        return []

    @property
    def upright_meanings(self) -> list[str]:
        """Upright divinatory meanings."""
        meanings = safe_get(self.data, "divinatory_meaning_upright", [])
        if isinstance(meanings, list):
            return meanings
        return []

    @property
    def reversed_meanings(self) -> list[str]:
        """Reversed divinatory meanings."""
        meanings = safe_get(self.data, "divinatory_meaning_reversed", [])
        if isinstance(meanings, list):
            return meanings
        return []

    @property
    def current_meanings(self) -> list[str]:
        """Meanings based on whether the card is upright or reversed."""
        if self._reversed:
            return self.reversed_meanings
        return self.upright_meanings

    @property
    def gd_meaning(self) -> str:
        """Golden Dawn / Book T meaning."""
        return str(safe_get(self.data, "gd_meaning", ""))

    @property
    def gd_title(self) -> str:
        """Golden Dawn esoteric title."""
        return str(safe_get(self.data, "gd_title", safe_get(self.data, "esoteric_title", "")))

    @property
    def hebrew_letter(self) -> str:
        """Hebrew letter (Major Arcana only)."""
        return str(safe_get(self.data, "hebrew_letter", ""))

    @property
    def astrological(self) -> str:
        """Astrological correspondence."""
        return str(safe_get(self.data, "astrological", ""))

    @property
    def tree_path(self) -> int:
        """Tree of Life path number (Major Arcana only)."""
        val = safe_get(self.data, "tree_path", 0)
        return int(val) if val else 0

    @property
    def number(self) -> Any:
        """Card number (for numbered cards)."""
        return safe_get(self.data, "number", 0)

    def set_reversed(self, reversed: bool) -> None:
        """Set the reversal state of this card."""
        self._reversed = reversed

    def to_dict(self) -> dict:
        """Serialize card to dictionary for session storage."""
        return {
            "card_id": self.card_id,
            "suit": self.suit,
            "name": self.name,
            "reversed": self._reversed,
            "element": self.element,
        }


class TarotDeck:
    """
    The full 78-card tarot deck.
    
    Loads cards from YAML data files. Handles shuffling (Fisher-Yates by default)
    and drawing cards with optional reversals.
    """

    # Map of YAML file names to suit names
    SUIT_FILES: dict[str, str] = {
        "major_arcana": "major",
        "minor_arcana_wands": "wands",
        "minor_arcana_cups": "cups",
        "minor_arcana_swords": "swords",
        "minor_arcana_pentacles": "pentacles",
    }

    # Court card types in GD order
    COURT_TYPES: list[str] = ["knight", "queen", "prince", "princess"]

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self._data_dir = data_dir or get_data_dir()
        self._cards: list[TarotCard] = []
        self._card_index: dict[str, TarotCard] = {}
        self._loaded: bool = False

    def load_cards(self) -> list[TarotCard]:
        """
        Load all 78 cards from YAML data files.
        Returns the list of loaded TarotCard objects.
        """
        self._cards = []
        self._card_index = {}

        # Load Major Arcana
        self._load_major_arcana()

        # Load each Minor Arcana suit
        for filename, suit_name in self.SUIT_FILES.items():
            if suit_name != "major":
                self._load_minor_arcana_suit(filename, suit_name)

        # Load Court Cards
        self._load_court_cards()

        self._loaded = True
        logger.info(f"Loaded {len(self._cards)} cards into deck")
        return list(self._cards)

    def shuffle(self, seed: Optional[int] = None) -> None:
        """
        Shuffle the deck using Fisher-Yates algorithm.
        
        Args:
            seed: Optional seed for reproducible shuffles.
                  If None, uses system randomness.
        """
        if not self._loaded:
            self.load_cards()

        rng = random.Random(seed)
        rng.shuffle(self._cards)
        logger.debug("Deck shuffled")

    def draw(
        self,
        count: int = 1,
        allow_reversals: bool = True,
        seed: Optional[int] = None,
    ) -> list[TarotCard]:
        """
        Draw cards from the top of the deck.
        
        Cards are drawn from the beginning of the internal list
        (which is shuffled first if not already done).
        
        Args:
            count: Number of cards to draw.
            allow_reversals: Whether cards may be drawn reversed.
            seed: Optional seed for reversal randomization.
        
        Returns:
            List of drawn TarotCard objects.
        """
        if not self._loaded:
            self.load_cards()

        if seed is not None:
            self.shuffle(seed)

        drawn: list[TarotCard] = []
        rng = random.Random() if seed is None else random.Random(seed + 1)

        for i in range(min(count, len(self._cards))):
            card = self._cards[i]
            if allow_reversals:
                card.set_reversed(rng.choice([True, False]))
            else:
                card.set_reversed(False)
            drawn.append(card)

        logger.info(f"Drew {len(drawn)} cards (reversals={'enabled' if allow_reversals else 'disabled'})")
        return drawn

    def draw_full_hand(
        self,
        count: int = 10,
        allow_reversals: bool = True,
        seed: Optional[int] = None,
    ) -> list[TarotCard]:
        """
        Draw a full hand for a reading, shuffling first.
        
        This is the primary method used by the reading engine.
        Always shuffles the deck before drawing.
        
        Args:
            count: Number of cards to draw.
            allow_reversals: Whether cards may be drawn reversed.
            seed: Optional seed for full reproducibility.
        
        Returns:
            List of drawn TarotCard objects.
        """
        # Always shuffle before a fresh reading
        self.shuffle(seed)
        return self.draw(count, allow_reversals, seed)

    def get_card_by_id(self, card_id: str) -> Optional[TarotCard]:
        """Get a specific card by its canonical ID."""
        if not self._loaded:
            self.load_cards()
        return self._card_index.get(card_id)

    def get_all_cards(self) -> list[TarotCard]:
        """Return a copy of the full card list."""
        if not self._loaded:
            self.load_cards()
        return list(self._cards)

    def get_cards_by_suit(self, suit: str) -> list[TarotCard]:
        """Return all cards of a given suit."""
        if not self._loaded:
            self.load_cards()
        return [c for c in self._cards if c.suit.lower() == suit.lower()]

    def get_major_arcana(self) -> list[TarotCard]:
        """Return all Major Arcana cards."""
        return self.get_cards_by_suit("major")

    def count(self) -> int:
        """Return the number of cards in the deck."""
        return len(self._cards)

    # ═══════════════════════════════════════
    # Private loading methods
    # ═══════════════════════════════════════

    def _load_major_arcana(self) -> None:
        """Load the 22 Major Arcana from major_arcana.yaml."""
        filepath = self._data_dir / "major_arcana.yaml"
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading Major Arcana: {e}")
            return

        cards_data = data.get("cards", [])
        if not isinstance(cards_data, list):
            logger.error("Major Arcana data is not a list")
            return

        for card_data in cards_data:
            if not isinstance(card_data, dict):
                continue
            num = safe_get(card_data, "number", 0)
            card_id = format_card_id("major", num)
            common_name = str(safe_get(card_data, "common_name", f"Major {num}"))
            
            card = TarotCard(
                card_id=card_id,
                suit="major",
                name=common_name,
                data=card_data,
            )
            self._cards.append(card)
            self._card_index[card_id] = card

        logger.debug(f"Loaded {len(cards_data)} Major Arcana cards")

    def _load_minor_arcana_suit(self, filename: str, suit_name: str) -> None:
        """Load the numbered minor arcana (Ace-10) for one suit."""
        filepath = self._data_dir / f"{filename}.yaml"
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading {suit_name}: {e}")
            return

        cards_data = data.get("cards", {})
        if not isinstance(cards_data, dict):
            logger.error(f"Minor arcana {suit_name} data is not a dict")
            return

        for key, card_data in cards_data.items():
            if not isinstance(card_data, dict):
                continue
            num = safe_get(card_data, "number", 0)
            card_id = format_card_id(suit_name, num)
            
            # Build display name from GD title or number
            gd_title = safe_get(card_data, "gd_title", "")
            name = f"{num} of {suit_display_name(suit_name)}"
            if isinstance(gd_title, str) and gd_title:
                name = f"{num} of {suit_display_name(suit_name)} — {gd_title}"

            # Special case for Aces
            if key == "ace" or num == 1:
                name = f"Ace of {suit_display_name(suit_name)}"
                if isinstance(gd_title, str) and gd_title:
                    name = f"Ace of {suit_display_name(suit_name)} — {gd_title}"
                card_id = format_card_id(suit_name, "ace")

            card = TarotCard(
                card_id=card_id,
                suit=suit_name,
                name=name,
                data=card_data,
            )
            self._cards.append(card)
            self._card_index[card_id] = card

    def _load_court_cards(self) -> None:
        """Load the 16 Court Cards from court_cards.yaml."""
        filepath = self._data_dir / "court_cards.yaml"
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading court cards: {e}")
            return

        cards_data = data.get("court_cards", [])
        if not isinstance(cards_data, list):
            logger.error("Court cards data is not a list")
            return

        for card_data in cards_data:
            if not isinstance(card_data, dict):
                continue
            suit = str(safe_get(card_data, "suit", "unknown")).lower()
            court_type = str(safe_get(card_data, "court_type", "unknown")).lower()
            card_id = format_card_id(suit, court_type)
            common_name = str(safe_get(card_data, "common_name", f"{court_type.title()} of {suit.title()}"))

            card = TarotCard(
                card_id=card_id,
                suit=suit,
                name=common_name,
                data=card_data,
            )
            self._cards.append(card)
            self._card_index[card_id] = card

        logger.debug(f"Loaded {len(cards_data)} Court Cards")

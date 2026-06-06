# RuneTarot — Spread Module
# Spread layout definitions and card-to-position assignment

"""
Spread management for RuneTarot.
Loads spread definitions from data/spreads.yaml.
Assigns drawn cards to spread positions.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from src.deck import TarotCard
from src.utils import get_data_dir, safe_get
from src.comprehensive_logging import get_logger

logger = get_logger("spreads")


@dataclass
class SpreadPosition:
    """A single position within a spread layout."""
    number: int
    name: str
    meaning: str
    gd_meaning: str
    row: int = 0
    col: int = 0
    crosses: Optional[int] = None  # Position number this card crosses (if any)


@dataclass
class Spread:
    """A complete spread definition with all its positions."""
    name: str
    description: str
    tradition: str
    card_count: int
    positions: list[SpreadPosition]

    def get_position(self, number: int) -> Optional[SpreadPosition]:
        """Get a specific position by its number."""
        for pos in self.positions:
            if pos.number == number:
                return pos
        return None


@dataclass
class PlacedCard:
    """A card placed in a specific spread position."""
    card: TarotCard
    position: SpreadPosition

    @property
    def position_name(self) -> str:
        return self.position.name

    @property
    def card_name(self) -> str:
        suffix = " (Reversed)" if self.card.is_reversed else ""
        return f"{self.card.display_name}{suffix}"

    @property
    def element(self) -> str:
        return self.card.element


class SpreadManager:
    """
    Manages spread definitions and card-to-position assignment.
    
    Loads all spread definitions from data/spreads.yaml.
    Provides methods to list, select, and populate spreads.
    """

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self._data_dir = data_dir or get_data_dir()
        self._spreads: dict[str, Spread] = {}
        self._loaded: bool = False

    def load_spreads(self) -> dict[str, Spread]:
        """Load all spread definitions from YAML."""
        filepath = self._data_dir / "spreads.yaml"
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading spreads: {e}")
            return {}

        spreads_data = data.get("spreads", {})
        if not isinstance(spreads_data, dict):
            logger.error("Spreads data is not a dict")
            return {}

        for spread_key, spread_data in spreads_data.items():
            if not isinstance(spread_data, dict):
                continue
            spread = self._parse_spread(spread_key, spread_data)
            if spread:
                self._spreads[spread_key] = spread

        self._loaded = True
        logger.info(f"Loaded {len(self._spreads)} spread definitions")
        return dict(self._spreads)

    def get_spread(self, name: str) -> Optional[Spread]:
        """
        Get a spread by its key name.
        Supports fuzzy matching — try exact match first, then partial.
        """
        if not self._loaded:
            self.load_spreads()

        # Exact match
        if name in self._spreads:
            return self._spreads[name]

        # Partial match on key
        for key, spread in self._spreads.items():
            if key.lower() == name.lower():
                return spread

        # Partial match on display name
        for spread in self._spreads.values():
            if spread.name.lower() == name.lower():
                return spread

        # Substring match
        for key, spread in self._spreads.items():
            if name.lower() in key.lower() or name.lower() in spread.name.lower():
                return spread

        return None

    def list_spreads(self) -> list[dict[str, Any]]:
        """
        List all available spreads with summary info.
        Returns a list of dicts: [{key, name, card_count, tradition}, ...]
        """
        if not self._loaded:
            self.load_spreads()

        result = []
        for key, spread in self._spreads.items():
            result.append({
                "key": key,
                "name": spread.name,
                "card_count": spread.card_count,
                "tradition": spread.tradition,
                "description": spread.description,
            })
        return result

    def assign_cards(
        self, spread: Spread, drawn_cards: list[TarotCard]
    ) -> list[PlacedCard]:
        """
        Assign drawn cards to spread positions.
        
        Cards are assigned in order — the first card goes to position 1,
        the second to position 2, etc.
        
        Args:
            spread: The spread definition.
            drawn_cards: The cards drawn for this reading.
        
        Returns:
            List of PlacedCard objects pairing each card with its position.
        """
        placed: list[PlacedCard] = []

        for i, position in enumerate(spread.positions):
            if i < len(drawn_cards):
                placed.append(PlacedCard(
                    card=drawn_cards[i],
                    position=position,
                ))
            else:
                logger.warning(
                    f"Not enough cards for position {position.number} "
                    f"({position.name}) in {spread.name}"
                )

        logger.debug(f"Assigned {len(placed)} cards to {spread.name} positions")
        return placed

    def _parse_spread(self, key: str, data: dict) -> Optional[Spread]:
        """Parse a single spread definition from YAML data."""
        try:
            name = str(safe_get(data, "name", key.replace("_", " ").title()))
            description = str(safe_get(data, "description", ""))
            tradition = str(safe_get(data, "tradition", "Unknown"))
            card_count = int(safe_get(data, "card_count", 0))

            positions_data = safe_get(data, "positions", [])
            if not isinstance(positions_data, list):
                logger.error(f"Positions for {key} is not a list")
                return None

            positions: list[SpreadPosition] = []
            for pos_data in positions_data:
                if not isinstance(pos_data, dict):
                    continue
                pos = SpreadPosition(
                    number=int(safe_get(pos_data, "number", 0)),
                    name=str(safe_get(pos_data, "name", "")),
                    meaning=str(safe_get(pos_data, "meaning", "")),
                    gd_meaning=str(safe_get(pos_data, "gd_meaning", "")),
                    row=int(safe_get(pos_data, "row", 0)),
                    col=int(safe_get(pos_data, "col", 0)),
                    crosses=safe_get(pos_data, "crosses"),
                )
                positions.append(pos)

            return Spread(
                name=name,
                description=description,
                tradition=tradition,
                card_count=card_count,
                positions=positions,
            )

        except Exception as e:
            logger.error(f"Error parsing spread {key}: {e}")
            return None

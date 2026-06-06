# RuneTarot — Session Manager
# Reading history and session persistence

"""
Session management for RuneTarot.
Saves and loads reading history from the session/ directory.
Supports exporting readings in multiple formats.
Never modifies base data files.
"""

from __future__ import annotations

import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict

from src.deck import TarotCard
from src.spreads import PlacedCard, Spread
from src.utils import get_session_dir, get_exports_dir
from src.comprehensive_logging import get_logger

logger = get_logger("session")


@dataclass
class Reading:
    """A single tarot reading with all its data."""
    reading_id: str = ""
    timestamp: str = ""
    question: str = ""
    spread_name: str = ""
    tradition: str = ""
    cards: list[dict] = field(default_factory=list)
    reading_text: str = ""
    ai_interpretation: str = ""
    elemental_balance: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize reading to dictionary."""
        return {
            "reading_id": self.reading_id,
            "timestamp": self.timestamp,
            "question": self.question,
            "spread_name": self.spread_name,
            "tradition": self.tradition,
            "cards": self.cards,
            "reading_text": self.reading_text,
            "ai_interpretation": self.ai_interpretation,
            "elemental_balance": self.elemental_balance,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Reading":
        """Deserialize reading from dictionary."""
        return cls(
            reading_id=data.get("reading_id", ""),
            timestamp=data.get("timestamp", ""),
            question=data.get("question", ""),
            spread_name=data.get("spread_name", ""),
            tradition=data.get("tradition", ""),
            cards=data.get("cards", []),
            reading_text=data.get("reading_text", ""),
            ai_interpretation=data.get("ai_interpretation", ""),
            elemental_balance=data.get("elemental_balance", {}),
        )


class SessionManager:
    """
    The Memory Keeper — manages reading history and persistence.
    
    All session data is stored in session/ directory.
    Exports go to exports/ directory.
    Never modifies data/ files.
    """

    def __init__(self, session_dir: Optional[Path] = None) -> None:
        self._session_dir = session_dir or get_session_dir()
        self._session_dir.mkdir(parents=True, exist_ok=True)
        self._readings_index: list[dict] = []
        self._load_index()

    def save_reading(
        self,
        placed_cards: list[PlacedCard],
        reading_text: str,
        question: str = "",
        spread: Optional[Spread] = None,
        ai_interpretation: str = "",
        elemental_balance: Optional[dict] = None,
    ) -> str:
        """
        Save a reading to the session directory.
        
        Returns:
            The reading ID (used for later retrieval).
        """
        # Generate reading ID
        timestamp = datetime.now().isoformat()
        reading_id = f"reading_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Serialize card data
        cards_data: list[dict] = []
        for pc in placed_cards:
            cards_data.append({
                "card_id": pc.card.card_id,
                "name": pc.card.display_name,
                "reversed": pc.card.is_reversed,
                "element": pc.card.element,
                "position": pc.position.number,
                "position_name": pc.position.name,
            })
        
        reading = Reading(
            reading_id=reading_id,
            timestamp=timestamp,
            question=question,
            spread_name=spread.name if spread else "Custom",
            tradition=spread.tradition if spread else "",
            cards=cards_data,
            reading_text=reading_text,
            ai_interpretation=ai_interpretation,
            elemental_balance=elemental_balance or {},
        )
        
        # Save as YAML
        filepath = self._session_dir / f"{reading_id}.yaml"
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                yaml.dump(
                    reading.to_dict(),
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                )
            logger.info(f"Reading saved: {reading_id}")
        except Exception as e:
            logger.error(f"Error saving reading: {e}")
            return ""
        
        # Update index
        index_entry = {
            "reading_id": reading_id,
            "timestamp": timestamp,
            "question": question[:80],
            "spread_name": reading.spread_name,
            "card_count": len(cards_data),
        }
        self._readings_index.append(index_entry)
        self._save_index()
        
        return reading_id

    def load_reading(self, reading_id: str) -> Optional[Reading]:
        """
        Load a specific reading by its ID.
        
        Args:
            reading_id: The reading identifier.
        
        Returns:
            A Reading object, or None if not found.
        """
        filepath = self._session_dir / f"{reading_id}.yaml"
        
        if not filepath.exists():
            logger.warning(f"Reading not found: {reading_id}")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return Reading.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading reading {reading_id}: {e}")
            return None

    def list_readings(self) -> list[dict]:
        """
        List all saved readings with summary info.
        Returns most recent first.
        """
        return list(reversed(self._readings_index))

    def get_recent_readings(self, count: int = 10) -> list[dict]:
        """Get the most recent readings."""
        return self.list_readings()[:count]

    def export_reading(
        self, reading_id: str, fmt: str = "markdown"
    ) -> Optional[str]:
        """
        Export a reading to a file in the exports directory.
        
        Args:
            reading_id: The reading to export.
            fmt: Export format ("markdown", "json", "text").
        
        Returns:
            Path to the exported file, or None on failure.
        """
        reading = self.load_reading(reading_id)
        if not reading:
            return None
        
        exports_dir = get_exports_dir()
        exports_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            if fmt == "json":
                filepath = exports_dir / f"{reading_id}.json"
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(reading.to_dict(), f, indent=2, ensure_ascii=False)
            elif fmt == "text":
                filepath = exports_dir / f"{reading_id}.txt"
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(reading.reading_text)
                    if reading.ai_interpretation:
                        f.write("\n\n═══ AI Interpretation ═══\n\n")
                        f.write(reading.ai_interpretation)
            else:  # markdown (default)
                filepath = exports_dir / f"{reading_id}.md"
                content = self._format_reading_markdown(reading)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
            
            logger.info(f"Reading exported: {filepath}")
            return str(filepath)
        
        except Exception as e:
            logger.error(f"Error exporting reading: {e}")
            return None

    def clear_history(self) -> int:
        """
        Clear all reading history.
        
        Returns:
            Number of readings deleted.
        """
        count = 0
        for filepath in self._session_dir.glob("reading_*.yaml"):
            try:
                filepath.unlink()
                count += 1
            except Exception as e:
                logger.error(f"Error deleting {filepath}: {e}")
        
        self._readings_index = []
        self._save_index()
        logger.info(f"Cleared {count} readings from history")
        return count

    # ═══════════════════════════════════════
    # Private methods
    # ═══════════════════════════════════════

    def _load_index(self) -> None:
        """Load the reading index from disk."""
        index_path = self._session_dir / "readings_index.yaml"
        
        try:
            if index_path.exists():
                with open(index_path, "r", encoding="utf-8") as f:
                    self._readings_index = yaml.safe_load(f) or []
                if not isinstance(self._readings_index, list):
                    self._readings_index = []
                logger.debug(f"Loaded {len(self._readings_index)} readings from index")
            else:
                # Rebuild index from existing files
                self._rebuild_index()
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            self._readings_index = []

    def _save_index(self) -> None:
        """Save the reading index to disk."""
        index_path = self._session_dir / "readings_index.yaml"
        
        try:
            with open(index_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self._readings_index,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                )
        except Exception as e:
            logger.error(f"Error saving index: {e}")

    def _rebuild_index(self) -> None:
        """Rebuild the index from existing reading files."""
        self._readings_index = []
        
        for filepath in sorted(self._session_dir.glob("reading_*.yaml")):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                
                self._readings_index.append({
                    "reading_id": data.get("reading_id", filepath.stem),
                    "timestamp": data.get("timestamp", ""),
                    "question": str(data.get("question", ""))[:80],
                    "spread_name": data.get("spread_name", ""),
                    "card_count": len(data.get("cards", [])),
                })
            except Exception as e:
                logger.error(f"Error rebuilding index from {filepath}: {e}")
        
        self._save_index()
        logger.info(f"Rebuilt index with {len(self._readings_index)} readings")

    @staticmethod
    def _format_reading_markdown(reading: Reading) -> str:
        """Format a reading as a Markdown document."""
        lines: list[str] = []
        
        lines.append(f"# {reading.spread_name} Reading")
        lines.append("")
        lines.append(f"**Date:** {reading.timestamp}")
        if reading.question:
            lines.append(f"**Question:** {reading.question}")
        lines.append(f"**Tradition:** {reading.tradition}")
        lines.append("")
        
        # Cards
        lines.append("## Cards Drawn")
        lines.append("")
        for card_data in reading.cards:
            name = card_data.get("name", "Unknown")
            reversed_flag = card_data.get("reversed", False)
            pos_name = card_data.get("position_name", "")
            element = card_data.get("element", "")
            
            rev_str = " (Reversed)" if reversed_flag else ""
            lines.append(f"- **{pos_name}**: {name}{rev_str} [{element}]")
        lines.append("")
        
        # Reading text
        lines.append("## Interpretation")
        lines.append("")
        lines.append(reading.reading_text)
        lines.append("")
        
        # AI interpretation
        if reading.ai_interpretation:
            lines.append("## AI Deep Interpretation")
            lines.append("")
            lines.append(reading.ai_interpretation)
            lines.append("")
        
        # Elemental balance
        if reading.elemental_balance:
            lines.append("## Elemental Balance")
            lines.append("")
            for elem, count in reading.elemental_balance.items():
                lines.append(f"- {elem.title()}: {count}")
            lines.append("")
        
        return "\n".join(lines)

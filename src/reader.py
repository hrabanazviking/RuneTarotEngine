# RuneTarot — Basic Tarot Reader
# Generates divinatory readings from card meanings and positions

"""
Basic reading interpreter for RuneTarot.
Generates text readings from card positional meanings,
Golden Dawn correspondences, and elemental dignity analysis.
No AI required — this is the built-in oracle.
"""

from __future__ import annotations

from typing import Any, Optional

from src.deck import TarotCard
from src.spreads import PlacedCard, Spread
from src.golden_dawn import GoldenDawnEngine
from src.utils import safe_get
from src.comprehensive_logging import get_logger

logger = get_logger("reader")


class TarotReader:
    """
    The Oracle Voice — generates basic divinatory readings.
    
    Uses card meanings, position descriptions, and elemental dignities
    to produce a structured reading without AI assistance.
    """

    def __init__(self, gd_engine: GoldenDawnEngine) -> None:
        self._gd = gd_engine

    def interpret_card_in_position(
        self, placed: PlacedCard, context: Optional[dict] = None
    ) -> str:
        """
        Generate an interpretation for a single card in its position.
        
        Args:
            placed: The placed card with its position data.
            context: Optional context dict with neighboring cards for dignity assessment.
        
        Returns:
            A formatted interpretation string.
        """
        card = placed.card
        position = placed.position
        lines: list[str] = []
        
        # Header
        reversal_str = " (Reversed)" if card.is_reversed else ""
        lines.append(f"▸ {position.name}")
        lines.append(f"  {card.display_name}{reversal_str}")
        
        # GD Title
        gd_title = card.gd_title
        if gd_title:
            lines.append(f"  Esoteric Title: {gd_title}")
        
        # Position meaning
        lines.append(f"  Position: {position.meaning}")
        
        # Card meanings based on orientation
        meanings = card.current_meanings
        if meanings:
            orientation = "Reversed" if card.is_reversed else "Upright"
            lines.append(f"  {orientation} meanings: {', '.join(meanings[:4])}")
        
        # GD meaning
        gd_meaning = card.gd_meaning
        if gd_meaning:
            lines.append(f"  Golden Dawn: {gd_meaning}")
        
        # GD position meaning
        if position.gd_meaning:
            lines.append(f"  GD Position: {position.gd_meaning}")
        
        # Elemental info
        elem = card.element
        if elem:
            lines.append(f"  Element: {elem}")
        
        # Hebrew letter (Major Arcana)
        if card.hebrew_letter:
            hebrew_data = self._gd.get_hebrew_for_card(card)
            if hebrew_data:
                name = safe_get(hebrew_data, "name", "")
                meaning = safe_get(hebrew_data, "meaning", "")
                lines.append(f"  Hebrew: {card.hebrew_letter} ({name}) — {meaning}")
        
        # Astrological
        astro = card.astrological
        if astro:
            lines.append(f"  Astrological: {astro}")
        
        # Elemental dignity with context
        if context and "neighbor_elements" in context:
            dignity_desc = context.get("dignity_description", "")
            if dignity_desc:
                lines.append(f"  Dignity: {dignity_desc}")
        
        return "\n".join(lines)

    def generate_reading_text(
        self,
        placed_cards: list[PlacedCard],
        question: str = "",
        spread: Optional[Spread] = None,
    ) -> str:
        """
        Generate a complete reading text from all placed cards.
        
        Args:
            placed_cards: List of cards placed in positions.
            question: The querent's question (may be empty).
            spread: The spread definition (for header info).
        
        Returns:
            A formatted reading string.
        """
        lines: list[str] = []
        
        # Header
        spread_name = spread.name if spread else "Custom Spread"
        lines.append(f"╔══════════════════════════════════════╗")
        lines.append(f"║     {spread_name:^30s}     ║")
        lines.append(f"╚══════════════════════════════════════╝")
        
        if question:
            lines.append(f"")
            lines.append(f"Question: {question}")
        
        lines.append(f"")
        
        # Elemental dignities assessment
        cards = [pc.card for pc in placed_cards]
        dignities = self._gd.assess_elemental_dignities(cards)
        balance = self._gd.get_elemental_balance(cards)
        
        # Individual card interpretations
        lines.append("── The Cards ──")
        lines.append("")
        
        for i, placed in enumerate(placed_cards):
            # Build context with dignity info
            context: dict[str, Any] = {}
            if i < len(dignities):
                d = dignities[i]
                context["neighbor_elements"] = True
                context["dignity_description"] = d.get("description", "")
            
            interpretation = self.interpret_card_in_position(placed, context)
            lines.append(interpretation)
            lines.append("")
        
        # Elemental Balance
        lines.append("── Elemental Balance ──")
        lines.append("")
        for elem, count in balance.items():
            bar = "█" * count + "░" * (10 - count)
            lines.append(f"  {elem.title():8s} {bar} {count}")
        lines.append("")
        
        # Dominant element analysis
        dominant = max(balance, key=balance.get) if balance else ""
        if dominant:
            elem_info = self._gd.get_elemental_correspondence(dominant)
            if elem_info:
                lines.append(f"Dominant element: {dominant.title()}")
                direction = safe_get(elem_info, "direction", "")
                if direction:
                    lines.append(f"  Direction: {direction}")
                archangel = safe_get(elem_info, "archangel", "")
                if archangel:
                    lines.append(f"  Archangel: {archangel}")
                season = safe_get(elem_info, "season", "")
                if season:
                    lines.append(f"  Season: {season}")
        
        # Missing element analysis
        missing = [e for e, c in balance.items() if c == 0]
        if missing:
            lines.append(f"Missing element(s): {', '.join(m.title() for m in missing)}")
            lines.append(f"  This suggests areas that need attention or are underrepresented.")
        
        lines.append("")
        
        # Elemental Dignities summary
        if dignities:
            lines.append("── Card Interactions (Elemental Dignities) ──")
            lines.append("")
            for d in dignities:
                rel = d.get("relationship", "unknown")
                desc = d.get("description", "")
                card_a = d.get("card_a", "")
                card_b = d.get("card_b", "")
                lines.append(f"  {card_a} ↔ {card_b}")
                lines.append(f"    {rel}: {desc}")
                lines.append("")
        
        # Summary
        lines.append("── Synthesis ──")
        lines.append("")
        summary = self.generate_summary(placed_cards, balance, dignities)
        lines.append(summary)
        
        return "\n".join(lines)

    def generate_summary(
        self,
        placed_cards: list[PlacedCard],
        balance: dict[str, int],
        dignities: list[dict],
    ) -> str:
        """
        Generate a brief summary of the reading.
        Draws patterns from elemental balance, dignity relationships, and card keywords.
        """
        lines: list[str] = []
        
        # Collect all keywords
        all_keywords: list[str] = []
        for pc in placed_cards:
            all_keywords.extend(pc.card.keywords)
        
        # Find most common themes
        keyword_counts: dict[str, int] = {}
        for kw in all_keywords:
            kw_lower = kw.lower()
            keyword_counts[kw_lower] = keyword_counts.get(kw_lower, 0) + 1
        
        # Top themes
        top_themes = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        if top_themes:
            lines.append("Key themes: " + ", ".join(t[0] for t in top_themes))
        
        # Reversal count
        reversed_count = sum(1 for pc in placed_cards if pc.card.is_reversed)
        upright_count = len(placed_cards) - reversed_count
        
        lines.append(
            f"Orientation: {upright_count} upright, {reversed_count} reversed"
        )
        
        if reversed_count > upright_count:
            lines.append("  The prevalence of reversed cards suggests internal resistance or blocked energy.")
        elif upright_count > reversed_count:
            lines.append("  The predominance of upright cards suggests energy flowing more freely.")
        
        # Dominant element interpretation
        dominant = max(balance, key=balance.get) if balance else ""
        if dominant:
            interpretations = {
                "fire": "The reading is dominated by Fire — passion, will, and creative energy are the driving forces.",
                "water": "The reading is dominated by Water — emotion, intuition, and receptivity are the prevailing currents.",
                "air": "The reading is dominated by Air — intellect, communication, and mental clarity are the primary modes.",
                "earth": "The reading is dominated by Earth — practicality, security, and material concerns are the foundation.",
            }
            if dominant in interpretations:
                lines.append(interpretations[dominant])
        
        # Friendly vs hostile dignities
        friendly_count = sum(1 for d in dignities if "friendly" in d.get("relationship", ""))
        hostile_count = sum(1 for d in dignities if "hostile" in d.get("relationship", ""))
        
        if friendly_count > hostile_count:
            lines.append("The cards interact mostly harmoniously — forces support each other.")
        elif hostile_count > friendly_count:
            lines.append("There is significant tension between cards — opposing forces create dynamic conflict.")
        
        return "\n".join(lines)

    def assess_numerological_patterns(
        self, placed_cards: list[PlacedCard]
    ) -> dict[str, Any]:
        """
        Assess numerological patterns in the reading.
        
        Looks for repeated numbers, sequential patterns, and 
        numerological significance.
        """
        numbers: list[int] = []
        for pc in placed_cards:
            num = pc.card.number
            if isinstance(num, int) and num > 0:
                numbers.append(num)
        
        if not numbers:
            return {"pattern": "no_minor_arcana_numbers", "description": "No numbered minor arcana cards to analyze."}
        
        # Count frequencies
        freq: dict[int, int] = {}
        for n in numbers:
            freq[n] = freq.get(n, 0) + 1
        
        # Find repeated numbers
        repeated = {n: c for n, c in freq.items() if c > 1}
        
        # Check for sequences
        sorted_nums = sorted(set(numbers))
        sequences: list[list[int]] = []
        current_seq = [sorted_nums[0]] if sorted_nums else []
        
        for i in range(1, len(sorted_nums)):
            if sorted_nums[i] == sorted_nums[i - 1] + 1:
                current_seq.append(sorted_nums[i])
            else:
                if len(current_seq) >= 2:
                    sequences.append(list(current_seq))
                current_seq = [sorted_nums[i]]
        if len(current_seq) >= 2:
            sequences.append(list(current_seq))
        
        # Build result
        result: dict[str, Any] = {
            "numbers_present": numbers,
            "frequency": freq,
            "repeated_numbers": repeated,
            "sequences": sequences,
        }
        
        # Descriptions
        descs: list[str] = []
        if repeated:
            for n, c in repeated.items():
                descs.append(f"Number {n} appears {c} times — its energy is strongly emphasized.")
        if sequences:
            for seq in sequences:
                descs.append(f"Sequential pattern detected: {'-'.join(str(s) for s in seq)} — a progression of energy.")
        
        result["description"] = " ".join(descs) if descs else "No strong numerological patterns detected."
        
        return result

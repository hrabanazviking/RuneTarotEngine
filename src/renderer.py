# RuneTarot — Card Renderer
# Beautiful terminal card rendering with Unicode/ASCII art

"""
Visual rendering for RuneTarot cards.
Creates Rich-renderable card displays with element-colored frames,
suit symbols, Hebrew letters, and mini art.
"""

from __future__ import annotations

from typing import Optional

from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.box import Box, ROUNDED, HEAVY
from rich.style import Style
from rich.align import Align
from rich.columns import Columns

from src.deck import TarotCard
from src.spreads import PlacedCard, Spread
from src.golden_dawn import GoldenDawnEngine
from src.utils import (
    elemental_color, suit_symbol, suit_emoji, suit_display_name,
    court_display_name, safe_get, format_hebrew
)
from src.comprehensive_logging import get_logger

logger = get_logger("renderer")


class CardRenderer:
    """
    The Visual Skald — creates beautiful card displays for the terminal.
    
    Uses Rich library for colored, styled terminal output.
    Supports both full-size and mini card renderings.
    """

    # Element → color mapping for Rich
    ELEMENT_STYLES: dict[str, Style] = {
        "fire": Style(color="red3", bold=True),
        "water": Style(color="dodger_blue1", bold=True),
        "air": Style(color="gold1", bold=True),
        "earth": Style(color="green4", bold=True),
        "major": Style(color="medium_purple4", bold=True),
    }

    # Element → display symbols
    ELEMENT_SYMBOLS: dict[str, str] = {
        "fire": "▲",
        "water": "▽",
        "air": "◈",
        "earth": "◆",
        "major": "✦",
    }

    # Suit → glyph for card art
    SUIT_GLYPHS: dict[str, str] = {
        "wands": "⌁",
        "cups": "⋒",
        "swords": "⌖",
        "pentacles": "⊛",
        "major": "✦",
    }

    def __init__(self, gd_engine: Optional[GoldenDawnEngine] = None) -> None:
        self._gd = gd_engine or GoldenDawnEngine()

    def render_card(
        self,
        card: TarotCard,
        width: int = 20,
        height: int = 12,
        show_position: str = "",
    ) -> Panel:
        """
        Render a single card as a Rich Panel.
        
        Args:
            card: The card to render.
            width: Card width in characters.
            height: Card height in rows (approximate).
            show_position: Optional position name to display.
        
        Returns:
            A Rich Panel object containing the card display.
        """
        element = self._get_card_element(card)
        style = self.ELEMENT_STYLES.get(element, Style(color="white"))
        symbol = self.ELEMENT_SYMBOLS.get(element, "✦")
        glyph = self.SUIT_GLYPHS.get(card.suit.lower(), "✦")
        
        # Build card content
        content = Text()
        
        # Card header: number and suit glyph
        name_line = self._format_card_header(card, glyph, style)
        content.append(name_line)
        content.append("\n")
        
        # Hebrew letter (Major Arcana)
        if card.hebrew_letter:
            hebrew_text = Text()
            hebrew_text.append(f"  {card.hebrew_letter}  ", style=Style(color="bright_white", bold=True))
            content.append(hebrew_text)
            content.append("\n")
        
        # Element symbol
        symbol_text = Text()
        symbol_style = Style(color=elemental_color(element), bold=True)
        symbol_text.append(f"  {symbol}  ", style=symbol_style)
        content.append(symbol_text)
        content.append("\n")
        
        # Mini art area
        art = self._generate_mini_art(card, element)
        content.append(art)
        content.append("\n")
        
        # Card name
        name_text = Text()
        max_name_len = width - 4
        display_name = card.display_name
        if len(display_name) > max_name_len:
            display_name = display_name[:max_name_len - 2] + ".."
        name_text.append(f" {display_name} ", style=style)
        content.append(name_text)
        
        # Reversed indicator
        if card.is_reversed:
            content.append("\n")
            rev_text = Text()
            rev_text.append(" ↕ REVERSED ", style=Style(color="yellow", bold=True))
            content.append(rev_text)
        
        # Position label
        if show_position:
            content.append("\n")
            pos_text = Text()
            max_pos_len = width - 4
            pos_display = show_position
            if len(pos_display) > max_pos_len:
                pos_display = pos_display[:max_pos_len - 2] + ".."
            pos_text.append(f" {pos_display} ", style=Style(color="grey70", italic=True))
            content.append(pos_text)
        
        # Border style based on element
        border_color = elemental_color(element)
        border_style = Style(color=border_color)
        
        return Panel(
            content,
            width=width,
            border_style=border_style,
            box=HEAVY,
            padding=(0, 1),
        )

    def render_card_back(self, width: int = 20, height: int = 12) -> Panel:
        """Render the back of a card (face-down)."""
        content = Text()
        content.append("\n")
        content.append("  ✦✦✦  ", style=Style(color="medium_purple4"))
        content.append("\n\n")
        content.append("  RUNE  ", style=Style(color="grey50"))
        content.append("\n")
        content.append(" TAROT  ", style=Style(color="grey50"))
        content.append("\n\n")
        content.append("  ✦✦✦  ", style=Style(color="medium_purple4"))
        
        return Panel(
            content,
            width=width,
            border_style=Style(color="grey50"),
            box=HEAVY,
            padding=(0, 1),
        )

    def render_mini_card(self, card: TarotCard) -> Text:
        """
        Render a compact card representation for inline display.
        Returns a Text object (not a Panel).
        """
        element = self._get_card_element(card)
        style = self.ELEMENT_STYLES.get(element, Style())
        symbol = self.ELEMENT_SYMBOLS.get(element, "✦")
        
        text = Text()
        reversal = "↕" if card.is_reversed else ""
        text.append(f"{symbol}{card.display_name}{reversal}", style=style)
        
        return text

    def render_spread_visual(
        self,
        spread: Spread,
        placed_cards: list[PlacedCard],
    ) -> Table:
        """
        Render a visual representation of the spread layout.
        
        Uses a grid table to show cards in their approximate positions.
        """
        # Determine grid dimensions
        max_row = max((p.position.row for p in placed_cards), default=0)
        max_col = max((p.position.col for p in placed_cards), default=0)
        
        rows = max_row + 1
        cols = max_col + 1
        
        # Build grid
        grid: dict[tuple[int, int], PlacedCard] = {}
        for pc in placed_cards:
            key = (pc.position.row, pc.position.col)
            grid[key] = pc
        
        # Create table
        table = Table(
            show_header=False,
            show_lines=False,
            expand=True,
            box=None,
            padding=(0, 1),
        )
        
        for _ in range(cols):
            table.add_column(justify="center", width=22)
        
        for row in range(rows):
            row_cells: list[str] = []
            for col in range(cols):
                pc = grid.get((row, col))
                if pc:
                    element = self._get_card_element(pc.card)
                    symbol = self.ELEMENT_SYMBOLS.get(element, "✦")
                    rev = "↕" if pc.card.is_reversed else ""
                    
                    # Compact card display for grid
                    name = pc.card.display_name
                    if len(name) > 14:
                        name = name[:12] + ".."
                    
                    cell = f"[{elemental_color(element)}]{symbol} {name}{rev}[/{elemental_color(element)}]"
                    pos_name = pc.position.name
                    if len(pos_name) > 14:
                        pos_name = pos_name[:12] + ".."
                    cell += f"\n[dim italic]{pos_name}[/dim italic]"
                    row_cells.append(cell)
                else:
                    row_cells.append("")
            
            table.add_row(*row_cells)
        
        return table

    def render_correspondence_table(self, card: TarotCard) -> Table:
        """
        Render a table of correspondences for a card.
        """
        table = Table(
            title=f"✦ {card.display_name} — Correspondences ✦",
            show_header=True,
            box=ROUNDED,
            border_style=Style(color="medium_purple4"),
        )
        
        table.add_column("Category", style="bold")
        table.add_column("Value")
        
        # Basic info
        element = self._get_card_element(card)
        table.add_row("Element", f"[{elemental_color(element)}]{element.title()}[/{elemental_color(element)}]")
        
        # GD Title
        gd_title = card.gd_title
        if gd_title:
            table.add_row("GD Title", gd_title)
        
        # Hebrew letter
        if card.hebrew_letter:
            hebrew_data = self._gd.get_hebrew_for_card(card)
            if hebrew_data:
                name = safe_get(hebrew_data, "name", "")
                meaning = safe_get(hebrew_data, "meaning", "")
                table.add_row("Hebrew", f"{card.hebrew_letter} ({name}) — {meaning}")
                table.add_row("Letter Type", str(safe_get(hebrew_data, "type", "")))
        
        # Astrological
        astro = card.astrological
        if astro:
            table.add_row("Astrological", astro)
        
        # Tree of Life
        path_num = card.tree_path
        if path_num:
            path_data = self._gd.get_tree_path(path_num)
            if path_data:
                connects = safe_get(path_data, "connects", "")
                table.add_row("Path", f"{path_num}: {connects}")
        
        # Keywords
        if card.keywords:
            table.add_row("Keywords", ", ".join(card.keywords[:6]))
        
        # Upright meanings
        if card.upright_meanings:
            table.add_row("Upright", ", ".join(card.upright_meanings[:4]))
        
        # Reversed meanings
        if card.reversed_meanings:
            table.add_row("Reversed", ", ".join(card.reversed_meanings[:4]))
        
        return table

    # ═══════════════════════════════════════
    # Private rendering helpers
    # ═══════════════════════════════════════

    def _get_card_element(self, card: TarotCard) -> str:
        """Determine the primary element for styling a card."""
        raw = card.element.lower() if card.element else ""
        if card.suit.lower() == "major":
            return "major"
        
        # Map from suit
        suit_map = {
            "wands": "fire",
            "cups": "water",
            "swords": "air",
            "pentacles": "earth",
        }
        suit_elem = suit_map.get(card.suit.lower(), "")
        if suit_elem:
            return suit_elem
        
        # Parse from element string
        for elem in ("fire", "water", "air", "earth"):
            if elem in raw:
                return elem
        
        return "major"

    def _format_card_header(
        self, card: TarotCard, glyph: str, style: Style
    ) -> Text:
        """Format the header line of a card display."""
        text = Text()
        
        if card.suit.lower() == "major":
            # Major Arcana: show roman numeral
            num = card.number if isinstance(card.number, int) else 0
            numeral = self._to_roman(num)
            text.append(f" {numeral} {glyph} ", style=style)
        else:
            # Minor Arcana: show number/court + suit glyph
            if isinstance(card.number, int) and card.number >= 2:
                text.append(f" {card.number} {glyph} ", style=style)
            elif isinstance(card.number, int) and card.number == 1:
                text.append(f" A {glyph} ", style=style)
            else:
                # Court card
                court_type = ""
                card_data = card.data
                if isinstance(card_data, dict):
                    court_type = str(safe_get(card_data, "court_type", "")).lower()
                if court_type:
                    abbr = court_type[:2].upper()
                    text.append(f" {abbr} {glyph} ", style=style)
                else:
                    text.append(f" ? {glyph} ", style=style)
        
        return text

    def _generate_mini_art(self, card: TarotCard, element: str) -> Text:
        """Generate a simple text-art motif for the card based on its element and type."""
        text = Text()
        
        motifs = {
            "fire": [
                "    ⚡    ",
                "   🔥   ",
                "  ⌁⌁⌁  ",
            ],
            "water": [
                "  ∿∿∿∿  ",
                " ∿∿∿∿∿∿ ",
                "  ∿∿∿∿  ",
            ],
            "air": [
                "   ≋≋≋   ",
                "  ≋≋≋≋  ",
                "   ≋≋≋   ",
            ],
            "earth": [
                "   ◆◆◆   ",
                "  ◆◆◆◆  ",
                "   ◆◆◆   ",
            ],
            "major": [
                "   ✦✦✦   ",
                "  ✦✦✦✦  ",
                "   ✦✦✦   ",
            ],
        }
        
        lines = motifs.get(element, motifs["major"])
        for line in lines:
            text.append(line + "\n", style=Style(color=elemental_color(element), dim=True))
        
        return text

    @staticmethod
    def _to_roman(num: int) -> str:
        """Convert an integer to a Roman numeral string."""
        roman_map = [
            (0, "O"),
            (1, "I"),
            (2, "II"),
            (3, "III"),
            (4, "IV"),
            (5, "V"),
            (6, "VI"),
            (7, "VII"),
            (8, "VIII"),
            (9, "IX"),
            (10, "X"),
            (11, "XI"),
            (12, "XII"),
            (13, "XIII"),
            (14, "XIV"),
            (15, "XV"),
            (16, "XVI"),
            (17, "XVII"),
            (18, "XVIII"),
            (19, "XIX"),
            (20, "XX"),
            (21, "XXI"),
        ]
        
        for value, numeral in roman_map:
            if num == value:
                return numeral
        
        return str(num)

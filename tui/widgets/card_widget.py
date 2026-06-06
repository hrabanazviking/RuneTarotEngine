# RuneTarot — Card Widget
# Rich widget for displaying tarot cards in the TUI

"""
Card display widget for RuneTarot TUI.
Renders individual cards with element-colored borders and suit symbols.
"""

from __future__ import annotations

from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text
from rich.panel import Panel
from rich.style import Style

from src.deck import TarotCard
from src.renderer import CardRenderer


class CardWidget(Static):
    """
    A widget that displays a single tarot card.
    
    Supports both face-up and face-down rendering,
    with optional position label overlay.
    """

    # Reactive properties — widget updates when these change
    card: reactive[object | None] = reactive(None)  # type: ignore[assignment]
    face_down: reactive[bool] = reactive(False)  # type: ignore[assignment]
    position_label: reactive[str] = reactive("")  # type: ignore[assignment]

    def __init__(
        self,
        card: TarotCard | None = None,
        face_down: bool = False,
        position_label: str = "",
        width: int = 22,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._renderer = CardRenderer()
        self._card_width = width
        self.card = card
        self.face_down = face_down
        self.position_label = position_label

    def watch_card(self, card: TarotCard | None) -> None:
        """Called when the card property changes."""
        self._update_display()

    def watch_face_down(self, face_down: bool) -> None:
        """Called when face_down changes."""
        self._update_display()

    def watch_position_label(self, label: str) -> None:
        """Called when position_label changes."""
        self._update_display()

    def _update_display(self) -> None:
        """Update the widget's display based on current state."""
        if self.face_down or self.card is None:
            panel = self._renderer.render_card_back(
                width=self._card_width,
            )
            self.update(panel)
        else:
            panel = self._renderer.render_card(
                card=self.card,
                width=self._card_width,
                show_position=self.position_label,
            )
            self.update(panel)

    def flip(self) -> None:
        """Flip the card face-up."""
        self.face_down = False

    def reveal(self, card: TarotCard, position_label: str = "") -> None:
        """Reveal a card, setting its data and position label."""
        self.card = card
        self.position_label = position_label
        self.face_down = False

# RuneTarot — Card Library Screen
# Browse all 78 cards with GD correspondences

"""
Card library screen for RuneTarot TUI.
Allows browsing cards by category (Major Arcana, Minor Arcana by suit, Court Cards).
Shows correspondence tables and detailed card information.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Vertical, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button, Header, Footer, Label, Static, Select, Collapsible,
)
from textual.reactive import reactive
from rich.text import Text
from rich.markdown import Markdown
from rich.style import Style
from rich.panel import Panel

from src.deck import TarotCard
from src.utils import suit_display_name, elemental_color


class CardLibraryScreen(Screen):
    """Browse the complete 78-card tarot library."""

    CSS = """
    CardLibraryScreen {
        align: center top;
    }
    
    #library-container {
        align: center top;
        width: 100%;
        height: 100%;
        padding: 0 2;
    }
    
    #library-title {
        text-align: center;
        padding: 1 0;
    }
    
    #card-list {
        height: auto;
        max-height: 20;
        padding: 0 1;
    }
    
    #card-detail {
        height: auto;
        padding: 0 1;
    }
    
    #button-row {
        align: center middle;
        height: 3;
        width: 100%;
        dock: bottom;
    }
    
    .action-button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    # Currently selected card ID
    selected_card_id: reactive[str] = reactive("")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cards_by_category: dict[str, list[TarotCard]] = {}

    def on_mount(self) -> None:
        """Load card data on mount."""
        try:
            engine = self.app.engine  # type: ignore[attr-defined]
            
            # Organize cards by category
            self._cards_by_category = {
                "Major Arcana": engine.deck.get_major_arcana(),
                "Wands (Fire)": engine.deck.get_cards_by_suit("wands"),
                "Cups (Water)": engine.deck.get_cards_by_suit("cups"),
                "Swords (Air)": engine.deck.get_cards_by_suit("swords"),
                "Pentacles (Earth)": engine.deck.get_cards_by_suit("pentacles"),
            }
            
            self._build_card_options()
        except Exception:
            self._cards_by_category = {}

    def _build_card_options(self) -> None:
        """Build the card selection options from loaded data."""
        options: list[tuple[str, str]] = []
        
        for category, cards in self._cards_by_category.items():
            for card in cards:
                label = f"{category}: {card.display_name}"
                options.append((label, card.card_id))
        
        self._card_options = options

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Vertical(id="library-container"):
            yield Label(
                Text.from_markup("[bold medium_purple4]✦ Card Library ✦[/bold medium_purple4]\n[dim]78 Cards of the Golden Dawn Tarot[/dim]"),
                id="library-title",
            )
            
            yield Label("Select a card to view:")
            yield Select(
                self._card_options if hasattr(self, '_card_options') and self._card_options else [("Loading...", "")],
                id="card-select",
                prompt="Choose a card...",
            )
            
            with VerticalScroll(id="card-detail"):
                yield Static(id="card-display")
                yield Static(id="correspondence-display")

            with Horizontal(id="button-row"):
                yield Button("← Back", id="btn-back", classes="action-button")
                yield Button("🤖 AI Analysis", id="btn-ai-card", variant="primary", classes="action-button")

        yield Footer()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle card selection."""
        if event.select.id == "card-select" and event.value:
            self.selected_card_id = str(event.value)
            self._update_card_display()

    def _update_card_display(self) -> None:
        """Update the card detail display."""
        if not self.selected_card_id:
            return
        
        try:
            engine = self.app.engine  # type: ignore[attr-defined]
            details = engine.get_card_details(self.selected_card_id)
            
            if details:
                card = details["card"]
                
                # Card display
                card_display = self.query_one("#card-display", Static)
                card_render = engine.renderer.render_card(card, width=30)
                card_display.update(card_render)
                
                # Correspondence table
                corr_display = self.query_one("#correspondence-display", Static)
                corr_table = details.get("correspondence_table")
                if corr_table:
                    corr_display.update(corr_table)
                else:
                    report = details.get("correspondences", "")
                    if report:
                        corr_display.update(Markdown(report))
                    else:
                        corr_display.update(Text("No correspondence data available.", style="dim"))
            
        except Exception as e:
            try:
                display = self.query_one("#card-display", Static)
                display.update(Text.from_markup(f"[red]Error loading card: {e}[/red]"))
            except Exception:
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-ai-card":
            self._request_ai_analysis()

    def _request_ai_analysis(self) -> None:
        """Request an AI deep analysis of the selected card."""
        if not self.selected_card_id:
            self.app.notify("Please select a card first.", severity="warning")
            return
        
        try:
            engine = self.app.engine  # type: ignore[attr-defined]
            
            if not engine.is_ai_available():
                self.app.notify(
                    "No API key configured. Use Settings to set your OpenRouter API key.",
                    title="⚠ No API Key",
                    severity="warning",
                )
                return
            
            self.app.notify("Requesting AI card analysis...", title="🤖 Analyzing")
            
            analysis = engine.get_ai_interpretation(self.selected_card_id)
            
            # Update the correspondence display with AI analysis
            corr_display = self.query_one("#correspondence-display", Static)
            corr_display.update(Markdown(analysis))
            
            self.app.notify("AI analysis complete!", title="✦ Complete")
            
        except Exception as e:
            self.app.notify(f"AI analysis failed: {e}", severity="error")

    def action_go_back(self) -> None:
        """Return to main menu."""
        self.app.pop_screen()
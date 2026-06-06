# RuneTarot — Reading Display Screen
# The main reading screen where cards are drawn and interpreted

"""
Reading display screen for RuneTarot TUI.
Shows drawn cards, the basic interpretation, and optionally
the AI deep interpretation. Allows saving and exporting.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Vertical, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button, Header, Footer, Label, Static, Collapsible,
)
from textual.reactive import reactive
from rich.text import Text
from rich.markdown import Markdown
from rich.panel import Panel
from rich.style import Style

from src.deck import TarotCard
from src.spreads import PlacedCard, Spread


class ReadingScreen(Screen):
    """
    The reading display screen — shows the full tarot reading.
    
    Displays:
    - Visual card layout
    - Basic interpretation (always available)
    - AI interpretation (if API key is configured)
    - Elemental balance
    - Save/export options
    """

    CSS = """
    ReadingScreen {
        align: center top;
    }
    
    #reading-container {
        align: center top;
        width: 100%;
        height: 100%;
        padding: 0 2;
    }
    
    #reading-title {
        text-align: center;
        padding: 1 0;
    }
    
    #cards-display {
        height: auto;
        max-height: 15;
        padding: 0 0;
    }
    
    #reading-content {
        height: auto;
        padding: 1 0;
    }
    
    #ai-section {
        height: auto;
        padding: 0 0 1 0;
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
        ("s", "save_reading", "Save"),
        ("a", "request_ai", "AI Reading"),
    ]

    # Reading parameters (set before screen is pushed)
    _spread_name: str = "Celtic Cross"
    _question: str = ""
    _seed: int = 0
    
    # Reading results
    _reading_data: dict = {}
    _ai_interpretation: str = ""
    _ai_requested: bool = False

    def set_reading_params(
        self, spread_name: str = "Celtic Cross",
        question: str = "", seed: int = 0,
    ) -> None:
        """Set the reading parameters before this screen is displayed."""
        self._spread_name = spread_name
        self._question = question
        self._seed = seed

    def on_mount(self) -> None:
        """Generate the reading when screen is mounted."""
        self._generate_reading()

    def _generate_reading(self) -> None:
        """Generate the tarot reading using the engine."""
        try:
            engine = self.app.engine  # type: ignore[attr-defined]
            self._reading_data = engine.generate_reading(
                spread_name=self._spread_name,
                question=self._question,
                seed=self._seed,
            )
            self._ai_interpretation = self._reading_data.get("ai_interpretation", "")
            self._update_display()
        except Exception as e:
            self._show_error(f"Reading generation failed: {e}")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Vertical(id="reading-container"):
            yield Label(id="reading-title")
            
            with Horizontal(id="cards-display"):
                pass  # Cards will be dynamically added
            
            with VerticalScroll(id="reading-content"):
                yield Static(id="reading-text")
            
            with Vertical(id="ai-section"):
                with Collapsible(title="✦ AI Deep Interpretation ✦", id="ai-collapsible", collapsed=True):
                    yield Static(id="ai-text")
            
            with Horizontal(id="button-row"):
                yield Button("← Back", id="btn-back", classes="action-button")
                yield Button("💾 Save", id="btn-save", classes="action-button")
                yield Button("📤 Export", id="btn-export", classes="action-button")
                if not self._ai_interpretation:
                    yield Button("🤖 AI Reading", id="btn-ai", variant="primary", classes="action-button")

        yield Footer()

    def _update_display(self) -> None:
        """Update all display elements with reading data."""
        if not self._reading_data:
            return
        
        spread = self._reading_data.get("spread")
        placed_cards = self._reading_data.get("placed_cards", [])
        reading_text = self._reading_data.get("reading_text", "")
        
        # Title
        title = self.query_one("#reading-title", Label)
        spread_name = spread.name if spread else "Custom Spread"
        title.update(
            Text.from_markup(
                f"[bold medium_purple4]✦ {spread_name} ✦[/bold medium_purple4]\n"
            )
        )
        
        if self._question:
            title.update(
                Text.from_markup(
                    f"[bold medium_purple4]✦ {spread_name} ✦[/bold medium_purple4]\n"
                    f"[dim italic]Question: {self._question}[/dim italic]\n"
                )
            )
        
        # Cards display — show mini card list
        cards_display = self.query_one("#cards-display")
        # Clear existing
        for child in cards_display.children:
            child.remove()
        
        if placed_cards:
            card_lines = Text()
            for pc in placed_cards:
                elem = pc.card.element.split()[0].lower() if pc.card.element else "major"
                color_map = {"fire": "red3", "water": "dodger_blue1", "air": "gold1", "earth": "green4", "major": "medium_purple4"}
                color = color_map.get(elem, "white")
                rev = " ↕" if pc.card.is_reversed else ""
                card_lines.append(f"  {pc.position.name}: ", style="dim")
                card_lines.append(f"{pc.card.display_name}{rev}", style=Style(color=color, bold=True))
                card_lines.append("\n")
            
            cards_display.mount(Static(card_lines))

        # Reading text
        reading_static = self.query_one("#reading-text", Static)
        reading_static.update(Markdown(reading_text))

        # AI interpretation (if available)
        if self._ai_interpretation:
            ai_text = self.query_one("#ai-text", Static)
            ai_text.update(Markdown(self._ai_interpretation))
            ai_collapsible = self.query_one("#ai-collapsible", Collapsible)
            ai_collapsible.collapsed = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-save":
            self._save_reading()
        elif event.button.id == "btn-export":
            self._export_reading()
        elif event.button.id == "btn-ai":
            self._request_ai_interpretation()

    def action_go_back(self) -> None:
        """Return to spread selection."""
        self.app.pop_screen()

    def action_save_reading(self) -> None:
        """Save the current reading."""
        self._save_reading()

    def action_request_ai(self) -> None:
        """Request an AI interpretation."""
        self._request_ai_interpretation()

    def _save_reading(self) -> None:
        """Save the reading (it's already saved by the engine, but show confirmation)."""
        reading_id = self._reading_data.get("reading_id", "")
        if reading_id:
            self.app.notify(f"Reading saved: {reading_id}", title="💾 Saved")
        else:
            self.app.notify("Reading already saved.", title="💾 Saved")

    def _export_reading(self) -> None:
        """Export the reading to a file."""
        reading_id = self._reading_data.get("reading_id", "")
        if reading_id:
            try:
                engine = self.app.engine  # type: ignore[attr-defined]
                filepath = engine.session.export_reading(reading_id, "markdown")
                if filepath:
                    self.app.notify(f"Exported to: {filepath}", title="📤 Exported")
                else:
                    self.app.notify("Export failed.", title="❌ Error", severity="error")
            except Exception as e:
                self.app.notify(f"Export failed: {e}", title="❌ Error", severity="error")

    def _request_ai_interpretation(self) -> None:
        """Request an AI deep interpretation of the current reading."""
        try:
            engine = self.app.engine  # type: ignore[attr-defined]
            
            if not engine.is_ai_available():
                self.app.notify(
                    "No API key configured. Use Settings to set your OpenRouter API key.",
                    title="⚠ No API Key",
                    severity="warning",
                )
                return
            
            placed_cards = self._reading_data.get("placed_cards", [])
            spread = self._reading_data.get("spread")
            
            self.app.notify("Requesting AI interpretation...", title="🤖 AI Reading")
            
            # Generate AI interpretation
            ai_text = engine.ai_reader.generate_interpretation(
                placed_cards=placed_cards,
                question=self._question,
                spread=spread,
            )
            
            self._ai_interpretation = ai_text
            
            # Update the AI display
            ai_static = self.query_one("#ai-text", Static)
            ai_static.update(Markdown(ai_text))
            
            ai_collapsible = self.query_one("#ai-collapsible", Collapsible)
            ai_collapsible.collapsed = False
            
            # Update the reading in session
            reading_id = self._reading_data.get("reading_id", "")
            if reading_id:
                reading = engine.session.load_reading(reading_id)
                if reading:
                    reading.ai_interpretation = ai_text
                    # Re-save with AI interpretation
                    engine.session.save_reading(
                        placed_cards=placed_cards,
                        reading_text=self._reading_data.get("reading_text", ""),
                        question=self._question,
                        spread=spread,
                        ai_interpretation=ai_text,
                        elemental_balance=self._reading_data.get("elemental_balance", {}),
                    )
            
            # Remove the AI button since we now have the interpretation
            try:
                ai_btn = self.query_one("#btn-ai", Button)
                ai_btn.remove()
            except Exception:
                pass
            
            self.app.notify("AI interpretation complete!", title="✦ Complete")
            
        except Exception as e:
            self.app.notify(
                f"AI interpretation failed: {e}",
                title="❌ Error",
                severity="error",
            )

    def _show_error(self, message: str) -> None:
        """Display an error message."""
        try:
            reading_text = self.query_one("#reading-text", Static)
            reading_text.update(
                Text.from_markup(f"[bold red]Error: {message}[/bold red]")
            )
        except Exception:
            pass
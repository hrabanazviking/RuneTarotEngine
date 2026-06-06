# RuneTarot — Spread Selection Screen
# Choose a spread layout and enter a question

"""
Spread selection screen for RuneTarot TUI.
Lists all available spreads and allows the querent to enter their question.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Vertical, Horizontal
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Button, Header, Footer, Label, Input, Static, Select,
)
from textual.reactive import reactive
from rich.text import Text


class SpreadSelectScreen(Screen):
    """Choose a spread and enter your question."""

    CSS = """
    SpreadSelectScreen {
        align: center middle;
    }
    
    #spread-container {
        align: center middle;
        width: 70;
        height: auto;
        max-height: 35;
        padding: 1 2;
    }
    
    #spread-title {
        text-align: center;
        padding: 0 0 1 0;
    }
    
    #question-input {
        margin: 1 0;
    }
    
    .action-button {
        margin: 0 1;
    }
    
    #button-row {
        align: center middle;
        height: 3;
        width: 100%;
    }
    
    #spread-info {
        margin: 1 0;
        padding: 0 1;
        max-height: 6;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
    ]

    # Reactive: currently selected spread key
    selected_spread: reactive[str] = reactive("celtic_cross")

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._spreads_info: list[dict] = []

    def on_mount(self) -> None:
        """Load spread data on mount."""
        try:
            engine = self.app.engine  # type: ignore[attr-defined]
            self._spreads_info = engine.spread_manager.list_spreads()
        except Exception:
            self._spreads_info = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Center():
            with Vertical(id="spread-container"):
                yield Label(
                    Text.from_markup("[bold medium_purple4]✦ Choose Your Spread ✦[/bold medium_purple4]"),
                    id="spread-title",
                )
                
                # Build spread options
                spread_options = []
                for info in self._spreads_info or []:
                    name = info.get("name", "Unknown")
                    count = info.get("card_count", 0)
                    spread_options.append((name, name))
                
                if not spread_options:
                    spread_options = [("Celtic Cross", "Celtic Cross")]
                
                yield Select(
                    spread_options,
                    value=spread_options[0][1] if spread_options else "",
                    id="spread-select",
                    prompt="Select a spread...",
                )
                
                yield Static(id="spread-info")
                
                yield Label("Your question (optional):")
                yield Input(
                    placeholder="What guidance do you seek?",
                    id="question-input",
                )
                
                with Horizontal(id="button-row"):
                    yield Button("← Back", id="btn-back", classes="action-button")
                    yield Button("✦ Draw Cards ✦", id="btn-draw", variant="primary", classes="action-button")

        yield Footer()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle spread selection change."""
        if event.select.id == "spread-select":
            self.selected_spread = str(event.value) if event.value else ""
            self._update_spread_info()

    def _update_spread_info(self) -> None:
        """Update the spread description display."""
        info_widget = self.query_one("#spread-info", Static)
        
        for info in self._spreads_info:
            if info.get("name") == self.selected_spread:
                desc = info.get("description", "No description available.")
                count = info.get("card_count", 0)
                tradition = info.get("tradition", "")
                
                text = Text()
                text.append(f"{desc}\n", style="dim")
                text.append(f"Cards: {count}  |  Tradition: {tradition}", style="italic")
                
                info_widget.update(text)
                return
        
        info_widget.update("Select a spread to see details.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-draw":
            self._start_reading()

    def _start_reading(self) -> None:
        """Navigate to the reading screen with selected options."""
        question_input = self.query_one("#question-input", Input)
        question = question_input.value.strip()
        
        # Generate a random seed based on current time for variety
        import time
        seed = int(time.time() * 1000) % (2**31)
        
        # Pass data to the reading screen
        reading_screen = self.app.get_screen("reading")
        if hasattr(reading_screen, 'set_reading_params'):
            reading_screen.set_reading_params(
                spread_name=self.selected_spread,
                question=question,
                seed=seed,
            )
        
        self.app.push_screen("reading")

    def action_go_back(self) -> None:
        """Return to main menu."""
        self.app.pop_screen()
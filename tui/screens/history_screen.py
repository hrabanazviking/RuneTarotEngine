# RuneTarot — Reading History Screen
# View and manage saved readings

"""
Reading history screen for RuneTarot TUI.
Lists all saved readings with date, spread, and question.
Allows viewing, exporting, and clearing history.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Vertical, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button, Header, Footer, Label, Static, Select, Collapsible,
)
from rich.text import Text
from rich.markdown import Markdown
from rich.style import Style


class HistoryScreen(Screen):
    """View and manage reading history."""

    CSS = """
    HistoryScreen {
        align: center top;
    }
    
    #history-container {
        align: center top;
        width: 100%;
        height: 100%;
        padding: 0 2;
    }
    
    #history-title {
        text-align: center;
        padding: 1 0;
    }
    
    #history-list {
        height: auto;
        max-height: 10;
        padding: 0 1;
    }
    
    #history-detail {
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

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Vertical(id="history-container"):
            yield Label(
                Text.from_markup("[bold medium_purple4]✦ Reading History ✦[/bold medium_purple4]\n[dim]Your past divinations[/dim]"),
                id="history-title",
            )
            
            yield Label("Select a reading to view:")
            yield Select(
                self._get_history_options(),
                id="history-select",
                prompt="Choose a reading...",
            )
            
            with VerticalScroll(id="history-detail"):
                yield Static(id="history-display")
            
            with Horizontal(id="button-row"):
                yield Button("← Back", id="btn-back", classes="action-button")
                yield Button("📤 Export", id="btn-export", classes="action-button")
                yield Button("🗑️ Clear History", id="btn-clear", variant="error", classes="action-button")

        yield Footer()

    def _get_history_options(self) -> list[tuple[str, str]]:
        """Build options list from reading history."""
        try:
            engine = self.app.engine  # type: ignore[attr-defined]
            readings = engine.session.list_readings()
            
            options: list[tuple[str, str]] = []
            for r in readings:
                rid = r.get("reading_id", "")
                timestamp = r.get("timestamp", "")[:19].replace("T", " ")
                question = r.get("question", "No question")
                spread = r.get("spread_name", "")
                
                label = f"{timestamp} | {spread} | {question[:40]}"
                options.append((label, rid))
            
            return options if options else [("No readings yet", "")]
        except Exception:
            return [("Error loading history", "")]

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle reading selection."""
        if event.select.id == "history-select" and event.value:
            self._load_reading(str(event.value))

    def _load_reading(self, reading_id: str) -> None:
        """Load and display a saved reading."""
        if not reading_id:
            return
        
        try:
            engine = self.app.engine  # type: ignore[attr-defined]
            reading = engine.session.load_reading(reading_id)
            
            if reading:
                display = self.query_one("#history-display", Static)
                
                parts: list[str] = []
                parts.append(f"# {reading.spread_name} Reading\n")
                parts.append(f"**Date:** {reading.timestamp}\n")
                if reading.question:
                    parts.append(f"**Question:** {reading.question}\n")
                
                # Cards
                parts.append("## Cards\n")
                for c in reading.cards:
                    name = c.get("name", "Unknown")
                    rev = " ↕ Reversed" if c.get("reversed") else ""
                    pos = c.get("position_name", "")
                    parts.append(f"- **{pos}**: {name}{rev}")
                parts.append("")
                
                # Reading text
                parts.append("## Interpretation\n")
                parts.append(reading.reading_text)
                parts.append("")
                
                # AI interpretation
                if reading.ai_interpretation:
                    parts.append("## AI Deep Interpretation\n")
                    parts.append(reading.ai_interpretation)
                
                display.update(Markdown("\n".join(parts)))
            else:
                self.query_one("#history-display", Static).update(
                    Text("Reading not found.", style="dim")
                )
        except Exception as e:
            self.query_one("#history-display", Static).update(
                Text.from_markup(f"[red]Error: {e}[/red]")
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-export":
            self._export_selected()
        elif event.button.id == "btn-clear":
            self._clear_history()

    def _export_selected(self) -> None:
        """Export the currently selected reading."""
        try:
            select = self.query_one("#history-select", Select)
            if select.value:
                engine = self.app.engine  # type: ignore[attr-defined]
                filepath = engine.session.export_reading(str(select.value), "markdown")
                if filepath:
                    self.app.notify(f"Exported to: {filepath}", title="📤 Exported")
                else:
                    self.app.notify("Export failed.", severity="error")
        except Exception as e:
            self.app.notify(f"Export error: {e}", severity="error")

    def _clear_history(self) -> None:
        """Clear all reading history after confirmation."""
        try:
            engine = self.app.engine  # type: ignore[attr-defined]
            count = engine.session.clear_history()
            self.app.notify(f"Cleared {count} readings.", title="🗑️ Cleared")
            
            # Refresh the select options
            select = self.query_one("#history-select", Select)
            select.set_options(self._get_history_options())
            
            # Clear display
            self.query_one("#history-display", Static).update(
                Text("History cleared.", style="dim")
            )
        except Exception as e:
            self.app.notify(f"Error: {e}", severity="error")

    def action_go_back(self) -> None:
        """Return to main menu."""
        self.app.pop_screen()
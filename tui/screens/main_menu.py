# RuneTarot — Main Menu Screen
# The opening gateway to all features

"""
Main menu screen for RuneTarot TUI.
Provides navigation to all major features:
New Reading, Card Library, Reading History, Settings, Depart.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import Screen
from textual.widgets import Button, Header, Footer, Label
from rich.text import Text
from rich.style import Style


class MainMenuScreen(Screen):
    """The main menu — gateway to all RuneTarot features."""

    CSS = """
    MainMenuScreen {
        align: center middle;
    }
    
    #menu-title {
        text-align: center;
        padding: 1 2;
        width: 100%;
    }
    
    #menu-container {
        align: center middle;
        width: 60;
        height: auto;
        max-height: 30;
        padding: 1 2;
    }
    
    .menu-button {
        width: 100%;
        margin: 1 0;
    }
    
    .menu-button:hover {
        text-style: bold;
    }
    
    .menu-button:focus {
        text-style: bold reverse;
    }
    """

    BINDINGS = [
        ("q", "quit", "Depart"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Center():
            with Vertical(id="menu-container"):
                yield Label(
                    Text.from_markup(
                        "[bold medium_purple4]✦ RUNE TAROT ✦[/bold medium_purple4]\n"
                        "[dim]Golden Dawn Divination Engine[/dim]\n"
                    ),
                    id="menu-title",
                )
                yield Button("🔮  New Reading", id="btn-new-reading", classes="menu-button")
                yield Button("📖  Card Library", id="btn-card-library", classes="menu-button")
                yield Button("📜  Reading History", id="btn-history", classes="menu-button")
                yield Button("⚙️  Settings", id="btn-settings", classes="menu-button")
                yield Button("🚪  Depart", id="btn-depart", classes="menu-button")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle menu button presses."""
        button_id = event.button.id
        
        if button_id == "btn-new-reading":
            self.app.push_screen("spread_select")
        elif button_id == "btn-card-library":
            self.app.push_screen("card_library")
        elif button_id == "btn-history":
            self.app.push_screen("history")
        elif button_id == "btn-settings":
            self.app.push_screen("config")
        elif button_id == "btn-depart":
            self.app.action_quit()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
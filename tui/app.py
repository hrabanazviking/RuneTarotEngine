# RuneTarot — Main Textual Application
# The top-level TUI app that orchestrates all screens

"""
Main Textual application for RuneTarot.
Initializes the engine, registers all screens, and launches the TUI.
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen

from src.engine import RuneTarotEngine
from src.comprehensive_logging import setup_logging, get_logger

logger = get_logger("app")


class RuneTarotApp(App):
    """
    RuneTarot — Golden Dawn Divination Engine.
    
    A beautiful TUI tarot application built with Textual,
    rooted in the Hermetic Order of the Golden Dawn's Book T system.
    """

    TITLE = "✦ RuneTarot ✦"
    SUB_TITLE = "Golden Dawn Divination Engine"

    CSS = """
    Screen {
        background: $surface;
    }
    
    Header {
        background: $primary;
        color: $text;
    }
    
    Footer {
        background: $primary-darken-2;
    }
    
    Button {
        margin: 0 1;
    }
    
    Button:focus {
        text-style: bold;
    }
    
    Input {
        margin: 1 0;
    }
    
    Select {
        margin: 1 0;
    }
    """

    # Register all screens by name
    SCREENS: dict[str, type[Screen]] = {}

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+b", "back", "Back", show=False),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.engine = RuneTarotEngine()
        
        # Import screens here to avoid circular imports at module level
        from tui.screens.main_menu import MainMenuScreen
        from tui.screens.spread_select import SpreadSelectScreen
        from tui.screens.reading_screen import ReadingScreen
        from tui.screens.card_library import CardLibraryScreen
        from tui.screens.config_screen import ConfigScreen
        from tui.screens.history_screen import HistoryScreen
        
        self.SCREENS = {
            "main_menu": MainMenuScreen,
            "spread_select": SpreadSelectScreen,
            "reading": ReadingScreen,
            "card_library": CardLibraryScreen,
            "config": ConfigScreen,
            "history": HistoryScreen,
        }

    def on_mount(self) -> None:
        """Initialize the engine and show the main menu."""
        # Initialize the engine
        success = self.engine.initialize_subsystems()
        
        if not success:
            logger.error("Engine initialization failed!")
            self.exit(message="Failed to initialize RuneTarot engine. Check logs.")
            return
        
        logger.info("RuneTarot TUI mounted successfully")
        
        # Push the main menu screen
        self.push_screen("main_menu")

    def action_back(self) -> None:
        """Navigate back one screen."""
        if len(self.screen_stack) > 1:
            self.pop_screen()

    def action_quit(self) -> None:
        """Clean up and quit the application."""
        logger.info("RuneTarot shutting down...")
        self.exit()

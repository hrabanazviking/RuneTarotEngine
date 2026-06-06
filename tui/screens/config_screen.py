# RuneTarot — Settings/Config Screen
# Configure API key, model, reversals, and display options

"""
Settings screen for RuneTarot TUI.
Allows configuration of:
- OpenRouter API key (for AI readings)
- AI model selection
- Reversal settings
- Card ordering (GD vs RW)
- Theme and display options
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Center, Vertical, Horizontal
from textual.screen import Screen
from textual.widgets import (
    Button, Header, Footer, Label, Input, Static, Switch, Select,
)
from rich.text import Text


class ConfigScreen(Screen):
    """Settings and configuration screen."""

    CSS = """
    ConfigScreen {
        align: center middle;
    }
    
    #config-container {
        align: center middle;
        width: 70;
        height: auto;
        max-height: 35;
        padding: 1 2;
    }
    
    #config-title {
        text-align: center;
        padding: 0 0 1 0;
    }
    
    .setting-row {
        height: 3;
        padding: 0 1;
    }
    
    .setting-label {
        padding: 1 0;
    }
    
    .setting-input {
        width: 100%;
    }
    
    #api-section {
        border: round medium_purple4;
        padding: 1 2;
        margin: 1 0;
    }
    
    #display-section {
        border: round dodger_blue1;
        padding: 1 2;
        margin: 1 0;
    }
    
    #button-row {
        align: center middle;
        height: 3;
        width: 100%;
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
        
        with Center():
            with Vertical(id="config-container"):
                yield Label(
                    Text.from_markup("[bold medium_purple4]✦ Settings ✦[/bold medium_purple4]"),
                    id="config-title",
                )
                
                # API Settings Section
                yield Static(Text.from_markup("[bold medium_purple4]── AI / OpenRouter API ──[/bold medium_purple4]"), id="api-section")
                
                yield Label("API Key:", classes="setting-label")
                yield Input(
                    placeholder="sk-or-... (your OpenRouter API key)",
                    id="input-api-key",
                    password=True,
                    classes="setting-input",
                )
                
                yield Label("AI Model:", classes="setting-label")
                yield Select(
                    [
                        ("Claude Sonnet 4", "anthropic/claude-sonnet-4"),
                        ("Claude Haiku 3.5", "anthropic/claude-3-5-haiku"),
                        ("GPT-4o Mini", "openai/gpt-4o-mini"),
                        ("GPT-4o", "openai/gpt-4o"),
                        ("Llama 3.1 70B", "meta-llama/llama-3.1-70b-instruct"),
                        ("Mistral Large", "mistralai/mistral-large"),
                    ],
                    id="select-model",
                    allow_blank=False,
                )
                
                # Display Settings Section
                yield Static(Text.from_markup("[bold dodger_blue1]── Display Options ──[/bold dodger_blue1]"), id="display-section")
                
                yield Horizontal(
                    Label("Allow Reversed Cards:", classes="setting-label"),
                    Switch(id="switch-reversals", value=True),
                    classes="setting-row",
                )
                
                yield Label("Card Ordering:", classes="setting-label")
                yield Select(
                    [
                        ("Golden Dawn (Justice=8, Strength=11)", "golden_dawn"),
                        ("Rider-Waite (Justice=11, Strength=8)", "rider_waite"),
                    ],
                    id="select-ordering",
                    allow_blank=False,
                )
                
                yield Label("AI Interpretation Depth:", classes="setting-label")
                yield Select(
                    [
                        ("Brief", "brief"),
                        ("Standard", "standard"),
                        ("Full", "full"),
                    ],
                    id="select-depth",
                    allow_blank=False,
                )
                
                with Horizontal(id="button-row"):
                    yield Button("← Back", id="btn-back", classes="action-button")
                    yield Button("💾 Save", id="btn-save", variant="primary", classes="action-button")

        yield Footer()

    def on_mount(self) -> None:
        """Load current settings into the form."""
        try:
            engine = self.app.engine  # type: ignore[attr-defined]
            config = engine.config
            
            # API key (masked)
            api_key = config.get_api_key()
            api_input = self.query_one("#input-api-key", Input)
            if api_key:
                api_input.value = api_key
            
            # Reversals
            show_rev = config.get("display.show_reversals", True)
            rev_switch = self.query_one("#switch-reversals", Switch)
            rev_switch.value = show_rev
            
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.pop_screen()
        elif event.button.id == "btn-save":
            self._save_settings()

    def _save_settings(self) -> None:
        """Save all settings from the form."""
        try:
            engine = self.app.engine  # type: ignore[attr-defined]
            config = engine.config
            
            # API key
            api_input = self.query_one("#input-api-key", Input)
            new_key = api_input.value.strip()
            config.set_api_key(new_key)
            
            # Model
            model_select = self.query_one("#select-model", Select)
            if model_select.value:
                config.set("api.model", str(model_select.value))
            
            # Reversals
            rev_switch = self.query_one("#switch-reversals", Switch)
            config.set("display.show_reversals", rev_switch.value)
            
            # Ordering
            ordering_select = self.query_one("#select-ordering", Select)
            if ordering_select.value:
                config.set("tarot.ordering", str(ordering_select.value))
            
            # AI depth
            depth_select = self.query_one("#select-depth", Select)
            if depth_select.value:
                config.set("api.ai_interpretation_depth", str(depth_select.value))
            
            # Save to disk
            config.save_config()
            
            # Refresh AI reader with new settings
            engine.refresh_ai_reader()
            
            # Notify user
            if new_key:
                self.app.notify("Settings saved! AI readings are now available.", title="✦ Saved")
            else:
                self.app.notify("Settings saved. Set an API key to enable AI readings.", title="✦ Saved")
            
        except Exception as e:
            self.app.notify(f"Error saving settings: {e}", title="❌ Error", severity="error")

    def action_go_back(self) -> None:
        """Return to main menu."""
        self.app.pop_screen()
"""Modern Textual-based TUI for skill scraper."""

from typing import List, Dict, Optional
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Button, Static, DataTable, Input,
    Label, ProgressBar, Checkbox, Tree, ListView, ListItem,
    TabbedContent, TabPane, RadioSet, RadioButton, Select
)
from textual.binding import Binding
from textual.screen import Screen
from textual import events
from textual.reactive import reactive
from loguru import logger

from scraper import RepoScraper
from storage import RepoStorage
from skill_generator import SkillGenerator
from skill_detector import SkillDetector
from skill_extractor import SkillExtractor
from config import ExtractionConfig


class WelcomeScreen(Screen):
    """Welcome screen with action selection."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("1", "action_scrape", "Scrape"),
        Binding("2", "action_load", "Load"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield Container(
            Static(
                """
   ____  _    _ _ _    ____
  / ___|| | _(_) | |  / ___|  ___ _ __ __ _ _ __   ___ _ __
  \___ \| |/ / | | |  \___ \ / __| '__/ _` | '_ \ / _ \ '__|
   ___) |   <| | | |   ___) | (__| | | (_| | |_) |  __/ |
  |____/|_|\_\_|_|_|  |____/ \___|_|  \__,_| .__/ \___|_|
                                            |_|

  🚀 Scrape awesome-* lists and install Claude Code skills 🎯
                """,
                classes="banner"
            ),
            Static("What would you like to do?", classes="title"),
            Vertical(
                Button("📥 Scrape new awesome list", id="scrape", variant="primary"),
                Button("📁 Load from existing repos.json", id="load", variant="default"),
                Button("❌ Exit", id="exit", variant="error"),
                classes="button-container"
            ),
            classes="welcome-container"
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "scrape":
            self.app.push_screen(ScrapeScreen())
        elif event.button.id == "load":
            self.app.push_screen(LoadScreen())
        elif event.button.id == "exit":
            self.app.exit()

    def action_scrape(self) -> None:
        """Scrape action."""
        self.app.push_screen(ScrapeScreen())

    def action_load(self) -> None:
        """Load action."""
        self.app.push_screen(LoadScreen())


class ScrapeScreen(Screen):
    """Screen for entering GitHub URL and scraping."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield Container(
            Static("🔍 Scrape Awesome List", classes="title"),
            Label("Enter the GitHub URL of an awesome-* repository:"),
            Input(placeholder="https://github.com/...", id="github_url"),
            Checkbox("Fetch detailed descriptions (slower)", id="fetch_details"),
            Horizontal(
                Button("Start Scraping", variant="primary", id="start"),
                Button("Cancel", variant="default", id="cancel"),
                classes="button-row"
            ),
            Static(id="status"),
            classes="form-container"
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "start":
            url_input = self.query_one("#github_url", Input)
            url = url_input.value

            if not url or not url.startswith("http"):
                status = self.query_one("#status", Static)
                status.update("❌ Please enter a valid URL")
                return

            # TODO: Implement actual scraping
            status = self.query_one("#status", Static)
            status.update("🔄 Scraping in progress...")
            self.app.push_screen(WelcomeScreen())

        elif event.button.id == "cancel":
            self.app.pop_screen()

    def action_back(self) -> None:
        """Go back."""
        self.app.pop_screen()


class LoadScreen(Screen):
    """Screen for loading from storage."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        yield Container(
            Static("📁 Load from Storage", classes="title"),
            Static("Loading repositories from repos.json...", id="status"),
            Button("Continue", variant="primary", id="continue"),
            Button("Back", variant="default", id="back"),
            classes="form-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load repositories on mount."""
        storage = RepoStorage()
        if storage.exists():
            repos = storage.load_repos()
            status = self.query_one("#status", Static)
            status.update(f"✅ Loaded {len(repos)} repositories")
        else:
            status = self.query_one("#status", Static)
            status.update("❌ No repos.json file found")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "continue":
            # TODO: Navigate to repository selection
            self.app.pop_screen()
        elif event.button.id == "back":
            self.app.pop_screen()

    def action_back(self) -> None:
        """Go back."""
        self.app.pop_screen()


class SkillScraperApp(App):
    """Main Textual application for Skill Scraper."""

    CSS = """
    .banner {
        content-align: center middle;
        text-style: bold;
        color: cyan;
        margin: 1;
    }

    .title {
        content-align: center middle;
        text-style: bold;
        color: bright_cyan;
        margin: 1;
        text-size: 2;
    }

    .welcome-container {
        align: center middle;
        width: 100%;
        height: 100%;
    }

    .form-container {
        align: center middle;
        width: 80;
        height: auto;
        padding: 2;
        border: solid cyan;
    }

    .button-container {
        align: center middle;
        width: 60;
        height: auto;
    }

    .button-row {
        align: center middle;
        width: 100%;
        height: auto;
        margin: 1;
    }

    Button {
        margin: 1;
        min-width: 40;
    }

    Input {
        margin: 1;
    }

    Label {
        margin: 1;
        color: white;
    }

    Static#status {
        margin: 1;
        content-align: center middle;
        color: yellow;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("d", "toggle_dark", "Toggle Dark Mode", show=True),
    ]

    TITLE = "Skill Scraper TUI"
    SUB_TITLE = "Enhanced Terminal User Interface"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        yield WelcomeScreen()
        yield Footer()

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark


def run_tui():
    """Run the Textual TUI application."""
    app = SkillScraperApp()
    app.run()


if __name__ == "__main__":
    run_tui()

"""Terminal UI for repository selection."""

from typing import List, Dict, Optional

import questionary
from questionary import Choice
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import box
from rich.text import Text

from config import ExtractionConfig


class RepoSelector:
    """Interactive terminal UI for selecting repositories."""

    def __init__(self):
        self.console = Console()

    def select_repos(
        self,
        repos: List[Dict[str, str]],
        detection_results: Optional[Dict[str, Dict]] = None
    ) -> List[Dict[str, str]]:
        """
        Display interactive checkbox UI for repository selection.

        Args:
            repos: List of repository dictionaries
            detection_results: Optional dict mapping repo full_name to detection results

        Returns:
            List of selected repository dictionaries
        """
        if not repos:
            logger.warning("No repositories to select")
            return []

        choices = []

        for repo in repos:
            description = repo.get('description', 'No description')

            skill_indicator = ""
            if detection_results and repo['full_name'] in detection_results:
                result = detection_results[repo['full_name']]
                if result.get('is_skill_repo'):
                    skill_count = result.get('skill_count', 0)
                    confidence = result.get('confidence', 0)
                    skill_indicator = f" [🎯 ~{skill_count} skills, {confidence:.0%}]"

            combined_desc = f"{description}{skill_indicator}"
            if len(combined_desc) > 80:
                combined_desc = combined_desc[:77] + "..."

            choice_name = f"{repo['full_name']}: {combined_desc}"
            choices.append(Choice(title=choice_name, value=repo))

        self._show_repository_summary(repos, detection_results)

        self.console.print("[dim]Use arrow keys to navigate, space to select/deselect, 'a' to toggle all, enter to confirm[/dim]\n")

        selected = questionary.checkbox(
            "Select repositories to add as Claude skills:",
            choices=choices,
        ).ask()

        if selected is None:
            logger.info("Selection cancelled")
            return []

        logger.info(f"Selected {len(selected)} repositories")
        return selected

    def confirm_action(self, message: str) -> bool:
        """
        Ask for confirmation.

        Args:
            message: Confirmation message

        Returns:
            True if confirmed, False otherwise
        """
        self.console.print()  # Add spacing before prompt
        result = questionary.confirm(message).ask()
        return result if result is not None else False

    def select_action(self) -> str:
        """
        Select main action.

        Returns:
            Selected action
        """
        self.console.print()  # Add spacing before prompt
        action = questionary.select(
            "What would you like to do?",
            choices=[
                Choice("Scrape new awesome list", value="scrape"),
                Choice("Load from existing repos.json", value="load"),
                Choice("Exit", value="exit"),
            ]
        ).ask()

        return action if action is not None else "exit"

    def get_github_url(self) -> str:
        """
        Prompt for GitHub URL input.

        Returns:
            GitHub URL
        """
        self.console.print()  # Add spacing before prompt
        url = questionary.text(
            "Enter the GitHub URL of an awesome-* repository:",
            validate=lambda x: x.startswith("http") or "Please enter a valid URL"
        ).ask()

        return url if url is not None else ""

    def select_extraction_mode(self) -> ExtractionConfig:
        """
        Select extraction mode for skill repositories.

        Returns:
            ExtractionConfig with selected mode
        """
        self.console.print()  # Add spacing before prompt
        mode = questionary.select(
            "How should skill repositories be handled?",
            choices=[
                Choice(
                    "🎯 Smart Mode: Auto-detect and extract actual skills (recommended)",
                    value="both"
                ),
                Choice(
                    "📦 Extract Only: Download and install actual skills from repositories",
                    value="extract"
                ),
                Choice(
                    "📝 Metadata Only: Create reference skills pointing to repositories (fast)",
                    value="metadata"
                ),
            ]
        ).ask()

        if mode is None:
            mode = "metadata"

        config = ExtractionConfig(mode=mode)

        if mode in ["extract", "both"]:
            config.confirm_extraction = self.confirm_action(
                "Ask for confirmation before extracting skills from each repository?"
            )

        logger.info(f"Extraction mode selected: {mode}")
        return config

    def confirm_skill_extraction(
        self,
        repo: Dict[str, str],
        detection_result: Dict
    ) -> bool:
        """
        Ask for confirmation to extract skills from a specific repository.

        Args:
            repo: Repository dictionary
            detection_result: Detection result with skill count

        Returns:
            True if user confirms extraction
        """
        skill_count = detection_result.get('skill_count', 0)
        confidence = detection_result.get('confidence', 0)

        self.console.print()  # Add spacing before prompt
        message = (
            f"Extract ~{skill_count} skills from {repo['full_name']} "
            f"(confidence: {confidence:.0%})?"
        )

        return self.confirm_action(message)

    def _show_repository_summary(self, repos: List[Dict], detection_results: Optional[Dict] = None):
        """Display repository summary with Rich formatting."""
        table = Table(title=f"📦 Found {len(repos)} Repositories", box=box.ROUNDED, show_header=False)

        table.add_column("Info", style="cyan", no_wrap=False)

        if detection_results:
            skill_repos = sum(1 for r in detection_results.values() if r.get('is_skill_repo'))
            if skill_repos > 0:
                table.add_row(f"[green]🎯 Detected {skill_repos} skill repositories[/green]")

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")

    def show_summary(
        self,
        total: int,
        successful: int,
        failed: int,
        extracted: int = 0,
        extraction_mode: str = None
    ) -> None:
        """
        Display summary of skill installation with Rich formatting.

        Args:
            total: Total repositories selected
            successful: Number of successful installations
            failed: Number of failed installations
            extracted: Number of skills extracted from repositories
            extraction_mode: The extraction mode used
        """
        mode_labels = {
            "metadata": "📝 Metadata Only",
            "extract": "📦 Extract Only",
            "both": "🎯 Smart Mode (Metadata + Extract)"
        }

        table = Table(title="✨ Installation Summary", box=box.DOUBLE, show_header=True)
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Count", justify="right", style="magenta")

        table.add_row("Total selected", str(total))
        table.add_row("Successfully added", f"[green]{successful}[/green]")

        if extraction_mode and extraction_mode in ["extract", "both"]:
            table.add_row("Skills extracted", f"[yellow]{extracted}[/yellow]")

        if failed > 0:
            table.add_row("Failed", f"[red]{failed}[/red]")
        else:
            table.add_row("Failed", "0")

        if extraction_mode:
            table.add_row("Mode", mode_labels.get(extraction_mode, extraction_mode))

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")

    def show_progress(self, description: str, total: int):
        """
        Create a progress bar for long operations.

        Args:
            description: Description of the operation
            total: Total number of items to process

        Returns:
            Progress context manager
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        )

    def print_status(self, message: str, style: str = ""):
        """Print a status message with Rich formatting."""
        self.console.print(message, style=style)

    def print_panel(self, content: str, title: str = "", style: str = "cyan"):
        """Print content in a Rich panel."""
        panel = Panel(content, title=title, border_style=style, box=box.ROUNDED)
        self.console.print(panel)

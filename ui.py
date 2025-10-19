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
                Choice("Scrape new GitHub repository", value="scrape"),
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
            "Enter the GitHub repository URL (skill repo or list of repos):",
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

            install_location = self.select_installation_location()
            config.install_location = install_location

            selection_mode = self.select_selection_mode()
            config.selection_mode = selection_mode

        logger.info(f"Extraction mode selected: {mode}")
        return config

    def select_installation_location(self) -> str:
        """
        Select installation location for skills.

        Returns:
            Installation location ('local' or 'global')
        """
        self.console.print()  # Add spacing before prompt
        location = questionary.select(
            "Where should extracted skills be installed?",
            choices=[
                Choice(
                    "🌍 Global (~/.claude/skills) - Available to all Claude Code instances",
                    value="global"
                ),
                Choice(
                    "📁 Local (./.claude/skills) - Project-specific skills only",
                    value="local"
                ),
            ]
        ).ask()

        if location is None:
            location = "global"

        logger.info(f"Installation location selected: {location}")
        return location

    def select_installation_location_for_skills(self, skill_count: int) -> str:
        """
        Select installation location for selected skills.

        Args:
            skill_count: Number of skills being installed

        Returns:
            Installation location ('local' or 'global')
        """
        self.console.print()  # Add spacing before prompt
        location = questionary.select(
            f"Where should the {skill_count} selected skills be installed?",
            choices=[
                Choice(
                    "🌍 Global (~/.claude/skills) - Available to all Claude Code instances",
                    value="global"
                ),
                Choice(
                    "📁 Local (./.claude/skills) - Project-specific skills only",
                    value="local"
                ),
            ]
        ).ask()

        if location is None:
            location = "global"

        logger.info(f"Installation location selected: {location}")
        return location

    def confirm_repo_merge(self, existing_count: int) -> bool:
        """
        Ask if user wants to merge with existing repos or replace them.

        Args:
            existing_count: Number of existing repos

        Returns:
            True if user wants to merge
        """
        self.console.print()  # Add spacing before prompt
        message = (
            f"Found {existing_count} existing repositories in storage. "
            "Merge with new repos or replace completely?"
        )

        result = questionary.select(
            message,
            choices=[
                Choice("🔀 Merge - Combine with existing repos (recommended)", value=True),
                Choice("♻️  Replace - Discard existing repos", value=False),
            ]
        ).ask()

        return result if result is not None else True

    def confirm_skill_update(self) -> bool:
        """
        Ask if user wants to update existing skills.

        Returns:
            True if user wants to update existing skills
        """
        self.console.print()  # Add spacing before prompt
        result = questionary.select(
            "How should existing skills be handled?",
            choices=[
                Choice("⏭️  Skip - Keep existing skills unchanged (recommended)", value=False),
                Choice("🔄 Update - Overwrite existing skills with new versions", value=True),
            ]
        ).ask()

        return result if result is not None else False

    def select_selection_mode(self) -> str:
        """
        Select skill selection mode after extraction.

        Returns:
            Selection mode ('auto' or 'manual')
        """
        self.console.print()  # Add spacing before prompt
        mode = questionary.select(
            "How should extracted skills be selected for installation?",
            choices=[
                Choice(
                    "✋ Manual - Review and select which skills to install (recommended)",
                    value="manual"
                ),
                Choice(
                    "⚡ Auto - Automatically install all extracted skills",
                    value="auto"
                ),
            ]
        ).ask()

        if mode is None:
            mode = "manual"

        logger.info(f"Selection mode selected: {mode}")
        return mode

    def review_extracted_skills(self, staged_skills: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Display and select from extracted skills in staging.

        Args:
            staged_skills: List of skill dictionaries from staging

        Returns:
            List of selected skills to install with installation location
        """
        if not staged_skills:
            logger.warning("No staged skills to review")
            return []

        self._show_staged_skills_summary(staged_skills)

        self.console.print()
        initial_state = questionary.select(
            "How would you like to start the selection?",
            choices=[
                Choice("🔲 All Off - Start with nothing selected (recommended)", value="none"),
                Choice("☑️  All On - Start with all skills selected", value="all"),
            ]
        ).ask()

        if initial_state is None:
            logger.info("Skill selection cancelled")
            return []

        checked_defaults = [skill for skill in staged_skills] if initial_state == "all" else []

        self.console.print()
        self.console.print("[bold cyan]Skill Selection Interface[/bold cyan]")
        self.console.print("[dim]Keyboard shortcuts:[/dim]")
        self.console.print("[dim]  • Arrow keys: Navigate up/down[/dim]")
        self.console.print("[dim]  • Space: Select/deselect current skill[/dim]")
        self.console.print("[dim]  • 'a': Toggle all (invert all selections)[/dim]")
        self.console.print("[dim]  • 'i': Invert selection (swap selected/unselected)[/dim]")
        self.console.print("[dim]  • Enter: Confirm and continue[/dim]")
        self.console.print()

        choices = []
        for skill in staged_skills:
            description = skill.get('description', 'No description available')
            if len(description) > 100:
                description = description[:97] + "..."

            choice_name = f"{skill['skill_name']}\n   {description}"
            choices.append(Choice(title=choice_name, value=skill, checked=skill in checked_defaults))

        selected = questionary.checkbox(
            f"Select skills to install ({len(staged_skills)} available):",
            choices=choices,
        ).ask()

        if selected is None or len(selected) == 0:
            logger.info("No skills selected")
            return []

        self.console.print(f"\n[green]✓ {len(selected)} skills selected[/green]\n")

        install_location = self.select_installation_location_for_skills(len(selected))

        for skill in selected:
            skill['install_location'] = install_location

        logger.info(f"Selected {len(selected)} skills for installation to {install_location}")
        return selected

    def _show_staged_skills_summary(self, staged_skills: List[Dict[str, str]]):
        """Display summary of staged skills with Rich formatting."""
        table = Table(
            title=f"🎯 Extracted {len(staged_skills)} Skills - Ready for Review",
            box=box.DOUBLE,
            show_header=True
        )

        table.add_column("Skill Name", style="cyan", no_wrap=False, width=30)
        table.add_column("Description", style="white", no_wrap=False)

        for skill in staged_skills[:10]:
            skill_name = skill.get('skill_name', skill['name'])
            description = skill.get('description', 'No description available')
            if len(description) > 80:
                description = description[:77] + "..."

            table.add_row(skill_name, description)

        if len(staged_skills) > 10:
            table.add_row(
                f"[dim]... and {len(staged_skills) - 10} more[/dim]",
                "[dim]Review all in selection below[/dim]"
            )

        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")

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
        skipped: int = 0,
        extraction_mode: str = None
    ) -> None:
        """
        Display summary of skill installation with Rich formatting.

        Args:
            total: Total repositories selected
            successful: Number of successful installations
            failed: Number of failed installations
            extracted: Number of skills extracted from repositories
            skipped: Number of repositories skipped during extraction
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
            if skipped > 0:
                table.add_row("Skipped", f"[dim]{skipped}[/dim]")

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

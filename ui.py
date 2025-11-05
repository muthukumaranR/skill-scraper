"""Terminal UI for repository selection with enhanced visuals and interactivity."""

from typing import List, Dict, Optional
import time

import questionary
from questionary import Choice
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn,
    TaskProgressColumn, TimeRemainingColumn, MofNCompleteColumn
)
from rich import box
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
from rich.columns import Columns
from rich.style import Style
from rich.tree import Tree
from rich.markdown import Markdown
try:
    import pyfiglet
    PYFIGLET_AVAILABLE = True
except ImportError:
    PYFIGLET_AVAILABLE = False

from config import ExtractionConfig


class RepoSelector:
    """Interactive terminal UI for selecting repositories with enhanced visuals."""

    # Color themes for different elements
    THEME = {
        'primary': 'cyan',
        'secondary': 'magenta',
        'success': 'green',
        'warning': 'yellow',
        'error': 'red',
        'info': 'blue',
        'skill_repo': 'bright_green',
        'normal_repo': 'white',
        'highlight': 'bright_cyan',
        'dim': 'dim',
    }

    # Emoji/icon set
    ICONS = {
        'skill': '🎯',
        'repo': '📦',
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'star': '⭐',
        'download': '📥',
        'upload': '📤',
        'search': '🔍',
        'filter': '🔬',
        'rocket': '🚀',
        'sparkles': '✨',
        'gear': '⚙️',
        'folder': '📁',
        'globe': '🌍',
        'lightning': '⚡',
        'manual': '✋',
        'merge': '🔀',
        'recycle': '♻️',
        'skip': '⏭️',
        'update': '🔄',
    }

    def __init__(self):
        self.console = Console()
        self._stats = {
            'total_processed': 0,
            'success_count': 0,
            'fail_count': 0,
            'start_time': None
        }

    def select_repos(
        self,
        repos: List[Dict[str, str]],
        detection_results: Optional[Dict[str, Dict]] = None
    ) -> List[Dict[str, str]]:
        """
        Display interactive checkbox UI for repository selection with enhanced visuals.

        Args:
            repos: List of repository dictionaries
            detection_results: Optional dict mapping repo full_name to detection results

        Returns:
            List of selected repository dictionaries
        """
        if not repos:
            logger.warning("No repositories to select")
            return []

        # Show enhanced repository summary
        self._show_enhanced_repository_summary(repos, detection_results)

        # Add search option
        if len(repos) > 10:
            search = questionary.confirm(
                f"{self.ICONS['search']} Would you like to filter repositories? (You can search by name or description)"
            ).ask()

            if search:
                repos = self._filter_repos(repos)
                if not repos:
                    self.console.print(f"\n[{self.THEME['warning']}]{self.ICONS['warning']} No repositories match your filter[/{self.THEME['warning']}]")
                    return []

        # Sort repos - skill repos first
        sorted_repos = sorted(
            repos,
            key=lambda r: (
                -1 if detection_results and detection_results.get(r['full_name'], {}).get('is_skill_repo') else 0,
                r['full_name'].lower()
            )
        )

        choices = []
        for repo in sorted_repos:
            description = repo.get('description', 'No description')

            skill_indicator = ""
            icon = self.ICONS['repo']
            style = self.THEME['normal_repo']

            if detection_results and repo['full_name'] in detection_results:
                result = detection_results[repo['full_name']]
                if result.get('is_skill_repo'):
                    skill_count = result.get('skill_count', 0)
                    confidence = result.get('confidence', 0)
                    icon = self.ICONS['skill']
                    style = self.THEME['skill_repo']
                    skill_indicator = f" [{style}][~{skill_count} skills, {confidence:.0%}][/{style}]"

            combined_desc = f"{description}{skill_indicator}"
            if len(combined_desc) > 90:
                combined_desc = combined_desc[:87] + "..."

            choice_name = f"{icon} {repo['full_name']}: {combined_desc}"
            choices.append(Choice(title=choice_name, value=repo))

        # Show keyboard shortcuts
        self._show_keyboard_hints()

        selected = questionary.checkbox(
            f"{self.ICONS['sparkles']} Select repositories to add as Claude skills:",
            choices=choices,
        ).ask()

        if selected is None:
            logger.info("Selection cancelled")
            return []

        # Show selection summary
        self._show_selection_preview(selected, detection_results)

        logger.info(f"Selected {len(selected)} repositories")
        return selected

    def _filter_repos(self, repos: List[Dict]) -> List[Dict]:
        """Filter repositories by search term."""
        search_term = questionary.text(
            f"{self.ICONS['search']} Enter search term (name or description):"
        ).ask()

        if not search_term:
            return repos

        search_lower = search_term.lower()
        filtered = [
            repo for repo in repos
            if search_lower in repo['full_name'].lower() or
               search_lower in repo.get('description', '').lower()
        ]

        self.console.print(
            f"\n[{self.THEME['info']}]{self.ICONS['filter']} Found {len(filtered)} repositories matching '{search_term}'[/{self.THEME['info']}]\n"
        )

        return filtered

    def _show_keyboard_hints(self):
        """Display keyboard shortcuts in a nice format."""
        hints = Table.grid(padding=(0, 2))
        hints.add_column(style=self.THEME['dim'])
        hints.add_column(style=self.THEME['highlight'])

        hints.add_row("↑↓", "Navigate")
        hints.add_row("Space", "Select/Deselect")
        hints.add_row("a", "Toggle All")
        hints.add_row("Enter", "Confirm")

        panel = Panel(
            hints,
            title=f"{self.ICONS['gear']} Keyboard Shortcuts",
            border_style=self.THEME['dim'],
            box=box.ROUNDED,
            padding=(0, 2)
        )
        self.console.print(panel)
        self.console.print()

    def _show_selection_preview(self, selected: List[Dict], detection_results: Optional[Dict] = None):
        """Show a preview of selected repositories."""
        if not selected:
            return

        skill_count = 0
        if detection_results:
            skill_count = sum(
                1 for repo in selected
                if detection_results.get(repo['full_name'], {}).get('is_skill_repo')
            )

        preview = Table(box=box.ROUNDED, show_header=False, border_style=self.THEME['success'])
        preview.add_column("Info", style=self.THEME['success'])

        preview.add_row(f"{self.ICONS['success']} Selected: {len(selected)} repositories")
        if skill_count > 0:
            preview.add_row(f"{self.ICONS['skill']} Skill repositories: {skill_count}")
            preview.add_row(f"{self.ICONS['repo']} Regular repositories: {len(selected) - skill_count}")

        self.console.print()
        self.console.print(preview)
        self.console.print()

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
        Select main action with enhanced visuals.

        Returns:
            Selected action
        """
        self.console.print()  # Add spacing before prompt
        action = questionary.select(
            f"{self.ICONS['rocket']} What would you like to do?",
            choices=[
                Choice(f"{self.ICONS['download']} Scrape new awesome list", value="scrape"),
                Choice(f"{self.ICONS['folder']} Load from existing repos.json", value="load"),
                Choice(f"{self.ICONS['error']} Exit", value="exit"),
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
        Select extraction mode for skill repositories with enhanced descriptions.

        Returns:
            ExtractionConfig with selected mode
        """
        self.console.print()  # Add spacing before prompt

        # Show mode comparison table
        self._show_mode_comparison()

        mode = questionary.select(
            f"{self.ICONS['gear']} How should skill repositories be handled?",
            choices=[
                Choice(
                    f"{self.ICONS['skill']} Smart Mode: Auto-detect and extract actual skills (recommended)",
                    value="both"
                ),
                Choice(
                    f"{self.ICONS['repo']} Extract Only: Download and install actual skills from repositories",
                    value="extract"
                ),
                Choice(
                    f"{self.ICONS['lightning']} Metadata Only: Create reference skills pointing to repositories (fast)",
                    value="metadata"
                ),
            ]
        ).ask()

        if mode is None:
            mode = "metadata"

        config = ExtractionConfig(mode=mode)

        if mode in ["extract", "both"]:
            config.confirm_extraction = self.confirm_action(
                f"{self.ICONS['info']} Ask for confirmation before extracting skills from each repository?"
            )

            install_location = self.select_installation_location()
            config.install_location = install_location

            selection_mode = self.select_selection_mode()
            config.selection_mode = selection_mode

        logger.info(f"Extraction mode selected: {mode}")
        return config

    def _show_mode_comparison(self):
        """Display a comparison table of extraction modes."""
        table = Table(
            title=f"{self.ICONS['info']} Extraction Mode Comparison",
            box=box.ROUNDED,
            show_header=True,
            border_style=self.THEME['info']
        )

        table.add_column("Mode", style=self.THEME['highlight'], no_wrap=True)
        table.add_column("Speed", justify="center")
        table.add_column("Thoroughness", justify="center")
        table.add_column("Best For")

        table.add_row(
            f"{self.ICONS['skill']} Smart",
            "[green]Medium[/green]",
            "[green]High[/green]",
            "Balanced approach (recommended)"
        )
        table.add_row(
            f"{self.ICONS['repo']} Extract",
            "[yellow]Slow[/yellow]",
            "[green]Highest[/green]",
            "When you know repos contain skills"
        )
        table.add_row(
            f"{self.ICONS['lightning']} Metadata",
            "[green]Fast[/green]",
            "[yellow]Low[/yellow]",
            "Quick exploration or manual control"
        )

        self.console.print()
        self.console.print(table)
        self.console.print()

    def select_installation_location(self) -> str:
        """
        Select installation location for skills with enhanced visuals.

        Returns:
            Installation location ('local' or 'global')
        """
        self.console.print()  # Add spacing before prompt
        location = questionary.select(
            f"{self.ICONS['folder']} Where should extracted skills be installed?",
            choices=[
                Choice(
                    f"{self.ICONS['globe']} Global (~/.claude/skills) - Available to all Claude Code instances",
                    value="global"
                ),
                Choice(
                    f"{self.ICONS['folder']} Local (./.claude/skills) - Project-specific skills only",
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

        # Show info panel
        info = f"[{self.THEME['info']}]{self.ICONS['info']} Found {existing_count} existing repositories in storage[/{self.THEME['info']}]"
        self.console.print(Panel(info, box=box.ROUNDED, border_style=self.THEME['info']))

        result = questionary.select(
            f"{self.ICONS['gear']} How should new repositories be combined with existing ones?",
            choices=[
                Choice(f"{self.ICONS['merge']} Merge - Combine with existing repos (recommended)", value=True),
                Choice(f"{self.ICONS['recycle']} Replace - Discard existing repos", value=False),
            ]
        ).ask()

        return result if result is not None else True

    def confirm_skill_update(self) -> bool:
        """
        Ask if user wants to update existing skills with enhanced visuals.

        Returns:
            True if user wants to update existing skills
        """
        self.console.print()  # Add spacing before prompt
        result = questionary.select(
            f"{self.ICONS['gear']} How should existing skills be handled?",
            choices=[
                Choice(f"{self.ICONS['skip']} Skip - Keep existing skills unchanged (recommended)", value=False),
                Choice(f"{self.ICONS['update']} Update - Overwrite existing skills with new versions", value=True),
            ]
        ).ask()

        return result if result is not None else False

    def select_selection_mode(self) -> str:
        """
        Select skill selection mode after extraction with enhanced visuals.

        Returns:
            Selection mode ('auto' or 'manual')
        """
        self.console.print()  # Add spacing before prompt
        mode = questionary.select(
            f"{self.ICONS['gear']} How should extracted skills be selected for installation?",
            choices=[
                Choice(
                    f"{self.ICONS['manual']} Manual - Review and select which skills to install (recommended)",
                    value="manual"
                ),
                Choice(
                    f"{self.ICONS['lightning']} Auto - Automatically install all extracted skills",
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
        Display and select from extracted skills in staging with enhanced visuals.

        Args:
            staged_skills: List of skill dictionaries from staging

        Returns:
            List of selected skills to install
        """
        if not staged_skills:
            logger.warning("No staged skills to review")
            return []

        self._show_staged_skills_summary(staged_skills)

        # Add search option for many skills
        search_skills = staged_skills
        if len(staged_skills) > 20:
            if questionary.confirm(
                f"{self.ICONS['search']} Would you like to filter skills?"
            ).ask():
                search_term = questionary.text(
                    f"{self.ICONS['search']} Enter search term (name or description):"
                ).ask()
                if search_term:
                    search_lower = search_term.lower()
                    search_skills = [
                        skill for skill in staged_skills
                        if search_lower in skill.get('skill_name', '').lower() or
                           search_lower in skill.get('description', '').lower()
                    ]
                    self.console.print(
                        f"\n[{self.THEME['info']}]{self.ICONS['filter']} Found {len(search_skills)} skills matching '{search_term}'[/{self.THEME['info']}]\n"
                    )

        # Show keyboard shortcuts
        self._show_keyboard_hints()

        choices = []
        for skill in search_skills:
            description = skill.get('description', 'No description available')
            if len(description) > 100:
                description = description[:97] + "..."

            skill_name = skill.get('skill_name', skill.get('name', 'Unknown'))
            choice_name = f"{self.ICONS['skill']} {skill_name}\n   [dim]{description}[/dim]"
            choices.append(Choice(title=choice_name, value=skill))

        selected = questionary.checkbox(
            f"{self.ICONS['sparkles']} Select skills to install ({len(search_skills)} available):",
            choices=choices,
        ).ask()

        if selected is None:
            logger.info("Skill selection cancelled")
            return []

        # Show selection summary
        if selected:
            summary = f"[{self.THEME['success']}]{self.ICONS['success']} Selected {len(selected)} skills for installation[/{self.THEME['success']}]"
            self.console.print()
            self.console.print(Panel(summary, box=box.ROUNDED, border_style=self.THEME['success']))

        logger.info(f"Selected {len(selected)} skills for installation")
        return selected

    def _show_staged_skills_summary(self, staged_skills: List[Dict[str, str]]):
        """Display summary of staged skills with enhanced Rich formatting."""
        table = Table(
            title=f"{self.ICONS['skill']} Extracted {len(staged_skills)} Skills - Ready for Review",
            box=box.DOUBLE,
            show_header=True,
            border_style=self.THEME['skill_repo']
        )

        table.add_column("Skill Name", style=self.THEME['highlight'], no_wrap=False, width=35)
        table.add_column("Description", style=self.THEME['normal_repo'], no_wrap=False)
        table.add_column("Source", style=self.THEME['dim'], no_wrap=True, width=20)

        for skill in staged_skills[:12]:
            skill_name = skill.get('skill_name', skill.get('name', 'Unknown'))
            description = skill.get('description', 'No description available')
            source = skill.get('source_repo', 'Unknown')

            if len(description) > 60:
                description = description[:57] + "..."
            if len(source) > 18:
                source = source[:15] + "..."

            table.add_row(
                f"{self.ICONS['skill']} {skill_name}",
                description,
                source
            )

        if len(staged_skills) > 12:
            table.add_row(
                f"[{self.THEME['dim']}]... and {len(staged_skills) - 12} more[/{self.THEME['dim']}]",
                f"[{self.THEME['dim']}]Review all in selection below[/{self.THEME['dim']}]",
                ""
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

    def _show_enhanced_repository_summary(self, repos: List[Dict], detection_results: Optional[Dict] = None):
        """Display enhanced repository summary with Rich formatting and statistics."""

        # Create a detailed statistics table
        stats_table = Table(
            title=f"{self.ICONS['repo']} Repository Overview",
            box=box.DOUBLE_EDGE,
            show_header=True,
            border_style=self.THEME['primary']
        )

        stats_table.add_column("Metric", style=self.THEME['highlight'], no_wrap=True)
        stats_table.add_column("Count", justify="right", style=self.THEME['success'], no_wrap=True)
        stats_table.add_column("Details", style=self.THEME['dim'])

        stats_table.add_row(
            f"{self.ICONS['repo']} Total Repositories",
            str(len(repos)),
            "Ready for selection"
        )

        if detection_results:
            skill_repos = sum(1 for r in detection_results.values() if r.get('is_skill_repo'))
            regular_repos = len(repos) - skill_repos

            if skill_repos > 0:
                stats_table.add_row(
                    f"{self.ICONS['skill']} Skill Repositories",
                    str(skill_repos),
                    "Contains actual skills"
                )
                stats_table.add_row(
                    f"{self.ICONS['repo']} Regular Repositories",
                    str(regular_repos),
                    "Will create metadata skills"
                )

                # Calculate total estimated skills
                total_skills = sum(
                    r.get('skill_count', 0)
                    for r in detection_results.values()
                    if r.get('is_skill_repo')
                )
                if total_skills > 0:
                    stats_table.add_row(
                        f"{self.ICONS['sparkles']} Estimated Total Skills",
                        f"~{total_skills}",
                        "From skill repositories"
                    )

        # Show top repositories preview
        preview_table = Table(
            title=f"{self.ICONS['star']} Top Repositories Preview",
            box=box.ROUNDED,
            show_header=True,
            border_style=self.THEME['secondary']
        )

        preview_table.add_column("Repository", style=self.THEME['highlight'], no_wrap=False, width=30)
        preview_table.add_column("Type", style=self.THEME['info'], justify="center", width=10)
        preview_table.add_column("Description", style=self.THEME['normal_repo'], no_wrap=False)

        # Sort by skill repos first
        sorted_repos = sorted(
            repos[:8],
            key=lambda r: (
                -1 if detection_results and detection_results.get(r['full_name'], {}).get('is_skill_repo') else 0,
                r['full_name'].lower()
            )
        )

        for repo in sorted_repos:
            repo_type = self.ICONS['repo']
            type_label = "Regular"

            if detection_results and repo['full_name'] in detection_results:
                result = detection_results[repo['full_name']]
                if result.get('is_skill_repo'):
                    repo_type = self.ICONS['skill']
                    skill_count = result.get('skill_count', 0)
                    type_label = f"~{skill_count} skills"

            description = repo.get('description', 'No description')
            if len(description) > 50:
                description = description[:47] + "..."

            preview_table.add_row(
                f"{repo_type} {repo['full_name']}",
                type_label,
                description
            )

        if len(repos) > 8:
            preview_table.add_row(
                f"[{self.THEME['dim']}]... and {len(repos) - 8} more[/{self.THEME['dim']}]",
                "",
                ""
            )

        self.console.print("\n")
        self.console.print(stats_table)
        self.console.print("\n")
        self.console.print(preview_table)
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
        Display enhanced summary of skill installation with Rich formatting and statistics.

        Args:
            total: Total repositories selected
            successful: Number of successful installations
            failed: Number of failed installations
            extracted: Number of skills extracted from repositories
            extraction_mode: The extraction mode used
        """
        mode_labels = {
            "metadata": f"{self.ICONS['lightning']} Metadata Only",
            "extract": f"{self.ICONS['repo']} Extract Only",
            "both": f"{self.ICONS['skill']} Smart Mode (Metadata + Extract)"
        }

        # Create main summary table
        table = Table(
            title=f"{self.ICONS['sparkles']} Installation Summary {self.ICONS['sparkles']}",
            box=box.DOUBLE,
            show_header=True,
            border_style=self.THEME['primary']
        )
        table.add_column("Metric", style=self.THEME['highlight'], no_wrap=True, width=25)
        table.add_column("Count", justify="right", style=self.THEME['secondary'], width=12)
        table.add_column("Status", style=self.THEME['dim'], width=20)

        # Calculate success rate
        success_rate = (successful / total * 100) if total > 0 else 0

        table.add_row(
            f"{self.ICONS['repo']} Total Selected",
            str(total),
            "Repositories"
        )

        success_color = self.THEME['success'] if success_rate >= 90 else self.THEME['warning']
        table.add_row(
            f"{self.ICONS['success']} Successfully Added",
            f"[{success_color}]{successful}[/{success_color}]",
            f"[{success_color}]{success_rate:.1f}% success rate[/{success_color}]"
        )

        if extraction_mode and extraction_mode in ["extract", "both"] and extracted > 0:
            table.add_row(
                f"{self.ICONS['download']} Skills Extracted",
                f"[{self.THEME['info']}]{extracted}[/{self.THEME['info']}]",
                "Actual skill files"
            )

        if failed > 0:
            table.add_row(
                f"{self.ICONS['error']} Failed",
                f"[{self.THEME['error']}]{failed}[/{self.THEME['error']}]",
                "Check logs for details"
            )
        else:
            table.add_row(
                f"{self.ICONS['success']} Failed",
                f"[{self.THEME['success']}]0[/{self.THEME['success']}]",
                "Perfect!"
            )

        if extraction_mode:
            mode_label = mode_labels.get(extraction_mode, extraction_mode)
            table.add_row(
                f"{self.ICONS['gear']} Extraction Mode",
                mode_label,
                ""
            )

        # Create completion message
        completion_msg = Text()
        if failed == 0:
            completion_msg.append(f"\n{self.ICONS['success']} All operations completed successfully! ", style=f"bold {self.THEME['success']}")
            completion_msg.append(f"{self.ICONS['sparkles']}", style=self.THEME['success'])
        else:
            completion_msg.append(f"\n{self.ICONS['warning']} Completed with some errors. ", style=f"bold {self.THEME['warning']}")
            completion_msg.append("Check logs for details.", style=self.THEME['dim'])

        self.console.print("\n")
        self.console.print("=" * 80)
        self.console.print(table)
        self.console.print(Align.center(completion_msg))
        self.console.print("=" * 80)
        self.console.print("\n")

    def show_progress(self, description: str, total: int):
        """
        Create an enhanced progress bar for long operations with better visuals.

        Args:
            description: Description of the operation
            total: Total number of items to process

        Returns:
            Progress context manager
        """
        return Progress(
            SpinnerColumn(spinner_name="dots12", style=self.THEME['primary']),
            TextColumn("[bold {color}]{task.description}".format(color=self.THEME['highlight'])),
            BarColumn(
                complete_style=self.THEME['success'],
                finished_style=self.THEME['skill_repo'],
                pulse_style=self.THEME['info']
            ),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
            expand=False
        )

    def print_status(self, message: str, style: str = ""):
        """Print a status message with enhanced Rich formatting."""
        self.console.print(message, style=style)

    def print_panel(self, content: str, title: str = "", style: str = "cyan"):
        """Print content in an enhanced Rich panel."""
        panel = Panel(
            content,
            title=title,
            border_style=style,
            box=box.DOUBLE if title else box.ROUNDED,
            padding=(1, 2)
        )
        self.console.print(panel)

    def show_error(self, message: str, details: str = ""):
        """Display an error message with helpful context."""
        error_panel = Panel(
            f"[{self.THEME['error']}]{self.ICONS['error']} {message}[/{self.THEME['error']}]\n\n"
            f"[{self.THEME['dim']}]{details}[/{self.THEME['dim']}]" if details else
            f"[{self.THEME['error']}]{self.ICONS['error']} {message}[/{self.THEME['error']}]",
            title=f"{self.ICONS['error']} Error",
            border_style=self.THEME['error'],
            box=box.HEAVY
        )
        self.console.print()
        self.console.print(error_panel)
        self.console.print()

    def show_info(self, message: str, title: str = "Info"):
        """Display an info message in a nice format."""
        info_panel = Panel(
            f"[{self.THEME['info']}]{self.ICONS['info']} {message}[/{self.THEME['info']}]",
            title=f"{self.ICONS['info']} {title}",
            border_style=self.THEME['info'],
            box=box.ROUNDED
        )
        self.console.print()
        self.console.print(info_panel)
        self.console.print()

    def show_success(self, message: str):
        """Display a success message."""
        success_text = Text()
        success_text.append(f"{self.ICONS['success']} {message}", style=f"bold {self.THEME['success']}")
        self.console.print()
        self.console.print(Align.center(success_text))
        self.console.print()

    def show_tips(self):
        """Display helpful tips for using the tool."""
        tips = [
            f"{self.ICONS['info']} Use the search feature to quickly find specific repositories",
            f"{self.ICONS['skill']} Skill repositories are automatically sorted to the top",
            f"{self.ICONS['lightning']} Metadata mode is fastest for quick exploration",
            f"{self.ICONS['gear']} Smart mode balances speed and thoroughness (recommended)",
        ]

        tips_table = Table(
            title=f"{self.ICONS['sparkles']} Pro Tips",
            box=box.ROUNDED,
            show_header=False,
            border_style=self.THEME['info'],
            padding=(0, 1)
        )
        tips_table.add_column("Tip", style=self.THEME['info'])

        for tip in tips:
            tips_table.add_row(tip)

        self.console.print()
        self.console.print(tips_table)
        self.console.print()

"""Terminal UI for repository selection."""

from typing import List, Dict

import questionary
from questionary import Choice
from loguru import logger


class RepoSelector:
    """Interactive terminal UI for selecting repositories."""

    def select_repos(self, repos: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Display interactive checkbox UI for repository selection.

        Args:
            repos: List of repository dictionaries

        Returns:
            List of selected repository dictionaries
        """
        if not repos:
            logger.warning("No repositories to select")
            return []

        choices = []

        for repo in repos:
            description = repo.get('description', 'No description')
            if len(description) > 80:
                description = description[:77] + "..."

            choice_name = f"{repo['full_name']}: {description}"
            choices.append(Choice(title=choice_name, value=repo))

        print("\n" + "=" * 80)
        print(f"Found {len(repos)} repositories")
        print("=" * 80 + "\n")

        print("Use arrow keys to navigate, space to select/deselect, 'a' to toggle all, enter to confirm\n")

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
        result = questionary.confirm(message).ask()
        return result if result is not None else False

    def select_action(self) -> str:
        """
        Select main action.

        Returns:
            Selected action
        """
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
        url = questionary.text(
            "Enter the GitHub URL of an awesome-* repository:",
            validate=lambda x: x.startswith("http") or "Please enter a valid URL"
        ).ask()

        return url if url is not None else ""

    def show_summary(self, total: int, successful: int, failed: int) -> None:
        """
        Display summary of skill installation.

        Args:
            total: Total repositories selected
            successful: Number of successful installations
            failed: Number of failed installations
        """
        print("\n" + "=" * 80)
        print("INSTALLATION SUMMARY")
        print("=" * 80)
        print(f"Total selected:     {total}")
        print(f"Successfully added: {successful}")
        print(f"Failed:             {failed}")
        print("=" * 80 + "\n")

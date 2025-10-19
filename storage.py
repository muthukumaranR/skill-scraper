"""Storage module for repository data."""

import json
from pathlib import Path
from typing import List, Dict

from loguru import logger


class RepoStorage:
    """Handles storage and retrieval of repository data."""

    def __init__(self, storage_file: str = "repos.json"):
        self.storage_path = Path(storage_file)

    def save_repos(self, repos: List[Dict[str, str]]) -> None:
        """
        Save repositories to JSON file.

        Args:
            repos: List of repository dictionaries
        """
        logger.info(f"Saving {len(repos)} repositories to {self.storage_path}")

        with open(self.storage_path, 'w') as f:
            json.dump(repos, f, indent=2)

        logger.info(f"Successfully saved repositories to {self.storage_path}")

    def load_repos(self) -> List[Dict[str, str]]:
        """
        Load repositories from JSON file.

        Returns:
            List of repository dictionaries
        """
        if not self.storage_path.exists():
            logger.warning(f"Storage file {self.storage_path} does not exist")
            return []

        logger.info(f"Loading repositories from {self.storage_path}")

        with open(self.storage_path, 'r') as f:
            repos = json.load(f)

        logger.info(f"Loaded {len(repos)} repositories")
        return repos

    def exists(self) -> bool:
        """Check if storage file exists."""
        return self.storage_path.exists()

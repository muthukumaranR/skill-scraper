"""Storage module for repository data."""

import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from loguru import logger


class RepoStorage:
    """Handles storage and retrieval of repository data."""

    def __init__(self, storage_file: str = "repos.json"):
        self.storage_path = Path(storage_file)

    def save_repos(self, repos: List[Dict[str, str]], merge: bool = False, source: Optional[str] = None) -> None:
        """
        Save repositories to JSON file.

        Args:
            repos: List of repository dictionaries
            merge: If True, merge with existing repos instead of overwriting
            source: Optional source identifier (e.g., awesome list URL)
        """
        timestamp = datetime.now().isoformat()

        for repo in repos:
            if 'scraped_at' not in repo:
                repo['scraped_at'] = timestamp
            if source and 'source' not in repo:
                repo['source'] = source

        if merge and self.exists():
            existing_repos = self.load_repos()
            merged = self._merge_repos(existing_repos, repos)
            repos_to_save = merged
            logger.info(f"Merging {len(repos)} new repositories with {len(existing_repos)} existing")
        else:
            repos_to_save = repos
            logger.info(f"Saving {len(repos)} repositories to {self.storage_path}")

        with open(self.storage_path, 'w') as f:
            json.dump(repos_to_save, f, indent=2)

        logger.info(f"Successfully saved {len(repos_to_save)} repositories to {self.storage_path}")

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

    def _merge_repos(self, existing: List[Dict[str, str]], new: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Merge new repositories with existing ones.

        Strategy:
        - Use full_name as unique key
        - If repo exists, update it with newer data
        - If repo is new, add it
        - Keep all existing repos not in new batch

        Args:
            existing: Existing repository list
            new: New repository list

        Returns:
            Merged repository list
        """
        repo_map = {repo['full_name']: repo for repo in existing}

        updated_count = 0
        added_count = 0

        for new_repo in new:
            full_name = new_repo['full_name']

            if full_name in repo_map:
                repo_map[full_name].update(new_repo)
                updated_count += 1
                logger.debug(f"Updated existing repo: {full_name}")
            else:
                repo_map[full_name] = new_repo
                added_count += 1
                logger.debug(f"Added new repo: {full_name}")

        logger.info(f"Merge complete: {added_count} added, {updated_count} updated, {len(repo_map)} total")

        return list(repo_map.values())

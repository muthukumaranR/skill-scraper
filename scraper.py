"""GitHub repository scraper for any repository."""

import re
from typing import List, Dict
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from loguru import logger


class RepoScraper:
    """Scrapes GitHub repositories from READMEs or direct skill repositories."""

    def __init__(self):
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        )
        self.github_pattern = re.compile(
            r'https?://(?:www\.)?github\.com/([^/]+)/([^/#?\s)]+)'
        )

    def scrape_awesome_repo(self, github_url: str) -> List[Dict[str, str]]:
        """
        Scrape a GitHub repository for linked repositories or return itself if it's a skill repo.

        Args:
            github_url: URL to the GitHub repository

        Returns:
            List of dictionaries containing repo information
        """
        logger.info(f"Scraping repository: {github_url}")

        parsed = urlparse(github_url)
        path_parts = parsed.path.strip('/').split('/')

        if len(path_parts) < 2:
            logger.error(f"Invalid GitHub URL: {github_url}")
            return []

        owner, repo = path_parts[0], path_parts[1]

        if self._is_direct_skill_repo(owner, repo):
            logger.info(f"{owner}/{repo} appears to be a skill repository itself")
            repo_dict = {
                "owner": owner,
                "name": repo,
                "full_name": f"{owner}/{repo}",
                "url": github_url.rstrip('/'),
                "description": "Skill repository"
            }
            self.fetch_repo_details(repo_dict)
            return [repo_dict]

        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"

        try:
            response = self.client.get(raw_url)
            if response.status_code == 404:
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
                response = self.client.get(raw_url)

            response.raise_for_status()
            content = response.text

            logger.info(f"Successfully fetched README from {raw_url}")
            repos = self._extract_repos(content)

            if not repos:
                logger.info(f"No linked repositories found, treating {owner}/{repo} as standalone repository")
                repo_dict = {
                    "owner": owner,
                    "name": repo,
                    "full_name": f"{owner}/{repo}",
                    "url": github_url.rstrip('/'),
                    "description": self._extract_first_paragraph(content) or "No description available"
                }
                return [repo_dict]

            return repos

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch {raw_url}: {e}")
            logger.info(f"Treating {owner}/{repo} as standalone repository")
            repo_dict = {
                "owner": owner,
                "name": repo,
                "full_name": f"{owner}/{repo}",
                "url": github_url.rstrip('/'),
                "description": "No description available"
            }
            return [repo_dict]

    def _is_direct_skill_repo(self, owner: str, repo_name: str) -> bool:
        """
        Check if a repository contains SKILL.md files directly.

        Args:
            owner: Repository owner
            repo_name: Repository name

        Returns:
            True if repository contains SKILL.md files
        """
        skill_paths = [
            f"https://raw.githubusercontent.com/{owner}/{repo_name}/main/SKILL.md",
            f"https://raw.githubusercontent.com/{owner}/{repo_name}/master/SKILL.md",
            f"https://raw.githubusercontent.com/{owner}/{repo_name}/main/skills/SKILL.md",
            f"https://raw.githubusercontent.com/{owner}/{repo_name}/master/skills/SKILL.md",
        ]

        for skill_url in skill_paths:
            try:
                response = self.client.head(skill_url, timeout=10.0)
                if response.status_code == 200:
                    logger.info(f"Found SKILL.md at {skill_url}")
                    return True
            except Exception:
                continue

        return False

    def _extract_repos(self, markdown_content: str) -> List[Dict[str, str]]:
        """Extract GitHub repositories from markdown content."""
        repos = []
        seen = set()

        matches = self.github_pattern.finditer(markdown_content)

        for match in matches:
            full_url = match.group(0)
            owner = match.group(1)
            repo_name = match.group(2)

            repo_name = repo_name.rstrip('.')

            repo_key = f"{owner}/{repo_name}"

            if repo_key in seen:
                continue

            seen.add(repo_key)

            repos.append({
                "owner": owner,
                "name": repo_name,
                "full_name": repo_key,
                "url": f"https://github.com/{repo_key}",
            })

        logger.info(f"Extracted {len(repos)} unique repositories")
        return repos

    def fetch_repo_details(self, repo: Dict[str, str]) -> Dict[str, str]:
        """
        Fetch additional details about a repository from its README.

        Args:
            repo: Repository dictionary with owner and name

        Returns:
            Updated repository dictionary with description
        """
        owner = repo["owner"]
        name = repo["name"]

        raw_url = f"https://raw.githubusercontent.com/{owner}/{name}/main/README.md"

        try:
            response = self.client.get(raw_url)
            if response.status_code == 404:
                raw_url = f"https://raw.githubusercontent.com/{owner}/{name}/master/README.md"
                response = self.client.get(raw_url)

            response.raise_for_status()
            content = response.text

            first_paragraph = self._extract_first_paragraph(content)
            repo["description"] = first_paragraph or "No description available"

        except httpx.HTTPError as e:
            logger.warning(f"Failed to fetch details for {repo['full_name']}: {e}")
            repo["description"] = "No description available"

        return repo

    def _extract_first_paragraph(self, markdown: str) -> str:
        """Extract the first meaningful paragraph from markdown."""
        lines = markdown.split('\n')
        candidates = []

        for line in lines:
            line = line.strip()

            if line.startswith('#'):
                continue
            if line.startswith('[!['):
                continue
            if line.startswith('!['):
                continue
            if not line:
                continue

            cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', line)
            cleaned = re.sub(r'[*_`]', '', cleaned)
            cleaned = cleaned.strip()

            if len(cleaned) > 20:
                candidates.append(cleaned)

        if candidates:
            best = max(candidates[:5], key=len)
            return best[:200]

        return ""

    def close(self):
        """Close the HTTP client."""
        self.client.close()

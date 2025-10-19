"""GitHub repository scraper for awesome-* lists."""

import re
from typing import List, Dict
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from loguru import logger


class RepoScraper:
    """Scrapes GitHub repositories from awesome-* lists."""

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
        Scrape an awesome-* GitHub repository for linked repositories.

        Args:
            github_url: URL to the awesome-* GitHub repository

        Returns:
            List of dictionaries containing repo information
        """
        logger.info(f"Scraping awesome list: {github_url}")

        parsed = urlparse(github_url)
        path_parts = parsed.path.strip('/').split('/')

        if len(path_parts) < 2:
            logger.error(f"Invalid GitHub URL: {github_url}")
            return []

        owner, repo = path_parts[0], path_parts[1]
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"

        try:
            response = self.client.get(raw_url)
            if response.status_code == 404:
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
                response = self.client.get(raw_url)

            response.raise_for_status()
            content = response.text

            logger.info(f"Successfully fetched README from {raw_url}")
            return self._extract_repos(content)

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch {raw_url}: {e}")
            return []

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

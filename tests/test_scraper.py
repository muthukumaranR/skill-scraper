"""Tests for scraper module."""

import pytest
from scraper import RepoScraper


class TestRepoScraper:
    """Test cases for RepoScraper class."""

    def test_extract_repos_from_markdown(self):
        """Test extracting GitHub repos from markdown content."""
        scraper = RepoScraper()

        markdown = """
# Awesome List

- [repo1](https://github.com/owner1/repo1) - Description 1
- [repo2](https://github.com/owner2/repo2) - Description 2
- [Same repo again](https://github.com/owner1/repo1) - Should deduplicate

https://github.com/owner3/repo3
"""

        repos = scraper._extract_repos(markdown)

        assert len(repos) == 3
        assert repos[0]["full_name"] == "owner1/repo1"
        assert repos[1]["full_name"] == "owner2/repo2"
        assert repos[2]["full_name"] == "owner3/repo3"

        scraper.close()

    def test_extract_first_paragraph(self):
        """Test extracting first paragraph from markdown."""
        scraper = RepoScraper()

        markdown = """
# Title

Some badges and stuff

This is the first real paragraph with description.

Another paragraph.
"""

        result = scraper._extract_first_paragraph(markdown)

        assert "first real paragraph" in result.lower()

        scraper.close()

    def test_github_pattern_matching(self):
        """Test GitHub URL pattern matching."""
        scraper = RepoScraper()

        test_urls = [
            "https://github.com/owner/repo",
            "http://github.com/owner/repo",
            "https://www.github.com/owner/repo",
        ]

        for url in test_urls:
            match = scraper.github_pattern.search(url)
            assert match is not None
            assert match.group(1) == "owner"
            assert match.group(2) == "repo"

        scraper.close()

    def test_remove_trailing_dots(self):
        """Test that trailing dots are removed from repo names."""
        scraper = RepoScraper()

        markdown = "Check out [repo](https://github.com/owner/repo)."

        repos = scraper._extract_repos(markdown)

        assert len(repos) == 1
        assert repos[0]["name"] == "repo"
        assert not repos[0]["name"].endswith(".")

        scraper.close()

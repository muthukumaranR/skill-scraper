"""Detector for identifying skill repositories."""

from typing import Dict, Optional
import re
import httpx
from loguru import logger


class SkillDetector:
    """Detects if a repository contains Claude skills."""

    def __init__(self):
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        )

    def detect_skills(self, repo: Dict[str, str]) -> Dict[str, any]:
        """
        Detect if a repository contains skills.

        Args:
            repo: Repository dictionary with owner and name

        Returns:
            Detection result with is_skill_repo, skill_count estimate, structure
        """
        owner = repo["owner"]
        name = repo["name"]

        logger.info(f"Detecting skills in {owner}/{name}")

        result = {
            "is_skill_repo": False,
            "skill_count": 0,
            "structure": None,
            "confidence": 0.0,
            "indicators": []
        }

        readme_indicators = self._check_readme(owner, name)
        result["indicators"].extend(readme_indicators)

        tree_indicators = self._check_repo_tree(owner, name)
        result["indicators"].extend(tree_indicators)

        result["is_skill_repo"] = len(result["indicators"]) > 0
        result["confidence"] = min(len(result["indicators"]) * 0.3, 1.0)

        for indicator in result["indicators"]:
            if "skill_count" in indicator:
                result["skill_count"] += indicator["skill_count"]

        if result["is_skill_repo"]:
            logger.info(
                f"Detected skill repository: {owner}/{name} "
                f"(~{result['skill_count']} skills, confidence: {result['confidence']:.0%})"
            )
        else:
            logger.debug(f"Not a skill repository: {owner}/{name}")

        return result

    def _check_readme(self, owner: str, name: str) -> list:
        """Check README for skill repository indicators."""
        indicators = []

        raw_url = f"https://raw.githubusercontent.com/{owner}/{name}/main/README.md"

        try:
            response = self.client.get(raw_url)
            if response.status_code == 404:
                raw_url = f"https://raw.githubusercontent.com/{owner}/{name}/master/README.md"
                response = self.client.get(raw_url)

            response.raise_for_status()
            content = response.text.lower()

            skill_keywords = [
                "claude skill", "claude code skill", "skill.md",
                "skills folder", "skills directory", "claude agent skill"
            ]

            for keyword in skill_keywords:
                if keyword in content:
                    indicators.append({
                        "type": "readme_keyword",
                        "value": keyword,
                        "skill_count": 1
                    })

            skill_md_count = len(re.findall(r'skill\.md', content, re.IGNORECASE))
            if skill_md_count > 0:
                indicators.append({
                    "type": "readme_skill_md_mentions",
                    "value": skill_md_count,
                    "skill_count": skill_md_count
                })

        except httpx.HTTPError as e:
            logger.debug(f"Could not fetch README for {owner}/{name}: {e}")

        return indicators

    def _check_repo_tree(self, owner: str, name: str) -> list:
        """Check repository structure via GitHub API."""
        indicators = []

        tree_url = f"https://api.github.com/repos/{owner}/{name}/git/trees/main?recursive=1"

        try:
            response = self.client.get(tree_url)
            if response.status_code == 404:
                tree_url = f"https://api.github.com/repos/{owner}/{name}/git/trees/master?recursive=1"
                response = self.client.get(tree_url)

            if response.status_code == 403:
                logger.debug(f"Rate limited on GitHub API for {owner}/{name}")
                return indicators

            response.raise_for_status()
            tree_data = response.json()

            if "tree" not in tree_data:
                return indicators

            skill_md_files = [
                item for item in tree_data["tree"]
                if item["path"].endswith("SKILL.md")
            ]

            if skill_md_files:
                indicators.append({
                    "type": "repo_skill_md_files",
                    "value": len(skill_md_files),
                    "skill_count": len(skill_md_files),
                    "paths": [item["path"] for item in skill_md_files]
                })

            skills_folder = any(
                item["path"].startswith("skills/") or item["path"] == "skills"
                for item in tree_data["tree"]
            )

            if skills_folder:
                indicators.append({
                    "type": "repo_skills_folder",
                    "value": True,
                    "skill_count": 5
                })

        except httpx.HTTPError as e:
            logger.debug(f"Could not fetch tree for {owner}/{name}: {e}")
        except Exception as e:
            logger.debug(f"Error parsing tree for {owner}/{name}: {e}")

        return indicators

    def close(self):
        """Close the HTTP client."""
        self.client.close()

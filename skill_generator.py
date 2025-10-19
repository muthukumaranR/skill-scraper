"""Claude skill generator for GitHub repositories."""

import shutil
from pathlib import Path
from typing import Dict

from loguru import logger


class SkillGenerator:
    """Generates Claude skills from GitHub repositories."""

    def __init__(self, skills_dir: str = "~/.claude/skills"):
        self.skills_dir = Path(skills_dir).expanduser()
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Skills directory: {self.skills_dir}")

    def generate_skill(self, repo: Dict[str, str]) -> bool:
        """
        Generate a SKILL.md file for a repository.

        Args:
            repo: Repository dictionary with owner, name, description, url

        Returns:
            True if successful, False otherwise
        """
        skill_name = f"{repo['owner']}-{repo['name']}"
        skill_folder = self.skills_dir / skill_name

        if skill_folder.exists():
            logger.warning(f"Skill {skill_name} already exists, skipping")
            return False

        skill_folder.mkdir(parents=True, exist_ok=True)
        skill_file = skill_folder / "SKILL.md"

        skill_content = self._create_skill_content(repo)

        try:
            with open(skill_file, 'w') as f:
                f.write(skill_content)

            logger.info(f"Created skill: {skill_name} at {skill_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to create skill {skill_name}: {e}")
            if skill_folder.exists():
                shutil.rmtree(skill_folder)
            return False

    def _create_skill_content(self, repo: Dict[str, str]) -> str:
        """Create SKILL.md content for a repository."""
        skill_name = f"{repo['owner']}/{repo['name']}"
        description = repo.get('description', 'No description available')

        content = f"""---
name: {skill_name}
description: {description}
---

# {skill_name}

GitHub Repository: {repo['url']}

## Description

{description}

## Usage

This skill provides context about the {repo['name']} repository by {repo['owner']}.

Visit the repository for more information: {repo['url']}
"""

        return content

    def remove_skill(self, repo: Dict[str, str]) -> bool:
        """
        Remove a skill folder.

        Args:
            repo: Repository dictionary

        Returns:
            True if successful, False otherwise
        """
        skill_name = f"{repo['owner']}-{repo['name']}"
        skill_folder = self.skills_dir / skill_name

        if not skill_folder.exists():
            logger.warning(f"Skill {skill_name} does not exist")
            return False

        try:
            shutil.rmtree(skill_folder)
            logger.info(f"Removed skill: {skill_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove skill {skill_name}: {e}")
            return False

    def list_installed_skills(self) -> list:
        """List all installed skills."""
        if not self.skills_dir.exists():
            return []

        skills = [d.name for d in self.skills_dir.iterdir() if d.is_dir()]
        logger.info(f"Found {len(skills)} installed skills")
        return skills

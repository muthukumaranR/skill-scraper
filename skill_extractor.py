"""Extractor for downloading and extracting skills from repositories."""

import shutil
import tempfile
from pathlib import Path
from typing import Dict, List
import subprocess
import re

from loguru import logger
from config import ExtractionConfig


class SkillExtractor:
    """Extracts actual skills from skill repositories."""

    def __init__(self, skills_dir: str = None, config: ExtractionConfig = None):
        self.config = config or ExtractionConfig()

        if skills_dir is None:
            if self.config.install_location == "local":
                skills_dir = "./.claude/skills"
            else:
                skills_dir = "~/.claude/skills"

        self.skills_dir = Path(skills_dir).expanduser()
        self.skills_dir.mkdir(parents=True, exist_ok=True)

        self.staging_dir = Path(tempfile.mkdtemp(prefix="skill-scraper-staging-"))

        logger.info(f"SkillExtractor initialized with mode: {self.config.mode}")
        logger.info(f"Installation location: {self.config.install_location} ({self.skills_dir})")
        logger.info(f"Staging directory: {self.staging_dir}")

    def extract_skills(self, repo: Dict[str, str], detection_result: Dict) -> Dict[str, any]:
        """
        Extract skills from a repository.

        Args:
            repo: Repository dictionary
            detection_result: Result from SkillDetector

        Returns:
            Extraction result with extracted skills
        """
        owner = repo["owner"]
        name = repo["name"]
        url = repo["url"]

        logger.info(f"Extracting skills from {owner}/{name}")

        result = {
            "success": False,
            "extracted_count": 0,
            "skipped_count": 0,
            "failed_count": 0,
            "skills": []
        }

        temp_dir = Path(tempfile.mkdtemp(prefix=f"skill-scraper-{owner}-{name}-"))

        try:
            if not self._clone_repo(url, temp_dir):
                logger.error(f"Failed to clone {url}")
                return result

            skill_files = self._find_skill_files(temp_dir)

            if not skill_files:
                logger.warning(f"No SKILL.md files found in {owner}/{name}")
                return result

            logger.info(f"Found {len(skill_files)} skill(s) in {owner}/{name}")

            for skill_file in skill_files[:self.config.max_skills_per_repo]:
                extraction = self._extract_single_skill(
                    skill_file, temp_dir, repo, detection_result
                )

                if extraction["success"]:
                    result["extracted_count"] += 1
                    result["skills"].append(extraction["skill"])
                elif extraction.get("skipped"):
                    result["skipped_count"] += 1
                else:
                    result["failed_count"] += 1

            result["success"] = result["extracted_count"] > 0

            logger.info(
                f"Extraction complete for {owner}/{name}: "
                f"{result['extracted_count']} extracted, "
                f"{result['skipped_count']} skipped, "
                f"{result['failed_count']} failed"
            )

        except Exception as e:
            logger.error(f"Error extracting skills from {owner}/{name}: {e}", exc_info=True)

        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temp directory: {temp_dir}")

        return result

    def _clone_repo(self, url: str, target_dir: Path) -> bool:
        """Clone a repository to a temporary directory."""
        try:
            logger.info(f"Cloning {url} to {target_dir}")

            cmd = [
                "git", "clone",
                "--depth", str(self.config.clone_depth),
                "--quiet",
                url,
                str(target_dir)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                logger.error(f"Git clone failed: {result.stderr}")
                return False

            logger.info(f"Successfully cloned {url}")
            return True

        except subprocess.TimeoutExpired:
            logger.error(f"Git clone timed out for {url}")
            return False
        except Exception as e:
            logger.error(f"Error cloning {url}: {e}")
            return False

    def _find_skill_files(self, repo_dir: Path) -> List[Path]:
        """Find all SKILL.md files in a repository."""
        skill_files = list(repo_dir.rglob("SKILL.md"))

        skill_files = [
            f for f in skill_files
            if ".git" not in f.parts
        ]

        logger.info(f"Found {len(skill_files)} SKILL.md files")
        return skill_files

    def _extract_single_skill(
        self,
        skill_file: Path,
        repo_dir: Path,
        source_repo: Dict[str, str],
        detection_result: Dict
    ) -> Dict[str, any]:
        """Extract a single skill from a file."""
        result = {
            "success": False,
            "skipped": False,
            "skill": None
        }

        try:
            skill_folder = skill_file.parent
            relative_path = skill_folder.relative_to(repo_dir)

            skill_name = self._determine_skill_name(skill_folder, relative_path, source_repo)

            target_folder = self.skills_dir / skill_name

            if target_folder.exists() and self.config.skip_existing:
                logger.info(f"Skill already exists, skipping: {skill_name}")
                result["skipped"] = True
                return result

            target_folder.mkdir(parents=True, exist_ok=True)

            self._copy_skill_files(skill_folder, target_folder)

            self._enrich_skill_metadata(
                target_folder / "SKILL.md",
                source_repo,
                skill_name,
                detection_result
            )

            logger.info(f"Extracted skill: {skill_name}")

            result["success"] = True
            result["skill"] = {
                "name": skill_name,
                "path": str(target_folder),
                "source_repo": source_repo["full_name"]
            }

        except Exception as e:
            logger.error(f"Error extracting skill from {skill_file}: {e}", exc_info=True)

        return result

    def _determine_skill_name(
        self,
        skill_folder: Path,
        relative_path: Path,
        source_repo: Dict[str, str]
    ) -> str:
        """Determine the name for an extracted skill."""
        folder_name = skill_folder.name

        if folder_name == "." or folder_name == source_repo["name"]:
            return f"{source_repo['owner']}-{source_repo['name']}"

        if relative_path.parts and relative_path.parts[0] == "skills":
            if len(relative_path.parts) > 1:
                return f"{source_repo['owner']}-{relative_path.parts[1]}"

        return f"{source_repo['owner']}-{folder_name}"

    def _copy_skill_files(self, source_folder: Path, target_folder: Path):
        """Copy skill files from source to target."""
        for item in source_folder.iterdir():
            if item.name.startswith('.'):
                continue

            if item.name == '__pycache__':
                continue

            if item.is_file():
                shutil.copy2(item, target_folder / item.name)
                logger.debug(f"Copied file: {item.name}")
            elif item.is_dir():
                shutil.copytree(item, target_folder / item.name, dirs_exist_ok=True)
                logger.debug(f"Copied directory: {item.name}")

    def _enrich_skill_metadata(
        self,
        skill_file: Path,
        source_repo: Dict[str, str],
        skill_name: str,
        detection_result: Dict
    ):
        """Add metadata to extracted skill."""
        if not skill_file.exists():
            return

        try:
            content = skill_file.read_text()

            if "extracted-from:" not in content.lower():
                metadata_footer = f"""

---
**Extracted from**: [{source_repo['full_name']}]({source_repo['url']})
**Detection confidence**: {detection_result.get('confidence', 0):.0%}
**Installed as**: {skill_name}
"""
                content += metadata_footer
                skill_file.write_text(content)
                logger.debug(f"Enriched metadata for {skill_name}")

        except Exception as e:
            logger.warning(f"Could not enrich metadata for {skill_name}: {e}")

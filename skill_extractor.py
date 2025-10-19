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
        """Extract a single skill from a file to staging directory."""
        result = {
            "success": False,
            "skipped": False,
            "skill": None
        }

        try:
            skill_folder = skill_file.parent
            relative_path = skill_folder.relative_to(repo_dir)

            skill_name = self._determine_skill_name(skill_folder, relative_path, source_repo)

            final_target_folder = self.skills_dir / skill_name

            if final_target_folder.exists():
                if self.config.skip_existing and not self.config.update_existing:
                    logger.info(f"Skill already exists, skipping: {skill_name}")
                    result["skipped"] = True
                    return result
                elif self.config.update_existing:
                    logger.info(f"Skill already exists, will update: {skill_name}")

            staging_folder = self.staging_dir / skill_name
            staging_folder.mkdir(parents=True, exist_ok=True)

            self._copy_skill_files(skill_folder, staging_folder)

            skill_md_path = staging_folder / "SKILL.md"
            self._enrich_skill_metadata(
                skill_md_path,
                source_repo,
                skill_name,
                detection_result
            )

            metadata = self._parse_skill_metadata(skill_md_path)

            logger.info(f"Extracted skill to staging: {skill_name}")

            result["success"] = True
            result["skill"] = {
                "name": skill_name,
                "staging_path": str(staging_folder),
                "final_path": str(final_target_folder),
                "source_repo": source_repo["full_name"],
                "description": metadata.get("description", "No description available"),
                "skill_name": metadata.get("name", skill_name),
                "metadata": metadata
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

    def _parse_skill_metadata(self, skill_file: Path) -> Dict[str, str]:
        """Parse metadata from SKILL.md file."""
        metadata = {
            "name": "",
            "description": "No description available",
            "content": ""
        }

        if not skill_file.exists():
            return metadata

        try:
            content = skill_file.read_text()
            metadata["content"] = content

            frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if frontmatter_match:
                frontmatter = frontmatter_match.group(1)
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        if key in ['name', 'description']:
                            metadata[key] = value

            if not metadata["description"] or metadata["description"] == "No description available":
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('# ') and i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and not next_line.startswith('#'):
                            metadata["description"] = next_line[:200]
                            break

        except Exception as e:
            logger.warning(f"Could not parse metadata from {skill_file}: {e}")

        return metadata

    def install_skills(self, skills_to_install: List[Dict[str, str]]) -> Dict[str, any]:
        """
        Install selected skills from staging to final location.

        Args:
            skills_to_install: List of skill dictionaries with staging_path and install_location

        Returns:
            Installation result with success count
        """
        result = {
            "success": 0,
            "failed": 0,
            "errors": [],
            "installed_local": 0,
            "installed_global": 0
        }

        for skill in skills_to_install:
            try:
                staging_path = Path(skill["staging_path"])

                install_location = skill.get("install_location", self.config.install_location)

                default_global = Path("~/.claude/skills").expanduser()
                default_local = Path("./.claude/skills").expanduser()

                if self.skills_dir != default_global and self.skills_dir != default_local:
                    skills_base_dir = self.skills_dir
                elif install_location == "local":
                    skills_base_dir = default_local
                else:
                    skills_base_dir = default_global

                skills_base_dir.mkdir(parents=True, exist_ok=True)

                final_path = skills_base_dir / skill["name"]

                if not staging_path.exists():
                    logger.error(f"Staging path does not exist: {staging_path}")
                    result["failed"] += 1
                    result["errors"].append(f"{skill['name']}: Staging path not found")
                    continue

                if final_path.exists():
                    shutil.rmtree(final_path)
                    logger.debug(f"Removed existing skill at {final_path}")

                shutil.copytree(staging_path, final_path)
                logger.info(f"Installed skill: {skill['name']} to {final_path} ({install_location})")
                result["success"] += 1

                if install_location == "local":
                    result["installed_local"] += 1
                else:
                    result["installed_global"] += 1

            except Exception as e:
                logger.error(f"Failed to install skill {skill['name']}: {e}", exc_info=True)
                result["failed"] += 1
                result["errors"].append(f"{skill['name']}: {str(e)}")

        return result

    def cleanup_staging(self):
        """Clean up the staging directory."""
        try:
            if self.staging_dir.exists():
                shutil.rmtree(self.staging_dir)
                logger.info(f"Cleaned up staging directory: {self.staging_dir}")
        except Exception as e:
            logger.warning(f"Could not clean up staging directory: {e}")

    def get_staged_skills(self) -> List[Dict[str, str]]:
        """
        Get list of all skills currently in staging.

        Returns:
            List of skill dictionaries with metadata
        """
        staged_skills = []

        if not self.staging_dir.exists():
            return staged_skills

        for skill_folder in self.staging_dir.iterdir():
            if not skill_folder.is_dir():
                continue

            skill_md = skill_folder / "SKILL.md"
            if not skill_md.exists():
                continue

            metadata = self._parse_skill_metadata(skill_md)
            staged_skills.append({
                "name": skill_folder.name,
                "staging_path": str(skill_folder),
                "final_path": str(self.skills_dir / skill_folder.name),
                "description": metadata.get("description", "No description available"),
                "skill_name": metadata.get("name", skill_folder.name),
                "metadata": metadata
            })

        return staged_skills

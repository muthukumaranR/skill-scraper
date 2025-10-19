"""Tests for skill_extractor module."""

import pytest
from pathlib import Path
from skill_extractor import SkillExtractor
from config import ExtractionConfig


class TestSkillExtractor:
    """Test cases for SkillExtractor class."""

    def test_extractor_initialization(self, tmp_path):
        """Test extractor can be initialized."""
        skills_dir = tmp_path / "skills"
        config = ExtractionConfig.metadata_only()

        extractor = SkillExtractor(str(skills_dir), config)

        assert extractor.skills_dir == skills_dir
        assert extractor.config == config
        assert skills_dir.exists()

    def test_extractor_with_default_config(self, tmp_path):
        """Test extractor with default config."""
        skills_dir = tmp_path / "skills"

        extractor = SkillExtractor(str(skills_dir))

        assert extractor.config.mode == "metadata"

    def test_find_skill_files(self, tmp_path):
        """Test finding SKILL.md files."""
        repo_dir = tmp_path / "test-repo"
        repo_dir.mkdir()

        (repo_dir / "SKILL.md").write_text("# Test Skill")

        skill_folder = repo_dir / "skills" / "skill1"
        skill_folder.mkdir(parents=True)
        (skill_folder / "SKILL.md").write_text("# Skill 1")

        git_folder = repo_dir / ".git"
        git_folder.mkdir()
        (git_folder / "SKILL.md").write_text("# Should be ignored")

        config = ExtractionConfig.metadata_only()
        extractor = SkillExtractor(str(tmp_path / "skills"), config)

        skill_files = extractor._find_skill_files(repo_dir)

        assert len(skill_files) == 2
        assert all(f.name == "SKILL.md" for f in skill_files)
        assert not any(".git" in str(f) for f in skill_files)

    def test_determine_skill_name_simple(self, tmp_path):
        """Test skill name determination for simple case."""
        config = ExtractionConfig.metadata_only()
        extractor = SkillExtractor(str(tmp_path / "skills"), config)

        skill_folder = tmp_path / "test-skill"
        relative_path = Path("test-skill")

        source_repo = {
            "owner": "testowner",
            "name": "testrepo",
            "full_name": "testowner/testrepo"
        }

        skill_name = extractor._determine_skill_name(
            skill_folder,
            relative_path,
            source_repo
        )

        assert skill_name == "testowner-test-skill"

    def test_determine_skill_name_from_skills_folder(self, tmp_path):
        """Test skill name determination from skills folder."""
        config = ExtractionConfig.metadata_only()
        extractor = SkillExtractor(str(tmp_path / "skills"), config)

        skill_folder = tmp_path / "skills" / "my-skill"
        relative_path = Path("skills") / "my-skill"

        source_repo = {
            "owner": "testowner",
            "name": "testrepo",
            "full_name": "testowner/testrepo"
        }

        skill_name = extractor._determine_skill_name(
            skill_folder,
            relative_path,
            source_repo
        )

        assert skill_name == "testowner-my-skill"

    def test_copy_skill_files(self, tmp_path):
        """Test copying skill files."""
        source = tmp_path / "source"
        source.mkdir()

        (source / "SKILL.md").write_text("# Test")
        (source / "script.py").write_text("print('hello')")

        subfolder = source / "resources"
        subfolder.mkdir()
        (subfolder / "data.json").write_text("{}")

        (source / ".hidden").write_text("should be ignored")
        (source / "__pycache__").mkdir()

        target = tmp_path / "target"
        target.mkdir()

        config = ExtractionConfig.metadata_only()
        extractor = SkillExtractor(str(tmp_path / "skills"), config)

        extractor._copy_skill_files(source, target)

        assert (target / "SKILL.md").exists()
        assert (target / "script.py").exists()
        assert (target / "resources" / "data.json").exists()
        assert not (target / ".hidden").exists()
        assert not (target / "__pycache__").exists()

    def test_extraction_result_structure(self, tmp_path):
        """Test extraction result structure."""
        skills_dir = tmp_path / "skills"
        config = ExtractionConfig.metadata_only()
        extractor = SkillExtractor(str(skills_dir), config)

        test_repo = {
            "owner": "test",
            "name": "test-repo",
            "full_name": "test/test-repo",
            "url": "https://github.com/test/test-repo"
        }

        detection_result = {
            "is_skill_repo": False,
            "skill_count": 0,
            "confidence": 0.0
        }

        result = extractor.extract_skills(test_repo, detection_result)

        assert "success" in result
        assert "extracted_count" in result
        assert "skipped_count" in result
        assert "failed_count" in result
        assert "skills" in result

        assert isinstance(result["success"], bool)
        assert isinstance(result["extracted_count"], int)
        assert isinstance(result["skills"], list)

    def test_parse_skill_metadata_with_frontmatter(self, tmp_path):
        """Test parsing skill metadata with frontmatter."""
        skills_dir = tmp_path / "skills"
        config = ExtractionConfig.metadata_only()
        extractor = SkillExtractor(str(skills_dir), config)

        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("""---
name: Test Skill
description: A test skill for testing
---

# Test Skill

This is a test skill.""")

        metadata = extractor._parse_skill_metadata(skill_md)

        assert metadata["name"] == "Test Skill"
        assert metadata["description"] == "A test skill for testing"
        assert "Test Skill" in metadata["content"]

    def test_parse_skill_metadata_without_frontmatter(self, tmp_path):
        """Test parsing skill metadata without frontmatter."""
        skills_dir = tmp_path / "skills"
        config = ExtractionConfig.metadata_only()
        extractor = SkillExtractor(str(skills_dir), config)

        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("""# My Skill
This is the description from the content.""")

        metadata = extractor._parse_skill_metadata(skill_md)

        assert "This is the description from the content." in metadata["description"]

    def test_get_staged_skills(self, tmp_path):
        """Test getting staged skills."""
        skills_dir = tmp_path / "skills"
        config = ExtractionConfig.metadata_only()
        extractor = SkillExtractor(str(skills_dir), config)

        skill1 = extractor.staging_dir / "skill1"
        skill1.mkdir(parents=True)
        (skill1 / "SKILL.md").write_text("""---
name: Skill 1
description: First skill
---""")

        skill2 = extractor.staging_dir / "skill2"
        skill2.mkdir(parents=True)
        (skill2 / "SKILL.md").write_text("""---
name: Skill 2
description: Second skill
---""")

        staged_skills = extractor.get_staged_skills()

        assert len(staged_skills) == 2
        assert any(s["name"] == "skill1" for s in staged_skills)
        assert any(s["name"] == "skill2" for s in staged_skills)
        assert all("description" in s for s in staged_skills)
        assert all("staging_path" in s for s in staged_skills)
        assert all("final_path" in s for s in staged_skills)

    def test_install_skills(self, tmp_path):
        """Test installing skills from staging."""
        skills_dir = tmp_path / "skills"
        config = ExtractionConfig.metadata_only()
        extractor = SkillExtractor(str(skills_dir), config)

        skill_staging = extractor.staging_dir / "test-skill"
        skill_staging.mkdir(parents=True)
        (skill_staging / "SKILL.md").write_text("# Test")

        skills_to_install = [{
            "name": "test-skill",
            "staging_path": str(skill_staging),
            "final_path": str(skills_dir / "test-skill")
        }]

        result = extractor.install_skills(skills_to_install)

        assert result["success"] == 1
        assert result["failed"] == 0
        assert (skills_dir / "test-skill" / "SKILL.md").exists()

    def test_cleanup_staging(self, tmp_path):
        """Test cleanup of staging directory."""
        skills_dir = tmp_path / "skills"
        config = ExtractionConfig.metadata_only()
        extractor = SkillExtractor(str(skills_dir), config)

        staging_dir = extractor.staging_dir
        assert staging_dir.exists()

        (staging_dir / "test.txt").write_text("test")

        extractor.cleanup_staging()

        assert not staging_dir.exists()

    def test_local_installation_path(self, tmp_path):
        """Test local installation path configuration."""
        config = ExtractionConfig(install_location="local")
        extractor = SkillExtractor(config=config)

        assert ".claude/skills" in str(extractor.skills_dir)

    def test_global_installation_path(self, tmp_path):
        """Test global installation path configuration."""
        config = ExtractionConfig(install_location="global")
        extractor = SkillExtractor(config=config)

        assert ".claude/skills" in str(extractor.skills_dir)

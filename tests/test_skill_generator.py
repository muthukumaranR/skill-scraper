"""Tests for skill_generator module."""

import pytest
from pathlib import Path
from skill_generator import SkillGenerator


class TestSkillGenerator:
    """Test cases for SkillGenerator class."""

    def test_generate_skill(self, tmp_path):
        """Test generating a skill."""
        skills_dir = tmp_path / "skills"
        generator = SkillGenerator(str(skills_dir))

        test_repo = {
            "owner": "testowner",
            "name": "testrepo",
            "full_name": "testowner/testrepo",
            "url": "https://github.com/testowner/testrepo",
            "description": "A test repository"
        }

        result = generator.generate_skill(test_repo)

        assert result is True

        skill_folder = skills_dir / "testowner-testrepo"
        skill_file = skill_folder / "SKILL.md"

        assert skill_folder.exists()
        assert skill_file.exists()

        content = skill_file.read_text()

        assert "name: testowner/testrepo" in content
        assert "description: A test repository" in content
        assert "https://github.com/testowner/testrepo" in content

    def test_generate_duplicate_skill(self, tmp_path):
        """Test that duplicate skills are not created."""
        skills_dir = tmp_path / "skills"
        generator = SkillGenerator(str(skills_dir))

        test_repo = {
            "owner": "testowner",
            "name": "testrepo",
            "full_name": "testowner/testrepo",
            "url": "https://github.com/testowner/testrepo",
            "description": "A test repository"
        }

        result1 = generator.generate_skill(test_repo)
        assert result1 is True

        result2 = generator.generate_skill(test_repo)
        assert result2 is False

    def test_remove_skill(self, tmp_path):
        """Test removing a skill."""
        skills_dir = tmp_path / "skills"
        generator = SkillGenerator(str(skills_dir))

        test_repo = {
            "owner": "testowner",
            "name": "testrepo",
            "full_name": "testowner/testrepo",
            "url": "https://github.com/testowner/testrepo",
            "description": "A test repository"
        }

        generator.generate_skill(test_repo)

        skill_folder = skills_dir / "testowner-testrepo"
        assert skill_folder.exists()

        result = generator.remove_skill(test_repo)
        assert result is True

        assert not skill_folder.exists()

    def test_remove_nonexistent_skill(self, tmp_path):
        """Test removing a non-existent skill."""
        skills_dir = tmp_path / "skills"
        generator = SkillGenerator(str(skills_dir))

        test_repo = {
            "owner": "testowner",
            "name": "testrepo",
            "full_name": "testowner/testrepo",
            "url": "https://github.com/testowner/testrepo",
            "description": "A test repository"
        }

        result = generator.remove_skill(test_repo)
        assert result is False

    def test_list_installed_skills(self, tmp_path):
        """Test listing installed skills."""
        skills_dir = tmp_path / "skills"
        generator = SkillGenerator(str(skills_dir))

        test_repos = [
            {
                "owner": "owner1",
                "name": "repo1",
                "full_name": "owner1/repo1",
                "url": "https://github.com/owner1/repo1",
                "description": "Repo 1"
            },
            {
                "owner": "owner2",
                "name": "repo2",
                "full_name": "owner2/repo2",
                "url": "https://github.com/owner2/repo2",
                "description": "Repo 2"
            }
        ]

        for repo in test_repos:
            generator.generate_skill(repo)

        skills = generator.list_installed_skills()

        assert len(skills) == 2
        assert "owner1-repo1" in skills
        assert "owner2-repo2" in skills

    def test_skill_content_format(self, tmp_path):
        """Test that skill content has correct format."""
        skills_dir = tmp_path / "skills"
        generator = SkillGenerator(str(skills_dir))

        test_repo = {
            "owner": "testowner",
            "name": "testrepo",
            "full_name": "testowner/testrepo",
            "url": "https://github.com/testowner/testrepo",
            "description": "A test repository"
        }

        generator.generate_skill(test_repo)

        skill_file = skills_dir / "testowner-testrepo" / "SKILL.md"
        content = skill_file.read_text()

        assert content.startswith("---\n")
        assert "---\n" in content[4:]
        assert "# testowner/testrepo" in content

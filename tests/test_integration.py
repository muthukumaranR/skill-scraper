"""Integration tests for the complete workflow."""

import pytest
from pathlib import Path
from scraper import RepoScraper
from storage import RepoStorage
from skill_generator import SkillGenerator


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_complete_workflow_scrape_to_skill(self, tmp_path):
        """Test complete workflow from scraping to skill generation."""
        storage_file = tmp_path / "test_repos.json"
        skills_dir = tmp_path / "skills"

        scraper = RepoScraper()
        storage = RepoStorage(str(storage_file))
        skill_gen = SkillGenerator(str(skills_dir))

        test_markdown = """
# Awesome Test List

- [repo1](https://github.com/owner1/repo1) - Test repo 1
- [repo2](https://github.com/owner2/repo2) - Test repo 2
"""

        repos = scraper._extract_repos(test_markdown)
        assert len(repos) == 2

        storage.save_repos(repos)
        assert storage_file.exists()

        loaded_repos = storage.load_repos()
        assert len(loaded_repos) == 2

        for repo in loaded_repos[:1]:
            result = skill_gen.generate_skill(repo)
            assert result is True

        skills = skill_gen.list_installed_skills()
        assert len(skills) == 1
        assert "owner1-repo1" in skills

        skill_file = skills_dir / "owner1-repo1" / "SKILL.md"
        assert skill_file.exists()

        content = skill_file.read_text()
        assert "name: owner1/repo1" in content
        assert "https://github.com/owner1/repo1" in content

        scraper.close()

    def test_workflow_with_duplicate_prevention(self, tmp_path):
        """Test that duplicate skills are prevented in workflow."""
        skills_dir = tmp_path / "skills"
        skill_gen = SkillGenerator(str(skills_dir))

        test_repo = {
            "owner": "testowner",
            "name": "testrepo",
            "full_name": "testowner/testrepo",
            "url": "https://github.com/testowner/testrepo",
            "description": "Test repository"
        }

        result1 = skill_gen.generate_skill(test_repo)
        assert result1 is True

        result2 = skill_gen.generate_skill(test_repo)
        assert result2 is False

        skills = skill_gen.list_installed_skills()
        assert len(skills) == 1

    def test_workflow_storage_persistence(self, tmp_path):
        """Test that storage persists across instances."""
        storage_file = tmp_path / "test_repos.json"

        storage1 = RepoStorage(str(storage_file))

        test_repos = [
            {
                "owner": "owner1",
                "name": "repo1",
                "full_name": "owner1/repo1",
                "url": "https://github.com/owner1/repo1",
                "description": "Repo 1"
            }
        ]

        storage1.save_repos(test_repos)

        storage2 = RepoStorage(str(storage_file))
        loaded_repos = storage2.load_repos()

        assert len(loaded_repos) == 1
        assert loaded_repos[0]["full_name"] == "owner1/repo1"

    def test_workflow_skill_removal(self, tmp_path):
        """Test skill generation and removal workflow."""
        skills_dir = tmp_path / "skills"
        skill_gen = SkillGenerator(str(skills_dir))

        test_repo = {
            "owner": "testowner",
            "name": "testrepo",
            "full_name": "testowner/testrepo",
            "url": "https://github.com/testowner/testrepo",
            "description": "Test repository"
        }

        skill_gen.generate_skill(test_repo)

        skills = skill_gen.list_installed_skills()
        assert "testowner-testrepo" in skills

        skill_gen.remove_skill(test_repo)

        skills = skill_gen.list_installed_skills()
        assert "testowner-testrepo" not in skills

    def test_workflow_multiple_repos(self, tmp_path):
        """Test workflow with multiple repositories."""
        storage_file = tmp_path / "test_repos.json"
        skills_dir = tmp_path / "skills"

        storage = RepoStorage(str(storage_file))
        skill_gen = SkillGenerator(str(skills_dir))

        test_repos = [
            {
                "owner": f"owner{i}",
                "name": f"repo{i}",
                "full_name": f"owner{i}/repo{i}",
                "url": f"https://github.com/owner{i}/repo{i}",
                "description": f"Repo {i}"
            }
            for i in range(1, 6)
        ]

        storage.save_repos(test_repos)

        loaded_repos = storage.load_repos()
        assert len(loaded_repos) == 5

        successful = 0
        for repo in loaded_repos[:3]:
            if skill_gen.generate_skill(repo):
                successful += 1

        assert successful == 3

        skills = skill_gen.list_installed_skills()
        assert len(skills) == 3

    def test_workflow_scraper_deduplication(self, tmp_path):
        """Test that scraper deduplicates repositories."""
        scraper = RepoScraper()

        markdown_with_duplicates = """
# Awesome List

- [repo1](https://github.com/owner1/repo1) - First mention
- [repo2](https://github.com/owner2/repo2) - Another repo
- [repo1 again](https://github.com/owner1/repo1) - Duplicate
"""

        repos = scraper._extract_repos(markdown_with_duplicates)

        assert len(repos) == 2
        assert repos[0]["full_name"] == "owner1/repo1"
        assert repos[1]["full_name"] == "owner2/repo2"

        scraper.close()

"""Tests for storage module."""

import json
import pytest
from pathlib import Path
from storage import RepoStorage


class TestRepoStorage:
    """Test cases for RepoStorage class."""

    def test_save_and_load_repos(self, tmp_path):
        """Test saving and loading repositories."""
        storage_file = tmp_path / "test_repos.json"
        storage = RepoStorage(str(storage_file))

        test_repos = [
            {
                "owner": "owner1",
                "name": "repo1",
                "full_name": "owner1/repo1",
                "url": "https://github.com/owner1/repo1",
                "description": "Test repo 1"
            },
            {
                "owner": "owner2",
                "name": "repo2",
                "full_name": "owner2/repo2",
                "url": "https://github.com/owner2/repo2",
                "description": "Test repo 2"
            }
        ]

        storage.save_repos(test_repos)

        assert storage_file.exists()

        loaded_repos = storage.load_repos()

        assert len(loaded_repos) == 2
        assert loaded_repos[0]["owner"] == "owner1"
        assert loaded_repos[1]["owner"] == "owner2"

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading from non-existent file."""
        storage_file = tmp_path / "nonexistent.json"
        storage = RepoStorage(str(storage_file))

        repos = storage.load_repos()

        assert repos == []

    def test_exists_check(self, tmp_path):
        """Test exists() method."""
        storage_file = tmp_path / "test.json"
        storage = RepoStorage(str(storage_file))

        assert not storage.exists()

        storage.save_repos([])

        assert storage.exists()

    def test_save_empty_list(self, tmp_path):
        """Test saving empty repository list."""
        storage_file = tmp_path / "empty.json"
        storage = RepoStorage(str(storage_file))

        storage.save_repos([])

        assert storage_file.exists()

        with open(storage_file, 'r') as f:
            content = json.load(f)

        assert content == []

    def test_merge_repos_new_and_existing(self, tmp_path):
        """Test merging new repos with existing ones."""
        storage_file = tmp_path / "repos.json"
        storage = RepoStorage(str(storage_file))

        existing_repos = [
            {"owner": "user1", "name": "repo1", "full_name": "user1/repo1", "url": "https://github.com/user1/repo1"},
            {"owner": "user2", "name": "repo2", "full_name": "user2/repo2", "url": "https://github.com/user2/repo2"},
        ]

        storage.save_repos(existing_repos)

        new_repos = [
            {"owner": "user1", "name": "repo1", "full_name": "user1/repo1", "url": "https://github.com/user1/repo1", "description": "Updated"},
            {"owner": "user3", "name": "repo3", "full_name": "user3/repo3", "url": "https://github.com/user3/repo3"},
        ]

        storage.save_repos(new_repos, merge=True)

        all_repos = storage.load_repos()

        assert len(all_repos) == 3

        repo1 = next(r for r in all_repos if r["full_name"] == "user1/repo1")
        assert repo1.get("description") == "Updated"

    def test_merge_repos_only_new(self, tmp_path):
        """Test merging when all repos are new."""
        storage_file = tmp_path / "repos.json"
        storage = RepoStorage(str(storage_file))

        existing_repos = [
            {"owner": "user1", "name": "repo1", "full_name": "user1/repo1", "url": "https://github.com/user1/repo1"},
        ]

        storage.save_repos(existing_repos)

        new_repos = [
            {"owner": "user2", "name": "repo2", "full_name": "user2/repo2", "url": "https://github.com/user2/repo2"},
            {"owner": "user3", "name": "repo3", "full_name": "user3/repo3", "url": "https://github.com/user3/repo3"},
        ]

        storage.save_repos(new_repos, merge=True)

        all_repos = storage.load_repos()

        assert len(all_repos) == 3

    def test_save_without_merge_overwrites(self, tmp_path):
        """Test that saving without merge overwrites existing repos."""
        storage_file = tmp_path / "repos.json"
        storage = RepoStorage(str(storage_file))

        existing_repos = [
            {"owner": "user1", "name": "repo1", "full_name": "user1/repo1", "url": "https://github.com/user1/repo1"},
        ]

        storage.save_repos(existing_repos)

        new_repos = [
            {"owner": "user2", "name": "repo2", "full_name": "user2/repo2", "url": "https://github.com/user2/repo2"},
        ]

        storage.save_repos(new_repos, merge=False)

        all_repos = storage.load_repos()

        assert len(all_repos) == 1
        assert all_repos[0]["full_name"] == "user2/repo2"

    def test_save_with_source_tracking(self, tmp_path):
        """Test that source tracking is added when provided."""
        storage_file = tmp_path / "repos.json"
        storage = RepoStorage(str(storage_file))

        repos = [
            {"owner": "user1", "name": "repo1", "full_name": "user1/repo1", "url": "https://github.com/user1/repo1"},
        ]

        source_url = "https://github.com/awesome/list"
        storage.save_repos(repos, source=source_url)

        saved_repos = storage.load_repos()

        assert saved_repos[0].get("source") == source_url
        assert "scraped_at" in saved_repos[0]

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

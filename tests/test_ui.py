"""Tests for ui module."""

import pytest
from unittest.mock import MagicMock, patch
from ui import RepoSelector


class TestRepoSelector:
    """Test cases for RepoSelector class."""

    def test_select_repos_empty_list(self):
        """Test selecting from empty repository list."""
        selector = RepoSelector()

        result = selector.select_repos([])

        assert result == []

    @patch('ui.questionary.checkbox')
    def test_select_repos_with_repositories(self, mock_checkbox):
        """Test selecting repositories with valid list."""
        selector = RepoSelector()

        test_repos = [
            {
                "owner": "owner1",
                "name": "repo1",
                "full_name": "owner1/repo1",
                "url": "https://github.com/owner1/repo1",
                "description": "Test description 1"
            },
            {
                "owner": "owner2",
                "name": "repo2",
                "full_name": "owner2/repo2",
                "url": "https://github.com/owner2/repo2",
                "description": "Test description 2"
            }
        ]

        mock_ask = MagicMock(return_value=[test_repos[0]])
        mock_checkbox.return_value.ask = mock_ask

        result = selector.select_repos(test_repos)

        assert len(result) == 1
        assert result[0]["full_name"] == "owner1/repo1"

    @patch('ui.questionary.checkbox')
    def test_select_repos_cancelled(self, mock_checkbox):
        """Test cancelling repository selection."""
        selector = RepoSelector()

        test_repos = [
            {
                "owner": "owner1",
                "name": "repo1",
                "full_name": "owner1/repo1",
                "url": "https://github.com/owner1/repo1",
                "description": "Test description"
            }
        ]

        mock_ask = MagicMock(return_value=None)
        mock_checkbox.return_value.ask = mock_ask

        result = selector.select_repos(test_repos)

        assert result == []

    @patch('ui.questionary.checkbox')
    def test_select_repos_truncates_long_description(self, mock_checkbox):
        """Test that long descriptions are truncated."""
        selector = RepoSelector()

        long_description = "A" * 100

        test_repos = [
            {
                "owner": "owner1",
                "name": "repo1",
                "full_name": "owner1/repo1",
                "url": "https://github.com/owner1/repo1",
                "description": long_description
            }
        ]

        mock_ask = MagicMock(return_value=[test_repos[0]])
        mock_checkbox.return_value.ask = mock_ask

        result = selector.select_repos(test_repos)

        assert len(result) == 1

    @patch('ui.questionary.confirm')
    def test_confirm_action_yes(self, mock_confirm):
        """Test confirming action."""
        selector = RepoSelector()

        mock_ask = MagicMock(return_value=True)
        mock_confirm.return_value.ask = mock_ask

        result = selector.confirm_action("Test message?")

        assert result is True

    @patch('ui.questionary.confirm')
    def test_confirm_action_no(self, mock_confirm):
        """Test declining action."""
        selector = RepoSelector()

        mock_ask = MagicMock(return_value=False)
        mock_confirm.return_value.ask = mock_ask

        result = selector.confirm_action("Test message?")

        assert result is False

    @patch('ui.questionary.confirm')
    def test_confirm_action_cancelled(self, mock_confirm):
        """Test cancelling confirm action."""
        selector = RepoSelector()

        mock_ask = MagicMock(return_value=None)
        mock_confirm.return_value.ask = mock_ask

        result = selector.confirm_action("Test message?")

        assert result is False

    @patch('ui.questionary.select')
    def test_select_action_scrape(self, mock_select):
        """Test selecting scrape action."""
        selector = RepoSelector()

        mock_ask = MagicMock(return_value="scrape")
        mock_select.return_value.ask = mock_ask

        result = selector.select_action()

        assert result == "scrape"

    @patch('ui.questionary.select')
    def test_select_action_load(self, mock_select):
        """Test selecting load action."""
        selector = RepoSelector()

        mock_ask = MagicMock(return_value="load")
        mock_select.return_value.ask = mock_ask

        result = selector.select_action()

        assert result == "load"

    @patch('ui.questionary.select')
    def test_select_action_exit(self, mock_select):
        """Test selecting exit action."""
        selector = RepoSelector()

        mock_ask = MagicMock(return_value="exit")
        mock_select.return_value.ask = mock_ask

        result = selector.select_action()

        assert result == "exit"

    @patch('ui.questionary.select')
    def test_select_action_cancelled(self, mock_select):
        """Test cancelling action selection."""
        selector = RepoSelector()

        mock_ask = MagicMock(return_value=None)
        mock_select.return_value.ask = mock_ask

        result = selector.select_action()

        assert result == "exit"

    @patch('ui.questionary.text')
    def test_get_github_url_valid(self, mock_text):
        """Test getting valid GitHub URL."""
        selector = RepoSelector()

        mock_ask = MagicMock(return_value="https://github.com/owner/repo")
        mock_text.return_value.ask = mock_ask

        result = selector.get_github_url()

        assert result == "https://github.com/owner/repo"

    @patch('ui.questionary.text')
    def test_get_github_url_cancelled(self, mock_text):
        """Test cancelling GitHub URL input."""
        selector = RepoSelector()

        mock_ask = MagicMock(return_value=None)
        mock_text.return_value.ask = mock_ask

        result = selector.get_github_url()

        assert result == ""

    def test_show_summary(self, capsys):
        """Test showing installation summary."""
        selector = RepoSelector()

        selector.show_summary(total=10, successful=8, failed=2)

        captured = capsys.readouterr()

        assert "Installation Summary" in captured.out
        assert "Total selected" in captured.out
        assert "10" in captured.out
        assert "Successfully added" in captured.out
        assert "8" in captured.out
        assert "Failed" in captured.out
        assert "2" in captured.out

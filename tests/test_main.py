"""Tests for main module."""

import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path


class TestMainWorkflow:
    """Test cases for main workflow."""

    @patch('main.SkillGenerator')
    @patch('main.RepoSelector')
    @patch('main.RepoStorage')
    @patch('main.RepoScraper')
    def test_main_exit_immediately(self, mock_scraper_class, mock_storage_class,
                                   mock_ui_class, mock_skill_gen_class):
        """Test exiting immediately."""
        from main import main

        mock_ui = MagicMock()
        mock_ui.select_action.return_value = "exit"
        mock_ui_class.return_value = mock_ui

        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper

        main()

        mock_ui.select_action.assert_called_once()
        mock_scraper.close.assert_called_once()

    @patch('main.SkillGenerator')
    @patch('main.RepoSelector')
    @patch('main.RepoStorage')
    @patch('main.RepoScraper')
    def test_main_scrape_no_url(self, mock_scraper_class, mock_storage_class,
                                mock_ui_class, mock_skill_gen_class):
        """Test scrape action with no URL provided."""
        from main import main

        mock_ui = MagicMock()
        mock_ui.select_action.return_value = "scrape"
        mock_ui.get_github_url.return_value = ""
        mock_ui_class.return_value = mock_ui

        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper

        main()

        mock_ui.select_action.assert_called_once()
        mock_ui.get_github_url.assert_called_once()
        mock_scraper.close.assert_called_once()

    @patch('main.SkillGenerator')
    @patch('main.RepoSelector')
    @patch('main.RepoStorage')
    @patch('main.RepoScraper')
    def test_main_scrape_no_repos_found(self, mock_scraper_class, mock_storage_class,
                                       mock_ui_class, mock_skill_gen_class):
        """Test scrape action with no repositories found."""
        from main import main

        mock_ui = MagicMock()
        mock_ui.select_action.return_value = "scrape"
        mock_ui.get_github_url.return_value = "https://github.com/owner/repo"
        mock_ui_class.return_value = mock_ui

        mock_scraper = MagicMock()
        mock_scraper.scrape_awesome_repo.return_value = []
        mock_scraper_class.return_value = mock_scraper

        main()

        mock_scraper.scrape_awesome_repo.assert_called_once()
        mock_scraper.close.assert_called_once()

    @patch('main.SkillExtractor')
    @patch('main.SkillDetector')
    @patch('main.SkillGenerator')
    @patch('main.RepoSelector')
    @patch('main.RepoStorage')
    @patch('main.RepoScraper')
    def test_main_scrape_success_no_details(self, mock_scraper_class, mock_storage_class,
                                           mock_ui_class, mock_skill_gen_class,
                                           mock_detector_class, mock_extractor_class):
        """Test successful scrape without fetching details."""
        from main import main
        from config import ExtractionConfig

        test_repos = [
            {
                "owner": "owner1",
                "name": "repo1",
                "full_name": "owner1/repo1",
                "url": "https://github.com/owner1/repo1"
            }
        ]

        config = ExtractionConfig.metadata_only()

        mock_ui = MagicMock()
        mock_ui.select_action.return_value = "scrape"
        mock_ui.get_github_url.return_value = "https://github.com/owner/awesome-list"
        mock_ui.confirm_action.return_value = False
        mock_ui.select_extraction_mode.return_value = config
        mock_ui.select_repos.return_value = [test_repos[0]]
        mock_ui_class.return_value = mock_ui

        mock_scraper = MagicMock()
        mock_scraper.scrape_awesome_repo.return_value = test_repos
        mock_scraper_class.return_value = mock_scraper

        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        mock_skill_gen = MagicMock()
        mock_skill_gen.generate_skill.return_value = True
        mock_skill_gen.skills_dir = Path("~/.claude/skills")
        mock_skill_gen_class.return_value = mock_skill_gen

        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        main()

        mock_scraper.scrape_awesome_repo.assert_called_once()
        mock_storage.save_repos.assert_called_once()
        mock_skill_gen.generate_skill.assert_called_once()
        mock_ui.show_summary.assert_called_once()

    @patch('main.SkillGenerator')
    @patch('main.RepoSelector')
    @patch('main.RepoStorage')
    @patch('main.RepoScraper')
    def test_main_scrape_success_with_details(self, mock_scraper_class, mock_storage_class,
                                             mock_ui_class, mock_skill_gen_class):
        """Test successful scrape with fetching details."""
        from main import main

        test_repos = [
            {
                "owner": "owner1",
                "name": "repo1",
                "full_name": "owner1/repo1",
                "url": "https://github.com/owner1/repo1"
            },
            {
                "owner": "owner2",
                "name": "repo2",
                "full_name": "owner2/repo2",
                "url": "https://github.com/owner2/repo2"
            }
        ]

        mock_ui = MagicMock()
        mock_ui.select_action.return_value = "scrape"
        mock_ui.get_github_url.return_value = "https://github.com/owner/awesome-list"
        mock_ui.confirm_action.return_value = True
        mock_ui.select_repos.return_value = test_repos
        mock_ui_class.return_value = mock_ui

        mock_scraper = MagicMock()
        mock_scraper.scrape_awesome_repo.return_value = test_repos
        mock_scraper_class.return_value = mock_scraper

        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        mock_skill_gen = MagicMock()
        mock_skill_gen.generate_skill.return_value = True
        mock_skill_gen.skills_dir = Path("~/.claude/skills")
        mock_skill_gen_class.return_value = mock_skill_gen

        main()

        assert mock_scraper.fetch_repo_details.call_count == 2
        mock_storage.save_repos.assert_called_once()

    @patch('main.SkillGenerator')
    @patch('main.RepoSelector')
    @patch('main.RepoStorage')
    @patch('main.RepoScraper')
    def test_main_load_no_file(self, mock_scraper_class, mock_storage_class,
                               mock_ui_class, mock_skill_gen_class):
        """Test load action with no existing file."""
        from main import main

        mock_ui = MagicMock()
        mock_ui.select_action.return_value = "load"
        mock_ui_class.return_value = mock_ui

        mock_storage = MagicMock()
        mock_storage.exists.return_value = False
        mock_storage_class.return_value = mock_storage

        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper

        main()

        mock_storage.exists.assert_called_once()
        mock_scraper.close.assert_called_once()

    @patch('main.SkillExtractor')
    @patch('main.SkillDetector')
    @patch('main.SkillGenerator')
    @patch('main.RepoSelector')
    @patch('main.RepoStorage')
    @patch('main.RepoScraper')
    def test_main_load_success(self, mock_scraper_class, mock_storage_class,
                               mock_ui_class, mock_skill_gen_class,
                               mock_detector_class, mock_extractor_class):
        """Test successful load from storage."""
        from main import main
        from config import ExtractionConfig

        test_repos = [
            {
                "owner": "owner1",
                "name": "repo1",
                "full_name": "owner1/repo1",
                "url": "https://github.com/owner1/repo1"
            }
        ]

        config = ExtractionConfig.metadata_only()

        mock_ui = MagicMock()
        mock_ui.select_action.return_value = "load"
        mock_ui.select_extraction_mode.return_value = config
        mock_ui.select_repos.return_value = test_repos
        mock_ui_class.return_value = mock_ui

        mock_storage = MagicMock()
        mock_storage.exists.return_value = True
        mock_storage.load_repos.return_value = test_repos
        mock_storage_class.return_value = mock_storage

        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper

        mock_skill_gen = MagicMock()
        mock_skill_gen.generate_skill.return_value = True
        mock_skill_gen.skills_dir = Path("~/.claude/skills")
        mock_skill_gen_class.return_value = mock_skill_gen

        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        main()

        mock_storage.load_repos.assert_called_once()
        mock_skill_gen.generate_skill.assert_called_once()

    @patch('main.SkillGenerator')
    @patch('main.RepoSelector')
    @patch('main.RepoStorage')
    @patch('main.RepoScraper')
    def test_main_no_repos_selected(self, mock_scraper_class, mock_storage_class,
                                    mock_ui_class, mock_skill_gen_class):
        """Test when no repositories are selected."""
        from main import main

        test_repos = [
            {
                "owner": "owner1",
                "name": "repo1",
                "full_name": "owner1/repo1",
                "url": "https://github.com/owner1/repo1"
            }
        ]

        mock_ui = MagicMock()
        mock_ui.select_action.return_value = "load"
        mock_ui.select_repos.return_value = []
        mock_ui_class.return_value = mock_ui

        mock_storage = MagicMock()
        mock_storage.exists.return_value = True
        mock_storage.load_repos.return_value = test_repos
        mock_storage_class.return_value = mock_storage

        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper

        main()

        mock_storage.load_repos.assert_called_once()

    @patch('main.SkillGenerator')
    @patch('main.RepoSelector')
    @patch('main.RepoStorage')
    @patch('main.RepoScraper')
    def test_main_keyboard_interrupt(self, mock_scraper_class, mock_storage_class,
                                    mock_ui_class, mock_skill_gen_class):
        """Test handling keyboard interrupt."""
        from main import main

        mock_ui = MagicMock()
        mock_ui.select_action.side_effect = KeyboardInterrupt()
        mock_ui_class.return_value = mock_ui

        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper

        main()

        mock_scraper.close.assert_called_once()

    @patch('main.SkillGenerator')
    @patch('main.RepoSelector')
    @patch('main.RepoStorage')
    @patch('main.RepoScraper')
    def test_main_unexpected_error(self, mock_scraper_class, mock_storage_class,
                                   mock_ui_class, mock_skill_gen_class):
        """Test handling unexpected error."""
        from main import main

        mock_ui = MagicMock()
        mock_ui.select_action.side_effect = ValueError("Test error")
        mock_ui_class.return_value = mock_ui

        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper

        main()

        mock_scraper.close.assert_called_once()

    @patch('main.SkillExtractor')
    @patch('main.SkillDetector')
    @patch('main.SkillGenerator')
    @patch('main.RepoSelector')
    @patch('main.RepoStorage')
    @patch('main.RepoScraper')
    def test_main_skill_generation_partial_failure(self, mock_scraper_class, mock_storage_class,
                                                   mock_ui_class, mock_skill_gen_class,
                                                   mock_detector_class, mock_extractor_class):
        """Test when some skills fail to generate."""
        from main import main
        from config import ExtractionConfig

        test_repos = [
            {
                "owner": "owner1",
                "name": "repo1",
                "full_name": "owner1/repo1",
                "url": "https://github.com/owner1/repo1"
            },
            {
                "owner": "owner2",
                "name": "repo2",
                "full_name": "owner2/repo2",
                "url": "https://github.com/owner2/repo2"
            },
            {
                "owner": "owner3",
                "name": "repo3",
                "full_name": "owner3/repo3",
                "url": "https://github.com/owner3/repo3"
            }
        ]

        config = ExtractionConfig.metadata_only()

        mock_ui = MagicMock()
        mock_ui.select_action.return_value = "load"
        mock_ui.select_extraction_mode.return_value = config
        mock_ui.select_repos.return_value = test_repos
        mock_ui_class.return_value = mock_ui

        mock_storage = MagicMock()
        mock_storage.exists.return_value = True
        mock_storage.load_repos.return_value = test_repos
        mock_storage_class.return_value = mock_storage

        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper

        mock_skill_gen = MagicMock()
        mock_skill_gen.generate_skill.side_effect = [True, False, True]
        mock_skill_gen.skills_dir = Path("~/.claude/skills")
        mock_skill_gen_class.return_value = mock_skill_gen

        mock_detector = MagicMock()
        mock_detector_class.return_value = mock_detector

        main()

        mock_ui.show_summary.assert_called_once()

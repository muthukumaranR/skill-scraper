"""Tests for config module."""

import pytest
from config import ExtractionConfig


class TestExtractionConfig:
    """Test cases for ExtractionConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = ExtractionConfig()

        assert config.mode == "metadata"
        assert config.auto_detect is True
        assert config.confirm_extraction is True
        assert config.max_skills_per_repo == 50
        assert config.skip_existing is True
        assert config.clone_depth == 1

    def test_metadata_only_preset(self):
        """Test metadata-only preset."""
        config = ExtractionConfig.metadata_only()

        assert config.mode == "metadata"
        assert config.auto_detect is False

    def test_extract_all_preset(self):
        """Test extract-all preset."""
        config = ExtractionConfig.extract_all()

        assert config.mode == "extract"
        assert config.auto_detect is True
        assert config.confirm_extraction is False

    def test_smart_mode_preset(self):
        """Test smart mode preset."""
        config = ExtractionConfig.smart_mode()

        assert config.mode == "both"
        assert config.auto_detect is True
        assert config.confirm_extraction is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = ExtractionConfig(
            mode="extract",
            max_skills_per_repo=100,
            skip_existing=False
        )

        assert config.mode == "extract"
        assert config.max_skills_per_repo == 100
        assert config.skip_existing is False

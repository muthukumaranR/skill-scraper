"""Tests for skill_detector module."""

import pytest
from skill_detector import SkillDetector


class TestSkillDetector:
    """Test cases for SkillDetector class."""

    def test_detector_initialization(self):
        """Test detector can be initialized."""
        detector = SkillDetector()
        assert detector is not None
        detector.close()

    def test_check_readme_indicators(self):
        """Test README keyword detection."""
        detector = SkillDetector()

        indicators = detector._check_readme("anthropics", "skills")

        assert isinstance(indicators, list)

        detector.close()

    def test_detect_skills_structure(self):
        """Test detection result structure."""
        detector = SkillDetector()

        test_repo = {
            "owner": "test",
            "name": "test-repo",
            "full_name": "test/test-repo",
            "url": "https://github.com/test/test-repo"
        }

        result = detector.detect_skills(test_repo)

        assert "is_skill_repo" in result
        assert "skill_count" in result
        assert "structure" in result
        assert "confidence" in result
        assert "indicators" in result

        assert isinstance(result["is_skill_repo"], bool)
        assert isinstance(result["skill_count"], int)
        assert isinstance(result["confidence"], float)
        assert isinstance(result["indicators"], list)

        detector.close()

    def test_close_detector(self):
        """Test detector can be closed."""
        detector = SkillDetector()
        detector.close()

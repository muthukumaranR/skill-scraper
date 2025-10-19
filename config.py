"""Configuration module for skill scraper."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ExtractionConfig:
    """Configuration for skill extraction behavior."""

    mode: Literal["metadata", "extract", "both"] = "metadata"
    """How to handle skill repositories:
    - metadata: Create wrapper SKILL.md pointing to repo (fast)
    - extract: Download and extract actual skills from repos (thorough)
    - both: Create metadata AND extract actual skills
    """

    auto_detect: bool = True
    """Automatically detect if a repo contains skills"""

    confirm_extraction: bool = True
    """Ask for confirmation before extracting skills from detected repos"""

    max_skills_per_repo: int = 50
    """Maximum number of skills to extract from a single repository"""

    skip_existing: bool = True
    """Skip skills that already exist"""

    clone_depth: int = 1
    """Git clone depth (1 = shallow clone for speed)"""

    temp_dir: str = "/tmp/skill-scraper-clone"
    """Temporary directory for cloning repositories"""

    @classmethod
    def from_interactive(cls) -> "ExtractionConfig":
        """Create config from interactive prompts."""
        return cls()

    @classmethod
    def metadata_only(cls) -> "ExtractionConfig":
        """Quick mode - metadata only."""
        return cls(mode="metadata", auto_detect=False)

    @classmethod
    def extract_all(cls) -> "ExtractionConfig":
        """Full extraction mode."""
        return cls(mode="extract", auto_detect=True, confirm_extraction=False)

    @classmethod
    def smart_mode(cls) -> "ExtractionConfig":
        """Smart mode - detect and ask."""
        return cls(mode="both", auto_detect=True, confirm_extraction=True)

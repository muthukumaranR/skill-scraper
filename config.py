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

    update_existing: bool = False
    """Update existing skills instead of skipping them"""

    clone_depth: int = 1
    """Git clone depth (1 = shallow clone for speed)"""

    temp_dir: str = "/tmp/skill-scraper-clone"
    """Temporary directory for cloning repositories"""

    selection_mode: Literal["auto", "manual"] = "manual"
    """Post-extraction skill selection mode:
    - auto: Automatically install all extracted skills
    - manual: Show review UI and let user select which skills to install
    """

    install_location: Literal["local", "global"] = "global"
    """Installation location for skills:
    - global: ~/.claude/skills (available to all Claude Code instances)
    - local: ./.claude/skills (project-specific skills)
    """

    show_skill_review: bool = True
    """Show post-extraction review UI with skill metadata"""

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

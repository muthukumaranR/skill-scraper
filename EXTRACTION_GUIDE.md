# Skill Extraction Guide

This guide explains the new skill extraction features in detail.

## Overview

The skill scraper now has the ability to detect and extract actual skills from skill repositories (like `anthropics/skills` or `obra/superpowers`), not just create metadata references.

## Extraction Modes

### 🎯 Smart Mode (Recommended)

**Best for**: Most use cases

Smart Mode automatically detects which repositories contain actual skills and handles them appropriately:
- Detects skill repositories by looking for `SKILL.md` files and skills folders
- Extracts real skills from detected repositories
- Creates metadata references for regular repositories
- Shows detection confidence and estimated skill count in the UI

**Example**:
```
? How should skill repositories be handled?
> 🎯 Smart Mode: Auto-detect and extract actual skills (recommended)
```

### 📦 Extract Only

**Best for**: When you know most/all repositories contain skills

Extract Only mode treats all repositories as potential skill collections:
- Downloads every selected repository
- Searches for `SKILL.md` files in each repo
- Extracts any skills found
- Slower but most thorough

**Example**:
```
? How should skill repositories be handled?
> 📦 Extract Only: Download and install actual skills from repositories
```

### 📝 Metadata Only

**Best for**: Quick exploration or manual control

Metadata Only mode creates lightweight reference skills:
- No cloning or downloading
- Creates `SKILL.md` files that point to the repository
- Fastest option
- Good for browsing before committing to full extraction

**Example**:
```
? How should skill repositories be handled?
> 📝 Metadata Only: Create reference skills pointing to repositories (fast)
```

## How Detection Works

The skill detector analyzes repositories to determine if they contain Claude skills:

### README Analysis
- Searches for keywords like "claude skill", "SKILL.md", "skills folder"
- Counts mentions of SKILL.md files
- Higher keyword matches = higher confidence

### Repository Structure Analysis
- Uses GitHub API to examine repo file tree
- Looks for `SKILL.md` files
- Checks for `skills/` directory
- Counts actual skill files found

### Confidence Scoring
- Each indicator adds to confidence score
- Displayed as percentage in UI
- Example: `[🎯 ~5 skills, 90%]`

## UI Experience

### Repository Selection

When skill detection is enabled, the UI shows rich metadata:

```
Found 8 repositories
Detected 3 skill repositories (marked with 🎯)
================================================================================

? Select repositories to add as Claude skills:
 » ○ anthropics/skills: Skills are folders... [🎯 ~12 skills, 100%]
   ○ regular-repo/tool: A useful tool for...
   ○ obra/superpowers: Give Claude Code... [🎯 ~25 skills, 90%]
```

### Extraction Confirmation

If configured, you'll be asked before extracting from each repository:

```
? Extract ~12 skills from anthropics/skills (confidence: 100%)? Yes
```

### Installation Summary

The summary shows detailed extraction statistics:

```
================================================================================
INSTALLATION SUMMARY
================================================================================
Total selected:     5
Successfully added: 3
Skills extracted:   37
Failed:             0
Mode:               Smart Mode (Metadata + Extract)
================================================================================
```

## Example Workflows

### Scenario 1: Scraping an Awesome List of Skills

```bash
$ uv run python main.py

? What would you like to do? Scrape new awesome list
? Enter the GitHub URL: https://github.com/BehiSecc/awesome-claude-skills
? Fetch detailed descriptions? Yes

# ... fetching ...

? How should skill repositories be handled?
> 🎯 Smart Mode: Auto-detect and extract actual skills (recommended)
? Ask for confirmation before extracting? No

# ... detecting ...

Detected 5 skill repositories

? Select repositories to add:
 » ☑ anthropics/skills [🎯 ~12 skills, 100%]
   ☑ obra/superpowers [🎯 ~25 skills, 90%]

# ... extracting ...

Extracting skills from anthropics/skills...
Extracted 12 skills from anthropics/skills

Successfully installed 37 skills!
```

### Scenario 2: Quick Metadata-Only Browse

```bash
$ uv run python main.py

? What would you like to do? Load from existing repos.json

? How should skill repositories be handled?
> 📝 Metadata Only: Create reference skills pointing to repositories (fast)

# ... quick installation of metadata references ...

Total selected:     10
Successfully added: 10
Mode:               Metadata Only
```

### Scenario 3: Targeted Extraction

```bash
$ uv run python main.py

? What would you like to do? Load from existing repos.json

? How should skill repositories be handled?
> 🎯 Smart Mode: Auto-detect and extract actual skills (recommended)
? Ask for confirmation before extracting? Yes

Detected 3 skill repositories

? Select repositories:
 » ☑ anthropics/skills [🎯 ~12 skills, 100%]

? Extract ~12 skills from anthropics/skills (confidence: 100%)? Yes

Extracting...
Extracted 12 skills from anthropics/skills

Total selected:     1
Skills extracted:   12
```

## Extracted Skill Structure

Extracted skills maintain their original structure and get enriched with metadata:

```
~/.claude/skills/
  anthropics-prompt-engineering/
    SKILL.md              # Original skill content
    examples/             # Original resource folder
    templates/            # Original resource folder

  anthropics-debugging/
    SKILL.md              # + Extraction metadata footer
    scripts/
      debug.py
```

### Metadata Footer

Extracted skills get an automatic footer:

```markdown
---
**Extracted from**: [anthropics/skills](https://github.com/anthropics/skills)
**Detection confidence**: 100%
**Installed as**: anthropics-prompt-engineering
```

## Configuration Options

Advanced users can customize extraction behavior via `config.py`:

```python
from config import ExtractionConfig

# Create custom config
config = ExtractionConfig(
    mode="both",                    # metadata | extract | both
    auto_detect=True,               # Auto-detect skills
    confirm_extraction=False,       # Skip confirmation prompts
    max_skills_per_repo=50,        # Limit skills per repo
    skip_existing=True,             # Skip already installed
    clone_depth=1,                  # Git clone depth
)
```

## Troubleshooting

### No Skills Detected

If repositories aren't being detected as skill repos:
- Check if they actually contain `SKILL.md` files
- Try "Extract Only" mode to force extraction
- Detection requires either README keywords or GitHub API access

### Extraction Fails

Common issues:
- **Git not installed**: Extraction requires `git` command
- **Network issues**: Check internet connection
- **Rate limiting**: GitHub API may be rate-limited (switch to README-only detection)
- **Permission denied**: Check repository is public

### Skills Not Installing

- Check `skill_scraper.log` for detailed error messages
- Verify `~/.claude/skills` directory is writable
- Ensure no name conflicts with existing skills

## Performance Tips

1. **Use Smart Mode** for best balance of speed and thoroughness
2. **Save repos.json** and reuse it to avoid re-scraping
3. **Disable confirmations** for batch extraction: `confirm_extraction=False`
4. **Limit max skills** if repos have many skills: `max_skills_per_repo=10`
5. **Use shallow clones** (default): `clone_depth=1`

## See Also

- [README.md](README.md) - Main documentation
- [WORKFLOW.md](WORKFLOW.md) - Technical workflow details
- [config.py](config.py) - Configuration options

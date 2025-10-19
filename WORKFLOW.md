# Skill Scraper Workflow

## Overview

This tool automates the process of discovering GitHub repositories from awesome-* lists and converting them into Claude Code skills.

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     1. SELECT ACTION                        │
│  ┌─────────────────┐              ┌────────────────────┐   │
│  │ Scrape New List │      or      │ Load Existing Data │   │
│  └────────┬────────┘              └─────────┬──────────┘   │
└───────────┼───────────────────────────────────┼─────────────┘
            │                                   │
            v                                   v
┌───────────────────────┐           ┌──────────────────────┐
│   2a. SCRAPE REPOS    │           │   2b. LOAD REPOS     │
│                       │           │                      │
│ • Fetch README.md     │           │ • Read repos.json    │
│ • Extract GitHub URLs │           │                      │
│ • Deduplicate         │           │                      │
│ • Fetch descriptions  │           │                      │
│ • Save to repos.json  │           │                      │
└───────────┬───────────┘           └──────────┬───────────┘
            │                                   │
            └───────────────┬───────────────────┘
                            v
            ┌───────────────────────────────┐
            │   3. SELECT REPOSITORIES      │
            │                               │
            │ Interactive checkbox UI:      │
            │ • Arrow keys to navigate      │
            │ • Space to select/deselect    │
            │ • 'a' to toggle all           │
            │ • Enter to confirm            │
            └───────────────┬───────────────┘
                            v
            ┌───────────────────────────────┐
            │   4. GENERATE SKILLS          │
            │                               │
            │ For each selected repo:       │
            │ • Create SKILL.md             │
            │ • Add YAML frontmatter        │
            │ • Include description         │
            │ • Copy to ~/.claude/skills    │
            └───────────────┬───────────────┘
                            v
            ┌───────────────────────────────┐
            │   5. SUMMARY & COMPLETION     │
            │                               │
            │ • Total selected              │
            │ • Successfully installed      │
            │ • Failed (already exist)      │
            └───────────────────────────────┘
```

## Data Flow

### Input Sources
- **GitHub awesome-* repository URL** (e.g., `https://github.com/sindresorhus/awesome`)
- **Existing repos.json file** (from previous scrapes)

### Processing Steps

1. **Scraping** (`scraper.py`)
   - Fetches raw README content from GitHub
   - Uses regex to extract GitHub repository URLs
   - Deduplicates based on owner/repo combination
   - Optionally fetches descriptions from each repo's README

2. **Storage** (`storage.py`)
   - Saves/loads repository data as JSON
   - Structure: `[{owner, name, full_name, url, description}, ...]`

3. **Selection** (`ui.py`)
   - Interactive terminal UI using questionary
   - Multi-select checkbox interface
   - Returns selected repositories

4. **Skill Generation** (`skill_generator.py`)
   - Creates `~/.claude/skills/{owner}-{repo}/SKILL.md`
   - YAML frontmatter with name and description
   - Markdown content with repository information

### Output
- **Skills directory**: `~/.claude/skills/`
- **Cached data**: `repos.json`
- **Logs**: `skill_scraper.log`

## SKILL.md Format

Each generated skill follows this format:

```markdown
---
name: owner/repo
description: Repository description
---

# owner/repo

GitHub Repository: https://github.com/owner/repo

## Description

Repository description here.

## Usage

This skill provides context about the repo repository by owner.

Visit the repository for more information: https://github.com/owner/repo
```

## Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `main.py` | Orchestrates workflow, handles errors |
| `scraper.py` | Fetches and parses GitHub repositories |
| `storage.py` | Persists repository data to JSON |
| `ui.py` | Interactive terminal interface |
| `skill_generator.py` | Creates SKILL.md files and installs |

## Error Handling

- **Network errors**: Logged and skipped (continues with other repos)
- **Invalid URLs**: Validated before scraping
- **Duplicate skills**: Skipped with warning
- **Missing files**: Graceful fallback to default values
- **User cancellation**: Clean exit via Ctrl+C

## Logging

All operations are logged with loguru:
- **Console**: INFO level (user-facing)
- **File**: DEBUG level (detailed troubleshooting)
- **Format**: Timestamp, level, message
- **Rotation**: 10MB max, 7 days retention

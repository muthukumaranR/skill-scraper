# Prompt Visibility Fix

## Issue
User-facing confirmation prompts were not visible due to Rich progress bars and console output covering questionary prompts.

## Root Cause
- Rich console output was printing immediately before questionary prompts
- Progress bars were leaving the terminal in a state that obscured prompts
- No visual separation between Rich output and questionary input

## Solution Implemented

### 1. Added Spacing Before All Prompts
Every questionary prompt now has a blank line before it:

```python
def confirm_action(self, message: str) -> bool:
    self.console.print()  # ← Add spacing before prompt
    result = questionary.confirm(message).ask()
    return result if result is not None else False
```

Applied to:
- `select_action()` - Main action selection
- `get_github_url()` - URL input
- `select_extraction_mode()` - Mode selection
- `confirm_action()` - All confirmation prompts
- `confirm_skill_extraction()` - Per-repo extraction confirmation

### 2. Progress Bar Isolation
Added spacing before and after progress bars to ensure clean separation:

```python
# Before progress bar
console.print()  # Clear line

with ui.show_progress(...) as progress:
    # ... progress operations ...

# After progress bar
console.print()  # Clear line
```

Applied to three progress bar locations:
1. **Fetching repository details** (main.py:94, 105)
2. **Detecting skill repositories** (main.py:132, 143)
3. **Installing skills** (main.py:155, 204)

### 3. Status Message Enhancements
Added clear status messages with proper spacing:

```python
# After scraping
ui.print_status(f"\n✓ Found [green]{len(repos)}[/green] repositories\n", style="bold")

# After saving
ui.print_status("✓ Saved repositories to repos.json\n", style="green")

# After loading
ui.print_status(f"✓ Loaded [green]{len(repos)}[/green] repositories from storage\n", style="bold")

# After detection
ui.print_status(f"✓ Detected [green]{skill_repo_count}[/green] skill repositories\n", style="bold")
```

## Visual Flow Improvement

### Before (Prompts Hidden)
```
⠋ Fetching: anthropics/skills ━━━━━━━━━━━━━━ 100% 8/8
? Fetch detailed descriptions? (This may take a while)  ← HIDDEN!
```

### After (Prompts Visible)
```
⠋ Fetching: anthropics/skills ━━━━━━━━━━━━━━ 100% 8/8

✓ Found 8 repositories

? Fetch detailed descriptions? (This may take a while)  ← VISIBLE!
```

## Complete User Flow Example

```bash
╔══════════════════════════════════════════════════════╗
║  ____  _    _ _ _    ____                            ║
║ / ___|| | _(_) | |  / ___|  ___ _ __ __ _ _ __   ___ ║
║ [... banner ...]                                     ║
╚══════════════════════════════════════════════════════╝

? What would you like to do? (Use arrow keys)
 » Scrape new awesome list
   Load from existing repos.json
   Exit

? Enter the GitHub URL of an awesome-* repository:
https://github.com/BehiSecc/awesome-claude-skills

✓ Found 8 repositories

? Fetch detailed descriptions? (This may take a while) (Y/n)
Yes

⠋ Fetching: anthropics/skills ━━━━━━━━━━━━━━ 100% 8/8

✓ Saved repositories to repos.json

? How should skill repositories be handled? (Use arrow keys)
 » 🎯 Smart Mode: Auto-detect and extract actual skills (recommended)
   📦 Extract Only: Download and install actual skills from repositories
   📝 Metadata Only: Create reference skills pointing to repositories (fast)

? Ask for confirmation before extracting skills from each repository? (Y/n)
No

⠙ Checking: anthropics/skills ━━━━━━━━━━━━━━ 100% 8/8

✓ Detected 3 skill repositories

      📦 Found 8 Repositories
╭──────────────────────────────────╮
│ 🎯 Detected 3 skill repositories │
╰──────────────────────────────────╯

Use arrow keys to navigate, space to select/deselect, 'a' to toggle all, enter to confirm

? Select repositories to add as Claude skills: (Use arrow keys)
 » ○ anthropics/skills [🎯 ~12 skills, 100%]
   ○ obra/superpowers [🎯 ~25 skills, 90%]

⠹ Processing: anthropics/skills ━━━━━━━━━━━━ 100% 2/2

                  ✨ Installation Summary
╔════════════════════╦════════════════════════════════════╗
║ Total selected     ║                                  2 ║
║ Successfully added ║                                  2 ║
║ Skills extracted   ║                                 37 ║
║ Failed             ║                                  0 ║
║ Mode               ║ 🎯 Smart Mode (Metadata + Extract) ║
╚════════════════════╩════════════════════════════════════╝
```

## Changes Summary

### Files Modified
1. **ui.py** - Added `console.print()` before all questionary prompts (6 locations)
2. **main.py** - Added spacing before/after progress bars (6 locations) + status messages (4 locations)

### Code Additions
- 6 lines: Spacing before prompts
- 6 lines: Spacing around progress bars
- 4 lines: Enhanced status messages
- **Total: 16 lines added for improved UX**

## Testing

All 61 tests pass:
```bash
$ uv run pytest tests/ -v
======================== 61 passed, 1 warning in 1.85s =========================
```

## User Impact

### Before
- ❌ Prompts often hidden by progress bars
- ❌ Confusing workflow interruptions
- ❌ User doesn't know what's being asked
- ❌ Poor terminal state management

### After
- ✅ All prompts clearly visible
- ✅ Clean separation between operations
- ✅ Clear status messages
- ✅ Professional user experience
- ✅ Progress bars properly isolated

## Implementation Details

### Spacing Strategy
1. **Before prompts**: `console.print()` adds a blank line
2. **Before progress bars**: `console.print()` ensures clean start
3. **After progress bars**: `console.print()` clears terminal state
4. **Status messages**: Include `\n` for proper spacing

### Why It Works
- Rich console and questionary both write to stdout
- Rich can leave terminal in states that affect questionary rendering
- Explicit blank lines ensure clean transitions
- Status messages provide context between operations

## Backward Compatibility

✅ **Fully compatible** - No breaking changes:
- All tests pass unchanged
- Workflow logic identical
- Only visual improvements
- No API changes

## Future Enhancements

Potential improvements:
- Dynamic spacing based on terminal height
- Smart detection of terminal state
- Progress bar cleanup hooks
- Custom questionary themes matching Rich colors

## Conclusion

Simple, effective fix that dramatically improves UX:
- 16 lines of code
- 100% backward compatible
- All prompts now clearly visible
- Professional, polished experience

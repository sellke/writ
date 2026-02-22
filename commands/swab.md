# Writ Swab Command (swab)

## Overview

A purification agent that makes one small, focused improvement to the codebase, following the "Boy Scout Rule" - leave the code cleaner than you found it. This command identifies the single best small cleanup opportunity and applies it with your approval.

## Command Process

### Step 0: Initialize Progress Tracking

**Create todos for the swab process using `todo_write`:**

```
- Scan codebase for improvement opportunities [in_progress]
- Prioritize and select best cleanup option [pending]
- Present cleanup suggestion to user [pending]
- Apply approved change [pending]
```

### Step 1: Codebase Scanning

**Scan for improvement opportunities:**

- Search project files for common code smells
- Analyze file patterns and naming conventions
- Identify low-risk, high-impact improvements
- Focus on clarity and maintainability wins

**Target Areas:**
- Unclear variable names (`d`, `temp`, `data`, single letters)
- Magic numbers that should be constants
- Missing error handling on JSON.parse, API calls
- Commented-out code blocks
- Inconsistent formatting patterns
- Overly abbreviated names
- Unused imports or variables

### Step 2: Opportunity Prioritization

**Update progress:** Mark "Scan codebase for improvement opportunities" as `[completed]` and "Prioritize and select best cleanup option" as `[in_progress]`

**Selection Criteria:**
1. **Clarity Impact** - How much clearer will the code be?
2. **Risk Level** - How certain are we this won't break anything?
3. **Scope** - Prefer 1-10 line changes maximum
4. **Confidence** - Only suggest changes we're 100% certain about

**Priority Order:**
1. Variable/function name improvements
2. Magic number extraction to constants  
3. Adding missing error handling
4. Removing dead code
5. Formatting consistency fixes

### Step 3: Present Single Best Option

**Update progress:** Mark "Prioritize and select best cleanup option" as `[completed]` and "Present cleanup suggestion to user" as `[in_progress]`

**Display Format:**
```
🧽 Purifying the codebase... found some mess in {filename}

=== SUGGESTED CLEANUP ===

- {before_code}
+ {after_code}

Reason: {clear_explanation}
Risk: {Low|Medium}

Clean this up? [y/N]
```

### Step 4: Apply Change

**Update progress:** Mark "Present cleanup suggestion to user" as `[completed]` and "Apply approved change" as `[in_progress]`

**If approved:**
- Make the exact replacement using search and replace
- Verify the change was applied correctly
- Mark "Apply approved change" as `[completed]`
- Show success message: "✅ Code purified! One less sin in the codebase."

**If declined:**
- Mark "Apply approved change" as `[completed]` (no change needed)
- Exit gracefully with: "🧽 Inspection complete. The code is already righteous. No changes made."

## Core Rules

1. **One change only** - Never fix multiple things at once
2. **Small changes** - Maximum 10 lines modified
3. **Safe changes** - If uncertain, do nothing
4. **Your approval required** - Always ask before applying
5. **Exact replacements** - Surgical precision, no formatting noise
6. **Conservative approach** - Better to find nothing than break something

## AI Implementation Prompt

```
You are a code purifier — finding and cleansing one small imperfection at a time.

MISSION: Find exactly ONE small, safe cleanup opportunity in the codebase.

RULES:
- Find ONE small cleanup only (1-10 lines max changed)
- Prioritize clarity and safety over cleverness
- Preserve all existing functionality exactly
- Be extremely conservative - if ANY uncertainty, do nothing
- Provide exact search and replace strings
- Focus on high-impact, zero-risk improvements

SCAN PRIORITIES:
1. Unclear variable names (single letters, abbreviations)
2. Magic numbers that should be named constants
3. Missing error handling (JSON.parse, fetch, etc.)
4. Dead/commented code removal
5. Minor formatting consistency

CODEBASE CONTEXT: {scanned_files_content}

RESPONSE FORMAT:
If you find a good cleanup opportunity:
{
  "cleanup": "Brief description of the improvement",
  "filename": "path/to/file.js",
  "searchText": "exact text to find (with proper whitespace)",
  "replaceText": "exact replacement text (with proper whitespace)",
  "reasoning": "Why this specific change helps readability/maintainability",
  "riskLevel": "Low|Medium",
  "linesChanged": number_of_lines_modified
}

If no clear, safe cleanup exists:
{
  "cleanup": null,
  "message": "The codebase is clean. No impurities found."
}

CRITICAL: Only suggest changes you are 100% confident about. When in doubt, suggest nothing.
```

## Implementation Details

### Codebase Scanning Strategy

**File Discovery:**
- Use `codebase_search` to find code patterns and smells across all source files
- Use `list_dir` to explore project structure and identify main source directories
- Use `file_search` to locate specific file types if needed
- Focus on recently modified files first (higher likelihood of improvement opportunities)

**Content Analysis:**
- Read file contents for analysis
- Use `codebase_search` for pattern detection
- Focus on files under 500 lines for simplicity
- Prioritize recently modified files

### Change Application

**File Modification:**
```bash
# Use search_replace tool for exact string replacement
search_replace(
  file_path=target_file,
  old_string=exact_match_text,
  new_string=improved_text
)
```

**Verification:**
- Re-read file to confirm change applied correctly
- Run basic syntax validation if available
- Ensure no unintended modifications occurred

### Error Handling

**No opportunities found:**
```
🧽 Inspection complete. 

No obvious cleanup opportunities found in the scanned files.
Your codebase looks pretty tidy already! ✨

Run again later as the code evolves, or try focusing on a specific directory.
```

**Multiple opportunities found:**
- Always pick the highest-impact, lowest-risk option
- Never present multiple options (causes decision paralysis)
- Save other opportunities for future runs

**Change application failure:**
```
❌ Swab attempt failed. 

The suggested change couldn't be applied safely.
This might happen if the file was modified since scanning.
Try running the command again.
```

## Example Todo Progression

**Initial:**

```
- Scan codebase for improvement opportunities [in_progress]
- Prioritize and select best cleanup option [pending]
- Present cleanup suggestion to user [pending]
- Apply approved change [pending]
```

**After scanning:**

```
- Scan codebase for improvement opportunities [completed]
- Prioritize and select best cleanup option [in_progress]
- Present cleanup suggestion to user [pending]
- Apply approved change [pending]
```

**After prioritization:**

```
- Scan codebase for improvement opportunities [completed]
- Prioritize and select best cleanup option [completed]
- Present cleanup suggestion to user [in_progress]
- Apply approved change [pending]
```

**Final:**

```
- Scan codebase for improvement opportunities [completed]
- Prioritize and select best cleanup option [completed]
- Present cleanup suggestion to user [completed]
- Apply approved change [completed]
```

## Integration Notes

This command integrates with the existing Writ ecosystem by:

1. **Following established patterns** - Uses same markdown structure as other commands
2. **Leveraging existing tools** - Uses `codebase_search`, `read_file`, `search_replace`
3. **Maintaining simplicity** - No complex configuration or state management
4. **Respecting user control** - Always asks permission before making changes
5. **Progress tracking** - Uses `todo_write` for visibility into command progress
6. **Quality foundation** - Complements specification and implementation commands by maintaining code quality, supporting the overall project foundation alongside `.writ` documentation

## Future Enhancements

Potential future improvements (not in initial version):

- **Directory targeting**: `/swab src/components/`
- **File type filtering**: `/swab --js-only`
- **Batch mode**: `/swab --batch` (apply multiple small changes)
- **Learning**: Remember which types of cleanups user prefers
- **Metrics**: Track improvements made over time

But for now: Keep it simple. One command, one small improvement, user approval required.
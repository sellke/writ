# Writ Status Command (status)

## Overview
A command that provides developers with a comprehensive status report when starting work or switching context. Analyzes current git state, active work, and project health to orient developers and suggest next actions.

## Command Structure

```bash
/status
```

Simple, no parameters needed. Works in any git repository with optional Writ project structure.

## Core Functionality

### 1. Git Status & Context Analysis
**Current Position:**
- Branch name and relationship to main/origin
- Commits ahead/behind main branch
- Last commit message and timestamp
- Uncommitted changes summary (files modified, added, deleted)
- Stash status if any

**Recent Activity:**
- Last 3-5 commits on current branch
- Recent activity on main branch that might affect current work
- Branch age and creation context

### 2. Active Work Detection
**Writ Integration:**
- Scan `.writ/specs/` for active specifications
- Parse current task progress from most recent spec's tasks.md
- Identify completed vs pending tasks
- Determine current user story context

**Project Context:**
- Detect if work appears to be mid-feature vs starting fresh
- Identify obvious next steps based on file changes
- Check for TODO comments in recently modified files

### 3. Project Health Check
**Basic Viability:**
- Can the project build/compile? (language-specific checks)
- Are core services startable?
- Any obvious configuration issues?
- Dependencies status (package.json, requirements.txt, etc.)

**Immediate Blockers:**
- Merge conflicts that need resolution
- Missing environment variables or config files
- Failed builds or critical errors

### 4. Contextual Command Suggestions
**Based on Current State:**
- If mid-task: Suggest `/implement-story`
- If no active work: Suggest `/create-spec`
- If specifications exist: Suggest implementation with `/implement-story`
- Always suggest `/refactor` for code cleanup

## Output Format

**Important**: The status report should be output as **clean, formatted text** (not wrapped in code blocks) for optimal readability in the chat interface.

### Standard Status Report

⚡ Writ Status Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 CURRENT POSITION
   Branch: feature/dashboard-websockets (2 commits ahead of main)
   Last commit: "Add WebSocket connection hook" (2 hours ago)
   Uncommitted: 3 modified files in src/components/

📋 ACTIVE WORK
   Spec: Real-time Dashboard with WebSocket Integration 
   Progress: Story 2 (User receives real-time notifications) - In Progress
   Tasks completed: 3/6 tasks (50%)
   Last completed: 2.3 Create notification display component ✅
   Next task: 2.4 Implement client-side WebSocket connection

🎯 SUGGESTED ACTIONS
   • Continue with task 2.4 (WebSocket connection management)
   • Commit current changes before switching tasks
   • Review recent main branch changes (3 new commits)

⚡ QUICK COMMANDS
   /implement-story     # Continue current task
   /commit-wip       # Commit work in progress  
   /sync-main        # Pull latest from main
   /refactor             # Quick code cleanup

### Clean State Example

⚡ Writ Status Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 CURRENT POSITION
   Branch: main (up to date)
   Last commit: "Fix user authentication bug" (1 day ago)
   Working directory: Clean ✅

📋 ACTIVE WORK
   No active specifications found
   Ready to start new work

🎯 SUGGESTED ACTIONS
   • Start new feature development
   • Review pending issues or backlog
   • Perform maintenance tasks

⚡ QUICK COMMANDS
   /create-spec      # Plan new feature
   /refactor             # Clean up existing code
   /review-specs     # Check previous specifications

### Problem State Example

⚡ Writ Status Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 CURRENT POSITION
   Branch: feature/payment-flow (5 commits ahead, 2 behind main)
   Last commit: "WIP: payment validation" (3 days ago)
   Uncommitted: 7 modified files, 2 conflicts

⚠️  IMMEDIATE ATTENTION
   • Merge conflicts in src/api/payments.js, package.json
   • Branch is 2 commits behind main (potential conflicts)
   • Stashed changes from 2 days ago

📋 ACTIVE WORK
   Spec: Payment Processing Integration
   Progress: Story 1 (User completes payment flow) - In Progress
   Tasks completed: 3/5 tasks (60%)
   Status: Task 1.4 appears incomplete
   Next task: 1.4 Validate payment with external API

🎯 SUGGESTED ACTIONS
   • Resolve merge conflicts first
   • Sync with main branch changes
   • Review stashed changes for relevance
   • Continue or restart task 1.4

⚡ QUICK COMMANDS
  /implement-story     # Continue current task
  /refactor            # Code cleanup

## Implementation Details

### Output Presentation

**Critical**: When Writ executes the status command, the report should be presented as **clean, formatted text** directly in the chat response, NOT wrapped in code blocks or markdown formatting. This ensures maximum readability and a professional presentation.

The status report uses Unicode characters (⚡, 📍, 📋, 🎯, 🔥, ⚠️) and box-drawing characters (━) for visual appeal. These should be output exactly as shown in the examples above.

### Git Analysis
**Commands to Run:**
```bash
git status --porcelain              # File changes
git log --oneline -5                # Recent commits
git log main..HEAD --oneline        # Commits ahead
git log HEAD..main --oneline        # Commits behind
git stash list                      # Stashed changes
git branch -v                       # Branch info
```

**Parsing Logic:**
- Extract meaningful context from commit messages
- Detect work patterns (feature vs bug fix vs refactor)
- Identify if work appears complete or in-progress
- Calculate time since last activity

### Writ Integration

**Spec Detection:**
```bash
# Find most recent spec directory
LATEST_SPEC=$(ls -t .writ/specs/*/spec.md | head -1 | xargs dirname)

# Read overall progress from user stories overview
cat "$LATEST_SPEC/user-stories/README.md"

# Find all individual story files
ls "$LATEST_SPEC/user-stories/story-"*.md
```

**Task Progress Analysis:**

For each individual story file (`user-stories/story-N-{name}.md`), parse the Implementation Tasks section:

```bash
# Count completed tasks (marked with [x])
grep -c "^\- \[x\].*✅" story-file.md

# Count total tasks (any checkbox)
grep -c "^\- \[[x ]\]" story-file.md

# Find next incomplete task
grep -n "^\- \[ \]" story-file.md | head -1
```

**Story Status Detection:**

Parse the story status from the header:
```bash
# Extract status from story file header
grep "^> \*\*Status:\*\*" story-file.md
```

Possible statuses:
- `Not Started` - No tasks completed
- `In Progress` - Some tasks completed, some remaining  
- `Completed ✅` - All tasks and acceptance criteria completed

**Progress Analysis:**
- Count completed vs total tasks across all stories
- Identify current active story (has In Progress status)
- Extract next logical task from current story
- Detect if entire spec work is complete
- Parse progress summary from `user-stories/README.md` table

**Active Work Prioritization:**

1. **Multiple specs exist**: Show the most recently modified spec (based on file timestamps)
2. **Single spec, multiple stories**: Show the story with "In Progress" status, or first "Not Started" story if none in progress
3. **All stories complete**: Show overall completion status and suggest next actions
4. **No specs found**: Indicate no Writ specifications exist

**Task Parsing Edge Cases:**

Handle various task formats that may exist in story files:
```bash
# Standard format with checkmark
- [x] 1.1 Implement authentication ✅

# Format without checkmark emoji
- [x] 1.1 Implement authentication

# Incomplete task
- [ ] 1.2 Add validation logic

# Tasks with sub-items (count as single task)
- [x] 1.3 Database setup
  - Created user table
  - Added indexes
```

**Validation:**
- Only count top-level task items (lines starting with `- [`)
- Ignore indented sub-items
- Handle both `[x]` and `[X]` as completed
- Treat any other character in brackets as incomplete

### Project Health Checks
**Language-Specific:**
```bash
# Node.js
npm run build --if-present
node -c package.json

# Python  
python -m py_compile main.py
pip check

# General
# Check for .env.example vs .env
# Verify critical config files exist
```

### Command Suggestion Logic
**Decision Tree:**
1. **Is there a merge conflict?** → Suggest conflict resolution
2. **Is working directory dirty?** → Suggest commit or stash
3. **Is branch behind main?** → Suggest sync
4. **Is there an active task?** → Suggest continue task
5. **Is current task complete?** → Suggest next task
6. **No active work?** → Suggest create spec
7. **Always:** → Suggest refactor for cleanup

## Usage Patterns

### Morning Routine
```bash
# Developer starts their day
$ /status

# Gets oriented on yesterday's work
# Sees exactly what to do next
# Jumps into flow state quickly
```

### Context Switching
```bash
# After meetings, interruptions, or breaks
$ /status

# Quick reminder of current state
# Understand what changed while away
# Resume work efficiently
```

### Project Handoff
```bash
# When picking up someone else's work
$ /status

# Understand current project state
# See what was being worked on
# Get oriented without diving into code
```

## Error Handling

### Not a Git Repository
```bash
❌ Not in a git repository
   Initialize git first: git init
```

### No Writ Structure
```bash
⚡ Writ Status Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 CURRENT POSITION
   Branch: main (up to date)
   Last commit: "Initial commit" (1 hour ago)
   Working directory: Clean ✅

📋 ACTIVE WORK
   No Writ specifications found
   Project structure: Standard git repository

🎯 SUGGESTED ACTIONS
   • Set up Writ workflow
   • Create first feature specification

⚡ QUICK COMMANDS
   /init             # Initialize Writ
   /create-spec      # Create first specification
```

### Corrupted Project State
```bash
⚠️  PROJECT ISSUES DETECTED
   • package.json syntax error
   • Missing critical dependencies
   • Build process failing

🔧 SUGGESTED FIXES
   • Fix package.json syntax
   • Run npm install or equivalent
   • Check build configuration

⚡ RECOVERY COMMANDS
   /doctor           # Diagnose and fix common issues
   /reset-deps       # Reinstall dependencies
```

## Security & Privacy

### Local-Only Analysis
- All analysis happens locally
- No external API calls or data transmission
- Git history and file contents remain private

### Sensitive Information
- Avoid displaying sensitive data in commit messages
- Mask environment variables or config values
- Sanitize file paths that might contain personal info

## Performance Considerations

### Fast Execution
- Target <2 second execution time
- Cache expensive operations when possible
- Limit git log queries to reasonable ranges

### Incremental Analysis
- Store last analysis timestamp
- Only re-analyze changed files/commits
- Use git's efficient diffing for change detection

## Integration Points

### Existing Writ Commands
- Status should inform other commands about current state
- Share analysis results to avoid duplicate work
- Coordinate with task execution and spec management

### Future Enhancements
- Integration with GitHub/GitLab for PR status
- Team activity awareness (without external dependencies)
- Customizable status report sections
- Export status for external tools or dashboards

## Success Metrics

### Developer Experience
- Time to context restoration after interruptions
- Frequency of "what was I working on?" moments
- Accuracy of suggested next actions
- Adoption rate and daily usage patterns

### Project Health
- Early detection of project issues
- Improved workflow consistency
- Better task completion rates
- Reduced context switching overhead

---

*⚡ Know thy codebase. Know thy standing. The truth shall set your project free.*

## Suggested Next Actions

Based on project state analysis, suggest relevant next steps:

- **No specs**: Suggest `/create-spec` or `/plan-product`
- **Specs ready for implementation**: Suggest `/implement-story`
- **Tasks ready**: Suggest `/implement-story`
- **Code quality issues**: Suggest `/refactor`
- **Missing architecture**: Suggest `/create-adr`
- **Research needed**: Suggest `/research`
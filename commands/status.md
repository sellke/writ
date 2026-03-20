# Status Command (status)

## Overview

Session orientation command. Reads stable project state — config, active spec, in-flight batch work, and refresh opportunities — and produces a skimmable report that tells you exactly where you are and what to do next. Under 10 seconds. No convention-detection questions when `.writ/config.md` is present.

## Invocation

```bash
/status
```

No parameters. Works in any git repository.

---

## Command Process

### Step 1: Load Config

**Read `.writ/config.md` first.** If present, parse:
- `Default Branch` — used for git position display
- `Test Runner` — informational, shown in project health
- `Writ Specs` — path to spec folder (default: `.writ/specs/`)
- `Writ Issues` — path to issues folder (default: `.writ/issues/`)

If `.writ/config.md` is **missing or incomplete** for any needed key, run detection for that key only. After detection, offer once: *"Save detected conventions to `.writ/config.md`? (y/n)"* — only write on **y**. Never auto-save.

See `.writ/docs/config-format.md` for the key reference and file format.

### Step 2: Gather Git Position

```bash
git branch --show-current           # Current branch
git status --porcelain              # Uncommitted changes
git log --oneline -5                # Recent commits
git log main..HEAD --oneline        # Commits ahead (use Default Branch from config)
git log HEAD..main --oneline        # Commits behind
git stash list                      # Stashed changes
```

Extract: branch name, commits ahead/behind default branch, last commit message and timestamp, uncommitted file count, stash count.

### Step 3: Detect Active Spec

```bash
# Find specs with non-Complete status (most recently modified first)
ls -t .writ/specs/*/spec.md
```

For the most recently modified spec that is not `Status: Complete`:
1. Read `spec.md` header — name, status, phase
2. Read `user-stories/README.md` — overall progress (X/Y tasks, Z%)
3. Find the active story: `In Progress` status, or first `Not Started` if none in progress
4. Read active story file — next unchecked task

### Step 4: Check for In-Flight Batch Jobs

```bash
ls .writ/state/execution-*.json 2>/dev/null
```

For each execution state file found, read and summarize:
- Spec name (from `"spec"` field)
- Started timestamp (from `"startedAt"` field)
- Story statuses from the `"stories"` object: count pending, in_progress, completed, failed
- Report as: *"Batch job in flight: [spec-name] — [N] of [M] stories complete"*

If no execution state files exist, omit this section from the output.

### Step 5: Needs Triage — Stale Issues

```bash
# Find issue files older than 7 days with no spec_ref
find .writ/issues -name "*.md" -type f 2>/dev/null
```

For each issue file found:
1. **Extract the date** — from filename prefix `YYYY-MM-DD-` (preferred) or file mtime as fallback
2. **Check age** — if the issue date is more than 7 days before today, it qualifies
3. **Check spec_ref** — read the file; if `spec_ref:` line is absent, empty, or still reads `_(set automatically...)_`, the issue has no promotion link
4. **Surface if both conditions met** (older than 7 days AND no spec_ref)

**Report format:**
```
⚠️ NEEDS TRIAGE (issues older than 7 days, not yet promoted):
   • .writ/issues/bugs/2026-03-01-login-timeout.md (19 days old)
   • .writ/issues/features/2026-02-28-export-csv.md (21 days old)
   → /create-spec --from-issue [path] to promote to a spec
```

If no issues qualify (all are recent or already have spec_ref), omit this section entirely. If `.writ/issues/` does not exist, omit silently.

### Step 6: Surface Refresh Opportunities

Check `.writ/state/refresh-log.md` (the canonical refresh log maintained by `/refresh-command`).

**How "last refresh" is determined:** For each command, find the most recent entry in `.writ/refresh-log.md` matching that command name (e.g., a line starting with `## [DATE] — /implement-story refreshed`). The date on that line is the last refresh timestamp. If no entry exists for a command, treat the command as never refreshed (threshold: 3+ any transcripts = suggest).

**How "new transcripts" are counted:** Count `.jsonl` files in the agent-transcripts directory whose modification time (or content timestamps) is after the last refresh date for that command, and whose content references that command (via the command identification logic in Phase 2.2 of `refresh-command.md`).

**Trigger threshold:** If **3 or more** new transcripts exist since the last logged refresh for a command, surface it as a refresh opportunity and suggest `--batch` mode.

**Report format (one line per command):**
```
🔄 Refresh opportunities:
   • 4 new /implement-story sessions since last refresh — consider: /refresh-command implement-story --batch
   • 3 new /ship sessions since last refresh — consider: /refresh-command ship --batch
```

If no command has 3+ new transcripts, omit this section.

If `.writ/state/refresh-log.md` does not exist yet, omit this section silently — no error.

### Step 7: Project Health Signals

Quick checks — run only what's fast and relevant:
- **Uncommitted changes:** flag count if > 0
- **Merge conflicts:** `git status --porcelain` — flag if `UU` entries exist
- **Stashed changes:** flag count if > 0
- **Branch age:** flag if branch was last committed > 5 days ago and has uncommitted changes

Do **not** run build or test commands inline in `/status` — those belong in `/release` and `/implement-story`.

### Step 8: Regenerate `.writ/context.md`

After gathering all state (Steps 1–7), fully rewrite `.writ/context.md` using the schema defined in `implement-story.md` Step 2. Each `/status` run replaces the entire file — no append, merge, or patch. Sources:

- **Product Mission** — 1–3 sentences from `.writ/product/mission-lite.md` (omit section if absent)
- **Active Spec** — spec id, title, status, active story N of M, tasks X/Y complete (from Steps 3–4)
- **Recent Drift** — last 3 entries from `.writ/specs/{spec}/drift-log.md` (omit if absent)
- **Open Issues** — count from `.writ/issues/` (omit if absent)
- **Last Updated** — current ISO 8601 timestamp

This ensures every agent run that follows a `/status` call starts with fresh, accurate context.

### Step 9: Suggest Next Actions

Based on the gathered state, produce 2–4 suggested next actions. Rules:

| Condition | Suggestion |
|---|---|
| Merge conflicts exist | Resolve conflicts before continuing |
| Uncommitted changes + active story | Commit or continue implementing |
| Active story in progress | `/implement-story` to continue the current story |
| Active spec, no story in progress | `/implement-story` to start next story |
| Active spec, all stories complete | `/ship` to open a PR |
| No active spec, clean state | `/create-spec` to plan new work |
| Stale untriaged issues (Step 5) | `/create-spec --from-issue [path]` to promote |
| Refresh opportunities exist (3+ new transcripts) | `/refresh-command [command] --batch` |
| In-flight batch job exists | `/implement-spec --resume` if needed |

**Command allowlist — only suggest commands that exist in the suite:**
`/create-spec`, `/implement-story`, `/implement-spec`, `/prototype`, `/review`, `/verify-spec`, `/refresh-command`, `/assess-spec`, `/ship`, `/release`, `/plan-product`, `/design`, `/research`, `/refactor`, `/status`, `/new-command`, `/initialize`, `/create-adr`, `/create-issue`, `/edit-spec`, `/migrate`, `/prisma-migration`, `/test-database`, `/retro`, `/security-audit`, `/explain-code`

Never suggest a command not in this list. If you need to suggest something that doesn't match an existing command, describe the action in plain English instead (e.g., "Resolve merge conflicts manually").

---

## Output Format

Present as **clean, formatted text** — not wrapped in code blocks. Use Unicode characters and box-drawing for visual clarity.

### Standard Output

```
⚡ Writ Status Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 CURRENT POSITION
   Branch: feature/auth-refresh (3 commits ahead of main)
   Last commit: "Add session token rotation" (4 hours ago)
   Uncommitted: 2 modified files in src/auth/

📋 ACTIVE WORK
   Spec: 2026-03-15-auth-system (In Progress)
   Progress: Story 3 of 5 — "Session timeout handling" (In Progress)
   Tasks: 3/6 complete (50%)
   Next task: 3.4 Add rotation grace period for active sessions

🔄 REFRESH OPPORTUNITIES
   • 4 new /implement-story sessions since last refresh
     → /refresh-command implement-story --batch

⚙️ IN-FLIGHT BATCH JOBS
   • 2026-03-18-dashboard-refactor: 3/5 stories complete (started 2 hours ago)

🎯 SUGGESTED ACTIONS
   • Continue task 3.4 (session rotation grace period)
   • Commit current changes first

⚡ QUICK COMMANDS
   /implement-story     # Continue Story 3
   /refresh-command implement-story --batch   # Update command from session patterns
```

### Clean State Example

```
⚡ Writ Status Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 CURRENT POSITION
   Branch: main (up to date)
   Last commit: "chore: release v1.4.0" (1 day ago)
   Working directory: Clean ✅

📋 ACTIVE WORK
   No active specifications found
   Ready to start new work

🎯 SUGGESTED ACTIONS
   • Plan a new feature

⚡ QUICK COMMANDS
   /create-spec      # Plan new feature
   /plan-product     # Define product strategy
   /research         # Investigate a technical question
```

### Problem State Example

```
⚡ Writ Status Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 CURRENT POSITION
   Branch: feature/payment-flow (5 commits ahead, 2 behind main)
   Last commit: "WIP: payment validation" (3 days ago)
   Uncommitted: 7 modified files, 2 conflicts

⚠️ IMMEDIATE ATTENTION
   • Merge conflicts: src/api/payments.js, package.json
   • Branch 2 commits behind main (potential conflicts)
   • Stashed changes from 2 days ago

📋 ACTIVE WORK
   Spec: 2026-03-10-payment-integration (In Progress)
   Progress: Story 1 — "User completes payment flow" (In Progress)
   Tasks: 3/5 complete (60%)
   Next task: 1.4 Validate payment with external API

🎯 SUGGESTED ACTIONS
   • Resolve merge conflicts first
   • Review stashed changes — they may be relevant
   • Continue task 1.4 after conflicts cleared

⚡ QUICK COMMANDS
   /implement-story     # Continue after conflicts resolved
   /refactor            # Code cleanup once stable
```

---

## Implementation Details

### Git Analysis Commands

```bash
git status --porcelain              # File changes and conflicts
git log --oneline -5                # Recent commits
git log main..HEAD --oneline        # Commits ahead (substitute configured default branch)
git log HEAD..main --oneline        # Commits behind
git stash list                      # Stashed changes
git branch -v                       # Branch info
```

### Spec Detection

```bash
# Find most recently modified non-complete spec
ls -t .writ/specs/*/spec.md | while read f; do
  grep -q "Status: Complete" "$f" || { echo "$f"; break; }
done

# Read overall progress
cat "$SPEC_DIR/user-stories/README.md"

# Find active story
grep -l "Status: In Progress" "$SPEC_DIR/user-stories/story-"*.md | head -1

# Count tasks
grep -c "^\- \[x\]" "$STORY_FILE"   # completed
grep -c "^\- \[[x ]\]" "$STORY_FILE" # total
```

### Task Progress Parsing

- Count top-level task items only (lines starting with `- [`)
- Ignore indented sub-items
- `[x]` and `[X]` both count as complete
- Any other character in brackets = incomplete

### In-Flight Batch Job Parsing

Read `.writ/state/execution-*.json` — fields to extract:

| JSON field | Used for |
|---|---|
| `"spec"` | Spec name to display |
| `"startedAt"` | Start time (ISO 8601) |
| `"stories"` | Object — each key is a story ID, value has `"status"` field |

A story is "in-flight" if its `"status"` is `"in_progress"` or `"pending"` (not yet reached). A job is "complete" if all stories are `"completed"`. Only show jobs that are not yet fully complete.

---

## Maintainer Note: Command Allowlist

The ⚡ QUICK COMMANDS section and 🎯 SUGGESTED ACTIONS section must only name commands from this allowlist. Future edits must not introduce commands that do not exist in `commands/*.md`:

`create-spec`, `implement-story`, `implement-spec`, `prototype`, `review`, `verify-spec`, `refresh-command`, `assess-spec`, `ship`, `release`, `plan-product`, `design`, `research`, `refactor`, `status`, `new-command`, `initialize`, `create-adr`, `create-issue`, `edit-spec`, `migrate`, `prisma-migration`, `test-database`, `retro`, `security-audit`, `explain-code`

If a new command is added to the suite, add it here. If a command is removed, remove it here.

---

## Error Handling

### Not a Git Repository

```
❌ Not in a git repository
   Initialize git first: git init
```

### No Writ Structure

The report still runs — git position, health signals, and suggested next actions work without `.writ/`. Simply omit the ACTIVE WORK section and adjust suggestions accordingly.

### Corrupted or Partial Spec State

If spec files exist but cannot be parsed (malformed README, missing story files), report what's available and flag the issue:

```
⚠️ Spec state partially readable
   Some story files could not be parsed — run /verify-spec to diagnose
```

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/initialize` | Seeds `.writ/config.md` — `/status` reads it on every run |
| `/implement-spec` | Writes `.writ/state/execution-*.json` — `/status` surfaces in-flight jobs |
| `/refresh-command` | Maintains `.writ/refresh-log.md` — `/status` surfaces `--batch` refresh opportunities when 3+ new transcripts |
| `/create-issue` | Creates issues in `.writ/issues/` — `/status` surfaces stale untriaged issues (Step 5) |
| `/create-spec --from-issue` | Promotes issues to specs — clears the Needs Triage flag by writing `spec_ref` |
| `/verify-spec` | Deep metadata diagnostic — use when `/status` flags spec inconsistencies |
| `/ship` | Next step when active spec is complete |

---
name: status
description: "Orient in under 10 seconds: config, active spec, in-flight batch work, and what to do next."
problem: "Picking work back up means re-deriving position from scattered sources — config, the newest spec folder, execution state files, the issue backlog — before anything can start."
outcome: "One skimmable orientation over the active spec, any in-flight batch execution and the stale-issue backlog, with .writ/context.md rewritten to agree with it."
exit_criteria:
  - ".writ/context.md has been replaced wholesale and carries an Active Spec section, an Artifact Map and a current Last Updated timestamp"
  - "the report names the active spec and its story progress or states that none is active, and ends with 2 to 4 suggested next actions"
  - "every execution state file under .writ/state/ was read without being written, and no build, test or git-mutating command ran"
---

# Status Command (status)

## Overview

Session orientation command. Reads stable project state — config, active spec, in-flight batch work, and refresh opportunities — and produces a skimmable report that tells you exactly where you are and what to do next. Under 10 seconds. No convention-detection questions when `.writ/config.md` is present.

## Required Artifacts

Verify per the preamble's **Artifact Integrity** rule before starting.

- **Required:** none — `/status` runs in any git repository and degrades per-section.
- **Optional:** everything (`.writ/config.md`, product docs, specs, issues) — each section omits gracefully when its source is absent.

## Invocation

```bash
/status
/status --archive
```

| Invocation | Behavior |
|---|---|
| `/status` | Standard orientation report (Steps 1–9 below). Never archives anything. |
| `/status --archive` | Runs the standard orientation report, then the **archive sweep** (see [Archive Sweep](#archive-sweep---archive) below) as an explicit, deliberate additional phase. |

`--archive` is opt-in only — routine `/status` (no flag) never triggers archival as a side effect, per Business Rule 2.

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

**Last audit note (read-only):** resolve the most recent git-notes audit digest on the
`refs/notes/writ` ref (see [`git-notes-audit-format.md`](../.writ/docs/git-notes-audit-format.md)):

```bash
git log --notes=writ -1 --format="%h %cs" $(git notes --ref=writ list 2>/dev/null | awk '{print $2}') 2>/dev/null
```

If at least one Writ audit note exists, add one line to the CURRENT POSITION output —
short SHA of the noted commit, the spec title from the note's `Spec:` line, and the
note date:

```
📝 Last audit note: {short-sha} — {spec title} ({date})
```

If no `refs/notes/writ` notes exist (empty ref), **omit the line entirely**. This is
read-only — `/status` never writes or syncs notes.

### Step 3: Detect Active Spec

```bash
# Find specs with non-Complete status (most recently modified first)
ls -t .writ/specs/*/spec.md
```

For the most recently modified spec that does not resolve to **complete-family**
under the format-tolerant classification in `scripts/spec-status.py` (see
[Spec Detection](#spec-detection) below — recognizes bold/unbold `Status:` labels
and `Complete` / `Completed ✅` / `Closed — Abandoned` as complete-family; an absent
status header conservatively resolves not-complete):
1. Read `spec.md` header — name, status, phase, owner
2. Read `user-stories/README.md` — overall progress (X/Y tasks, Z%)
3. Find the active story: `In Progress` status, or first `Not Started` if none in progress
4. Read active story file — next unchecked task

For the active-specs summary, include the owner from the spec header:

```
Active Specs:
  | Status      | Spec                              | Owner    |
  |-------------|-----------------------------------|----------|
  | In Progress | 2026-04-24-phase4-production...   | @adam    |
```

If a spec has no owner because it predates the owner field, display `—`.

### Step 4: Check for In-Flight Batch Jobs

```bash
ls .writ/state/execution-*.json .writ/state/phase-execution-*.json 2>/dev/null
```

For each **spec** execution state file (`execution-*.json`), read and summarize:
- Spec name (from `"spec"` field)
- Started timestamp (from `"startedAt"` field)
- Story statuses from the `"stories"` object: count pending, in_progress, completed, failed
- Report as: *"Batch job in flight: [spec-name] — [N] of [M] stories complete"*

For each **phase** execution state file (`phase-execution-*.json`, schema `phase-execution-v2`), summarize the **phase progress** and **production health** entirely **read-only** (no git mutation). Prefer the reducer over hand-parsing:

```bash
python3 scripts/phase-state.py progress --state <phase-execution-*.json>
python3 scripts/phase-state.py health   --state <phase-execution-*.json> --repo . \
  --eval <latest-eval-summary> --verification <latest-verification-report> --drift <drift-log>
```

- **Phase progress** — phase and current spec / active lane, per-status spec counts
  (`pending`, `implementing`, `integrated`, `failed`, `quarantined`, `skipped_blocked`,
  `challenge_required`, `closed_not_implemented`), and any **quarantine** branches so the
  maintainer can see preserved failed work and its recovery path. Report a
  `closed_not_implemented` spec as **closed by decision** with its recorded reason — never
  as work in flight. When a spec is `skipped_blocked`, say which cause blocked it
  (`quarantined` or `closed_not_implemented`, from the reducer's `blocked` map): `blockedBy`
  means "upstream reached a terminal status without delivering", so a reader told only
  "blocked" may go hunting for a quarantine branch that was never created.
- **Production health** — the reducer's **categorical** disposition (`Healthy` /
  `Warning` / `Attention`) computed from locally available evidence. Missing or stale
  evidence is reported as a Warning (never a silent pass); `Attention` means an
  affirmative current failure. Surface the `unavailable` and `failures` lists verbatim
  so the maintainer sees *why*.

This is a read-only recovery summary; `/status` never renames, merges, or deletes branches, and health never runs deep, external, or mutating checks.

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

Check `.writ/refresh-log.md` (the canonical, committed refresh log maintained by `/refresh-command`). This is read-only surfacing — `/status` never runs a refresh itself.

**How "last refresh" is determined:** For each command, find the most recent entry in `.writ/refresh-log.md` matching that command name (e.g., a line starting with `## [DATE] — /implement-story refreshed`). The date on that line is the last refresh timestamp. If no entry exists for a command, treat the command as never refreshed.

**How staleness is judged:** `/refresh-command` is human-driven — the maintainer runs a command, notices friction, and refreshes it with cited transcript evidence. `/status` does not scan or ingest transcripts. Instead, surface commands the maintainer has used recently in this project but not refreshed in a while (by the log dates above), so they can decide whether a refresh is worth running.

**Report format (one line per command):**
```
🔄 Refresh opportunities:
   • /implement-story last refreshed 2026-03-01 — consider: /refresh-command implement-story
   • /ship last refreshed 2026-03-15 — consider: /refresh-command ship
```

If nothing looks stale, omit this section.

If `.writ/refresh-log.md` does not exist yet, omit this section silently — no error.

### Step 7: Project Health Signals

Quick checks — run only what's fast and relevant:
- **Uncommitted changes:** flag count if > 0
- **Merge conflicts:** `git status --porcelain` — flag if `UU` entries exist
- **Stashed changes:** flag count if > 0
- **Branch age:** flag if branch was last committed > 5 days ago and has uncommitted changes

Do **not** run build or test commands inline in `/status` — those belong in `/release` and `/implement-story`.

**Quality configuration:** run `python3 scripts/quality-config-audit.py check --project .` — pure file reads, no subprocess, which is why this one and **not** `test-integrity.py coverage` or `build-smoke.py` may appear here; those execute tooling and would breach the terminal constraint below.

Render one line using the health vocabulary Step 4 already uses — `Healthy` when the verdict is `pass`, `Warning` when `unverifiable`, `Attention` when `fail` — with the count of findings **not** in `.writ/quality-baseline.md`:

```
Quality config: Attention — 2 new findings (3 baselined). `build_gate_disabled` next.
```

Surface the count and the newest finding code only; the enumeration lives in the baseline file. A block listing forty baselined items defeats a command meant to orient in under ten seconds.

**Omit the line entirely** when there are no findings, when `.writ/quality-baseline.md` is absent, or when the checker reports `unsupported_stack` — matching how Step 4's phase-health block and Step 5's stale-issue block already behave. An empty rendered block is worse than no block.

### Step 8: Regenerate `.writ/context.md`

After gathering all state (Steps 1–7), fully rewrite `.writ/context.md` using the schema defined in `implement-story.md` Step 2. Each `/status` run replaces the entire file — no append, merge, or patch. Sources:

- **Product Mission** — 1–3 sentences from `.writ/product/mission-lite.md` (omit section if absent)
- **Active Spec** — spec id, title, status, active story N of M, tasks X/Y complete (from Steps 3–4)
- **Artifact Map** — product/active-spec/knowledge/docs resolve list + Integrity line (present-conditional, wholesale; per the canonical `## Artifact Map` schema)
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
| Refresh opportunities exist (stale, recently used command) | `/refresh-command [command]` |
| In-flight batch job exists | `/implement-spec --resume` if needed |
| Quality-config findings, no `.writ/quality-baseline.md` (Step 7) | `/initialize` to record the baseline |
| New quality-config findings against an existing baseline (Step 7) | Fix the finding, or add a dated entry with a rationale to `.writ/quality-baseline.md` |

**Command allowlist — only suggest commands that exist in the suite:**
`/create-spec`, `/implement-story`, `/implement-spec`, `/implement-phase`, `/prototype`, `/review`, `/verify-spec`, `/refresh-command`, `/assess-spec`, `/ship`, `/release`, `/plan-product`, `/design`, `/research`, `/refactor`, `/status`, `/new-command`, `/new-skill`, `/initialize`, `/create-adr`, `/create-issue`, `/create-uat-plan`, `/edit-spec`, `/knowledge`, `/migrate`, `/retro`, `/security-audit`, `/update-writ`, `/reinstall-writ`, `/uninstall-writ`

Never suggest a command not in this list. If you need to suggest something that doesn't match an existing command, describe the action in plain English instead (e.g., "Resolve merge conflicts manually").

---

### Archive Sweep (`--archive`)

> Only runs when `/status --archive` is explicitly invoked — never as a side effect of routine `/status`, `create-spec`, or `implement-spec` (Business Rule 2). See `.writ/docs/spec-lifecycle.md` for the full convention this step implements.

When `--archive` is present, run this as an additional phase **after** Step 9:

1. **Scan and move.** Invoke the shared reducer:
   ```bash
   python3 scripts/archive-sweep.py sweep --specs-dir .writ/specs --knowledge-dir .writ/knowledge --repo-root .
   ```
   For each spec under `.writ/specs/*/spec.md` (single-level glob — never recurse into `archive/`), the reducer:
   - Classifies complete-family status via `scripts/spec-status.py` (Story 1's format-tolerant detector).
   - Checks eligibility: **complete-family status, alone** (Amendment 2026-08-04 to Business Rule 1 — knowledge evidence is no longer a gate). It also looks up whether any `.writ/knowledge/{decisions,conventions,glossary,lessons}/*.md` entry's `related_artifacts` frontmatter references the spec's folder name, purely to record it on the ledger line as enrichment.
   - Moves each eligible spec via `git mv .writ/specs/<name> .writ/specs/archive/<name>` and appends one line to `.writ/specs/archive/LEDGER.md` (created on first use, committed to git — never `.writ/state/`) — the evidence field reads "no knowledge evidence yet" when none exists.
   - Skips (never fails) on a destination collision or a `git mv` failure for that one spec, naming it in output, and continues the sweep for the rest.
2. **Report the terminal summary** from the reducer's JSON `summary` field, e.g.:
   ```
   📦 Archive sweep: 2 specs archived, 0 skipped
      • Archived: 2026-04-24-phase4-production-grade-substrate (evidence: 6 knowledge entries)
      • Archived: 2026-07-18-artifact-integrity-handshake (evidence: no knowledge evidence yet)
   ```
   If any collisions or `git mv` failures occurred, list them by name under a `⚠️` line — the sweep still completes for the rest.
3. **No confirmation prompt per spec.** Reversibility — a plain `git mv` plus a committed, append-only ledger — substitutes for a human "are you sure" (Business Rule 2) — this step never pauses to ask before moving an eligible spec.
4. **Idempotent by construction.** A spec already under `.writ/specs/archive/<name>/` no longer appears in the next sweep's `.writ/specs/*/spec.md` scan at all — running `/status --archive` twice in a row is a clean no-op the second time.

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
   📝 Last audit note: a1b2c3d — Auth System (2026-03-15)

📋 ACTIVE WORK
   Spec: 2026-03-15-auth-system (In Progress)
   Owner: @alex
   Progress: Story 3 of 5 — "Session timeout handling" (In Progress)
   Tasks: 3/6 complete (50%)
   Next task: 3.4 Add rotation grace period for active sessions

🔄 REFRESH OPPORTUNITIES
   • /implement-story last refreshed 2026-03-01 — used often since
     → /refresh-command implement-story

⚙️ IN-FLIGHT BATCH JOBS
   • 2026-03-18-dashboard-refactor: 3/5 stories complete (started 2 hours ago)

🎯 SUGGESTED ACTIONS
   • Continue task 3.4 (session rotation grace period)
   • Commit current changes first

⚡ QUICK COMMANDS
   /implement-story     # Continue Story 3
   /refresh-command implement-story   # Refresh the command with cited evidence
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
   Owner: @morgan
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
# Find most recently modified non-complete spec — format-tolerant classification
# (bold or unbold "Status:" label; Complete / Completed ✅ / Closed — Abandoned all
# resolve as complete-family; an absent header conservatively resolves not-complete).
# scripts/spec-status.py is the executable contract — invoke it rather than a
# literal substring grep, which does not match `> **Status:** Complete`.
ls -t .writ/specs/*/spec.md | while read f; do
  complete=$(python3 scripts/spec-status.py is-complete --file "$f" | python3 -c "import json,sys; print(json.load(sys.stdin)['complete'])")
  [ "$complete" = "True" ] || { echo "$f"; break; }
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

`create-spec`, `implement-story`, `implement-spec`, `implement-phase`, `prototype`, `review`, `verify-spec`, `refresh-command`, `assess-spec`, `ship`, `release`, `plan-product`, `design`, `research`, `refactor`, `status`, `new-command`, `new-skill`, `initialize`, `create-adr`, `create-issue`, `create-uat-plan`, `edit-spec`, `knowledge`, `migrate`, `retro`, `security-audit`, `update-writ`, `reinstall-writ`, `uninstall-writ`

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
| `/refresh-command` | Maintains `.writ/refresh-log.md` — `/status` surfaces stale refresh opportunities from the log dates (read-only) |
| `/create-issue` | Creates issues in `.writ/issues/` — `/status` surfaces stale untriaged issues (Step 5) |
| `/create-spec --from-issue` | Promotes issues to specs — clears the Needs Triage flag by writing `spec_ref` |
| `/verify-spec` | Deep metadata diagnostic — use when `/status` flags spec inconsistencies |
| `/ship` | Next step when active spec is complete |
| `/status --archive` | Moves Complete + knowledge-evidenced specs to `.writ/specs/archive/` via `scripts/archive-sweep.py`; see `.writ/docs/spec-lifecycle.md` |

## Completion

This command succeeds when `.writ/context.md` has been rewritten with an Active Spec section, an Artifact Map, and a current timestamp, and the report ends with two to four suggested next actions.

No active spec is a valid outcome. The report says so plainly rather than searching harder for one.

**Terminal constraint:** This command orients and nothing else — it reads state files without writing them and runs no build, test, or git-mutating command. Do not begin the next action it suggests.

---

## References

- Standing instructions: [`commands/_preamble.md`](_preamble.md)
- Identity & Prime Directive: [`system-instructions.md`](../system-instructions.md)

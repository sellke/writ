# Retro Command (retro)

## Overview

Git-based retrospective that turns commit history into actionable insight. Replaces gut-feel "how did that week go?" with data: what was built, how fast, what patterns emerged, and how it compares to the previous period.

`/retro` is opinionated about what matters: shipping velocity, code quality signals, and developer momentum. It's a focused snapshot that takes 30 seconds to read and surfaces the one or two things worth changing.

**Design Philosophy:**

- **Team-aware analysis** — even for solo devs, "you" is the team. Specific, commit-anchored praise.
- **Judgment over metrics** — raw numbers are context. The patterns and recommendations are the value.
- **Persistent snapshots** — JSON files enable trend comparison across weeks and months.
- **Tweetable summary** — a forcing function for distillation. If you can't summarize the period in one sentence, you don't understand it yet.

## Invocation

| Invocation | Behavior |
|---|---|
| `/retro` | Last 7 days from current branch |
| `/retro --period 14` | Last 14 days |
| `/retro --spec .writ/specs/2026-03-15-...` | Scope to a spec's lifetime |
| `/retro --compare` | Side-by-side with previous period |
| `/retro --all-branches` | Include all branches (default: current only) |

## Command Process

### Step 1: Auto-Detect Environment

Detect timezone, default branch, and period before collecting data. Never hardcode these values.

| Setting | Detection | Fallback |
|---|---|---|
| **Timezone** | System locale | UTC with warning |
| **Default branch** | `git remote show origin` → parse HEAD branch | Check for `main`/`master` locally |
| **Period** | Default 7 days | Suggest spec-scoped if a spec completed in last 14 days |

Display detected timezone in the report header so the user can verify correctness.

**Smart period suggestion:** When a Writ spec has status "Complete" with a completion date within the last 14 days, suggest running `/retro --spec` for that spec before proceeding with the default 7-day period. Let the user choose — don't auto-scope.

### Step 2: Collect Git Metrics

Collect from git history for the specified period and branch filter (`--all-branches` widens scope).

**Metrics to collect:**

- **Commits** — total count, excluding merge commits from volume metrics
- **Lines of code** — added (gross), removed (gross), net change (positive = growth, negative = cleanup)
- **Files touched** — unique files changed in the period
- **Test ratio** — test files changed / total files changed

**Test ratio benchmarks for interpretation:**

- **≥ 0.30** — strong test discipline. Tests are keeping pace with the code.
- **0.15–0.29** — adequate. Tests exist but aren't a priority.
- **< 0.15** — tests are being neglected. Flag this in Patterns.

### Step 3: Detect Sessions

Sessions are clusters of commits separated by inactivity gaps. They approximate focused work periods.

**Core heuristic:** Walk commit timestamps chronologically. A gap exceeding **2 hours** between consecutive commits starts a new session.

```
Commits at 10:00, 10:15, 10:45, 11:30  →  Session 1 (1.5 hours, 4 commits)
[4-hour gap]
Commits at 15:30, 16:00, 16:45         →  Session 2 (1.25 hours, 3 commits)
```

**Refinements — these matter:**

- **Single-commit sessions** are valid (quick fix) but exclude from average duration calculations
- **Sessions spanning midnight** — keep as one session if gap < threshold
- **Bot/CI commits** — filter out `dependabot`, `renovate`, `github-actions` and similar bot authors
- **Merge commits** — include in session detection but not commit volume (integration, not new work)
- **When in doubt, err toward fewer, larger sessions** — splitting a real work session is worse than merging two adjacent ones

**Session statistics to compute:** total sessions, average duration (excluding single-commit), average commits/session, longest session with start time.

**Time distribution:** Bucket sessions into morning (6–12), afternoon (12–18), evening (18–24), night (0–6). Clustering in one window is a meaningful pattern worth surfacing.

### Step 4: Track Streaks

A streak is consecutive calendar days with at least one commit on the tracked branch(es).

Compute: current streak (ending today or yesterday), longest streak in period, total active days, active day percentage (active days / total days).

I recommend **acknowledging streaks ≥ 5 days** — they indicate sustained momentum. But flag if a long streak includes mostly single-commit days or very short sessions. Sustained short sessions might indicate interrupt-driven work rather than deep work.

### Step 5: Collect Writ Context

If `.writ/` exists, collect additional context. **Gracefully skip any artifact that doesn't exist** — not all projects use all Writ features, and non-Writ projects should get a clean retro without errors.

**What to collect:**

- **Specs completed** — scan `.writ/specs/` for specs with "Complete" status and completion date within the period
- **Stories completed** — count "Completed ✅" stories in story READMEs for active/recent specs
- **Drift incidents** — parse `drift-log.md` files, group by severity (small/medium/large)
- **Commands refreshed** — count entries in `.writ/refresh-log.md` within the period

If no `.writ/` directory exists, note it and proceed — git metrics, sessions, and streaks still provide a complete retro.

### Step 6: Scope to Spec (`--spec` flag)

When `--spec [path]` is provided, override the default period with the spec's lifetime: extract the created date from `spec.md`, use completion date as end boundary (or today if in-progress). All git metrics, sessions, and streaks use this scoped period.

Display spec name, derived period, branch, and timezone in the output header. If the spec path doesn't exist, list available specs from `.writ/specs/`.

### Step 7: Produce Output

Format collected data into an opinionated markdown report printed to the conversation.

**Report structure:**

1. **Header** — period dates, branch, timezone (auto-detected)
2. **Metrics table** — commits, lines (net), files touched, test ratio, sessions, avg session duration, streak — each with a "Δ vs Last" column comparing to the previous snapshot. Show "—" if no previous snapshot exists and note "First retro — no baseline for comparison."
3. **Ship of the Week** — most impactful change, anchored to specific commits (see selection heuristic below)
4. **Patterns** — 2-3 opinionated observations derived from data (see pattern guidance below)
5. **Writ Integration** — specs completed, stories completed, drift incidents, commands refreshed. Omit section entirely for non-Writ projects.
6. **Tweetable** — one compelling sentence capturing the period's essence. Must be specific and anchored to real work, not generic motivation.

#### Ship of the Week Selection

Select the most impactful change using this priority:

1. **Spec/story completion** — completing a spec or story is likely the most significant work
2. **Commit breadth** — commits touching many files relative to the period average
3. **Commit message signals** — "implement", "add", "ship", "complete", "refactor" rank above "fix", "tweak", "update"
4. **LOC impact** — large net additions (new functionality) rank above large net deletions (cleanup)
5. **Writ context** — drift resolved, command refreshed, or spec milestone reached

I recommend **highlighting effort and impact, not just volume**. A tricky 50-line fix that unblocked a feature is more significant than 500 lines of boilerplate. Anchor to specific commit hashes. The Ship description should be 2-3 sentences explaining what was built and why it matters — not a changelog entry.

#### Patterns Section

This is where `/retro` provides its highest value — opinionated observations, not restated numbers.

| Pattern | Signal | Example |
|---|---|---|
| Test discipline | Test ratio trending up or down | "Test ratio hit 0.38 — highest in 6 weeks. The spec-healing work drove this." |
| Session clustering | Most sessions in one time window | "6 of 8 sessions were morning blocks. Afternoon sessions were shorter and scattered." |
| Velocity change | Commit rate significantly different from baseline | "Commit rate doubled — spec implementation phase creates natural acceleration." |
| Streak significance | Long streak with healthy session lengths | "5-day streak with 2+ hour sessions — sustained deep work, not just daily drive-bys." |
| Cleanup signal | Net lines negative | "Net -300 lines — you shipped a feature AND reduced the codebase. That's rare." |
| Test debt | Low test ratio during feature work | "Test ratio dropped to 0.12 during this push. Consider a test-focused session." |

I recommend **2-3 patterns per retro**. More than that dilutes the signal. Lead with the most important observation.

### Step 8: Persist Snapshot

Save raw metrics as JSON to `.writ/retros/YYYY-MM-DD.json` for trend comparison. Create the directory if needed.

**Required fields:**

- **Metadata** — version (for forward-compatible evolution), period (start, end, days), branch, timezone
- **Git** — commits, lines added, lines removed, lines net, files touched, test files touched, test ratio
- **Sessions** — count, avg duration hours, longest duration hours, time distribution (morning/afternoon/evening/night)
- **Streaks** — current, longest in period, active days, active day percentage
- **Writ** — specs completed, stories completed, drift counts by severity, commands refreshed. Omit if no `.writ/` exists.
- **Ship of the Week** — title, commit hash, date (captured for trend display across periods)

All numeric fields use raw values for computation, not formatted strings.

### Step 9: Update Trends

Maintain a rolling trends file at `.writ/retros/trends.json` for long-term analysis.

**On each retro run:** Read existing trends (or initialize), add the new snapshot reference, recalculate rolling averages from the last 6 weeks of snapshots.

**Required fields:** version, last-updated date, window size (default 6 weeks), rolling averages (commits/week, net lines/week, test ratio, sessions/week, avg session hours, active day percentage), and ordered list of snapshot filenames.

Rolling averages power the "Δ vs Last" column and provide context for Patterns ("highest in 6 weeks", "below your average").

The trends file can be gitignored — it's recomputed from snapshots on each run. Individual snapshots (`.writ/retros/YYYY-MM-DD.json`) should be committed for historical record.

### Step 10: Compare Mode (`--compare`)

When `--compare` is specified, produce a side-by-side comparison with the previous period.

Load the most recent snapshot in `.writ/retros/` older than the current period's start date. If none exists, note that comparison isn't available.

**Compare output adds:**

- A full metrics comparison table showing both periods, deltas (absolute and percentage), and trend arrows
- An opinionated "What Changed" analysis explaining the biggest shifts — what drove them and whether they're sustainable
- Focus on 1-2 meaningful changes, not line-by-line delta narration. "Commit rate doubled because you entered spec implementation phase" is useful. "Commits went from 22 to 34" is not.

---

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/create-spec` | Retro can highlight spec completion as Ship of the Week |
| `/assess-spec` | Retro surfaces velocity and test debt that assessment should consider |
| `/implement-spec` | After retro, velocity insights inform implementation pacing |
| `/review` | Use `/review` for pre-ship code quality; `/retro` for post-period reflection |

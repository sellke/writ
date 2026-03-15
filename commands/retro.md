# Retro Command (retro)

## Overview

Git-based retrospective that turns commit history into actionable insight. Replaces gut-feel "how did that week go?" with data: what was built, how fast, what patterns emerged, and how it compares to the previous period.

`/retro` is opinionated about what matters: shipping velocity, code quality signals, and developer momentum. It doesn't try to be a full analytics dashboard — it's a focused snapshot that takes 30 seconds to read and surfaces the one or two things worth changing.

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

Before collecting any data, detect the runtime environment. Never hardcode these values.

| Setting | Detection | Fallback |
|---|---|---|
| **Timezone** | `date +%Z` or system locale | UTC with warning |
| **Default branch** | `git remote show origin` → parse HEAD branch | Check for `main`/`master` locally |
| **Period** | Default 7 days | Smart suggestion if spec just completed |

**Timezone detection:**
```bash
TZ=$(date +%Z)
# Or on systems where date +%Z isn't reliable:
TZ=$(python3 -c "import time; print(time.tzname[0])" 2>/dev/null || echo "UTC")
```

Display detected timezone in the report header so the user can verify.

**Smart period suggestion:**

When a Writ spec exists with status "Complete" and a completion date within the last 14 days:

```
💡 Spec "Phase 2a: Shipping & Review" completed 3 days ago.
   Run /retro --spec .writ/specs/2026-03-15-phase2a-shipping-review/
   for a spec-scoped retrospective?
   [Enter for spec-scoped, or continue with default 7-day]
```

### Step 2: Collect Git Metrics

Run git commands to collect raw metrics for the specified period.

**Commits:**
```bash
git log --oneline --after="[start-date]" --before="[end-date]" [branch-filter]
```

Count total commits. If `--all-branches`:
```bash
git log --oneline --all --after="[start-date]" --before="[end-date]"
```

**Lines of code (net and gross):**
```bash
git log --numstat --after="[start-date]" --before="[end-date]" [branch-filter]
```

Parse output to calculate:
- **Lines added** (gross) — total insertions
- **Lines removed** (gross) — total deletions
- **Net change** — added minus removed (positive = growth, negative = cleanup)

**Files changed:**
```bash
git log --name-only --after="[start-date]" --before="[end-date]" [branch-filter] | sort -u
```

Count unique files touched in the period.

**Test file ratio:**

Identify test files by matching these patterns:
- `*test*`, `*spec*`, `*.test.*`, `*.spec.*`
- Files in `__tests__/`, `tests/`, `test/`, `spec/`
- Language-specific: `*_test.go`, `*_test.rb`, `Test*.java`

Calculate: `test files changed / total files changed`

**Benchmarks for interpretation:**
- **≥ 0.30** — strong test discipline. The tests are keeping pace with the code.
- **0.15–0.29** — adequate. Tests exist but aren't a priority.
- **< 0.15** — tests are being neglected. Flag this in Patterns.

### Step 3: Detect Sessions

Sessions are clusters of commits separated by inactivity gaps. They approximate focused work periods.

**Algorithm:**

1. Collect all commit timestamps in the period, sorted chronologically
2. Walk through timestamps sequentially
3. If gap between consecutive commits exceeds the threshold (default: 2 hours), start a new session
4. Record each session: start time, end time, commit count, duration

```
Commit at 10:00, 10:15, 10:45, 11:30  →  Session 1 (1.5 hours, 4 commits)
[gap: 4 hours]
Commit at 15:30, 16:00, 16:45          →  Session 2 (1.25 hours, 3 commits)
```

**Heuristic refinements:**

- **Single-commit sessions** are valid (quick fix) but excluded from average session duration calculations
- **Sessions spanning midnight:** keep as one session if gap < threshold
- **Bot/CI commits:** filter out commits from known bot authors (`dependabot`, `renovate`, `github-actions`) if detectable from the commit author field
- **Merge commits:** include in session detection but don't count toward commit volume metrics — they represent integration, not new work
- **When in doubt, err toward fewer, larger sessions** — splitting a real work session is worse than merging two adjacent ones

**Session statistics to compute:**

| Metric | Definition |
|---|---|
| Total sessions | Number of distinct work periods |
| Average duration | Mean session length (excluding single-commit sessions) |
| Average commits/session | Mean commits per session |
| Time distribution | Morning (6–12), Afternoon (12–18), Evening (18–24), Night (0–6) |
| Longest session | Maximum session duration with start time |

### Step 4: Track Streaks

A streak is consecutive calendar days with at least one commit on the tracked branch(es).

**Calculate:**
- **Current streak** — consecutive days ending today or yesterday (0 if today has no commits and yesterday didn't either)
- **Longest streak in period** — maximum consecutive-day run
- **Total active days** — days with at least one commit
- **Active day percentage** — active days / total days in period

I recommend **acknowledging streaks ≥ 5 days** — they indicate sustained momentum. But also flag if a long streak includes mostly single-commit days or very short sessions. Sustained short sessions might indicate interrupt-driven work rather than deep work.

### Step 5: Collect Writ Context

If the project uses Writ (`.writ/` directory exists), collect additional context. **Gracefully skip any artifact that doesn't exist** — not all projects use all Writ features, and non-Writ projects should get a clean retro without errors.

**Specs completed this period:**
1. Scan `.writ/specs/` directories
2. Read each `spec.md` header for `Status:` and completion date
3. Count specs with status "Complete" and completion date within the period

**Stories completed this period:**
1. For each active or recently-completed spec, read `user-stories/README.md`
2. Count stories with status "Completed ✅"
3. If completion dates are available in story files, filter to the period

**Drift incidents:**
1. Scan spec directories for `drift-log.md` files
2. Parse entries for the period
3. Group by severity: small (auto-healed), medium (flagged), large (paused)

**Commands refreshed:**
1. Read `.writ/refresh-log.md` if it exists
2. Count refresh entries within the period

**If Writ artifacts don't exist:**
```
ℹ️ No .writ/ directory found — Writ context integration skipped.
```

This is normal for non-Writ projects. The git metrics, sessions, and streaks still provide a complete retro.

### Step 6: Scope to Spec (`--spec` flag)

When `--spec [path]` is provided, override the default period with the spec's lifetime:

1. Read the spec's `spec.md` header → extract `Created:` date
2. If status is "Complete", use the completion date as end boundary
3. Otherwise, use today as end boundary
4. Override the period: `[created-date]` → `[end-date]`
5. All git metrics, sessions, and streaks use this scoped period

```
📋 Scoped to spec: Phase 2a — Shipping & Review
   Period: 2026-03-15 → 2026-03-22 (7 days)
   Branch: main
   Timezone: America/Los_Angeles
```

### Step 7: Produce Output

Format collected data into an opinionated markdown report. This is the primary output — printed to the conversation. Raw data is persisted separately as JSON (Step 8).

**Output template:**

```markdown
# Retro: [start-date] → [end-date]

> Branch: [branch] | Timezone: [tz] (auto-detected)

## 📊 This Period

| Metric | Value | Δ vs Last |
|--------|-------|-----------|
| Commits | [N] | [+/-N (+/-X%)] |
| Lines (net) | [+/-N] | [+/-N] |
| Files touched | [N] | [+/-N] |
| Test ratio | [0.XX] | [+/-0.XX] |
| Sessions | [N] | [+/-N] |
| Avg session | [N.N hrs] | [+/-N.N] |
| Streak | [N days] | [+/-N] |

## 🏆 Ship of the Week

**[Title]** — [2-3 sentence description of what was built and why
it matters. Anchor to specific commits.]

> Commit: [hash] ([date])

## 🔍 Patterns

- **[Pattern name]** — [Opinionated observation with specific data.
  "Test ratio 0.38 is above your 6-week average (0.29)" not just
  "Test ratio: 0.38".]
- **[Pattern name]** — [Another observation. Look for: session clustering,
  velocity changes, test discipline trends, streak significance.]

## 📋 Writ Integration

- Specs completed: [N] ([names if any])
- Stories completed: [N]
- Drift incidents: [N small (auto-healed), N medium (flagged), N large (paused)]
- Commands refreshed: [N]

[If no Writ artifacts: "ℹ️ No Writ project data found — git metrics only."]

## 🐦 Tweetable

"[One compelling sentence that captures the period's essence.
Must be specific and anchored to real work, not generic.]"
```

**The Δ vs Last column** compares against the previous period's JSON snapshot. If no previous snapshot exists, show "—" in the delta column and note "First retro — no baseline for comparison."

#### Ship of the Week Selection

The Ship of the Week highlights the most impactful change in the period. Select using this heuristic:

1. **Spec/story completion** — if a story or spec was completed, it's likely the most significant work
2. **Commit breadth** — commits touching many files relative to the period average suggest a significant change
3. **Commit message signals** — keywords like "implement", "add", "ship", "complete", "refactor" suggest higher impact than "fix", "tweak", "update"
4. **LOC impact** — large net additions (new functionality) rank higher than large net deletions (cleanup)
5. **Writ context** — drift detected and resolved, command refreshed, or spec milestone reached

I recommend **highlighting effort and impact, not just volume**. A tricky 50-line fix that unblocked a feature is more significant than 500 lines of boilerplate. Anchor the selection to specific commit hashes.

#### Patterns Section

The Patterns section is where `/retro` provides its highest value — opinionated observations derived from the data. Don't just restate numbers.

**Pattern types to look for:**

| Pattern | Signal | Example |
|---|---|---|
| Test discipline | Test ratio trending up or down | "Test ratio hit 0.38 — highest in 6 weeks. The spec-healing work drove this." |
| Session clustering | Most sessions in one time window | "6 of 8 sessions were morning blocks. Afternoon sessions were shorter and more scattered." |
| Velocity change | Commit rate significantly different from baseline | "Commit rate doubled this week — spec implementation phase creates natural acceleration." |
| Streak significance | Long streak with healthy session lengths | "5-day streak with 2+ hour sessions — sustained deep work, not just daily drive-bys." |
| Cleanup signal | Net lines negative | "Net -300 lines — you shipped a feature AND reduced the codebase. That's rare." |
| Test debt | Low test ratio during feature work | "Test ratio dropped to 0.12 during this push. Consider a test-focused session before shipping." |

I recommend **2-3 patterns per retro**. More than that dilutes the signal. Lead with the most important observation.

### Step 8: Persist Snapshot

Save raw metrics as JSON for trend comparison across periods.

**Snapshot file:** `.writ/retros/YYYY-MM-DD.json`

```json
{
  "version": 1,
  "period": {
    "start": "2026-03-08",
    "end": "2026-03-15",
    "days": 7
  },
  "branch": "main",
  "timezone": "America/Los_Angeles",
  "git": {
    "commits": 34,
    "lines_added": 1580,
    "lines_removed": 333,
    "lines_net": 1247,
    "files_touched": 18,
    "test_files_touched": 7,
    "test_ratio": 0.38
  },
  "sessions": {
    "count": 8,
    "avg_duration_hours": 1.8,
    "longest_duration_hours": 3.2,
    "distribution": {
      "morning": 4,
      "afternoon": 2,
      "evening": 2,
      "night": 0
    }
  },
  "streaks": {
    "current": 5,
    "longest_in_period": 5,
    "active_days": 6,
    "active_day_pct": 0.86
  },
  "writ": {
    "specs_completed": 1,
    "stories_completed": 7,
    "drift_small": 2,
    "drift_medium": 1,
    "drift_large": 0,
    "commands_refreshed": 0
  },
  "ship_of_week": {
    "title": "Tiered spec-healing agent",
    "commit": "abc1234",
    "date": "2026-03-11"
  }
}
```

**Schema notes:**
- `version` field enables forward-compatible evolution — future retro versions can handle old snapshots
- All numeric fields use raw values (not formatted strings) for computation
- `writ` section is null/omitted if no `.writ/` directory exists
- `ship_of_week` captured for trend display (recurring themes across periods)

**Create `.writ/retros/` directory if it doesn't exist.**

### Step 9: Update Trends

Maintain a rolling trends file for long-term analysis.

**Trends file:** `.writ/retros/trends.json`

```json
{
  "version": 1,
  "updated": "2026-03-15",
  "window_weeks": 6,
  "rolling_averages": {
    "commits_per_week": 28.5,
    "lines_net_per_week": 890,
    "test_ratio": 0.29,
    "sessions_per_week": 6.8,
    "avg_session_hours": 2.1,
    "active_day_pct": 0.78
  },
  "snapshots": [
    "2026-02-01.json",
    "2026-02-08.json",
    "2026-02-15.json",
    "2026-02-22.json",
    "2026-03-01.json",
    "2026-03-08.json",
    "2026-03-15.json"
  ]
}
```

**On each retro run:**
1. Read existing `trends.json` (or initialize if first run)
2. Add new snapshot filename to the `snapshots` array
3. Recalculate rolling averages from the last N snapshots (default window: 6 weeks)
4. Write updated `trends.json`

Rolling averages power the "Δ vs Last" column and provide context for Patterns observations ("highest in 6 weeks", "below your average").

**`trends.json` can be gitignored** — it's computed from snapshots and regenerated on each retro run. Individual snapshots (`.writ/retros/YYYY-MM-DD.json`) should be committed for historical record.

### Step 10: Compare Mode (`--compare`)

When `--compare` is specified, produce a side-by-side comparison with the previous period:

```markdown
# Retro Comparison: This Period vs Last

| Metric | This Period | Last Period | Δ | Trend |
|--------|-------------|-------------|---|-------|
| Commits | 34 | 22 | +12 (+54%) | ↗️ |
| Lines (net) | +1,247 | +867 | +380 | ↗️ |
| Test ratio | 0.38 | 0.33 | +0.05 | ↗️ |
| Sessions | 8 | 6 | +2 | ↗️ |
| Streak | 5 | 3 | +2 | ↗️ |

## What Changed

[Opinionated analysis of the biggest shifts between periods.
What drove the change? Is it sustainable?]
```

**Finding the previous period:**
1. Look for the most recent JSON snapshot in `.writ/retros/` that's older than the current period's start date
2. If no previous snapshot exists, note "No previous period data — comparison not available"
3. Load the previous snapshot and compute deltas for every metric

---

## Error Handling

**Not a git repository:**
```
⚠️ Not a git repository. /retro requires git history.
Initialize with: git init
```

**No commits in period:**
```
⚠️ No commits found in the last [N] days on [branch].
Try a longer period: /retro --period 30
Or include all branches: /retro --all-branches
```

**No remote configured:**
```
⚠️ No git remote found — can't auto-detect default branch.
Using current branch: [branch-name]
Metrics will cover the last [N] days.
```

**Spec not found (--spec flag):**
```
⚠️ Spec not found at [path].
Available specs:
  .writ/specs/2026-03-15-phase2a-shipping-review/
  .writ/specs/2026-02-27-phase1-foundation/
```

## When to Use /retro vs Other Commands

| Scenario | Command |
|---|---|
| Weekly development retrospective | `/retro` |
| Post-spec completion review | `/retro --spec .writ/specs/...` |
| Compare two periods | `/retro --compare` |
| Long-term trend analysis | `/retro --period 30 --compare` |
| Check what was shipped recently | `/retro --period 3` (quick check) |
| Review code quality before shipping | `/review` (not `/retro`) |

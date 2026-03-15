# Phase 2a: Shipping & Review — Technical Specification

> Created: 2026-03-15
> Last Updated: 2026-03-15
> Spec: Phase 2a Shipping & Review
> Status: In Progress — Dogfooding Pending

## Architecture Overview

All Phase 2a deliverables are **markdown files** — command definitions that AI agents follow. There is no runtime code, no CLI binary, no server, no database. Consistent with Phase 1 and Writ's methodology-first identity.

```
commands/
├── ship.md              ← NEW (Stories 1, 2) — Unified shipping workflow
├── review.md            ← NEW (Story 3) — Standalone pre-landing code review
├── retro.md             ← NEW (Stories 4, 5) — Git-based retrospective
├── create-spec.md       ← MODIFIED (Story 6) — Add error mapping sections to Step 2.8
└── implement-story.md   ← MODIFIED (Story 1) — Suggest /ship after pipeline completion

.writ/
└── retros/              ← NEW (Stories 4, 5) — JSON snapshots from /retro
    ├── YYYY-MM-DD.json  ← Raw metrics per period
    └── trends.json      ← Rolling averages (optional, gitignored)
```

---

## Feature 1: /ship Command

### File: `commands/ship.md` (new)

Unified shipping workflow that takes a green branch to a merged PR. PR agent behavior is absorbed — one command owns the full "branch to merged" path.

**5-step pipeline:**

1. **Detect Conventions** — Auto-detect without configuration
2. **Merge & Rebase** — Fetch, merge (or rebase), handle conflicts
3. **Run Tests** — Execute detected test runner, stream output
4. **Commit Intelligence** — Split into bisectable commits when beneficial
5. **PR Creation** — Structured body, auto-labels, draft/ready detection

### Convention Detection Chain (priority-ordered fallbacks)

| Convention | Detection Chain | Fallback |
|------------|-----------------|----------|
| **Default branch** | `git remote show origin` → check for `main`/`master`/`develop` | Ask user |
| **Test runner** | `package.json` scripts → `Makefile` → `pytest.ini`/`setup.cfg` → `mix.exs` → `Cargo.toml` | Ask user |
| **Merge strategy** | `.gitconfig` merge preference → repo convention detection | Default: merge |
| **PR tool** | `gh` CLI available → `GITHUB_TOKEN` set → `.gitlab-ci.yml` exists | Default: `gh` |

Detection results printed at start for user verification before proceeding.

### Commit Splitting Heuristic

**Split when beneficial:**
- Infrastructure changes (config, deps, migrations) → separate commit
- Model/schema changes → separate commit
- Business logic → separate commit
- Test additions → co-located with the code they test
- Version bumps → final commit

**Skip splitting for:**
- Single-file changes
- Changes < 50 lines total
- Tightly coupled changes (splitting would create broken intermediate states)

### PR Body Template

```markdown
## Summary
[2-3 sentence description from commit messages and diff analysis]

## Changes
[Bullet list of logical changes, grouped by domain]

## Spec Reference
[Link to .writ spec and story if available]

## Test Results
[Pass/fail summary from Step 3]

## Drift Report
[Summary from spec-healing drift-log if available, else "No spec drift detected"]

## Review Notes
[Findings from pipeline review or /review command]
```

### Auto-Labels (additive, not exclusive)

Based on file types and spec category: `infra`, `feature`, `fix`, `refactor`, `docs`

### Draft vs. Ready

- **Ready:** All tests pass + no medium/large drift
- **Draft:** Test warnings or medium drift → Draft PR with notes
- User override available in both directions

### Flags

| Flag | Behavior |
|------|----------|
| `--no-split` | Skip commit splitting (ship as-is) |
| `--draft` | Force draft PR regardless of test results |
| `--dry-run` | Show what would happen without executing |

---

## Feature 2: /review Command

### File: `commands/review.md` (new)

Standalone pre-landing code review. Produces judgment, not checklists. Goes deeper than the pipeline's Gate 3 review agent.

**5 review techniques:**

1. **Error & Rescue Map** — Method → What Fails → Exception Class → Rescued? → Test? → User Sees
2. **Shadow Path Tracing** — Happy, Nil input, Empty input, Upstream error
3. **Interaction Edge Cases** — double-click, navigate-away, stale state, back button
4. **Failure Modes Registry** — ID → Category → Severity → Description → Status
5. **Architecture Diagram** — Mandatory ASCII for non-trivial flows showing data path and failure points

### Integration with /ship

Review findings flow into PR "Review Notes" section when run before `/ship`.

### Invocation

| Invocation | Behavior |
|------------|----------|
| `/review` | Default: staged + unstaged changes on current branch |
| `/review --diff base` | Review all changes vs. specified base |
| `/review --file path` | Review a specific file's changes |
| `/review --spec path` | Review with spec context for richer analysis |

---

## Feature 3: /retro Command

### File: `commands/retro.md` (new)

Git-based retrospective. Turns commit history into actionable insight.

**Git metrics:** commits, LOC, files, test ratio, sessions, streaks

**Session detection:** Gap-based clustering. Default threshold: 2 hours between commits defines session boundaries.

**Writ context (if available):** specs completed, stories completed, drift incidents, commands refreshed

**Output:** Markdown with metrics table (Δ vs Last), Ship of Week, Patterns, Tweetable

### Persistence

- **JSON snapshots:** `.writ/retros/YYYY-MM-DD.json` — raw metrics
- **Trends:** `.writ/retros/trends.json` — rolling averages (optional, gitignored)
- Markdown output is ephemeral (printed to conversation); JSON is persistent

### Auto-Detection

- **Timezone:** `date +%Z` or system locale — never hardcode
- **Default branch:** `git remote show origin` — never assume `main`
- **Period suggestion:** Default 7 days; suggest spec-scoped retros when a spec just completed

---

## Feature 4: Error Mapping in /create-spec

### File: `commands/create-spec.md` (modification)

Add to **Step 2.8 (Technical Sub-Specs)** of the create-spec pipeline.

**Three required sections** for features with user-facing data flows:

1. **Error & Rescue Map (Planning Phase)** — Operation → What Can Fail → Planned Handling → Test Strategy
2. **Shadow Paths** — Flow → Happy → Nil → Empty → Upstream Error
3. **Interaction Edge Cases** — Edge Case → Planned Handling

### Scope Rules

**Required for:** API routes, auth, payments, file ops, external integrations

**Optional for:** Pure UI, docs, config, refactors

### Shared Format with /review

Same table structures. Enables plan-vs-actual comparison: did the code handle what the spec said it would? Planning in `/create-spec`, verification in `/review`.

---

## Story-to-File Mapping

| Story | Files | Description |
|-------|-------|-------------|
| Story 1: Ship core workflow | `commands/ship.md` (new), `commands/implement-story.md` (modify) | Pipeline steps 1–4, suggest /ship after completion |
| Story 2: Ship PR creation | `commands/ship.md` | Step 5, PR body, labels, draft/ready |
| Story 3: Standalone /review | `commands/review.md` (new) | Five techniques, invocation modes |
| Story 4: Retro git analysis | `commands/retro.md` (new) | Metrics, session detection |
| Story 5: Retro output & trends | `commands/retro.md`, `.writ/retros/` | Output format, persistence, trends |
| Story 6: Error mapping | `commands/create-spec.md` (modify) | Step 2.8 sections |
| Story 7: Integration | All above | Dogfooding, validation |

---

## Cross-Cutting Concerns

### Design Principle 6: Opinionated by Default

All commands lead with recommendations:

- **/ship:** "I recommend merge (not rebase) because..." then offer alternatives
- **/review:** "The critical gap is X because..." not a neutral findings list
- **/retro:** "Your biggest win was X, your biggest risk is Y" not raw metrics
- **Error mapping:** `[UNPLANNED]` markers force explicit decisions — either plan handling or declare out of scope

### Shared Error Format

`/create-spec` (planning) and `/review` (verification) use identical table structures. Plan-vs-actual comparison: did the code handle what the spec said it would?

### Context Window Management

- **/ship:** Concise — execution command, not discovery. Minimal prompt footprint.
- **/review:** Focus depth on the diff's critical paths, not exhaustive scanning.
- **/retro:** JSON snapshots keep persistent data small; markdown output is ephemeral.

### Platform Agnosticism

- All commands work on any AI platform that can read markdown instructions
- PR creation defaults to `gh` CLI but detection chain supports GitLab
- Test runner detection covers JS, Python, Elixir, Rust ecosystems
- No platform-specific runtime dependencies

### Adapter Considerations

Command files are platform-agnostic. For each platform:
- **Cursor:** Copy to `.cursor/commands/`
- **Claude Code:** Copy to `.claude/commands/`
- **OpenClaw:** Available via skill system

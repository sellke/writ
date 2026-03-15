# Phase 2a: Shipping & Review — Specification

> Created: 2026-03-15
> Last Updated: 2026-03-15
> Status: In Progress — Dogfooding Pending
> Contract Locked: ✅
> Planning Posture: HOLD — pressure-test workflow gaps, strengthen before expanding

## Contract Summary

**Deliverable:** Five capabilities that close Writ's shipping and review gaps — a unified shipping workflow (`/ship`), standalone code review (`/review`), git-based retrospectives (`/retro`), and failure-aware specs (error mapping in `/create-spec`). The PR agent concept from the original Phase 2 roadmap is absorbed into `/ship` rather than existing as a separate entity.

**Must Include:**
- `/ship` as a top-level command handling merge → test → commit splitting → PR creation with structured descriptions
- Standalone `/review` for pre-landing code review with error mapping, shadow paths, and failure mode analysis
- `/retro` with git-based metrics, persistent snapshots, and trend comparison
- Error & rescue map as a required section in technical sub-specs via `/create-spec`

**Hardest Constraint:** `/ship` needs to auto-detect the project's test runner, default branch, and git workflow conventions without configuration. Getting this detection reliable across diverse projects is the most fragile piece.

**Success Criteria:**
- `/ship` takes a green branch to merged PR with zero manual PR body writing
- `/review` catches at least one failure mode per review that the pipeline review agent missed
- `/retro` produces trend comparison against the previous period's snapshot
- Error mapping surfaces rescue gaps in technical sub-specs before implementation begins

**Scope Boundaries:**
- Included: `/ship` command (with PR agent behavior), standalone `/review`, `/retro`, error mapping in `/create-spec`
- Excluded: Skill system (Phase 2b), cross-project patterns (Phase 2b), MCP integration points (Phase 2b), browser QA (Phase 3), self-improving agents (Phase 3)

---

## Premise & Context

### Why Now

Phase 1 built the foundation: adaptive ceremony (`/prototype`), self-correcting pipeline (spec-healing), and compounding intelligence (`/refresh-command`). The biggest remaining gap in Writ's daily workflow is the space between "pipeline green" and "code merged." Today, after `/implement-story` completes, the developer manually creates commits, writes PR descriptions, and opens the PR. This is the ceremony that adaptive-ceremony hasn't yet reached.

### Why These Four (Not All Eight)

The Phase 2 roadmap contains 8 features. This spec covers the 4 with the most immediate daily value (plus `/retro` for closing the feedback loop). The remaining 3 — skill system (L), cross-project patterns (L), and MCP integration (M) — are intelligence infrastructure that depends on Phase 1 producing real drift reports, command improvements, and usage patterns through dogfooding. Building them before that signal exists risks the wrong abstraction.

### PR Agent → Folded Into `/ship`

The roadmap listed a "PR agent" and a "`/ship` command" separately. Both create PRs. The overlap is resolved by folding the PR agent's structured-description and auto-labeling behavior into `/ship` as its PR creation step. This gives one command that owns the full "branch to merged" path: `/implement-story` → pipeline green → `/ship` → merged PR. If a project doesn't use `/implement-story`, `/ship` still works standalone on any branch.

---

## Detailed Requirements

### Feature 1: `/ship` Command

#### Purpose

Unified shipping workflow that takes a green branch to a merged PR. Replaces the manual sequence of merge-main, run-tests, organize-commits, write-PR, push, open-PR. Non-interactive by default — momentum over ceremony.

#### Design Philosophy

`/ship` is the *last mile* command. It assumes the code is ready (tests pass, review complete) and focuses on getting it merged cleanly. It's not a second review gate — that's what `/review` and the pipeline are for. `/ship` is about shipping with confidence and a clean git history.

The PR agent behavior (structured descriptions, auto-labels, draft/ready detection) lives inside `/ship` because PR creation without the surrounding workflow (merge, test, commit) is incomplete. A standalone PR agent would always need "but first merge main, but first run tests" — so `/ship` owns the full path.

#### Pipeline

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ DETECT       │──▶│ MERGE &      │──▶│ RUN          │──▶│ COMMIT       │──▶│ PR           │
│ CONVENTIONS  │   │ REBASE       │   │ TESTS        │   │ INTELLIGENCE │   │ CREATION     │
│              │   │              │   │              │   │              │   │              │
│ • branch     │   │ • fetch      │   │ • auto-      │   │ • bisectable │   │ • structured │
│ • test runner│   │   origin     │   │   detect     │   │   splitting  │   │   body       │
│ • PR style   │   │ • merge or   │   │   runner     │   │ • logical    │   │ • auto-label │
│              │   │   rebase     │   │ • report     │   │   grouping   │   │ • draft/ready│
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
                          │                  │                                      │
                     conflict?          test fail?                            ┌─────┴─────┐
                          ▼                  ▼                                │ PUSH &    │
                   ┌──────────────┐   ┌──────────────┐                       │ OPEN PR   │
                   │ PAUSE        │   │ REPORT &     │                       │ + URL     │
                   │ show conflict│   │ FIX OPTION   │                       └───────────┘
                   └──────────────┘   └──────────────┘
```

#### Step 1: Detect Conventions

Auto-detect without configuration:

| Convention | Detection Chain | Fallback |
|---|---|---|
| **Default branch** | `git remote show origin` → check for `main`/`master`/`develop` | Ask user |
| **Test runner** | `package.json` scripts → `Makefile` → `pytest.ini`/`setup.cfg` → `mix.exs` → `Cargo.toml` | Ask user |
| **Merge strategy** | Check for `.gitconfig` merge preference → repo convention detection | Default: merge (not rebase) |
| **PR tool** | `gh` CLI available → `GITHUB_TOKEN` set → `.gitlab-ci.yml` exists | Default: `gh` with guidance if unavailable |

Detection results are printed at the start so the user can verify before proceeding:

```
📋 Detected: main branch, npm test, merge strategy, gh CLI
   Override? [Enter to continue, or specify changes]
```

#### Step 2: Merge & Rebase

```
git fetch origin
git merge origin/[default-branch]
```

If conflicts: pause, show conflicting files, offer to open in editor. Do not auto-resolve.

#### Step 3: Run Tests

Execute the detected test command. Stream output. On failure:
- Show the failure summary
- Offer: "Fix and retry" / "Ship anyway (draft PR)" / "Abort"

On success: continue silently (momentum).

#### Step 4: Commit Intelligence

Analyze the diff and split into bisectable commits when beneficial:

**Splitting heuristic:**
- Infrastructure changes (config, deps, migrations) → separate commit
- Model/schema changes → separate commit
- Business logic → separate commit
- Test additions → co-located with the code they test
- Version bumps → final commit

**When NOT to split:**
- Single-file changes
- Changes < 50 lines total
- All changes are tightly coupled (splitting would create broken intermediate states)

Commit messages follow conventional commits format and reference the Writ spec/story if available:

```
feat(auth): add session timeout handling

Implements session expiration with configurable TTL.
Ref: .writ/specs/2026-03-15-auth-system/story-3-session-management.md
```

#### Step 5: PR Creation (PR Agent Behavior)

**Structured PR body generation:**

```markdown
## Summary
[2-3 sentence description derived from commit messages and diff analysis]

## Changes
[Bullet list of logical changes, grouped by domain]

## Spec Reference
[Link to .writ spec and story if available]

## Test Results
[Pass/fail summary from Step 3]

## Drift Report
[Summary from spec-healing drift-log if available, otherwise "No spec drift detected"]

## Review Notes
[Any flagged items from the pipeline review or /review command]
```

**Auto-labeling:** Based on file types changed and spec category:
- `infra` — config, CI, deps
- `feature` — new functionality
- `fix` — bug fixes
- `refactor` — restructuring without behavior change
- `docs` — documentation only

**Draft vs. Ready:**
- All tests pass + no medium/large drift → Ready for review
- Test warnings or medium drift → Draft PR with notes
- User override available in both directions

#### Invocation

| Invocation | Behavior |
|---|---|
| `/ship` | Full workflow from current branch |
| `/ship --no-split` | Skip commit splitting (ship as-is) |
| `/ship --draft` | Force draft PR regardless of test results |
| `/ship --dry-run` | Show what would happen without executing |

#### Output

On completion:
```
✅ Shipped!
   Branch: feature/session-timeout
   Commits: 3 (infra → logic → tests)
   PR: https://github.com/user/repo/pull/42 (Ready for review)
   Labels: feature, auth
```

---

### Feature 2: Standalone `/review` Command

#### Purpose

Pre-landing code review that goes deeper than the pipeline's Gate 3 review agent. The pipeline reviewer focuses on spec adherence and code quality within a story context. `/review` is an independent command that analyzes any diff for failure modes, shadow paths, and interaction edge cases — the things that break in production but look fine in a PR.

#### Design Philosophy

`/review` produces *judgment*, not a checklist. It identifies the specific ways this code can fail and whether those failures are handled. The output format forces completeness: if a failure mode has no rescue, no test, and the user sees nothing — that's a critical gap, and `/review` calls it out.

This is the standalone version of the techniques described in the roadmap's gstack-inspired review depth. The pipeline review agent may eventually absorb some of these techniques, but `/review` exists independently for:
- Pre-`/ship` review of accumulated changes
- Reviewing code not written through the Writ pipeline
- Deep review of critical paths that warrant extra scrutiny

#### Review Techniques

**1. Error & Rescue Map**

For every method/function in the diff that can fail:

| Method | What Fails | Exception Class | Rescued? | Test? | User Sees |
|---|---|---|---|---|---|
| `createSession()` | DB connection lost | `ConnectionError` | Yes — retry 3x | Yes | "Try again" toast |
| `validateToken()` | Token expired | `AuthError` | Yes — redirect to login | Yes | Login page |
| `processPayment()` | Stripe timeout | `TimeoutError` | **No** | **No** | **Silent failure** ← CRITICAL |

The rightmost columns are the signal: `RESCUED=N, TEST=N, USER SEES=Silent` is a critical gap.

**2. Shadow Path Tracing**

For critical data flows, trace four paths:

| Path | Input | Expected | Actual |
|---|---|---|---|
| Happy path | Valid user, valid data | Success | ✅ Handled |
| Nil input | `null`/`undefined` user | Graceful error | ⚠️ Unchecked — throws TypeError |
| Empty input | Empty string, empty array | Validation error | ✅ Handled |
| Upstream error | API returns 500 | Fallback UI | ❌ Unhandled — white screen |

**3. Interaction Edge Cases**

For user-facing features:

| Edge Case | Handled? | How |
|---|---|---|
| Double-click on submit | ❌ | No debounce — creates duplicate |
| Navigate away during async | ⚠️ | No cleanup — memory leak |
| Stale state after tab switch | ❌ | No refresh on focus |
| Back button after mutation | ✅ | Cache invalidation on popstate |

**4. Failure Modes Registry**

Aggregated view of all findings:

| ID | Category | Severity | Description | Status |
|---|---|---|---|---|
| FM-001 | Error handling | Critical | Payment timeout has no rescue | Unresolved |
| FM-002 | Shadow path | High | Null user input causes TypeError | Unresolved |
| FM-003 | Interaction | Medium | Double-click creates duplicate submissions | Unresolved |

**5. Architecture Diagram**

For non-trivial flows, mandatory ASCII diagram showing the data path and failure points:

```
User → [Form Submit] → API Route → [Validate] → DB Write → [Notify] → Response
                            ↓              ↓           ↓
                       AuthError      ConnError    QueueError
                       (rescued ✅)   (retry ✅)   (silent ❌ FM-001)
```

#### Invocation

| Invocation | Behavior |
|---|---|
| `/review` | Review staged + unstaged changes on current branch |
| `/review --diff main` | Review all changes vs. a specific base |
| `/review --file src/auth/session.ts` | Review a specific file's changes |
| `/review --spec .writ/specs/...` | Review with spec context for richer analysis |

#### Output

Structured markdown report. When run before `/ship`, the report's findings are automatically included in the PR's "Review Notes" section.

---

### Feature 3: `/retro` Command

#### Purpose

Git-based retrospective that turns commit history into actionable insight. Replaces "how did that sprint go?" gut feelings with data: what was built, how fast, what patterns emerged, and how it compares to the previous period.

#### Design Philosophy

`/retro` is opinionated about what matters: shipping velocity, code quality signals, and developer momentum. It doesn't try to be a full analytics dashboard — it's a focused snapshot that takes 30 seconds to read and surfaces the one or two things worth changing.

Inspired by gstack's retrospective patterns: team-aware analysis (even for solo devs — "you" is the team), commit-anchored specifics, and a tweetable summary that captures the period's essence.

#### Metrics Collected

**From git history:**
- Commits per day/week
- Lines added/removed (net and gross)
- Files changed (unique files touched)
- Test file ratio (test files changed / total files changed)
- Session detection: clusters of commits separated by gaps (configurable threshold, default 2 hours)
- Streak tracking: consecutive days with commits

**From Writ context (if available):**
- Specs completed this period
- Stories completed this period
- Drift incidents (from drift-log.md files)
- Commands refreshed (from refresh-log.md)

#### Session Detection

Sessions are clusters of commits separated by inactivity gaps:

```
Commit at 10:00, 10:15, 10:45, 11:30  →  Session 1 (1.5 hours)
[gap: 4 hours]
Commit at 15:30, 16:00, 16:45          →  Session 2 (1.25 hours)
```

Default gap threshold: 2 hours. Configurable.

#### Output Format

```markdown
# Retro: 2026-03-08 → 2026-03-15

> Branch: main | Timezone: America/Los_Angeles (auto-detected)

## 📊 This Period

| Metric | Value | Δ vs Last |
|--------|-------|-----------|
| Commits | 34 | +12 (+54%) |
| Lines (net) | +1,247 | +380 |
| Files touched | 18 | -3 |
| Test ratio | 0.38 | +0.05 |
| Sessions | 8 | +2 |
| Avg session | 1.8 hrs | -0.3 |
| Streak | 5 days | +2 |

## 🏆 Ship of the Week

**Tiered spec-healing agent** — Implemented severity classification
that auto-heals small drift, flags medium, and pauses on large
deviations. 6 files, 171 lines added to review-agent.md.

> Commit: abc1234 (2026-03-11)

## 🔍 Patterns

- **High test coverage period** — Test ratio 0.38 is above your
  6-week average (0.29). The spec-healing work drove this.
- **Session clustering** — 6 of 8 sessions were morning blocks.
  Afternoon sessions were shorter and more scattered.

## 📋 Writ Integration

- Specs completed: 1 (Pipeline Quality Improvements)
- Stories completed: 7
- Drift incidents: 2 small (auto-healed), 1 medium (flagged)
- Commands refreshed: 0

## 🐦 Tweetable

"Shipped tiered spec-healing and 7 stories this week. Test ratio
hit 0.38 — highest in 6 weeks. The pipeline is learning to
self-correct."
```

#### Persistence

Snapshots saved as JSON in `.writ/retros/`:

```
.writ/retros/
├── 2026-03-15.json    ← raw metrics
├── 2026-03-08.json    ← previous period
└── trends.json        ← rolling averages and trends
```

The JSON format enables trend comparison across periods. The markdown output is ephemeral (printed to conversation); the JSON is persistent.

#### Invocation

| Invocation | Behavior |
|---|---|
| `/retro` | Last 7 days from current branch |
| `/retro --period 14` | Last 14 days |
| `/retro --spec .writ/specs/2026-03-15-...` | Scope to a spec's lifetime |
| `/retro --compare` | Side-by-side with previous period |
| `/retro --all-branches` | Include all branches (default: current only) |

#### Auto-Detection

- **Timezone:** `date +%Z` or system locale — never hardcode
- **Default branch:** `git remote show origin` — never assume `main`
- **Period:** Default 7 days, but smart enough to suggest spec-scoped retros when a spec just completed

---

### Feature 4: Enhanced Error Mapping in `/create-spec`

#### Purpose

Add failure-aware analysis as a required section in technical sub-specs generated by `/create-spec`. This brings the error & rescue map, shadow paths, and interaction edge case analysis from `/review` upstream into the planning phase — catching failure modes before code is written rather than after.

#### Design Philosophy

This is the planning-phase counterpart to `/review`'s implementation-phase analysis. The same formats, the same rigor, but applied to the *spec* rather than the *code*. The key insight: if you can identify "payment timeout has no planned rescue" during spec creation, you save the cost of discovering it in review.

The error mapping format is shared between `/create-spec` (planning) and `/review` (verification). One format, two entry points.

#### Changes to `/create-spec`

**In Phase 2 (Spec Package Creation), Step 2.8 (Generate Technical Sub-Specs):**

`technical-spec.md` gains three required sections for features with user-facing data flows:

**1. Error & Rescue Map (Planning Phase)**

```markdown
## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Create session | DB unavailable | Retry 3x, then error page | Integration test with DB down |
| Validate token | Token expired | Redirect to login | Unit test with expired fixture |
| Process payment | Stripe timeout | [UNPLANNED] ← spec gap | — |
```

The `[UNPLANNED]` marker is the signal: it forces the spec author to either plan the handling or explicitly declare it out of scope.

**2. Shadow Paths (Planning Phase)**

```markdown
## Shadow Paths

For each critical data flow, document planned behavior for:

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| User registration | Create account | 422 + field errors | 422 + field errors | 503 + retry prompt |
| File upload | Store + thumbnail | 400 + "no file" msg | 400 + "empty file" | 502 + "service unavailable" |
```

**3. Interaction Edge Cases (Planning Phase)**

```markdown
## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Double-click on submit | Debounce — disable button after first click |
| Navigate away during async | Cancel pending requests, no cleanup issues |
| Stale state after tab switch | Refetch on window focus |
| Back button after mutation | Invalidate cache, show fresh state |
```

#### Scope

Error mapping is **required** for specs that touch:
- API routes or data endpoints
- Authentication or authorization flows
- Payment or financial transactions
- File operations (upload, download, processing)
- External service integrations

Error mapping is **optional** for:
- Pure UI changes (CSS, layout, copy)
- Documentation-only changes
- Configuration changes
- Internal refactors with no user-facing surface

#### Shared Format

The tables above are identical in structure to `/review`'s output. This is intentional — during `/review`, the reviewer can compare the *planned* error handling (from the spec) against the *actual* error handling (from the code) and flag discrepancies. The spec becomes a contract for failure handling, not just happy-path behavior.

---

## Implementation Approach

### Dependency Graph

```
Story 1: /ship core workflow ─────────────────── (independent)
Story 2: /ship PR creation & commit intel ────── depends on Story 1
Story 3: Standalone /review command ──────────── (independent)
Story 4: /retro git analysis & metrics ───────── (independent)
Story 5: /retro output, persistence & trends ─── depends on Story 4
Story 6: Error mapping in /create-spec ───────── (independent)
Story 7: Integration testing & dogfooding ────── depends on all above
```

### Parallel Execution Batches

```
Batch 1 (parallel): Story 1, Story 3, Story 4, Story 6
Batch 2 (parallel): Story 2, Story 5
Batch 3 (sequential): Story 7
```

### Technical Patterns

All deliverables are **command files** (markdown) and **agent extensions** (markdown). No runtime code, no CLI, no server. Consistent with Phase 1 and Writ's methodology-first identity.

**Files to create:**
- `commands/ship.md` — NEW (Stories 1, 2)
- `commands/review.md` — NEW (Story 3)
- `commands/retro.md` — NEW (Stories 4, 5)

**Files to modify:**
- `commands/create-spec.md` — MODIFIED (Story 6 — error mapping sections)
- `commands/implement-story.md` — MODIFIED (Story 1 — suggest `/ship` after pipeline completion)

### Cross-Cutting: Opinionated Posture (Design Principle 6)

All new commands follow the opinionated-by-default principle:
- `/ship` leads with "I recommend merge (not rebase) because..." then offers alternatives
- `/review` leads with "The critical gap is X because..." not a neutral findings list
- `/retro` leads with "Your biggest win was X, your biggest risk is Y" not raw metrics
- Error mapping surfaces `[UNPLANNED]` gaps with recommendations, not just blanks

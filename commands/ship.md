# Ship Command (ship)

## Overview

Unified shipping workflow that takes a green branch to a merged PR. Replaces the manual sequence of merge-main → run-tests → organize-commits → write-PR → push → open-PR. Non-interactive by default — momentum over ceremony.

`/ship` is the *last mile* command. It assumes the code is ready (review complete, confidence in correctness) and focuses on getting it merged cleanly. **Tests do not run by default** — use `/ship --test` when you want the suite after merging the default branch. It's not a second review gate — that's what `/review` is for.

Use `/ship` standalone on any branch, or as the natural next step after `/implement-story` completes.

**How `/ship` absorbs the PR agent concept:**

The roadmap listed a "PR agent" and a "`/ship` command" separately. Both create PRs. `/ship` folds the PR agent's structured-description, auto-labeling, and draft/ready detection into its PR creation step. One command owns the full "branch to merged" path: `/implement-story` → pipeline green → `/ship` → merged PR.

## Invocation

| Invocation | Behavior |
|---|---|
| `/ship` | Full workflow from current branch (no test run) |
| `/ship --test` | After merge/rebase, run the full test suite before commit intelligence |
| `/ship --no-split` | Skip commit splitting (ship as-is) |
| `/ship --draft` | Force draft PR regardless of test results |
| `/ship --rebase` | Use rebase instead of merge in Step 2 |
| `/ship --dry-run` | Show what would happen without executing |

## Pipeline

Default path **omits** tests. With `/ship --test`, the dashed box runs after merge.

```
┌──────────────┐   ┌──────────────┐   ┌ ╍╍╍╍╍╍╍╍╍╍╍╍ ┐   ┌──────────────┐   ┌──────────────┐
│ DETECT       │──▶│ MERGE &      │ ╷ │ RUN TESTS    │ ╷ │ COMMIT       │──▶│ PR           │
│ CONVENTIONS  │   │ REBASE       │ ╷ │ (--test)     │ ╷ │ INTELLIGENCE │   │ CREATION     │
│              │   │              │ ╵ │ optional     │ ╵ │              │   │              │
│ • branch     │   │ • fetch      │   └ ╍╍╍╍╍╍╍╍╍╍╍╍ ┘   │ • splitting  │   │ • structured │
│ • test runner│   │ • merge /    │          ▲            │ • grouping   │   │   body       │
│ • PR style   │   │   rebase     │    only if --test     │              │   │ • spec health│
└──────────────┘   └──────────────┘          │            └──────────────┘   └──────────────┘
                          │                  │                                      │
                     conflict?          test fail? (--test only)           ┌─────┴─────┐
                          ▼                  ▼                             │ PUSH &    │
                   ┌──────────────┐   ┌──────────────┐                       │ OPEN PR   │
                   │ PAUSE        │   │ FIX / DRAFT  │                       │ + URL     │
                   │ show conflict│   │ / ABORT      │                       └───────────┘
                   └──────────────┘   └──────────────┘
```

## Command Process

### Step 1: Detect Conventions

Auto-detect project conventions without configuration. Print results for user verification before proceeding.

| Convention | Detection Chain | Fallback |
|---|---|---|
| **Default branch** | `git remote show origin` → check for `main`/`master`/`develop` | Ask user |
| **Test runner** | `package.json` scripts → `Makefile` → `pytest.ini`/`setup.cfg` → `mix.exs` → `Cargo.toml` | Ask user |
| **Merge strategy** | `.gitconfig` merge preference → repo convention detection | Default: merge |
| **PR tool** | `gh` CLI available → `GITHUB_TOKEN` set → `.gitlab-ci.yml` exists | Default: `gh` |

**Detection chain details:**

**Default branch:**
1. Run `git remote show origin` and parse "HEAD branch:"
2. If no remote, check local branches for `main`, `master`, `develop` (in that order)
3. If ambiguous, ask user

**Test runner:**
1. Check `package.json` → look for `scripts.test` (run with `npm test`)
2. Check `Makefile` → look for `test:` target (run with `make test`)
3. Check `pytest.ini`, `setup.cfg`, `pyproject.toml` → Python (run with `pytest`)
4. Check `mix.exs` → Elixir (run with `mix test`)
5. Check `Cargo.toml` → Rust (run with `cargo test`)
6. If none found, ask user

**Merge strategy:**
1. Check `git config pull.rebase` and `git config merge.ff`
2. Scan recent merge commits on default branch for rebase vs merge patterns
3. Default to merge — it preserves commit history for bisection

**PR tool:**
1. Check if `gh` CLI is installed (`which gh`)
2. Check for `GITHUB_TOKEN` environment variable
3. Check for `.gitlab-ci.yml` (suggests GitLab, use `glab` if available)
4. Default to `gh` with guidance if unavailable

**Opinionated defaults (Design Principle 6):**

I recommend **merge** (not rebase) because it preserves commit history for bisection and avoids force-push risks on shared branches. Override with `--rebase` if your project uses a rebase-based workflow.

I recommend **`gh` CLI** for PR creation because it's the most widely available and requires the least configuration. The detection chain catches GitLab projects automatically.

**Output:**

```
📋 Detected: main branch, npm test, merge strategy, gh CLI
   Override? [Enter to continue, or specify changes]
```

If any convention can't be detected:

```
❓ Couldn't detect test runner. What command runs your tests?
   (e.g., npm test, pytest, mix test, cargo test)
```

### Step 2: Merge Default Branch

Bring the current branch up to date with the target branch before shipping.

```bash
git fetch origin
git merge origin/[default-branch]
```

**On clean merge:** Continue silently — momentum over ceremony.

**On already up-to-date:** Continue silently.

**On conflict:**

```
⚠️ Merge conflict detected.

Conflicting files:
- src/components/Header.tsx
- src/lib/auth.ts

Options:
1. Open in editor — resolve manually, then re-run /ship
2. Abort — stop shipping, resolve conflicts first
```

Do not auto-resolve merge conflicts. The cost of a bad resolution is much higher than pausing for 2 minutes of human judgment.

**If `--rebase` flag or rebase convention detected:**

```bash
git fetch origin
git rebase origin/[default-branch]
```

Same conflict handling applies. On rebase conflict, offer `git rebase --abort` as the abort option.

### Step 3: Run Tests (optional — `/ship --test`)

**If `--test` is not set:** Skip this step entirely — go to Step 4.

**If `--test` is set:** Execute the test command detected in Step 1. Stream output so the user sees progress in real time.

```bash
# Runs the command detected in Step 1:
npm test              # Node.js
pytest                # Python
mix test              # Elixir
cargo test            # Rust
make test             # Makefile-based
```

**On success:** Continue silently to Step 4.

**On failure:**

```
❌ Tests failed (3 failures, 47 passing)

[Failures summarized from runner output]

1. Fix and retry
2. Ship anyway — draft PR + tests-failing label, continue
3. Abort
```

**On option 1:** Analyze failures against the diff, attempt one focused fix pass, re-run tests; if still failing, present 1–3 again.

**On option 2:** Force `--draft`, add **`tests-failing`** label, include failure summary under **Test Results** in the PR body, continue to Step 4.

**On option 3:** Offer `git merge --abort` / `git rebase --abort` if helpful; stop.

### Step 4: Commit Intelligence

Analyze the diff and organize changes into bisectable commits when beneficial. The goal is a git history that supports future debugging — `git bisect` should land on meaningful boundaries, not arbitrary save points.

**Splitting heuristic — split when the diff contains distinct logical layers:**

| Layer | Grouping | Commit Prefix |
|---|---|---|
| Infrastructure | Config files, dependency changes, migrations, CI | `chore:` or `build:` |
| Models/Schema | Database schema, type definitions, data models | `feat:` or `refactor:` |
| Business logic | Application code, handlers, services | `feat:` or `fix:` |
| Tests | Test files co-located with the code they test | Grouped with their corresponding logic commit |
| Version bumps | `package.json` version, changelog entries | `chore: bump version` |

**When NOT to split — ship as a single commit:**
- Single-file changes — splitting would be artificial
- Changes < 50 lines total — not enough to benefit from splitting
- All changes are tightly coupled — splitting would create broken intermediate states (e.g., a type change + all its call sites)
- `--no-split` flag is set

**Each intermediate commit should leave the repo in a good state.** When `/ship --test` is used, avoid splits that would leave tests failing midway — merge layers if needed. When `--test` was not used, prioritize **buildability** (no syntax/type errors obvious from the split).

**Commit message format — conventional commits with Writ references:**

```
feat(auth): add session timeout handling

Implements session expiration with configurable TTL.
Ref: .writ/specs/2026-03-15-auth-system/story-3-session-management.md
```

| Component | Source |
|---|---|
| Type (`feat`, `fix`, `chore`, `refactor`, `docs`) | Inferred from file types and change nature |
| Scope (`auth`, `api`, `ui`) | Inferred from directory names in the diff |
| Summary | Generated from diff analysis — what changed and why |
| Body | Brief elaboration if the summary isn't self-explanatory |
| Ref | Link to `.writ/specs/` story file if available |

I recommend **conventional commits** because they're machine-parseable (changelogs, release notes) and human-scannable. If the project already uses a different convention (detected from recent commit history), match that instead.

**Splitting workflow:**

1. Analyze the full diff — categorize every changed file by layer
2. Determine if splitting is beneficial (apply the "when NOT to split" rules)
3. If splitting: stage files by layer group, create commits in dependency order (infra → models → logic → tests → version)
4. After each commit, verify the repo is in a buildable state
5. If any split commit would break the build, merge it with the adjacent commit

**Present the plan and wait for approval before executing:**

```
📦 Commit plan (3 commits):
  1. chore(deps): update auth library to v3.2
  2. feat(auth): add session timeout with configurable TTL
  3. test(auth): add session expiration test coverage

I recommend this split because it separates the dependency update from the feature,
making bisection possible if the auth library upgrade causes issues.
```

```
AskQuestion({
  title: "Confirm Commit Plan",
  questions: [{
    id: "commit_plan",
    prompt: "Proceed with this commit plan?",
    options: [
      { id: "yes", label: "Execute this plan" },
      { id: "no_split", label: "Ship as a single commit instead" },
      { id: "edit", label: "Adjust the plan (I'll specify changes)" }
    ]
  }]
})
```

This gate prevents the commit plan from executing without explicit approval — restructuring git history is not something to auto-proceed on.

### Step 5: PR Creation

Create a pull request with a structured body, auto-labels, and appropriate draft/ready status.

**PR body template:**

```markdown
## Summary
[2-3 sentence description derived from commit messages and diff analysis.
Focus on *what changed and why*, not implementation details.]

## Changes
[Bullet list of logical changes, grouped by domain:]
- **Auth:** Added session timeout with configurable TTL
- **Config:** Updated auth library to v3.2
- **Tests:** Added session expiration test coverage (3 new tests)

## Spec Reference
[Link to .writ spec and story if available, else "Standalone change (no spec)"]
- Spec: .writ/specs/2026-03-15-auth-system/spec.md
- Story: story-3-session-management.md

## Test Results
[/ship --test: pass/fail summary from Step 3]
[/ship without --test: "Tests not run (use `/ship --test` to execute the suite before opening the PR)."]

## Spec Health
[Omitted when clean — populated only if inline checks 1–3 find unfixable issues; see Step 5.]

## Drift Report
[Summary from spec-healing drift-log if available:]
No spec drift detected.
[Or: "1 small deviation auto-healed — see drift-log.md DEV-012"]

## Review Notes
[Findings from /review if run before /ship, else "No pre-landing review performed.
Run /review before /ship for failure mode analysis."]
```

**Populating the template:**

| Section | Source |
|---|---|
| Summary | Generated from commit messages + diff analysis |
| Changes | Parsed from commits created in Step 4 (or full diff if --no-split) |
| Spec Reference | Detected from `.writ/specs/` in the repo — match branch name or recent story file references in commits |
| Test Results | Step 3 if `--test`; otherwise explicit "not run" line (see template) |
| Spec Health | Step 5 — incomplete metadata issues that could not be auto-fixed (checks 1–3 only); **omit entire subsection** when clean |
| Drift Report | Read from `drift-log.md` in the active spec folder if it exists |
| Review Notes | Read from `.writ/state/review-[branch-name].md` if `/review` was run before `/ship` |

If any section has no data (no spec, no drift log, no review), use clear placeholder text — don't leave the section empty or omit it, **except Spec Health** which must be omitted when there is nothing to report. The consistent structure helps reviewers know where to look.

**Inline spec health (silent):** During Step 5, if `.writ/specs/` exists **and** an active spec is identified (same discovery as **Spec Reference**):

1. Run **`/verify-spec` checks 1–3 only** — story file integrity, status consistency, completion integrity (definitions identical to the standalone command).
2. **Auto-fix** safe metadata issues with no user prompts (README table, task totals, status headers, premature status, etc.).
3. If **unfixable** problems remain (phantom stories, false completions, structural gaps): add a `## Spec Health` subsection to the PR body with short bullets. If everything is clean after fixes, **omit** `## Spec Health` entirely.

**Auto-labeling — additive, not exclusive:**

| Label | Applied When |
|---|---|
| `infra` | Config, CI, dependency, or migration files changed |
| `feature` | New functionality added (detected from `feat:` commits or new files) |
| `fix` | Bug fix (detected from `fix:` commits or issue references) |
| `refactor` | Restructuring without behavior change (detected from `refactor:` commits) |
| `docs` | Documentation-only changes |

Multiple labels can apply to the same PR. A change that adds a feature and updates CI gets both `feature` and `infra`.

**Label fallback:** Before applying labels, check if they exist in the repo (`gh label list`). If a label doesn't exist, skip it silently — don't let label creation failure block PR creation. Log which labels were skipped:

```
ℹ️ Labels "feature", "auth" not found in repo — PR created without labels.
   Create them with: gh label create feature
```

Never fail the entire `/ship` flow because of missing labels. The PR is the deliverable, not the labels.

**Draft vs. Ready determination:**

| Condition | PR Status |
|---|---|
| Default (`/ship` without `--test`), no `--draft`, drift acceptable | **Ready for review** — tests were not executed in this flow |
| `/ship --test` with all tests passing + drift acceptable | **Ready for review** |
| `/ship --test` with failures shipped via "Ship anyway" | **Draft** with `tests-failing` label |
| Test warnings or medium drift | **Draft** with notes explaining why |
| `--draft` flag set | **Draft** regardless of status |

User can override in both directions — force draft on a clean PR, or force ready on a draft.

**Push and open PR:**

```bash
git push -u origin [branch-name]
gh pr create --title "[title]" --body "[structured body]" --label "[labels]" [--draft]
```

If `gh` CLI requires authentication:
```
⚠️ GitHub CLI needs authentication.
Run: gh auth login
Then re-run /ship.
```

**Completion output:**

```
✅ Shipped!
   Branch: feature/session-timeout
   Commits: 3 (infra → logic → tests)
   PR: https://github.com/user/repo/pull/42 (Ready for review)
   Labels: feature, auth

⚠️ The PR is now the source of truth. If you push more commits to this
   branch, make sure the PR is still open — commits pushed after merge
   will be orphaned. For follow-up changes, open a new branch.
```

This warning prevents the scenario where additional commits are pushed to the branch after the PR is merged on GitHub, resulting in lost work that requires manual cherry-pick recovery.

**`--dry-run` output for Steps 4-5:**

```
Step 4 — Commit Intelligence:
  Would split into 3 commits:
    1. chore(deps): update auth library to v3.2 (2 files)
    2. feat(auth): add session timeout (4 files)
    3. test(auth): session expiration coverage (2 files)

Step 5 — PR Creation:
  Title: feat(auth): add session timeout with configurable TTL
  Labels: feature
  Status: Ready for review
  Body: [preview of structured PR body]
```

---

## Dry Run Mode (`--dry-run`)

Shows what `/ship` would do without executing any git commands or creating any PR:

```
🔍 Dry Run: /ship

Step 1 — Conventions:
  Default branch: main (from git remote)
  Test runner: npm test (from package.json)
  Merge strategy: merge (default)
  PR tool: gh CLI (installed)

Step 2 — Merge:
  Would run: git fetch origin && git merge origin/main
  Current state: 3 commits behind origin/main

Step 3 — Tests:
  Skipped (default — pass --test to run)
  [With --test: Would run: npm test]

Step 4 — Commit Intelligence:
  Would split into 3 commits:
    1. chore(deps): update auth library to v3.2 (2 files)
    2. feat(auth): add session timeout (4 files)
    3. test(auth): session expiration coverage (2 files)

Step 5 — PR Creation:
  Title: feat(auth): add session timeout with configurable TTL
  Labels: feature
  Status: Ready for review
  Body: [preview of structured PR body]

No changes made.
```

## Error Handling

**Not on a feature branch:**
```
⚠️ You're on the default branch (main). /ship works on feature branches.

Options:
1. Create a branch now — I'll name it from the diff and check it out
2. Abort — create the branch yourself, then re-run /ship
```

If the user picks option 1, generate a branch name from the diff (e.g., `feat/session-timeout` from the most significant change), run `git checkout -b [name]`, and continue the pipeline. This eliminates the round-trip of telling the user to do something they'll immediately ask you to do anyway.

**No git remote configured:**
```
⚠️ No git remote found. /ship needs a remote to push to.
Add one: git remote add origin <url>
```

**No changes to ship:**
```
⚠️ No changes detected between your branch and [default-branch].
Nothing to ship.
```

**PR tool unavailable:**
```
⚠️ gh CLI not found. Install it:
  brew install gh    (macOS)
  See: https://cli.github.com/

Or push manually and create the PR in your browser:
  git push -u origin [branch-name]
```

**Uncommitted changes:**
```
⚠️ You have uncommitted changes. /ship works with committed code.

Options:
1. Commit now — I'll stage everything and create a commit, then continue shipping
2. Stash changes — git stash, ship, then git stash pop
3. Abort — commit or stash manually, then re-run /ship
```

I recommend **option 1** (commit now) — it's the most common intent. The commit will go through Step 4's splitting heuristic anyway, so the initial commit message is a draft. Stashing risks losing track of uncommitted work.

**Combined scenario — on main with uncommitted changes:**

When both issues are present (on default branch + uncommitted changes), handle them in sequence: create the branch first, then commit. Don't present two separate error flows — combine into one:

```
⚠️ You're on main with uncommitted changes. Let me fix both:

1. Create branch: git checkout -b [generated-name]
2. Commit changes: git add -A && git commit -m "[draft message]"
3. Continue /ship pipeline

Proceed? [Enter to continue, or specify a branch name]
```

## When to Use /ship vs Other Commands

| Scenario | Command |
|---|---|
| Feature branch ready to merge | `/ship` |
| Want tests after merging default branch | `/ship --test` |
| Need code review before shipping | `/review` → `/ship` |
| Implementing a spec story | `/implement-story` → `/ship` |
| After PR merges — cut a version | `/release` (see Integration) |
| Quick prototype, not ready for PR | `/prototype` |
| Need to split commits only (no PR) | Manual `git rebase -i` |
| Shipping without commit reorganization | `/ship --no-split` |

## Integration with Writ

| Command | Relationship |
|---------|-------------|
| `/review` | Optional quality pass before `/ship` |
| `/release` | Natural follow-up **after** the PR lands — runs its own gate (build + conditional tests + changelog) |
| `/verify-spec` | Standalone metadata diagnostic; `/ship` embeds checks **1–3** only when opening a PR |

**Typical flow:** `/ship` → merge PR → `/release --dry-run` → `/release`.

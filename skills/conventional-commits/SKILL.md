---
name: conventional-commits
description: "Write Conventional Commits messages — type, scope, summary, body, and footers — from a diff, matching the project's existing convention when one exists."
disable-model-invocation: true
status: proven
evidence:
  - date: 2026-05-06
    type: usage
    ref: commands/ship.md
    note: "Cited as the commit-message authority in /ship's commit-intelligence phase."
  - date: 2026-05-12
    type: usage
    ref: commands/release.md
    note: "Release changelog grouping consumes this skill's type vocabulary."
  - date: 2026-06-01
    type: usage
    ref: agents/coding-agent.md
    note: "coding-agent authors story commits through this skill's grammar."
---

# Conventional Commits

## Purpose

Produce a commit message that is **machine-parseable** (changelogs, semver
bumps, release notes) and **human-scannable** (bisect, blame, review). The
message is one logical unit per commit; if the diff covers multiple unrelated
changes, the consumer's job is to split it before invoking this skill.

This skill replaces the inline commit-format guidance previously duplicated
across shipping, release, and refactor workflows. It does not decide *what* to
commit — only *how to phrase* a single commit, given a diff and the project's
existing commit history.

## When to Use

- About to run `git commit` and need to author the message
- Reviewing or rewording an existing commit before push
- Generating a PR title from a single-commit branch (PR title follows the same
  grammar)
- Parsing existing commits to attribute changes to types (changelogs, release
  notes) — same vocabulary, applied in reverse

## How to Apply

### 1. Detect the project's convention first

Inspect recent history before assuming Conventional Commits applies:

```bash
git log --oneline -20
```

Three outcomes:

| Recent commits look like… | Action |
|---|---|
| `feat(...): ...`, `fix: ...`, `chore(deps): ...` | Conventional Commits — proceed with the rules below |
| `[AUTH] add session timeout`, `JIRA-123: fix bug`, freeform | Match the existing style; do **not** impose Conventional Commits |
| Mixed / no clear pattern | Default to Conventional Commits — it's the most widely understood |

When matching a non-Conventional style, still apply the universal craft rules
(imperative summary, ≤72 chars, body explains *why*) — they're not specific to
Conventional Commits, just good commit hygiene.

### 2. Pick the type

The Angular type vocabulary, in order of changelog prominence:

| Type | Use when the diff… |
|---|---|
| `feat` | adds user-visible capability (new API, new UI affordance, new flag) |
| `fix` | repairs broken behavior (bug, regression, incorrect output) |
| `perf` | improves performance without changing behavior |
| `refactor` | restructures code without changing behavior or surface |
| `docs` | touches documentation only (README, code comments, .md files) |
| `style` | formatting, whitespace, missing semicolons (no logic change) |
| `test` | adds or fixes tests; production code untouched |
| `build` | build system, package manifests, dependency updates |
| `ci` | CI/CD configuration only |
| `chore` | maintenance not covered above (renames, gitignore, scripts) |
| `revert` | reverts a previous commit (body should reference the revert target) |

**Tie-break rule:** when two types fit, pick the one that signals more
risk — `fix` outranks `test`, `feat` outranks `refactor`, `revert` outranks
everything. The reader should never be surprised by what's inside.

### 3. Pick (or skip) the scope

Scope is **optional** and lives in parentheses after the type:

```
feat(auth): add session timeout handling
fix: prevent crash when config file is missing
```

Use a scope when:
- The change is contained to one component, module, or directory
- The project's recent commits use scopes consistently in the same area

Skip the scope when:
- The change touches multiple unrelated areas (don't fabricate a scope from
  the first file in the diff — drop it instead)
- Recent commits in this codebase rarely use scopes
- The scope would just restate the type (e.g. `docs(docs): ...`)

Scope should be short, lowercase, and stable across commits — pick the one the
project already uses for that area (`auth`, `api`, `ui`, `cli`, `deps`).

### 4. Craft the summary

The summary is the part after `: ` on the header line.

**Hard rules:**
- **Imperative mood** — "add session timeout" not "added" or "adds"
- **Lowercase first letter** — `feat: add` not `feat: Add`
- **No trailing period** — the header is a label, not a sentence
- **≤72 characters** for the entire header line (including type + scope + colon)
- **Self-contained** — should make sense without reading the body or diff

**Quality rules:**
- Describe *what changed*, not *what you did* — "add X" beats "implement X"
- Skip filler verbs like "update", "improve", "refactor" unless that's
  literally the change — they convey almost nothing
- If you reach for "and" in the summary, the commit probably needs splitting

**Good vs bad:**

```
✅ feat(auth): add session timeout with configurable TTL
❌ feat(auth): Updated session handling code (and added some tests)

✅ fix: prevent crash when CONFIG_PATH env var is unset
❌ fix: bug fix

✅ refactor(parser): extract token validation into separate module
❌ refactor: cleanup
```

### 5. Write the body (when warranted)

Skip the body entirely when the summary tells the whole story (typo fixes,
trivial bumps, formatting). Write a body when any of these apply:

- The *why* isn't obvious from the diff
- There's a non-obvious trade-off or alternative considered
- The change has a behavioral knock-on effect a future bisector should know
- The commit is part of a planned series (reference the others)

**Mechanics:**
- One blank line between summary and body
- Wrap at ~72 columns (readability in `git log`, terminal mailers, GitHub)
- Use prose; bullets are fine for enumerations but don't bullet a single point
- Explain *why* and *what's notable*, not *what* — the diff already shows what

```
feat(auth): add session timeout with configurable TTL

Sessions previously persisted until the browser closed, which created
support load when shared workstations leaked authenticated state. The
TTL defaults to 30 minutes (matches the audit logger's window) and can
be overridden per-tenant via SESSION_TTL_SECONDS.

Considered server-side idle tracking instead, but it would have required
a Redis dependency we're not ready to take on.
```

### 6. Add footers when they earn their keep

Footers go after a blank line below the body. Each footer is a `Token: value`
pair (or `Token #value` for issue refs). The recognized vocabulary:

| Footer | Meaning |
|---|---|
| `BREAKING CHANGE: <description>` | Triggers a major version bump in semver tooling. Describe what broke and how to migrate. |
| `Closes #123` / `Fixes #456` | Closes the linked issue when merged to the default branch. |
| `Refs: #789` | References an issue without closing it. |
| `Co-authored-by: Name <email>` | Credits a co-author on GitHub. |
| `Reviewed-by: Name <email>` | Records a reviewer (Linux-kernel-style). |
| `Ref: .writ/specs/<date>-<slug>/story-N-<title>.md` | Writ-specific — links the commit to its originating spec story. |

Breaking-change example:

```
feat(api)!: replace /v1/users endpoint with /v2/accounts

Returns the new Account schema instead of legacy User. The /v1/users
route is removed entirely.

BREAKING CHANGE: Clients calling /v1/users must migrate to /v2/accounts.
The response shape changes from `{user: {...}}` to `{account: {...}}`,
and the `email` field is renamed to `primary_email`.
```

Note the `!` after the scope — it's an alternative to the `BREAKING CHANGE:`
footer that some tools recognize. Use **both** for maximum compatibility:
the `!` for visual scanning, the footer for semver tools.

Writ-spec reference example:

```
feat(timeline): render story dependency graph in spec view

Spec authors needed a quick way to see which stories block which during
contract review. Renders the existing `dependencies:` frontmatter as a
collapsed Mermaid diagram inline with the spec body.

Ref: .writ/specs/2026-04-12-spec-timeline/story-3-dependency-graph.md
```

## Examples

**Simple feature, scope from directory name:**

```
feat(parser): support trailing commas in array literals
```

**Bug fix, no scope (touches several files in different areas):**

```
fix: resolve race condition between cache warm-up and first request

Worker pool started accepting requests before the cache pre-load
completed, causing the first ~50 requests to fall through to the
slow path. Block worker readiness on cache hydration completion.

Closes #1247
```

**Documentation only:**

```
docs: clarify SESSION_TTL_SECONDS default in deployment guide
```

**Dependency bump (no body needed):**

```
build(deps): bump @types/node from 22.5.0 to 22.5.4
```

**Revert with reference:**

```
revert: feat(auth): add session timeout with configurable TTL

This reverts commit a3f8e21. Caused intermittent logouts during long-
running uploads on tenants with TTL < 60s. Re-introducing once #1312
adds activity-based TTL extension.
```

## Anti-patterns to refuse

| Pattern | Why it's wrong |
|---|---|
| `feat: Added new feature.` | Past tense + capitalized + trailing period (3 violations) |
| `update stuff` | No type, no specificity, conveys nothing |
| `feat(auth): add session timeout and fix logout bug and update tests` | Multiple changes in one commit — split it |
| `fix: bug` | Type without summary; unparseable for changelogs |
| `[FEAT] add session timeout` | Wrong format unless the project's existing commits use this style — then match it |
| Header > 72 chars | Truncates in `git log --oneline`, GitHub PR titles, email clients |

When the diff doesn't cleanly map to a single message, the answer is to split
the commit, not to compress two stories into one summary.

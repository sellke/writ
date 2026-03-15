# Review Command (review)

## Overview

Pre-landing code review that identifies failure modes, shadow paths, and interaction edge cases — the things that break in production but look fine in a PR. Produces *judgment*, not a checklist.

`/review` goes deeper than the pipeline's Gate 3 review agent. The pipeline reviewer focuses on spec adherence and code quality within a story context. `/review` analyzes any diff for the specific ways code can fail and whether those failures are handled.

Use it independently on any code — pipeline output, external contributions, or your own work before shipping. When run before `/ship`, findings automatically flow into the PR's Review Notes section.

**How `/review` differs from the pipeline review agent:**

| | Pipeline Review (Gate 3) | Standalone `/review` |
|---|---|---|
| **Focus** | Spec adherence, code quality, drift detection | Failure modes, rescue gaps, production risk |
| **Scope** | Single story's changes | Any diff, any context |
| **Depth** | Broad — covers all review dimensions | Deep — focuses on the ways code fails |
| **Output** | PASS/FAIL with feedback for coding agent | Structured failure report with severity ratings |
| **When** | During `/implement-story` pipeline | Before `/ship`, or standalone on any code |

## Invocation

| Invocation | Behavior |
|---|---|
| `/review` | Review all changes on current branch vs default branch |
| `/review --diff main` | Review all changes vs a specific base |
| `/review --file src/auth/session.ts` | Review a specific file's changes |
| `/review --spec .writ/specs/...` | Review with spec context for plan-vs-actual comparison |

## Command Process

### Step 1: Identify Review Scope

Determine what code to analyze based on invocation.

**Default (`/review`):**
```bash
git diff origin/[default-branch]...HEAD
```

**With `--diff [base]`:**
```bash
git diff [base]...HEAD
```

**With `--file [path]`:**
```bash
git diff origin/[default-branch]...HEAD -- [path]
```

**With `--spec [path]`:**
- Load `spec-lite.md` from the spec folder for context on planned behavior
- Compare planned error handling (from spec's error mapping tables) against actual implementation
- This enables plan-vs-actual comparison using the shared error mapping format

**Print the review scope before starting:**

```
🔍 Review scope: 8 files changed (+247, -31) vs origin/main
   Focus: src/auth/ (4 files), src/api/routes/ (2 files), tests/ (2 files)
```

### Step 2: Scan the Diff

Read the full diff and build a mental model of what changed:

1. **Categorize files** — which are data flows, which are UI, which are infrastructure
2. **Identify trust boundaries** — where does user input enter? Where does data cross services?
3. **Map external dependencies** — database calls, API requests, file I/O, third-party SDKs
4. **Note what's absent** — error handling not added, tests not updated, edge cases not covered

This scan determines which review techniques to prioritize. Not every technique applies to every diff.

### Step 3: Apply Review Techniques

Apply all applicable techniques. **Prioritize depth over breadth** — deeply analyzing 3 critical paths catches more real bugs than superficially scanning 20 functions.

---

#### Technique 1: Error & Rescue Map

For every method or function in the diff that can fail, produce this table:

| Method | What Fails | Exception Class | Rescued? | Test? | User Sees |
|---|---|---|---|---|---|
| `createSession()` | DB connection lost | `ConnectionError` | Yes — retry 3x | Yes | "Try again" toast |
| `validateToken()` | Token expired | `AuthError` | Yes — redirect | Yes | Login page |
| `processPayment()` | Stripe timeout | `TimeoutError` | **No** | **No** | **Silent failure** |

**Critical gap detection — the rightmost columns are the signal:**

| Pattern | Severity | Meaning |
|---|---|---|
| `RESCUED=No` + `TEST=No` | **Critical** | Unhandled failure with no test coverage |
| `RESCUED=No` + `USER SEES=Silent` | **Critical** | User gets no feedback on failure |
| `RESCUED=Yes` + `TEST=No` | **High** | Rescue exists but isn't tested — might not work |
| `TEST=No` on any error path | **Medium** | Error path untested |

I recommend **starting with methods that handle external I/O** — database, network, file system, third-party APIs. These are where failures actually happen. Pure computation rarely fails in ways that matter.

**Table format note:** This table structure is shared with the error mapping in `/create-spec`. When `--spec` is provided, compare planned handling (from spec) against actual handling (from code) and flag discrepancies.

---

#### Technique 2: Shadow Path Tracing

For critical data flows in the diff, trace four paths through each:

| Path | Input | Expected | Actual |
|---|---|---|---|
| Happy path | Valid user, valid data | Success | ✅ Handled |
| Nil input | `null`/`undefined` | Graceful error | ⚠️ Unchecked — throws TypeError |
| Empty input | Empty string, `[]`, `{}` | Validation error | ✅ Handled |
| Upstream error | API returns 500 | Fallback/retry | ❌ Unhandled — white screen |

**Prioritize flows where data crosses trust boundaries:**
- User input → server validation
- Server → database query/write
- Server → external API call
- API response → UI render
- File upload → processing pipeline

I recommend **tracing at most 5 critical flows**. Beyond that, diminishing returns — the most dangerous shadow paths are almost always in the first 3 flows you examine.

---

#### Technique 3: Interaction Edge Cases

For user-facing features in the diff, evaluate these standard scenarios:

| Edge Case | Handled? | How |
|---|---|---|
| Double-click on submit | | |
| Navigate away during async | | |
| Stale state after tab switch | | |
| Back button after mutation | | |
| Rapid input (paste large text) | | |
| Network loss mid-operation | | |
| Concurrent edits (two tabs) | | |

Mark each as: ✅ Handled (with description), ⚠️ Partial (with gap), ❌ Unhandled.

**Add feature-specific edge cases** beyond the standard set. A payment form needs "card declined" and "duplicate charge" scenarios. A file upload needs "oversized file" and "wrong format" scenarios. Think about what's specific to *this* code.

**Skip this technique for backend-only changes.** If the diff doesn't touch UI components or user-facing endpoints, note "No user-facing interactions in scope" and move on.

---

#### Technique 4: Failure Modes Registry

Aggregate all findings from Techniques 1–3 into a single prioritized list:

| ID | Category | Severity | Description | Status |
|---|---|---|---|---|
| FM-001 | Error handling | Critical | Payment timeout — no rescue, no test, silent failure | Unresolved |
| FM-002 | Shadow path | High | Null user input in registration — throws TypeError | Unresolved |
| FM-003 | Interaction | Medium | Double-click on submit creates duplicate entries | Unresolved |
| FM-004 | Error handling | Low | Debug log missing on cache miss | Unresolved |

**Severity classification:**

| Severity | Criteria |
|---|---|
| **Critical** | Silent failure, data loss, or security exposure. No rescue and no test. |
| **High** | Failure with rescue but no test, or unhandled shadow path in critical flow. |
| **Medium** | Interaction edge case that degrades UX but causes no data loss. |
| **Low** | Minor inconsistency, non-critical path, cosmetic or logging gap. |

I recommend **addressing all Critical and High items before shipping**. Medium items are worth noting in the PR but shouldn't block merge. Low items are informational.

---

#### Technique 5: Architecture Diagram

For non-trivial flows in the diff, produce a mandatory ASCII diagram showing the data path and failure points:

```
User → [Form Submit] → API Route → [Validate] → DB Write → [Notify] → Response
                            ↓              ↓           ↓
                       AuthError      ConnError    QueueError
                       (rescued ✅)   (retry ✅)   (silent ❌ FM-001)
```

Annotate each failure point with its registry ID and rescue status. The diagram makes the failure topology visible at a glance — something tables alone can't do.

**Include a diagram when:**
- The diff touches 3+ files in a request/response chain
- There's a data flow with multiple failure points
- The relationship between components isn't obvious from file names alone

**Skip when:**
- Single-file changes with no cross-component flow
- Pure utility/helper modifications
- Test-only changes

### Step 4: Produce Report

Generate a structured markdown report. This is the primary output of `/review`.

```markdown
# Code Review: [branch-name]

> Reviewed: YYYY-MM-DD
> Scope: N files changed (+X, -Y) vs [base]
> Spec: [path if --spec provided, else "Standalone review"]

## Architecture

[ASCII diagram showing data flow and failure points]

## Error & Rescue Map

[Table from Technique 1]

## Shadow Paths

[Tables from Technique 2, one per critical flow]

## Interaction Edge Cases

[Table from Technique 3, or "No user-facing interactions in scope"]

## Failure Modes Registry

[Aggregated table from Technique 4]

**Summary:** N findings — X critical, Y high, Z medium, W low

## Recommendation

**The critical gap is [most important finding] because [concrete impact].**

[Specific recommendation for addressing it — code-level guidance, not just "fix this".]

[If additional findings warrant attention, list them with brief recommendations.]

[If no critical/high findings: "This code is ready to ship. The medium/low findings
are worth noting but don't block merge."]
```

**The Recommendation section is the soul of `/review`.** Don't bury the lead in tables — open with the single most important thing the developer needs to know, and why it matters.

### Step 5: Save Report & Integrate with /ship

1. Create `.writ/state/` directory if it doesn't exist, then save the review report to `.writ/state/review-[branch-name].md`
2. When `/ship` runs on the same branch, it checks for this file
3. If found, the Failure Modes Registry is included in the PR body's "Review Notes" section
4. Critical and High findings are highlighted in the PR description

This integration is output-based: `/review` writes a file, `/ship` reads it. No tight coupling between the commands.

## Error Handling

**No changes to review:**
```
⚠️ No changes detected on this branch vs [base].
Nothing to review.
```

**Diff too large (>2000 lines):**
```
⚠️ Large diff detected (2,847 lines across 34 files).

I recommend narrowing the review scope:
  /review --file src/auth/session.ts    (specific file)
  /review --diff HEAD~5                 (recent commits only)

Or I can proceed with a focused review of the highest-risk files
(external I/O, authentication, data mutations).

Proceed with focused review? [Enter to continue, or specify scope]
```

I recommend **focused review over comprehensive-but-shallow** for large diffs. Three deeply-analyzed critical paths are worth more than forty superficially-checked functions.

**No default branch detected:**
```
⚠️ Can't detect default branch. Specify a base:
  /review --diff main
  /review --diff develop
```

## When to Use /review vs Other Commands

| Scenario | Command |
|---|---|
| Deep failure analysis before shipping | `/review` → `/ship` |
| Full story with pipeline review + drift | `/implement-story` (Gate 3 handles this) |
| Quick prototype check | `/prototype` (has built-in lint) |
| Review with plan-vs-actual comparison | `/review --spec .writ/specs/...` |
| Post-mortem on a production incident | `/review --diff [release-tag]` |
| Review a specific file in isolation | `/review --file path/to/file.ts` |

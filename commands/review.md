# Review Command (review)

## Overview

Pre-landing code review that identifies failure modes, shadow paths, and interaction edge cases — the things that break in production but look fine in a PR. Produces *judgment*, not a checklist.

`/review` goes deeper than the pipeline's Gate 3 review agent. The pipeline reviewer focuses on spec adherence and code quality within a story context. `/review` analyzes any diff for the specific ways code can fail and whether those failures are handled.

Use it independently on any code — pipeline output, external contributions, or your own work before shipping. When run before `/ship`, findings automatically flow into the PR's Review Notes section.

## Invocation

| Invocation | Behavior |
|---|---|
| `/review` | Review all changes on current branch vs default branch |
| `/review --diff main` | Review all changes vs a specific base |
| `/review --file src/auth/session.ts` | Review a specific file's changes |
| `/review --spec .writ/specs/...` | Review with spec context for plan-vs-actual comparison |

## Command Process

### Step 1: Identify Review Scope

Determine what code to analyze based on invocation. Default: `git diff origin/[default-branch]...HEAD`. The `--diff` and `--file` flags narrow the base or path accordingly.

With `--spec`, load `spec-lite.md` from the spec folder and compare planned error handling (from spec's error mapping tables) against actual implementation using the shared error mapping format.

Print the scope before starting:

```
🔍 Review scope: 8 files changed (+247, -31) vs origin/main
   Focus: src/auth/ (4 files), src/api/routes/ (2 files), tests/ (2 files)
```

### Step 2: Scan the Diff

Read the full diff and build a mental model of what changed:

1. **Categorize files** — data flows vs UI vs infrastructure
2. **Identify trust boundaries** — where user input enters, where data crosses services
3. **Map external dependencies** — database calls, API requests, file I/O, third-party SDKs
4. **Note what's absent** — error handling not added, tests not updated, edge cases not covered

This scan determines which techniques to prioritize. Not every technique applies to every diff.

### Step 3: Apply Review Techniques

Apply all applicable techniques. **Prioritize depth over breadth** — deeply analyzing 3 critical paths catches more real bugs than superficially scanning 20 functions.

---

#### Technique 1: Error & Rescue Map

For every method in the diff that can fail:

| Method | What Fails | Exception Class | Rescued? | Test? | User Sees |
|---|---|---|---|---|---|
| `createSession()` | DB connection lost | `ConnectionError` | Yes — retry 3x | Yes | "Try again" toast |
| `validateToken()` | Token expired | `AuthError` | Yes — redirect | Yes | Login page |
| `processPayment()` | Stripe timeout | `TimeoutError` | **No** | **No** | **Silent failure** |

**The rightmost columns are the signal:**

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

For critical data flows, trace four paths through each:

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

For user-facing features, evaluate these standard scenarios:

| Edge Case | Handled? | How |
|---|---|---|
| Double-click on submit | | |
| Navigate away during async | | |
| Stale state after tab switch | | |
| Back button after mutation | | |
| Rapid input (paste large text) | | |
| Network loss mid-operation | | |
| Concurrent edits (two tabs) | | |

Mark each as: ✅ Handled, ⚠️ Partial (with gap), ❌ Unhandled.

**Add feature-specific edge cases** beyond the standard set. A payment form needs "card declined" and "duplicate charge". A file upload needs "oversized file" and "wrong format". Think about what's specific to *this* code.

**Skip this technique for backend-only changes.**

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

For non-trivial flows, produce an ASCII diagram showing the data path and failure points:

```
User → [Form Submit] → API Route → [Validate] → DB Write → [Notify] → Response
                            ↓              ↓           ↓
                       AuthError      ConnError    QueueError
                       (rescued ✅)   (retry ✅)   (silent ❌ FM-001)
```

Annotate each failure point with its registry ID and rescue status. The diagram makes the failure topology visible at a glance — something tables alone can't do.

**Include when** the diff touches 3+ files in a chain, has multiple failure points, or the component relationship isn't obvious. **Skip for** single-file changes, pure utility modifications, or test-only changes.

### Step 4: Produce Report

Generate a structured markdown report:

```markdown
# Code Review: [branch-name]

> Reviewed: YYYY-MM-DD
> Scope: N files changed (+X, -Y) vs [base]
> Spec: [path if --spec provided, else "Standalone review"]

## Architecture
[ASCII diagram from Technique 5]

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
[Code-level guidance for addressing it, not just "fix this".]
```

**The Recommendation section is the soul of `/review`.** Don't bury the lead in tables — open with the single most important thing the developer needs to know, and why it matters. If no critical/high findings: state the code is ready to ship.

### Step 5: Integration with /ship

Save the report to `.writ/state/review-[branch-name].md` (create `.writ/state/` if needed). When `/ship` runs on the same branch, it reads this file and includes the Failure Modes Registry in the PR body's Review Notes section, highlighting Critical and High findings.

This integration is output-based: `/review` writes a file, `/ship` reads it. No tight coupling.

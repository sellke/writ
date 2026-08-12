# Exit Criteria Classification

> Parent spec: [`2026-08-12-machine-evaluable-exit-criteria`](../specs/2026-08-12-machine-evaluable-exit-criteria/spec.md)
> Produced by: Story 1 (`user-stories/story-1-criterion-classification.md`)
> Consumed by: Story 3, which implements `scripts/exit-criteria.py` against exactly this classification — no criterion here, no predicate there.

## Purpose

`commands/implement-phase.md`, `commands/implement-spec.md`, and
`commands/implement-story.md` declare 10 `exit_criteria` between them. This
document sorts each of the 10 into exactly one of three buckets and records the
evidence for the call:

- **evaluable-now** — a predicate can read existing disk/git state today and
  answer met/unmet with no new instrumentation.
- **needs-run-record** — the evidence is temporal (before/after, "ran," "during
  this run") and cannot be recovered from a post-hoc read; it requires one of
  the additive fields Story 2 adds while the command executes.
- **structurally-unobservable** — no field, however written, closes the gap. The
  criterion is temporal in a way no timestamp fixes, before/after in a way no
  ordering check fixes, report-only, or an interaction outcome. These return
  `unknown` with the exact reason string recorded below (Business Rule 2, and
  the Rollup rule that `unknown` is legal only for a criterion classified here).

Criterion identifiers (`implement-phase.c1` ... `implement-story.c3`) are
numbered in frontmatter order within each file, per the Story 1 notes. They are
stable — Story 3's checker uses these exact strings as JSON `id` values, and an
id absent from this document is `impossible`, not `unknown` (technical-spec.md
§ Rollup).

`/implement-story` is out of scope for the checker (`spec.md` § Excluded —
`/implement-story`). Its three criteria are classified below as `Scope:
excluded` rather than omitted, per Acceptance Criterion 3.

## Bucket Table

| Criterion ID | Command | Bucket | One-line reason |
|---|---|---|---|
| `implement-phase.c1` | implement-phase | evaluable-now | Spec statuses and quarantine-branch reachability are both readable today from phase state + git |
| `implement-phase.c2` | implement-phase | evaluable-now (split: presence + ordering) | Presence is a direct file read; ordering ("generated after") is recoverable via git log timestamp comparison, not a temporal gap |
| `implement-phase.c3` | implement-phase | needs-run-record | "Recorded pass or fail" only exists once `/implement-phase` writes `exitCriteria[]` — nothing to read before that |
| `implement-phase.c4` | implement-phase | structurally-unobservable (report-only) | The report's terminal line is transcript content, not a structured field; asserting one of three closed strings appeared is judging prose, not state |
| `implement-spec.c1` | implement-spec | needs-run-record | The claim is "before the first story ran" — a before/after clause a post-hoc read cannot recover without a timestamped record |
| `implement-spec.c2` | implement-spec | evaluable-now | Per-story terminal status (complete/skipped+chain/failed+reason) is already written to `execution-<ts>.json` by current instrumentation |
| `implement-spec.c3` | implement-spec | needs-run-record | The claim is "ran after the final story" — the same before/after gap as c1, closed by a `postRun` record instead of a `preflight` one |
| `implement-story.c1` | implement-story | Scope: excluded | Already disk-checkable from the story header; no unattended loop to gate |
| `implement-story.c2` | implement-story | Scope: excluded | Already disk-checkable from the story footer + README; no unattended loop to gate |
| `implement-story.c3` | implement-story | Scope: excluded | Reads a best-effort record whose authoring rule forbids blocking on it; also innermost loop, self-terminating |

Bucket counts: **evaluable-now: 3** (`implement-phase.c1`, `implement-phase.c2`,
`implement-spec.c2`) · **needs-run-record: 3** (`implement-phase.c3`,
`implement-spec.c1`, `implement-spec.c3`) · **structurally-unobservable: 1**
(`implement-phase.c4`) · **excluded: 3** (`implement-story.c1`–`c3`).

---

## `implement-phase.c1`

> "every spec resolved from the phase reached merged, quarantined,
> skipped_blocked, or closed_not_implemented in
> .writ/state/phase-execution-*.json, and failed work exists only on
> writ/quarantine/<spec-id> branches"

**Bucket:** evaluable-now

**Evidence:** Both halves of this criterion are readable today, from artifacts
that already exist without any new field.

- *Spec status coverage* — `scripts/phase-state.py` `cmd_progress` already
  returns a dict of per-spec status (merged / quarantined / skipped_blocked /
  closed_not_implemented) read straight from `.writ/state/phase-execution-*.json`.
  The predicate confirms every spec resolved from the phase appears in that dict
  with one of the four terminal statuses — no spec left in an in-progress or
  unrecorded state. This is the technical-spec.md CLI worked example's evidence
  string almost verbatim: `"5/5 specs terminal; 0 quarantine branches reachable
  from phase branch"`.
- *Quarantine confinement* — `scripts/phase-state.py reconcile` already detects
  state/git mismatches (an `impossible` trigger in its own right per
  technical-spec.md § Rollup). The same git read confirms any non-merged spec's
  work is reachable only from a `writ/quarantine/<spec-id>` branch and not from
  the phase branch itself — a `git branch --contains` / reachability check, not
  a new capability.

**Do not:** re-read the state file directly or reimplement quarantine-branch
discovery — both are exactly what `cmd_progress` and `reconcile` already do
(technical-spec.md § Reuse).

---

## `implement-phase.c2`

> "each merged spec folder contains a populated uat-plan.md generated after
> that spec was implemented"

**Bucket:** evaluable-now (recorded as a **split** entry — the two halves need
different evidence and neither should be rounded away)

This criterion bundles a presence check with an ordering claim. Both resolve to
evaluable-now, but by different mechanisms, so both are recorded rather than
letting the presence half stand in for the whole criterion (Story 1 Notes §
Risks: "a predicate that checks 60% of a criterion and reports met is worse than
one that reports unknown").

**Evidence — presence half:** `scripts/spec-status.py` `scan` (or `is-complete`)
already identifies which spec folders under `.writ/specs/` are merged/complete,
giving the set to check. For each, a direct read of `uat-plan.md` confirms it
exists and is populated rather than a heading-only stub — the same
stub-vs-populated distinction technical-spec.md's Error & Rescue Map already
uses for this exact file ("uat-plan.md present but a stub → unmet naming the
spec — a stub is not a populated plan").

**Evidence — ordering half ("generated after that spec was implemented"):** this
is a before/after claim, but unlike the structurally-unobservable criteria below,
git already carries the ordering evidence — no run-record field is needed. The
mechanism: compare the timestamp of the commit that first added
`<spec>/uat-plan.md` (`git log --follow --format=%ai --diff-filter=A -- <spec
folder>/uat-plan.md`, earliest entry) against the timestamp of the spec's
implementation-completion commit (the last story's recorded `> **Commit:**` SHA,
resolved via `git log -1 --format=%ai <sha>`, or the spec folder's merge commit
onto the phase branch). If the plan's first-add timestamp is later, the ordering
half is met; if the plan predates completion, it is unmet, naming the spec.

**Do not:** treat the ordering half as structurally-unobservable by analogy to
`implement-phase.c4` — the report-only reasoning there doesn't apply here
because git-log timestamps are structured, machine-readable state, not
transcript prose.

---

## `implement-phase.c3`

> "each machine-checkable roadmap exit criterion is recorded pass or fail with
> its evidence, and human-judgment criteria are handed off rather than
> self-certified"

**Bucket:** needs-run-record

**Evidence:** There is nothing on disk today that records a roadmap criterion's
verdict — that record only exists once `/implement-phase` Step 4.1 writes it
per criterion verified. A post-hoc read before that field exists finds nothing
to check, which is exactly the needs-run-record signature: not "false," but
"not yet evidenced."

**Field:** `exitCriteria[]` — specifically each entry's `.class` (`machine` or
`human`) and `.verdict` (`pass`, `fail`, `unachievable`, or `handed_off`). A
`machine`-class entry must resolve to `pass`/`fail`/`unachievable` with
`.evidence` populated; a `human`-class entry must resolve to `handed_off` rather
than `pass`/`fail` — that distinction is the literal text of "handed off rather
than self-certified."

**File:** `.writ/state/phase-execution-*.json` (`phase-execution-v2` schema,
`schemaVersion` unchanged at `2` — additive field, Business Rule 2).

---

## `implement-phase.c4`

> "the phase report ends in exactly one of COMPLETE, IMPLEMENTED pending human
> validation, or PARTIALLY COMPLETE"

**Bucket:** structurally-unobservable — **report-only**

**Reason (verbatim, returned by the checker as `unknown`'s `reason`):**

> `declared unobservable: report is transcript-only`

**Evidence for the classification:** The phase completion report is prose
handed to a human at Phase 4 — it is not written to a structured field the
checker can parse without re-parsing free text (which technical-spec.md's Error
& Rescue Map explicitly rules out as an evaluation strategy elsewhere: a
predicate judges state, not transcripts). This is confirmed by both worked
examples already in the contract: `spec.md` § Verdict Contract and
technical-spec.md § CLI Surface each show this exact criterion (`id`
`implement-phase.c4` / positional `id: 4`) returning
`{"verdict": "unknown", "reason": "declared unobservable: report is
transcript-only"}`. Per the Gate 0 architecture review, this stays
report-only rather than being reclassified against `terminalStatus`: that field
exists to support the `impossible`-trigger and rollup logic (a run that hit its
loop bound writes `haltReported`, not `terminalStatus` — the two are mutually
exclusive per technical-spec.md § Data Contracts), not to make c4 itself
evaluable. Nothing forces the report's prose to be byte-identical to whatever
`terminalStatus` holds, so reading the field would be asserting a synchronization
the criterion doesn't actually require.

---

## `implement-spec.c1`

> "scripts/story-deps.py validate returned status ok for the full story graph
> before the first story ran"

**Bucket:** needs-run-record

**Evidence:** The temporal clause — "before the first story ran" — is the gap.
`story-deps.py validate_graph` can be re-run against the current story graph at
any time, but doing so at check-time only proves the graph is valid *now*, not
that it was validated *before dispatch began* for *this* run. Re-running the
validator would silently substitute a different (weaker) claim for the one the
criterion actually makes. Per technical-spec.md § Reuse, the checker must not
reimplement cycle detection — it reads what was already recorded, not what it
can recompute.

**Field:** `preflight.storyDepsValidated` (the recorded outcome of
`story-deps.py validate_graph`) and `preflight.at` (the timestamp proving it ran
before batch 1).

**File:** `.writ/state/execution-<timestamp>.json`, written by `/implement-spec`
"after the story-graph pre-flight, before batch 1" (technical-spec.md § Data
Contracts).

---

## `implement-spec.c2`

> "no story remains pending in .writ/state/execution-<timestamp>.json - each is
> complete, skipped with its blocking chain, or failed with a reason"

**Bucket:** evaluable-now

**Evidence:** Unlike c1 and c3, this criterion names its own evidence file
directly and asks only about the current state of records that `/implement-spec`
already writes as part of its existing per-story tracking — no new Story 2 field
is required. A direct read of `.writ/state/execution-<timestamp>.json` confirms
every story entry carries a terminal per-story status (`complete`, `skipped`
with a `blockedBy` chain, or `failed` with a `reason`) and none is left
`pending`. This matches technical-spec.md's Shadow Paths row for the spec check:
`"met, exit 0, story counts in evidence"` and its empty-input caveat — "zero
stories in the batch plan → unmet ('no spec resolved')" — a vacuous pass must be
avoided the same way.

---

## `implement-spec.c3`

> "one typecheck plus full test suite ran after the final story, separate from
> the targeted per-story Gate 4 runs, and .writ/context.md was rewritten to the
> post-run story counts"

**Bucket:** needs-run-record

**Evidence:** Same before/after shape as c1, mirrored at the other end of the
run: "ran after the final story" cannot be distinguished, post-hoc, from a
typecheck/test run that happened at some other point (e.g., one of the per-story
Gate 4 runs) unless the run itself records that it happened at this specific
moment. `.writ/context.md`'s rewritten story counts are likewise a point-in-time
claim, not a standing invariant a filesystem read can date on its own.

**Field:** `postRun.typecheck`, `postRun.testSuite`, `postRun.contextRewritten`,
and `postRun.at`.

**File:** `.writ/state/execution-<timestamp>.json`, written by `/implement-spec`
"after the final story's batch" (technical-spec.md § Data Contracts).

---

## `implement-story.c1`

> "the story file header reads Status: Completed and carries a > **Commit:**
> line holding the full SHA of the completion commit, written once rather than
> duplicated on re-runs"

**Scope: excluded**

**Reasons (from `spec.md` § Excluded — `/implement-story`):**

1. **Already disk-checkable.** This criterion is fully readable from the story
   file's own header today — `Status:` and `> **Commit:**` are plain frontmatter
   text, and duplication-on-re-run is a direct string check. A stop-time gate
   adds nothing this doesn't already assert without one.
2. **Self-terminating.** `/implement-story`'s review loop already bounds itself
   at 3 cycles with `on_exhaustion: escalate` — it does not run unattended past
   a point nothing is watching.
3. **Innermost-loop / single-slot conflict.** Under `/goal`'s single-slot
   behavior (spec.md § What `/goal` showed), only the outermost active command
   may hold a goal; `/implement-story` is the innermost of the three and must
   never hold one regardless of what this spec builds.

---

## `implement-story.c2`

> "the story file ends with a ## What Was Built section naming files created,
> files modified, and test results, and user-stories/README.md progress counts
> match it"

**Scope: excluded**

**Reasons (from `spec.md` § Excluded — `/implement-story`):**

1. **Already disk-checkable.** Both halves — the `## What Was Built` section's
   presence/contents and `user-stories/README.md`'s progress counts matching it
   — are readable from disk today with no run-record needed; a gate over
   already-checkable state adds nothing.
2. **Self-terminating.** Same 3-cycle, `on_exhaustion: escalate` bound as c1 —
   there is no unattended stretch for a stop-time gate to guard.
3. **Innermost-loop / single-slot conflict.** Same as c1 — `/implement-story`
   can never hold a `/goal` regardless.

---

## `implement-story.c3`

> "Gate 4 recorded a 100 percent test pass rate with at least 80 percent line
> coverage on new files, and no gate was skipped without the story being marked
> DEGRADED instead of Completed"

**Scope: excluded**

**Reasons (from `spec.md` § Excluded — `/implement-story`):**

1. **Best-effort record, governing rule forbids gating on it.** This criterion's
   figures are read from the `## What Was Built` section, whose authoring skill
   declares as its **single governing rule**: "never block completion on
   incomplete data. Partial records are better than no records," with an
   explicit `**Verification:** N/A` fallback when a figure can't be produced. A
   stop-time gate reading that record and blocking on it would invert the rule
   the record was written under — the record is allowed to be incomplete by
   design, so a gate demanding completeness contradicts its own source.
2. **Self-terminating.** Same 3-cycle, `on_exhaustion: escalate` bound as c1/c2.
3. **Innermost-loop / single-slot conflict.** Same as c1/c2 — `/implement-story`
   can never hold a `/goal` regardless of what this spec builds.

---

## Cross-Check Against Story 2's Field List

Story 2 adds exactly these fields (technical-spec.md § Data Contracts):

| Field | File | Closes |
|---|---|---|
| `exitCriteria[]` (`.id`/`.source`/`.class`/`.verdict`/`.evidence`) | `.writ/state/phase-execution-*.json` | `implement-phase.c3` |
| `terminalStatus` | `.writ/state/phase-execution-*.json` | Rollup/`impossible`-trigger support — not a criterion directly (see `implement-phase.c4` entry above) |
| `haltReported` | `.writ/state/phase-execution-*.json` | `impossible`-trigger ("Loop bound tripped") — not a criterion directly |
| `preflight.storyDepsValidated` / `.at` | `.writ/state/execution-<timestamp>.json` | `implement-spec.c1` |
| `postRun.typecheck` / `.testSuite` / `.contextRewritten` / `.at` | `.writ/state/execution-<timestamp>.json` | `implement-spec.c3` |

Every field Story 2 adds is accounted for — either mapped to exactly one
needs-run-record entry above (`implement-phase.c3`, `implement-spec.c1`,
`implement-spec.c3`), or explicitly scoped to rollup/`impossible`-trigger
support rather than to a criterion directly. No gap in either direction (Task
1.6). `terminalStatus` and `haltReported` exist to support the
rollup and `impossible`-trigger machinery described in `spec.md` § Rollup rules
and technical-spec.md § `impossible` triggers, not to directly evidence any of
the 10 criteria — `implement-phase.c4` in particular stays
structurally-unobservable rather than being read against `terminalStatus` (see
that entry's evidence above).

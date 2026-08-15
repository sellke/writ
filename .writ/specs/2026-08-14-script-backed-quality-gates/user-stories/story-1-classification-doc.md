# Story 1: The Quality-Signal Classification Doc

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** None

## User Story

**As an** implementer about to write three checkers that must agree with each other
**I want** one document defining every finding code, its severity, and the rule for when a
check may say "I could not tell"
**So that** three scripts written in three stories decide the same way, and a disagreement
between a checker and the doc is resolvable by reading which one is wrong rather than by
arguing

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given the thirteen finding codes in `sub-specs/technical-spec.md`, when the doc is read, then each carries a code, an owning checker, a severity of `blocking` or `informational`, the precise condition that fires it, and at least one worked example of a real config or file shape that triggers it. `[AC-1.1]`
- [x] Given a checker that cannot compute an answer, when the doc's verdict rules are applied, then `unverifiable` is defined as a distinct outcome from both `pass` and `fail`, is reachable only through an enumerated list of causes, and is explicitly stated never to exit 2 — exit 2 belonging to the checker being unable to operate at all. `[AC-1.2]`
- [x] Given a config file the stdlib cannot parse, when the doc's `could_not_parse` rule is applied, then the rule states that every finding that file would have decided becomes `unverifiable` rather than absent, and names `next.config.js`, `jest.config.js` and `tsconfig.json` as the known cases with the heuristic each requires. `[AC-1.3]`
- [x] Given a stack with no handler, when the doc's support matrix is read, then Node/TypeScript is recorded first-class, Python best-effort, and every other stack `unsupported_stack`, with the evidence basis for that ordering stated rather than assumed. `[AC-1.4]`
- [x] Given a brownfield project adopting these checks, when the doc's baseline rules are read, then the format of `.writ/quality-baseline.md`, the requirement that each entry carry a date and a rationale, and the prohibition on automatic re-baselining are all specified precisely enough that Stories 2 and 6 implement against the doc rather than inventing. `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write `.writ/docs/quality-signal-classification.md` following the shape of `.writ/docs/acceptance-criteria-ids.md` — Purpose, then the normative sections, then a Legacy/Adoption posture section `[AC-1.1]`
- [x] 1.2 Specify the finding table: thirteen codes, owning checker, severity, firing condition, worked example `[AC-1.1]`
- [x] 1.3 Specify the verdict rules — the `pass`/`fail`/`unverifiable` trichotomy, its mapping onto `/status`'s existing `Healthy`/`Warning`/`Attention` vocabulary, the exit-code ladder, and the rule that `unverifiable` never exits 2 `[AC-1.2]`
- [x] 1.4 Specify the parse-failure rule and the three known-unparseable file shapes, including what a bounded regex heuristic may and may not conclude from a non-match `[AC-1.3]`
- [x] 1.5 Specify the stack-support matrix, citing the evidence basis: every finding in the parent spec derives from one Node/TypeScript project `[AC-1.4]`
- [x] 1.6 Specify the `.writ/quality-baseline.md` format, waiver syntax, dated-rationale requirement, and the no-auto-re-baseline prohibition `[AC-1.5]`
- [x] 1.7 Cross-check the doc against `sub-specs/technical-spec.md` and reconcile any divergence in the doc's favor, since Stories 2–4 implement against this file `[AC-1.1, AC-1.2, AC-1.3]`

## Notes

**Technical considerations:** This file lands in `.writ/docs/`, which
`append_manifest_writ_docs` globs with no registry — it ships to every target project
automatically and needs no `.writ/manifest.yaml` edit. That also means it is user-facing
documentation in every installed project, not an internal note, and should read that way.

The precedent is exact and worth following closely: `.writ/docs/acceptance-criteria-ids.md`
is the specification `scripts/ac-trace.py` implements against, and
`.writ/docs/exit-criteria-classification.md` plays the same role for
`scripts/exit-criteria.py`. Both are parsed at runtime by their checker, and both treat an
unregistered entry as a hard error rather than a silent pass. Decide deliberately whether
this doc is *parsed* by the three checkers (the `exit-criteria.py` model, which makes drift
impossible) or merely *bound* to them by `require_literal` in `scripts/eval.sh` (the
`ac-trace.py` model, which is simpler). Record the choice and its reason.

**Risks:** The failure mode for a document like this is being written after the code and
describing it, rather than before and constraining it. If Stories 2–4 discover the doc is
wrong, the doc is fixed first and the code follows — that ordering is what keeps it
authoritative rather than decorative.

Second risk: over-specifying severities before any of them have fired against a real project.
Where the correct severity is genuinely unknown, say so in the doc and let Stories 2–4's
yuss-fixture runs settle it, rather than inventing a confident answer that later gets quietly
contradicted.

**Integration:** Story 2, 3 and 4's `require_literal` bindings in `scripts/eval.sh` assert
every finding code against *both* the checker and this doc — the pattern
`check_ac_trace` uses for its seven codes. A code renamed here without being renamed there
fails eval, which is the intended coupling.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing (n/a — documentation story; the binding tests land with Stories 2–4)
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** the verdict trichotomy, "unparseable is not absent", "0 findings and 0
  things inspected must not read the same", baseline-then-ratchet, no permanent-warning
  instruments — from `spec.md` → `## 📋 Business Rules`
- **Finding vocabulary:** the thirteen-row table — from `sub-specs/technical-spec.md` →
  `## Finding Vocabulary`
- **Precedent to mirror:** `.writ/docs/acceptance-criteria-ids.md` (grammar-as-specification,
  legacy posture section), `.writ/docs/exit-criteria-classification.md` (bucket table parsed
  at runtime, unregistered id → `impossible`)

---

## What Was Built

**Implementation Date:** 2026-08-14

### Files Created

1. **`.writ/docs/quality-signal-classification.md`** (468 lines)
   - The specification Stories 2–4 implement against: finding vocabulary,
     verdict rules, parse-failure rule, stack matrix, baseline format
   - Ships to every target project automatically via
     `append_manifest_writ_docs`'s `.writ/docs/*.md` glob — no manifest edit needed

### Files Modified

None. The doc is a new artifact with no wiring of its own; `scripts/eval.sh`
bindings land with Stories 2–4, which is the coupling Story 1's Integration note
specifies.

### Implementation Decisions

1. **Bound, not parsed** — Task 1.1's note asked for a deliberate choice between the
   `exit-criteria.py` model (doc parsed at runtime, drift impossible) and the
   `ac-trace.py` model (doc bound by `require_literal` in `scripts/eval.sh`). Chose
   **bound**. The finding vocabulary is a fixed, small, code-shaped table — thirteen
   codes, two severities — not an open registry that grows per spec. Parsing it would
   add a runtime failure mode to instruments whose whole value is that they still work
   in a degraded project, and would buy nothing a `require_literal` pair does not
   already buy. Recorded in the doc's own *How this document binds to the checkers*
   section so the reasoning survives the decision.
2. **`unverifiable` reasons are a closed enumeration** — AC-1.2 requires `unverifiable`
   be reachable only through an enumerated list of causes. Eight reasons are registered
   (`could_not_parse`, `unsupported_stack`, `no_coverage_report`,
   `unknown_report_format`, `truncated_report`, `environment`, `timeout`,
   `nothing_inspected`), with the doc stating that an implementer finding a genuine
   ninth cause adds it here first and the checker second.
3. **Severity left explicitly unsettled where it is genuinely unknown** — Story 1's
   second recorded risk is over-specifying severities before any have fired. Twelve of
   thirteen codes have a firing condition observed against real code.
   `coverage_regression` does not: it needs two runs with a stored baseline between
   them. The doc records that gap in place, with the correct response if first contact
   shows it misfiring (narrow the condition, never downgrade to informational — which
   would create the permanent-warning instrument the same doc forbids).
4. **No third severity** — `blocking` and `informational` only. The doc states the
   reason inline rather than leaving it to the parent spec: Writ has already run the
   permanent-warning experiment, and a finding nobody must act on is a finding nobody
   reads.

### Test Results

**Verification:** Automated (static) — documentation story; the `require_literal`
binding tests land with Stories 2–4 per the Definition of Done.

- ✅ `bash scripts/eval.sh --check=broken-refs` passes — all five cross-references
  resolve (`acceptance-criteria-ids.md`, `exit-criteria-classification.md`,
  `adr-006-non-degrading-destination.md`, the parent spec, `technical-spec.md`)
- ✅ `bash scripts/eval.sh --check=length` passes
- ✅ Thirteen finding codes present, each with owning checker, severity, firing
  condition, and a worked example drawn from real code `[AC-1.1]`
- ✅ Exit-code ladder and the "`unverifiable` never exits 2" rule stated `[AC-1.2]`
- ✅ Three known-unparseable shapes named with their required heuristic `[AC-1.3]`
- ✅ Stack matrix with the evidence basis stated rather than assumed `[AC-1.4]`
- ✅ Baseline format, entry grammar, and the no-auto-re-baseline prohibition `[AC-1.5]`

**Coverage:** N/A — no executable code in this story.

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration
- **Drift:** Small — one reconciliation, recorded below
- **Security:** Clean — documentation only, no executable surface
- **Boundary Compliance:** The file lands in `.writ/docs/`, the development-workspace
  half of the `CLAUDE.md` split, but is shipped product by virtue of the glob. It is
  written as user-facing documentation for every installed project rather than as an
  internal note, per Story 1's Technical considerations.

### Deviations from Spec

- **[DEV-001] `tests_excluded_from_typecheck` widened to cover the linter** — Severity: Small
  - Spec said: `sub-specs/technical-spec.md`'s Finding Vocabulary row reads "the
    typechecker's include/exclude omits the test tree"
  - Reality: the doc defines it as "the typechecker's **or linter's** include/exclude
    omits the test tree"
  - Resolution: reconciled in the doc's favor, per task 1.7's explicit instruction. The
    narrow wording contradicts AC-2.4, which requires a `lint` script excluding the test
    tree to report this code, and the yuss evidence in the parent spec's Evidence Base
    §3 is a `lint` script exclusion, not a `tsconfig.json` one. The technical spec's row
    would have made AC-2.4 unimplementable as written.
  - Spec amendment: none required — the doc is authoritative by construction and says so;
    Stories 2–4 implement against the doc.

### Lessons Learned

1. **The doc had to be written before the code to be worth writing at all** — Story 1's
   first recorded risk is a classification doc written after the implementation and
   describing it. Writing it first surfaced DEV-001 as a genuine contradiction between
   two spec artifacts rather than as a post-hoc rationalization of whatever Story 2
   happened to implement.
2. **A closed enumeration of failure reasons is the cheap half of the hardest
   constraint** — the spec's stated hardest constraint is telling a code defect from an
   environment defect. Half of that is judgement in Story 4's classifier; the other half
   is simply refusing to let a checker invent a reason string, which costs one table.

### Next Story

**Stories 2, 3, 4:** the three checkers, implementable in parallel against this
vocabulary — `quality-config-audit.py`, `test-integrity.py`, `build-smoke.py`.

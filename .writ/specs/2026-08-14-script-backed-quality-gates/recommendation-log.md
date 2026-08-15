# Authoring Decisions — Script-Backed Quality Gates

> Created: 2026-08-14
> Why this file exists: `/create-spec` was invoked in its normal (non-`--recommend`) branch,
> where the contract lock at Step 1.4b is a human gate. The session was non-interactive, so
> the lock could not be taken. Rather than stall, the contract was auto-adopted from the
> evidence the invocation named and every material decision recorded here, following the
> `--recommend` branch's accountability floor ([ADR-013](../../decision-records/adr-013-recommended-autonomous-delivery.md)).
> **The contract is not locked.** It is proposed. Use `/edit-spec` to change it, or delete the
> folder if the direction is wrong.

## Decisions

### 1. Scope taken verbatim from the invocation

**Decision:** Spec recommendations 1–4 of
`.writ/research/2026-08-14-writ-dogfooding-quality-assessment-research.md`, excluding 5–8.
**Evidence:** the invocation named exactly that range.
**Alternatives:** including recommendation 5 (foundational data-model review at contract
time) — it is the one that would have caught yuss's `Float` money columns, and it is
adjacent. Rejected: it belongs to `/create-spec`, not to the gate pipeline, and mixing a
spec-authoring change into a gate-hardening spec blurs both.
**Risk / reversibility:** low; a later spec can pick up 5–8.

### 2. No new gate number

**Decision:** extend Gate 2 and Gate 4 in place rather than inserting Gate 2.6 / Gate 4.6.
**Evidence:** gate numbers are free-text with no registry, pinned by literal at
`scripts/eval.sh:2232–2236`, mirrored in `scripts/eval-leanness.py:257`,
`skills/subagent-result-completeness/SKILL.md:41–45`, and an ASCII diagram at
`agents/visual-qa-agent.md:149`. Extending costs a table cell and a `--quick` line.
**Alternatives:** a new gate reads more cleanly in the pipeline table. Rejected on blast
radius, and because these are not new stages — they are the missing halves of two existing
ones.
**Risk / reversibility:** low; a gate could be split out later if the block grows unwieldy.

### 3. Gate 4.5 left conditional on mockups

**Decision:** drop the research's recommendation to make Gate 4.5's launch step
unconditional.
**Evidence:** once Gate 2 boots the framework on every story, the DEV-004 class of defect is
caught earlier and more cheaply than a screenshot pass catches it.
**Alternatives:** doing both. Rejected as redundant cost.
**Risk / reversibility:** low, and it shrinks the spec.

### 4. TDD-order verification excluded

**Decision:** implement test *authenticity*; leave test *order* an instruction.
**Evidence:** yuss's mature-era convention is one commit per story with tests and code
together, so a commit-ordering check would fail every story and be disabled.
**Alternatives:** requiring a red-state artifact from the coding agent. Rejected — it is a
self-report, which is the category of guarantee this spec exists to stop trusting.
**Risk / reversibility:** the gap stays open and is now labeled rather than implied.

### 5. Six stories rather than four

**Decision:** split the four recommendations into a classification doc, three checkers, and
two wiring stories.
**Evidence:** the repo's own precedent — `2026-08-13-acceptance-criteria-traceability-ids`
put the grammar doc in Story 1 and the checker in Story 2 for the same reason.
**Alternatives:** four stories mapping 1:1 onto the recommendations. Rejected: the wiring
touches command files that two checkers share, and merging doc-with-checker would let the
vocabulary drift.
**Risk / reversibility:** six stories is at the upper end for one spec; `/assess-spec` is
named in the spec and the README with the decomposition seam recorded.

### 6. Story files written directly rather than by parallel subagents

**Decision:** Step 2.6's parallel `user-story-generator` fan-out was not used.
**Evidence:** the integration detail these stories depend on — exact line numbers, the five
pinned eval literals, the JSONC/executable-JS constraint, the three-way measurement
disagreement — was gathered in this session and would have had to be re-derived per agent.
**Alternatives:** the standard fan-out. Rejected on fidelity, not cost.
**Risk / reversibility:** none to the artifact; noted because it is a documented deviation
from the command.

### 7. Visual references resolved to `none`

**Decision:** no mockups; `mockups/` created empty.
**Evidence:** the spec has no user-facing UI — three CLI scripts and four markdown files.

## Corrections Made While Authoring

Two claims in the source research were checked and found wrong during authoring. Both are
corrected in the spec's Evidence Base and should be corrected in the research document:

1. **"Six unit test files import no source code at all."** The rigorous count is **four**.
   `components/__tests__/CompactActionBar.test.tsx:15` and
   `components/__tests__/EventSelector.test.tsx:13` both import their components. The
   research over-counted by 50% using the same class of heuristic this spec exists to
   replace — which is now recorded in the spec as evidence for why the checker must parse
   rather than pattern-match.
2. **The naive line-oriented regex flags 22 of 147 files** — an 82% false-positive rate,
   measured during authoring. This became the pinned fixture behind `AC-3.2`.

## Validation Run

| Check | Result |
|---|---|
| `ac-trace.py check --spec <this folder>` | **0 findings originating in this spec** (2 self-inflicted defects found and fixed — see below) |
| `spec-deps.py validate` | `ok` |
| `story-deps.py validate` | `ok` — batches `[[1], [2,3,4], [5,6]]`, matching the designed graph |
| `spec-status.py validate` | `ok` |
| `eval.sh --check=ac-trace` / `spec-status` / `spec-vocabulary` | exit 0 |
| `spec-lite.md` | 93 lines, under the 100-line blocking limit |

**The checker caught two defects in this spec while it was being authored.** Story 5's tasks
5.1 and 5.7 tagged criteria as `` `[AC-5.2], [AC-5.5]` `` — two separate bracket groups —
which leaves the first group un-anchored and therefore invisible as a citation, so AC-5.2 and
AC-5.5 both reported `untasked_criterion`. Fixed to a single comma-separated tag,
`` `[AC-5.2, AC-5.5]` ``. Worth recording because it is the mechanism this whole spec argues
for, catching its own author within minutes of the spec being written.

### A pre-existing framework finding this surfaced

Seven `dangling_reference` findings remain, none from this spec folder: `AC-3.6`, `AC-3.7`,
`AC-3.9`, `AC-9.9` in `scripts/tests/test_ac_trace.py` and `AC-7.1`–`AC-7.3` in
`scripts/tests/test_edit_spec_ac_stability_fixtures.py`. These are literal fixture strings
inside test files that collide with the live ID space of whatever spec is being checked.

This is the known issue recorded as DEV-4 in
`2026-08-13-acceptance-criteria-traceability-ids`, whose own note called it a "minor,
non-blocking follow-up". The observation worth adding: **it is not a one-time cost, it is a
per-spec tax.** Any future spec with a Story 3 inherits the `AC-3.x` collisions; any spec
reaching Story 7 or 9 inherits the rest. A blocking check that reports seven false findings on
every clean spec is the exact instrument-dismissal pattern the parent research names as
Finding 7 — the governor that warns permanently until people stop reading it. Renumbering the
fixture IDs out of any plausible live range (say `AC-900.x`) is a small change and would keep
`ac-trace` honest. Worth a `/create-issue`.

## Open Questions for the Owner

- **Story 4 (`build-smoke`) is the one to scrutinize.** It is the only executing check and
  the only one whose correctness rests on classifying failures it did not cause. `AC-4.5`
  licenses closing it `Closed — Not Implemented` on measured evidence. If you would rather
  not spend the attempt at all, cutting it before implementation is cheaper than cutting it
  after — and Story 5's Gate 2 half drops with it cleanly.
- **Does the classification doc get parsed at runtime** (the `exit-criteria.py` model, drift
  impossible) **or only bound by `require_literal`** (the `ac-trace.py` model, simpler)?
  Story 1 task 1.1 leaves this to the implementer with instructions to record the reason;
  it is a legitimate owner call to make now instead.
- **An ADR may be warranted.** "Mechanical enforcement over prompt-level instruction" is a
  convention-setting principle that would govern future gate design, which is ADR territory
  rather than spec territory. Not written — flagged.

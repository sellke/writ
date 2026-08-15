# Per-Criterion Traceability IDs and an Orphan Check

> **Status:** Complete
> **Created:** 2026-08-13
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Origin:** Promoted from issue: [.writ/issues/improvements/2026-08-13-acceptance-criteria-traceability-ids.md](../../issues/improvements/2026-08-13-acceptance-criteria-traceability-ids.md)

## Specification Contract

**Deliverable:** Every acceptance criterion gets a stable, never-renumbered ID, tasks and
tests cite the IDs they satisfy, and `/verify-spec` reports orphans in both directions as
blocking completion-integrity failures.

**Must Include:** The bidirectional check. A one-way "does every criterion have a task?"
scan is the half a diligent author already does by hand; the dangling-reference direction
is what catches a criterion deleted out from under a test that still claims to prove it.

**Hardest Constraint:** ID stability under `/edit-spec`. Every citation is a hardcoded
string in a task line or a test name, so a single renumber rots them silently and converts
the whole mechanism into noise.

**Success Criteria:** A criterion silently dropped mid-build makes `/verify-spec` fail the
story rather than confirm it; a test citing a deleted criterion is named with its ID; a
criterion inserted by `/edit-spec` leaves every sibling's ID byte-identical.

**Scope Boundaries:**

- **Included:** ID grammar doc, emitter changes (`/create-spec` + `agents/user-story-generator.md`),
  `scripts/ac-trace.py` with unit tests and an eval, `/verify-spec` Check 3e/3f,
  `/edit-spec` stability guard.
- **Excluded:** coverage percentages, a traceability-matrix artifact, a new command,
  backfilling existing specs, `/implement-story` gate enforcement (this is a linter finding,
  not a pipeline gate).

## Evidence Base

The issue gated its own rationale on pinning a citation before anything is built. It is
pinned:

> Mäder, P. & Egyed, A. (2015). *Do developers benefit from requirements traceability when
> evolving and maintaining a software system?* **Empirical Software Engineering** 20(2),
> 413–441. DOI [10.1007/s10664-014-9314-z](https://doi.org/10.1007/s10664-014-9314-z)

Controlled experiment: 71 subjects re-performing 461 real maintenance tasks on two
third-party systems (GanttProject, iTrust). Subjects with access to maintained trace links
completed tasks **24% faster** and produced **50% more correct solutions**.

**Recorded caveat (do not drop this when quoting the study).** The experiment measures
*human* maintenance work against *requirement-to-code* links. It does not measure AI-agent
implementation of story-level acceptance criteria, and it does not measure the effect of an
automated orphan check. The *mechanism* — an addressable requirement is one a worker can
confirm they satisfied — transfers plausibly to Writ's setting. The *effect size* does not,
and Writ must not repeat 24%/50% as a promise about its own pipeline.

**What this spec claims on that basis:** per-criterion addressing is the precondition for
verifying a spec contract below story granularity. Without it, Check 3a can confirm that a
box is ticked and nothing more. That claim is architectural and stands on its own; the
study establishes that the general property is worth paying for rather than merely tidy.

## Why This Is the Moat Work

[ADR-008](../../decision-records/adr-008-spec-as-team-contract-moat.md) claims
spec-as-team-contract as Writ's strategic moat, resting on three commitments: plain-text +
git substrate, contract-first command discipline, and first-class drift logs. The claim's
weak joint is *verifiability*: a negotiated contract that cannot be checked below story
granularity is a contract only by courtesy. A story can report `Completed ✅` with all four
criteria ticked while one of them was quietly abandoned in the third commit, and no
existing check can contradict it.

The precedent already exists one level up. `scripts/exit-criteria.py` binds dotted IDs
(`implement-phase.c1`) to verbatim criterion text, precisely so a phase's exit claims are
machine-checkable. Story-level criteria never got the same treatment. This spec applies the
existing pattern one level down.

## 📐 The Grammar

### Criterion definition

IDs are `AC-<story>.<n>` — story number, then a per-story ordinal — rendered as a
**trailing backticked tag** on the criterion line:

```markdown
## Acceptance Criteria

> **AC IDs assigned through:** AC-3.6

- [ ] Given a criterion no task cites, when the check runs, then it reports uncovered. `[AC-3.1]`
- [ ] Given a marker below the highest ID in use, when the check runs, then it reports a marker violation. `[AC-3.6]`
- [ ] Given an ID cited by a deleted test, when the check runs, then it names the dangling reference. `[AC-3.4]`
```

Above, `AC-3.6` was inserted *second* in reading order and `AC-3.2`, `AC-3.3`, `AC-3.5`
were retired by earlier edits. Reading order and ID order are deliberately independent.

### The tag is end-anchored, and prose mentions are not tags

A definition or citation is **only** a `` `[AC-n.m]` `` group at the end of the line. An
ID-shaped token anywhere else on the line is prose and is neither a definition nor a
citation.

This is not a nicety. This spec's own [Story 4](../user-stories/story-4-edit-spec-stability-guard.md)
has a criterion whose text reads *"Given a story with criteria `AC-2.1` through `AC-2.4` and a
marker reading `AC-2.4` …"* — three ID-shaped tokens that describe a fixture. A scanner that
treats any ID on a criterion line as a definition reads Story 4 as defining `AC-2.1`, `AC-2.4`,
and `AC-2.5`, then reports them untasked and cross-story. That failure was produced against
these very files during authoring, which is why the rule is recorded here rather than left to
the implementer's judgment:

- **Definition:** the trailing group on a `- [ ]`/`- [x]` line inside `## Acceptance Criteria`
- **Citation:** the trailing group on a task line inside `## Implementation Tasks`
- **Neither:** any ID token that is not inside a trailing group, including one inside backticks
- **Cross-story guard:** a definition tag whose story number differs from the story file's own
  number is a `marker_violation`, reported rather than silently re-homed

The same anchoring makes multi-ID groups unambiguous: `` `[AC-3.1, AC-3.6]` `` is one group
defining or citing two IDs, not two separate tags.

### Why suffix placement

`scripts/recommend-state.py` parses criterion lines with two anchored regexes:

| Site | Pattern | Consequence of a prefixed ID |
|---|---|---|
| [`recommend-state.py:378`](../../../scripts/recommend-state.py) | `^- \[([ xX])\] Given ` | Counts zero criteria |
| [`recommend-state.py:2981`](../../../scripts/recommend-state.py) | `(?m)^- \[x\] (Given .+)$` | Matches nothing → raises `ContractError("uat_derivation_mismatch")` |

A prefixed ID breaks UAT derivation for every story that adopts it, and repairing it means
touching the 191 KB script that owns the recommended-delivery contract plus fixture sets in
`eval-recommend-stage.py` and `eval-recommend-state-adversarial.py`. Suffix placement keeps
both regexes matching unchanged, so **this spec touches neither**.

The suffix also earns something. Because `recommend-state.py:2981` captures the criterion
text *including* the trailing tag, the generated UAT plan inherits the criterion ID in its
scenario text at no cost — extending the trace one step past implementation into acceptance
testing.

### The high-water mark

Each story's `## Acceptance Criteria` section carries one marker line directly beneath the
heading:

```markdown
> **AC IDs assigned through:** AC-3.6
```

A new criterion takes `<mark> + 1` and the marker advances. Siblings are never renumbered;
retired numbers are never reused. This is the whole stability mechanism, and it is stable
*by construction* rather than by a prose rule that a later editor must remember.

Rejected alternatives, recorded so they are not relitigated:

- **Content-hash IDs** (`AC-3.a7f2`) — stable without bookkeeping, but an editorial reword
  of the criterion text silently changes the ID, which is exactly the rot this spec exists
  to prevent.
- **Positional IDs plus a never-renumber prose rule** — enforcement becomes retroactive
  (diff against git history to detect a violation after it lands) rather than structural.

### Task citation

Implementation tasks carry the same trailing tag, comma-separated for multiple IDs:

```markdown
## Implementation Tasks

- [ ] 3.2 Implement the orphan scan `[AC-3.1, AC-3.6]`
```

Task-line parsers anchor on the `- [ ] N.M` prefix, so a trailing tag is non-breaking.

### Test citation

Tests cite IDs in a test name or docstring:

```python
def test_uncovered_criterion_is_blocking():
    """AC-3.1 — a criterion no task cites reports uncovered."""
```

A citation counts as a **test** citation only when it appears in a test-shaped path:
a path segment of `tests/`, `test/`, `spec/`, or `__tests__/`, or a basename matching
`test_*`, `*_test.*`, `*.test.*`, or `*.spec.*`. An ID occurrence elsewhere outside
`.writ/` is recorded as a **source** citation — informational, and it does not satisfy
coverage. `.writ/config.md` caches a `Test Runner` command but no test globs, and this spec
deliberately adds no config field to supply them; pattern classification is the whole
mechanism.

## 📋 Business Rules

### Finding vocabulary

Named codes, mirroring the style Check 4d already uses (`malformed_dependencies`,
`missing_reference`, …):

| Code | Condition | Severity |
|---|---|---|
| `untasked_criterion` | A defined ID that no implementation task in the spec cites | **Blocking**, at any story status |
| `untested_criterion` | Tasked, but no test citation, and the story reads `Completed ✅` | **Blocking** — the checked-but-uncovered failure |
| `dangling_reference` | A task or test cites an ID that no criterion in the spec defines | **Blocking** |
| `duplicate_id` | The same ID appears on two criterion lines | **Blocking** |
| `marker_violation` | An ID exceeds the marker, or the marker is missing/malformed while IDs are present | **Blocking** |
| `partial_adoption` | Some criteria in a story carry IDs and others do not | **Blocking** |
| `legacy_story` | Zero criteria in the story carry IDs | Informational, never blocking |

### Severity reasoning

- **`untasked_criterion` is blocking at any status** because task tags are written at spec
  *authoring* time, not implementation time. A criterion no task cites is a defect in the
  spec package the moment it is written, and deferring the finding until the story completes
  would let it ship.
- **`untested_criterion` is blocking only at `Completed ✅`** because tests do not exist
  until the work does. Before completion its absence is expected; at completion it is the
  precise failure the source issue names — "a criterion can be silently dropped mid-build
  while the story still reports Completed ✅" — and it belongs in the same class as Check
  3a's false completion.
- **`partial_adoption` is blocking, `legacy_story` is not.** Zero IDs is a pre-adoption
  story and reported informationally, mirroring how Check 4d treats a spec with no
  `Dependencies` header as `[]`. Some-but-not-all IDs is not a migration state — it is a
  half-applied grammar in which the unaddressed criteria are invisible to the check while
  the story appears to participate.

### Legacy and archive posture

- Archived specs under `.writ/specs/archive/` are never scanned. The single-level glob
  `.writ/specs/*/` that `/verify-spec --all` already uses excludes them by construction.
- No retroactive backfill. IDs assigned to an already-`Completed ✅` story could not be
  honestly bound to tests written without them; a backfilled ID would manufacture the
  appearance of a trace link that never existed.

### Auto-fix boundary

Nothing in 3e/3f is auto-fixable. Deciding which task covers a criterion, or whether a
dangling reference should be repointed or deleted, is authorial judgment. Checks 3e/3f are
therefore **report-only inside default mode** — they behave identically under `/verify-spec`
and `/verify-spec --check`, and Phase 4 never touches them.

## Implementation Approach

### The executable reference

Blocking checks in this codebase have a deterministic script behind them —
`scripts/spec-deps.py validate` backs Check 4d, `scripts/story-deps.py validate` backs the
story graph, `scripts/exit-criteria.py check` backs the stop-time gate. This check follows
the pattern:

```
python3 scripts/ac-trace.py check --spec .writ/specs/<folder> [--repo .]
```

Read-only. One JSON object on stdout. Exit `0` clean, `1` findings present, `2` usage or
structural error. The command file describes the contract; the script is what actually
decides, so a human and an agent reach the same verdict.

### Where the check lands in `/verify-spec`

Check **3** (Completion Integrity) gains **3e** (criterion coverage) and **3f** (dangling
and malformed references). It is deliberately *not* a new Check 9: `/verify-spec`'s declared
`exit_criteria` promise "an eight-row check table," and adding a ninth check would falsify
the command's own frontmatter. Placing the new sub-checks under Check 3 also matches the
issue's framing — the same class as Check 3a's false completion.

### Marker exclusion

The marker line lives inside `## Acceptance Criteria` and contains an ID-shaped token. The
scanner must consume it as the marker and exclude it from both the definition set and the
citation set. Without that exclusion every marker satisfies its own ID and the check reports
clean on a spec with no coverage at all.

### Files in Scope

| File | Change |
|---|---|
| `.writ/docs/acceptance-criteria-ids.md` | **New.** The grammar, marker rule, and finding vocabulary — the specification the checker implements against, in the manner of `exit-criteria-classification.md` |
| `commands/create-spec.md` | Emit the marker, criterion tags, and task tags in Step 2.6's story contract; carry criterion IDs into `spec-lite.md`'s Review-agent acceptance criteria |
| `agents/user-story-generator.md` | Prompt template emits IDs, marker, and task tags; `exit_criteria` updated to require them |
| `scripts/ac-trace.py` | **New.** The checker |
| `scripts/tests/test_ac_trace.py` | **New.** Unit tests, one per finding code plus the marker-exclusion and ordering guarantees |
| `scripts/eval-ac-trace.py` | **New.** Fixture scenarios emitting PASS/FAIL TSV |
| `scripts/eval.sh` | Register `check_ac_trace` |
| `commands/verify-spec.md` | Check 3e/3f, the executable reference, report rows, auto-fix boundary |
| `commands/edit-spec.md` | Step 2.2 story-management rules: never renumber, advance the marker, record assignments in the spec `CHANGELOG.md` |
| `.writ/docs/spec-format.md` | Point to the new grammar doc |

### Deliberately not touched

`scripts/recommend-state.py`, `scripts/eval-recommend-stage.py`, and
`scripts/eval-recommend-state-adversarial.py` — the direct consequence of suffix placement.
If a future edit moves the ID to a prefix, all three come into scope and both regexes above
must change first.

## 🎯 Experience Design

- **Entry point:** `/verify-spec` on a spec whose stories carry AC IDs, or
  `python3 scripts/ac-trace.py check --spec <folder>` directly.
- **Happy path:** the checker finds every defined ID cited by at least one task, every
  `Completed ✅` story's IDs cited by at least one test, and no citation without a
  definition. Check rows 3e and 3f read clean in the verification report.
- **Moment of truth:** a `Completed ✅` story reports `untested_criterion AC-3.4`. The
  criterion was ticked; nothing proves it. That is the failure the whole spec exists to make
  visible.
- **Feedback model:** findings appear in the verification report's Check 3 rows and in
  Outstanding Warnings, each naming its finding code and criterion ID. Every finding cites a
  file and the criterion text, so the reader never has to search for what `AC-3.4` was.
- **Error experience:** a malformed marker, or a spec folder with no `user-stories/`, exits
  `2` with the offending path named — distinct from exit `1`, which means the check ran
  correctly and found real problems. A missing marker on a story with zero IDs is neither:
  it is `legacy_story`, reported and not blocking.

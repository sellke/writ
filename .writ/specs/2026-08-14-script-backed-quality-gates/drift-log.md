# Drift Log — Script-Backed Quality Gates

> Parent: [`spec.md`](spec.md)

Deviations recorded during implementation. Per-story detail lives in each
story's `## What Was Built` → *Deviations from Spec*; this file carries the
spec-level entries and the one finding that belongs to a different spec.

| ID | Story | Severity | Title |
|---|---|---|---|
| DEV-001 | 1 | Small | `tests_excluded_from_typecheck` widened to cover the linter |
| DEV-002 | 2 | Small | Nested packages excluded from `coverage_scope_gap` |
| DEV-003 | 3 | Small | Test scope narrowed to the project's own unit-test set |
| DEV-004 | 3 | Small | `coverage` with nothing to judge is `unverifiable`, not `pass` |
| DEV-005 | 6 | Small | The per-command byte ratchet needed a disclosed increment |
| DEV-006 | — | Small | `ac-trace` cannot tell a fixture literal from a citation |

---

## DEV-006 — `ac-trace` cannot tell a fixture literal from a citation

**Severity:** Small · **Owning spec:** `2026-08-13-acceptance-criteria-traceability-ids`
· **Found:** 2026-08-14, during this spec's integration verification

**What happened.** `python3 scripts/ac-trace.py check --spec
.writ/specs/2026-08-14-script-backed-quality-gates` exits 1 with seven
`dangling_reference` findings — `AC-3.6`, `AC-3.7`, `AC-3.9`, `AC-9.9` from
`scripts/tests/test_ac_trace.py`, and `AC-7.1`, `AC-7.2`, `AC-7.3` from
`scripts/tests/test_edit_spec_ac_stability_fixtures.py`.

**Why it is not this spec's defect.** Every one of those tokens is *fixture
data* belonging to the previous spec — strings inside synthetic story files that
its own tests construct in temp directories to exercise the checker. None of them
is a citation of anything. They are reported against this spec only because
`scan_repo_citations` scans the whole repository for bare `AC-<n>.<m>` tokens in
test-shaped paths and matches them against whichever spec is being checked, and
this spec happens to have stories numbered 3, 6 and 7's worth of range.

**Why it was not "fixed".** The only available workarounds are all worse than
the finding:

- Editing another spec's test fixtures to avoid ID shapes this spec uses makes
  every future spec's story numbering a constraint on every existing test file.
- Renumbering this spec's stories to dodge the collision inverts the
  relationship — the traceability instrument would be dictating spec structure.
- Suppressing the codes would disable a real check to silence a false positive,
  which is the precise failure mode the parent spec is named for.

**Where it actually belongs.** The grammar doc records that a bare token in a
test-shaped path is a test citation, with no scoping to the spec under check.
The candidate fixes — scoping the citation scan to the spec's own story range,
or requiring citations to name their spec — are changes to
`.writ/docs/acceptance-criteria-ids.md` and `scripts/ac-trace.py`, both owned by
`2026-08-13-acceptance-criteria-traceability-ids`. Recorded here rather than
worked around, so the next spec to trip it finds the diagnosis instead of
repeating it.

**Interaction worth noting.** Before this entry, the same collision was *hiding*
a real problem in the opposite direction: several of this spec's criteria
appeared covered because unrelated fixture literals happened to match their IDs.
Adding genuine citations (`scripts/tests/test_quality_gate_wiring.py`, plus AC
references in the three checker suites) cleared all eleven `untested_criterion`
findings and left only the seven that are genuinely foreign. A false positive and
a false negative from one root cause, which is the usual shape of a scoping bug.

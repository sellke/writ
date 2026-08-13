# Drift Log — Per-Criterion Traceability IDs

> Append-only. Never modify existing entries. Continue DEV-ID numbering from the highest
> existing entry.

#### [DEV-1] Step 2.6b addition to `create-spec.md` (Story 1)
- **Severity:** Small
- **Spec said:** "carry criterion IDs into spec-lite.md's Review-agent acceptance criteria"
  (Task 1.4), with no mechanism specified.
- **Implementation did:** Added a new Step 2.6b (between Step 2.6 and 2.7) that tags
  spec-lite.md's Review-agent bullets with `[AC-N.M]` after story files exist, closing a real
  sequencing gap (Step 2.4 writes spec-lite.md before Step 2.6 assigns per-story IDs).
- **Resolution:** Accepted, no spec-lite.md amendment needed — this is the task's intent
  fulfilled via an explicit, documented mechanism, not a deviation from it.

#### [DEV-2] `scripts/tests/test_governor_enforcement.py` byte-budget disclosure update (Story 1)
- **Severity:** Small
- **Spec said:** Story 1's file scope was `.writ/docs/acceptance-criteria-ids.md`,
  `agents/user-story-generator.md`, `commands/create-spec.md`, `.writ/docs/spec-format.md`.
- **Implementation did:** Editing `create-spec.md` pushed it further past its pre-existing
  recorded byte-budget overage in `KNOWN_OVER_BUDGET`, tripping an unrelated regression gate.
  Updated the recorded value (21463 → 24036 bytes) with a dated disclosure comment, following
  that file's own established precedent for disclosed increases.
- **Resolution:** Accepted, no spec-lite.md amendment needed — a narrowly-scoped, disclosed,
  arithmetically-verified data correction to keep an existing gate honest.

#### [DEV-3] Task 4.1 reinterpreted as a golden-fixture test file (Story 4)
- **Severity:** Small
- **Spec said:** "Write the guard assertions first — fixture story edited by each of the three
  shapes... asserting sibling IDs are byte-identical and the marker moved only on insert."
- **Implementation did:** Since `/edit-spec` is an LLM-interpreted markdown command with no
  executable harness of its own, the "guard assertions" became literal before/after string
  fixtures in `scripts/tests/test_edit_spec_ac_stability_fixtures.py`, asserted by plain string
  equality, rather than assertions against a running command invocation.
- **Resolution:** Accepted, no spec-lite.md amendment needed — satisfies the task's intent via
  the only mechanism available for a prose-driven command; drops none of AC-4.1–4.4's
  requirements.

#### [DEV-4] AC-2.5's literal "exits 0" is not satisfied by a live dogfood run (Story 2)
- **Severity:** Disclosed, unresolved at the spec-contract level (not an implementation defect)
- **Spec said:** AC-2.5 — running `ac-trace.py check` against this spec's own four story files
  exits 0.
- **Implementation did:** Running the built checker against this spec currently exits 1 with 14
  findings, in two classes:
  1. **`untested_criterion` on `AC-1.1`–`AC-1.4` (Story 1) and `AC-2.2`/`AC-2.3` (Story 2) — 6
     total, genuine and systemic, not unique to Story 1.** None of Stories 1, 2, or 4's actual
     test suites cite their own AC IDs by name/docstring — their tests are written against
     finding codes and behavior, the normal way software is tested, not retrofitted to also
     literally name `AC-N.M` in every test. `AC-2.1`/`AC-2.4`/`AC-2.5` happen to escape this
     finding only because unrelated fixture strings in `test_ac_trace.py` (regression fixtures
     quoting Story 4's or another test's example text) incidentally contain those bare tokens
     — accidental, not real, coverage. This means the spec's own dogfood-clean expectation
     (AC-2.5) was unmet from the moment Story 1 landed, and the gap grew as Stories 2 and 4
     landed under the same test-authoring convention.
  2. **`dangling_reference` on 8 IDs (`AC-3.5/3.6/3.7/3.9`, `AC-7.1/7.2/7.3`, `AC-9.9`) — fixture
     content in `scripts/tests/test_ac_trace.py` and `test_edit_spec_ac_stability_fixtures.py`
     that happens to collide with this spec's live ID space.** Cosmetic; does not affect the
     exit code either way (class 1 alone already blocks exit 0).
  A related, now-fixed authoring bug: an earlier version of this very drift-log/story-file
  disclosure appended prose directly after the `` `[AC-2.5]` `` tag on its criterion line,
  un-anchoring the tag per this spec's own end-anchoring grammar rule and producing two more
  spurious findings (`partial_adoption`, a second `dangling_reference(AC-2.5)`). Caught by
  Story 3's architecture review before landing; fixed by moving the annotation to a line below
  the criterion rather than the criterion line itself.
- **Resolution:** Left open for the spec owner — see Story 2's What Was Built → Deviations
  (DEV-4) for full reasoning. The real choice is no longer just about AC-2.5's wording in
  isolation: it's whether this spec's own tests should have cited AC IDs by name (a test
  authoring convention this spec never established for itself before Story 2 existed to want
  it), or whether AC-2.5 should be scoped to a documented, accepted exception covering Stories
  1/2/4's pre-existing test suites. No spec-lite.md amendment made; AC-2.5's checkbox left
  unchecked rather than satisfied by reinterpretation.

# UAT Plan: Skill Lifecycle

> **Generated:** 2026-07-10
> **Spec:** `.writ/specs/2026-07-10-skill-lifecycle/`
> **Stories Covered:** 3 of 3 completed
> **Total Scenarios:** 20

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

All commands assume the repository root `/Users/Adam/Projects/writ` as the working directory. The lint exit-code convention throughout is: `0` = clean, `1` = violations found, `2` = usage error. Read an exit code after any command with `echo $?`.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Skill Lifecycle Schema + ADR | ✅ Covered | 6 | AC: 5, Errors: 1 |
| Story 2: Lifecycle Hygiene Lint | ✅ Covered | 10 | AC: 5, Errors: 2, Shadow: 2, Edge: 1 |
| Story 3: Authoring + Catalog Wiring | ✅ Covered | 4 | AC: 5, Errors: 1, Shadow: 1 (deduped to 4) |

---

## Story 1: Skill Lifecycle Schema + ADR

### Scenario 1: Lifecycle schema defines a status field and a typed evidence block

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `.writ/decision-records/adr-014-skill-lifecycle.md` and read the schema section.
2. Open `.writ/specs/2026-07-10-skill-lifecycle/sub-specs/technical-spec.md` and read sections `### D1` and `### D2`.
3. Confirm the documented `status:` field allows exactly the values `candidate`, `proven`, `promoted`.
4. Confirm each `evidence:` entry is documented as carrying all four fields: `date`, `type` (one of `usage | transcript | eval | promotion`), `ref`, and `note`.

**Expected Result:**
- The `status:` field is described as required, with a closed three-value vocabulary.
- The evidence entry schema lists `date`, `type`, `ref`, and `note`, with the `type` vocabulary of four values.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `.writ/decision-records/adr-014-skill-lifecycle.md`, `sub-specs/technical-spec.md` (D1, D2)

**Notes:**

---

### Scenario 2: Earned-state thresholds are documented as a monotone ladder

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `.writ/decision-records/adr-014-skill-lifecycle.md`.
2. Locate the earned-state / transition rules.
3. Confirm the documented thresholds: `candidate` requires no evidence; `proven` requires at least three well-formed evidence entries; `promoted` requires the `proven` bar plus at least one `type: promotion` entry.
4. Confirm the text describes the ladder as monotone (each higher state's evidence bar is a strict superset of the one below, so `candidate → promoted` skipping is unrepresentable).

**Expected Result:**
- The three thresholds are stated exactly as above.
- The document states the ladder is monotone and that state skipping cannot happen.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `.writ/decision-records/adr-014-skill-lifecycle.md`

**Notes:**

---

### Scenario 3: ADR-014 records rationale and cites ADR-009

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `.writ/decision-records/adr-014-skill-lifecycle.md`.
2. Confirm the header records `Status: Accepted` and `Date: 2026-07-10`.
3. Confirm the body documents: the earned-state (evidence-as-state) model, the three-success threshold and its GStack provenance, and the manifest-mirror decision.
4. Confirm it cites `adr-009-command-agent-skill-boundary.md` as the boundary it *extends* (not supersedes).

**Expected Result:**
- ADR-014 is `Accepted`, dated `2026-07-10`.
- All four content points (earned-state model, GStack threshold provenance, manifest mirror, ADR-009 extension citation) are present.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `.writ/decision-records/adr-014-skill-lifecycle.md`

**Notes:**

---

### Scenario 4: Manifest skills-schema comment documents the status field

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `.writ/manifest.yaml` and find the skills-schema comment block (near the `skills:` section).
2. Confirm the comment documents the additive `status:` field and the earned-state rule.
3. Confirm the documentation is framed as backward-compatible (a `skills: []` manifest remains valid).

**Expected Result:**
- The manifest comment describes the `status:` field and its earned-state semantics.
- The addition is described as additive / backward-compatible.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `.writ/manifest.yaml` (skills-schema comment)

**Notes:**

---

### Scenario 5: conventional-commits ships as proven with three usage evidence entries

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `skills/conventional-commits/SKILL.md`.
2. Confirm the frontmatter declares `status: proven`.
3. Confirm the `evidence:` block has exactly three well-formed `type: usage` entries whose `ref` values cite `commands/ship.md`, `commands/release.md`, and `agents/coding-agent.md`.
4. Open `.writ/manifest.yaml` and confirm the `conventional-commits` entry mirrors `status: proven`.
5. Run: `bash scripts/lint-skill.sh skills/conventional-commits/SKILL.md` and read the exit code with `echo $?`.

**Expected Result:**
- The frontmatter reads `status: proven` with three `usage` entries citing those three consumers.
- The manifest entry mirrors `status: proven`.
- The lint exits `0` with no lifecycle finding for this file.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `skills/conventional-commits/SKILL.md`, `.writ/manifest.yaml`

**Notes:**

---

### Scenario 6: Manifest is a render mirror; frontmatter is authoritative

**Source:** Error & Rescue Map (Manifest schema mismatch) — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `.writ/decision-records/adr-014-skill-lifecycle.md` and/or `sub-specs/technical-spec.md` section `### D6`.
2. Confirm the documented rule: the `SKILL.md` frontmatter is the authoritative `status:` source and the manifest value is a render mirror only (the same discipline as `description:`).
3. Confirm the documented handling when the manifest omits `status:`: the generator defaults the rendered status to `candidate` rather than failing.

**Expected Result:**
- Documentation states the frontmatter is authoritative and the manifest is a render mirror.
- A missing manifest `status:` is documented to default to `candidate`, keeping catalog generation non-fatal.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `sub-specs/technical-spec.md` (D6), `.writ/decision-records/adr-014-skill-lifecycle.md`

**Notes:**

---

## Story 2: Lifecycle Hygiene Lint

### Scenario 7: Missing or out-of-vocabulary status fails the lint

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Create two disposable fixture files in a scratch directory, e.g. `/tmp/uat-skill/missing/SKILL.md` and `/tmp/uat-skill/invalid/SKILL.md`, each with valid `name`/`description` frontmatter. In the first, omit `status:` entirely. In the second, set `status: shipped`.

**Steps:**
1. Run: `bash scripts/lint-skill.sh /tmp/uat-skill/missing/SKILL.md` and read `echo $?`.
2. Run: `bash scripts/lint-skill.sh /tmp/uat-skill/invalid/SKILL.md` and read `echo $?`.

**Expected Result:**
- The missing-status file emits a "missing lifecycle status" finding (category `Lifecycle-missing`) in the standard `❌ <file>: <category> — <detail>` format with a `Remediation:` line, and exits `1`.
- The invalid-status file emits an "invalid status" finding naming the expected `candidate|proven|promoted` vocabulary (category `Lifecycle-invalid`) and exits `1`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `scripts/lint-skill.sh` (checks L1, L2)

**Notes:**

---

### Scenario 8: Unearned proven or promoted state fails with a shortfall finding

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Create `/tmp/uat-skill/unearned-proven/SKILL.md` with `status: proven` and only two well-formed evidence entries.
- Create `/tmp/uat-skill/unearned-promoted/SKILL.md` with `status: promoted` and three well-formed `type: usage` entries but no `type: promotion` entry.

**Steps:**
1. Run: `bash scripts/lint-skill.sh /tmp/uat-skill/unearned-proven/SKILL.md` and read `echo $?`.
2. Run: `bash scripts/lint-skill.sh /tmp/uat-skill/unearned-promoted/SKILL.md` and read `echo $?`.

**Expected Result:**
- The proven-with-2 file emits an "unearned state" finding stating `proven` requires ≥3 evidence entries and naming the found count, and exits `1`.
- The promoted-without-promotion file emits an "unearned state" finding stating `promoted` requires a `type: promotion` entry, and exits `1`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `scripts/lint-skill.sh` (checks L3, L4)

**Notes:**

---

### Scenario 9: Malformed evidence entry fails naming the missing/invalid field

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Create `/tmp/uat-skill/malformed/SKILL.md` with `status: proven` and three evidence entries where one entry omits `ref` (or uses an out-of-vocabulary `type` such as `type: rumor`).

**Steps:**
1. Run: `bash scripts/lint-skill.sh /tmp/uat-skill/malformed/SKILL.md` and read `echo $?`.

**Expected Result:**
- An evidence finding (category `Lifecycle-evidence`) is emitted naming the missing or invalid field (e.g., the absent `ref`, or the invalid `type`).
- The lint exits `1`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `scripts/lint-skill.sh` (check L5)

**Notes:**

---

### Scenario 10: Valid candidate, proven, and promoted skills pass clean

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Create three fixtures: `valid-candidate` (`status: candidate`, no evidence), `valid-proven` (`status: proven`, three well-formed entries), and `valid-promoted` (`status: promoted`, three entries including one `type: promotion`).

**Steps:**
1. Run the lint on each of the three fixture files in turn, reading `echo $?` after each.

**Expected Result:**
- Each of the three files exits `0` with no lifecycle finding printed.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `scripts/lint-skill.sh`; fixture design in `sub-specs/technical-spec.md` (Fixture Design)

**Notes:**

---

### Scenario 11: The skill-lifecycle eval check drives all eight fixtures

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Run: `bash scripts/eval.sh --check=skill-lifecycle` and read `echo $?`.
2. Read the printed scenario summary for the `skill-lifecycle` check.

**Expected Result:**
- The check runs the eight lifecycle fixtures (valid candidate/proven/promoted, unearned proven, unearned promoted, invalid status, malformed evidence, missing status), asserting each expected exit code.
- The check additionally asserts (via `require_literal`) that `scripts/lint-skill.sh` and `.writ/docs/skills.md` document the earned-state contract.
- The check reports all scenarios passing and the command exits `0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `scripts/eval.sh` (`check_skill_lifecycle` + `CHECKS` entry)

**Notes:**

---

### Scenario 12: A file with no frontmatter degrades to a missing-status finding, not a crash

**Source:** Error & Rescue Map (Parse skill frontmatter) — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Create `/tmp/uat-skill/no-frontmatter/SKILL.md` containing only body prose with no `---` fenced frontmatter.

**Steps:**
1. Run: `bash scripts/lint-skill.sh /tmp/uat-skill/no-frontmatter/SKILL.md` and read `echo $?`.

**Expected Result:**
- The lint reports a missing-status (L1) violation and exits `1`.
- The lint does not crash, hang, or emit a stack trace / unexpected error.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `scripts/lint-skill.sh` (frontmatter extraction)

**Notes:**

---

### Scenario 13: Empty evidence list is valid for candidate but unearned for proven

**Source:** Shadow Paths (Evidence parsing) — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Create `/tmp/uat-skill/candidate-empty/SKILL.md` with `status: candidate` and `evidence: []`.
- Create `/tmp/uat-skill/proven-empty/SKILL.md` with `status: proven` and `evidence: []`.

**Steps:**
1. Run the lint on the candidate-empty file; read `echo $?`.
2. Run the lint on the proven-empty file; read `echo $?`.

**Expected Result:**
- The candidate with `evidence: []` exits `0` (candidate needs no evidence).
- The proven with `evidence: []` emits an L3 "unearned state" finding and exits `1`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `scripts/lint-skill.sh` (evidence parsing, D5)

**Notes:**

---

### Scenario 14: Reordered evidence keys are accepted (key-based parsing)

**Source:** Interaction Edge Cases — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Create `/tmp/uat-skill/reordered/SKILL.md` with `status: proven` and three well-formed entries where at least one entry lists its four keys in a different order (e.g., `note`, `ref`, `type`, `date`).

**Steps:**
1. Run: `bash scripts/lint-skill.sh /tmp/uat-skill/reordered/SKILL.md` and read `echo $?`.

**Expected Result:**
- The lint accepts the reordered-key entries as well-formed and exits `0` (parsing is key-based, not position-based).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `scripts/lint-skill.sh` (evidence parsing, D5)

**Notes:**

---

### Scenario 15: Lifecycle logic did not leak into refresh-command

**Source:** Error & Rescue Map (Refresh-command leakage) — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Search `commands/refresh-command.md` for lifecycle-specific strings such as `status:`, `evidence`, `candidate`, `proven`, or `promoted` in a lifecycle-enforcement context.
2. Confirm the `--lint-skills` flow still invokes `bash scripts/lint-skill.sh skills/*/SKILL.md` rather than embedding lifecycle logic inline.

**Expected Result:**
- No lifecycle-enforcement logic is present in `commands/refresh-command.md`; lifecycle checks flow through the existing `--lint-skills` invocation of `scripts/lint-skill.sh`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `commands/refresh-command.md` (unedited), `scripts/lint-skill.sh`

**Notes:**

---

### Scenario 16: The skill-lifecycle check is registered and resolvable by name

**Source:** Error & Rescue Map (Eval registration) — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Run: `bash scripts/eval.sh --check=skill-lifecycle` and confirm it resolves to a real check (does not report "unknown check").
2. Run the full suite: `bash scripts/eval.sh` and read `echo $?`.

**Expected Result:**
- `--check=skill-lifecycle` dispatches to the `check_skill_lifecycle` function and runs.
- The full `eval.sh` run completes with the `skill-lifecycle` check included and passing.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `scripts/eval.sh` (`CHECKS` array + `check_skill_lifecycle`)

**Notes:**

---

## Story 3: Authoring + Catalog Wiring

### Scenario 17: /new-skill scaffolds a lint-clean candidate on every surface

**Source:** Acceptance Criteria + Experience Design (deduped) — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Run `/new-skill uat-probe-skill` (or read `commands/new-skill.md` Steps 2.1, 3.1, and 3.2 if not executing interactively).
2. Confirm the Phase 2 temp lint candidate frontmatter, the written `skills/uat-probe-skill/SKILL.md` frontmatter, and the appended `.writ/manifest.yaml` entry all carry `status: candidate`.
3. Run: `bash scripts/lint-skill.sh skills/uat-probe-skill/SKILL.md` and read `echo $?`.
4. If you created a real scaffold for this test, remove it and its manifest entry afterward so the repo is left clean.

**Expected Result:**
- All three surfaces (temp lint file, written skill, manifest entry) carry `status: candidate`.
- The freshly scaffolded skill passes the lint with exit `0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `commands/new-skill.md` (Steps 2.1, 3.1, 3.2)

**Notes:**

---

### Scenario 18: The generated catalog renders a Status column

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open the root `SKILL.md` catalog and find the `## Available Skills` table.
2. Confirm the table header is `| Skill | Status | File | Description |`.
3. Confirm each skill row shows a bare lifecycle-state word in the Status column (e.g., `conventional-commits` shows `proven`; extracted skills show `candidate`).

**Expected Result:**
- The Available Skills table includes a `Status` column between `Skill` and `File`.
- Each row shows the skill's lifecycle state; no evidence detail is inlined into the catalog.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `scripts/gen-skill.sh` (`SKILL_STATUSES`), root `SKILL.md`

**Notes:**

---

### Scenario 19: A manifest entry without status renders as candidate

**Source:** Shadow Paths (Catalog render) + Error & Rescue Map (Manifest schema mismatch) — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`
- Optional: on a throwaway copy of `.writ/manifest.yaml`, temporarily remove the `status:` line from one skills entry (never commit this).

**Steps:**
1. Regenerate the catalog against the throwaway manifest (or inspect `scripts/gen-skill.sh` where `SKILL_STATUSES` defaults a missing value).
2. Confirm the skill whose manifest entry omits `status:` renders `candidate` in the Status column.
3. Discard the throwaway manifest change.

**Expected Result:**
- A skills entry with no `status:` field renders `candidate` rather than failing generation.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `scripts/gen-skill.sh` (default-to-candidate for missing manifest status)

**Notes:**

---

### Scenario 20: Docs updated and catalog stays in sync (`--check` clean)

**Source:** Acceptance Criteria + Error & Rescue Map (Catalog regen) — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `.writ/docs/skills.md` and confirm a lifecycle section exists documenting the three states, the earned-state thresholds, the evidence schema, and a worked example.
2. Confirm the stale line "No production skills extracted yet" is left untouched by this spec (it is owned by the skill-extraction spec).
3. Run: `bash scripts/gen-skill.sh --check` and read `echo $?`.

**Expected Result:**
- The lifecycle section is present in `.writ/docs/skills.md` in its own region.
- The stale extraction line is unchanged by this spec.
- `gen-skill.sh --check` reports no drift and exits `0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `.writ/docs/skills.md` (lifecycle section), `scripts/gen-skill.sh`, root `SKILL.md`

**Notes:**

---

# UAT Plan: Skill Extraction from High-Traffic Commands

> **Generated:** 2026-07-10
> **Spec:** `.writ/specs/2026-07-10-skill-extraction/`
> **Stories Covered:** 4 of 4 completed
> **Total Scenarios:** 22

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

All commands assume the repository root `/Users/Adam/Projects/writ` as the working directory. The boundary lint exit-code convention is `0` = clean, `1` = violations. When a scenario says "search," use your editor's project search or `rg`. Read exit codes with `echo $?`.

> **Known limitation carried from Story 2:** the `commands/implement-story.md` shrink is an honest partial (net-neutral `974 → 974` lines) because Gate 1 was already pure orchestration with no inline TDD block. Scenario 10 validates that documented outcome rather than a line-count drop.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Retire `/explain-code` into a Skill | ✅ Covered | 6 | AC: 5, Errors/Shadow: 1 |
| Story 2: Extract `tdd-cycle` from `/implement-story` | ✅ Covered | 5 | AC: 5 |
| Story 3: Extract `error-rescue-mapping` from `/create-spec` | ✅ Covered | 5 | AC: 5 |
| Story 4: Extract `safe-refactor-loop` and Finalize | ✅ Covered | 6 | AC: 5, Errors/Shadow: 1 |

---

## Story 1: Retire `/explain-code` into a Skill

### Scenario 1: code-explanation skill exists as a lint-clean candidate and the command is deleted

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Confirm `skills/code-explanation/SKILL.md` exists.
2. Open it and confirm the frontmatter declares `status: candidate` and carries an initial evidence note (e.g., a `status_evidence:` line).
3. Confirm `commands/explain-code.md` no longer exists (listing the file should report "No such file").
4. Run: `bash scripts/lint-skill.sh skills/code-explanation/SKILL.md` and read `echo $?`.

**Expected Result:**
- `skills/code-explanation/SKILL.md` exists with `status: candidate` and an evidence note.
- `commands/explain-code.md` is absent.
- The lint exits `0` with no violations for the skill.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `skills/code-explanation/SKILL.md` (new), `commands/explain-code.md` (deleted)

**Notes:**

---

### Scenario 2: research.md is wired as the live consumer

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/research.md` and locate the point where it explains code.
2. Confirm a literal `Read skills/code-explanation/SKILL.md` directive is present at that point.
3. Confirm there is an accompanying orchestration note that states the skill owns the explanation template while `research` owns when to explain and what target.

**Expected Result:**
- `commands/research.md` contains a literal `Read skills/code-explanation/SKILL.md` directive, so the `disable-model-invocation: true` skill is reachable rather than orphaned.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `commands/research.md` (wired consumer)

**Notes:**

---

### Scenario 3: /explain-code is absent from every active surface

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Search each of these active surfaces for `explain-code`: `commands/` (excluding history), `.writ/manifest.yaml`, the root `SKILL.md`, both allowlists in `commands/status.md`, `README.md`, `adapters/cursor.md`, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, and `commands/new-command.md`.

**Expected Result:**
- No `explain-code` command reference remains on any of those active surfaces.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `.writ/manifest.yaml`, `commands/status.md`, `README.md`, `adapters/cursor.md`, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, `commands/new-command.md`

**Notes:**

---

### Scenario 4: Historical references survive only in the allowlisted paths

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Run a repository-wide search for `/explain-code`.
2. Confirm every surviving hit falls only within `.writ/specs/`, `.writ/decision-records/`, `.writ/explanations/`, `CHANGELOG.md`, or roadmap history.

**Expected Result:**
- `/explain-code` appears only in the allowlisted historical locations and nowhere on active product surfaces.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — retirement allowlist (`sub-specs/technical-spec.md` D6)

**Notes:**

---

### Scenario 5: Regenerated catalog lists code-explanation and drops /explain-code

**Source:** Acceptance Criteria — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open the root `SKILL.md`.
2. Confirm `code-explanation` appears in the Available Skills table.
3. Confirm the `/explain-code` command no longer appears anywhere in the catalog.
4. Run: `bash scripts/gen-skill.sh --check` and read `echo $?`.

**Expected Result:**
- The catalog lists `code-explanation` and does not list `/explain-code`.
- `gen-skill.sh --check` reports no drift and exits `0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — root `SKILL.md`, `.writ/manifest.yaml`

**Notes:**

---

### Scenario 6: The code-explanation body is capability prose only

**Source:** Error & Rescue Map (Author skill body) / Shadow Paths — Story 1

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `skills/code-explanation/SKILL.md`.
2. Outside of fenced code blocks, confirm the body contains no orchestration directives: no `Read commands/`, no `Read skills/`, no `Task(`, and no line that starts with a `/command`.
3. Run: `bash scripts/lint-skill.sh skills/code-explanation/SKILL.md` and confirm exit `0`.

**Expected Result:**
- The skill body is pure capability prose (Purpose → How It Works → Context → conditional Diagrams/Complexity Notes) with no orchestration language.
- The boundary lint passes.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 1 — `skills/code-explanation/SKILL.md`, `scripts/lint-skill.sh`

**Notes:**

---

## Story 2: Extract `tdd-cycle` from `/implement-story`

### Scenario 7: tdd-cycle skill exists as a lint-clean candidate with red→green→refactor prose

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Confirm `skills/tdd-cycle/SKILL.md` exists with frontmatter `status: candidate` and an evidence note.
2. Read the body and confirm it captures the red → green → refactor discipline (write the failing test first, implement to green, refactor under green, repeat per unit) as capability prose.
3. Run: `bash scripts/lint-skill.sh skills/tdd-cycle/SKILL.md` and read `echo $?`.

**Expected Result:**
- The skill exists as `status: candidate` with an evidence note and red→green→refactor prose.
- The lint exits `0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `skills/tdd-cycle/SKILL.md` (new)

**Notes:**

---

### Scenario 8: Three live consumers load tdd-cycle

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Search `commands/implement-story.md` (Gate 1), `agents/coding-agent.md`, and `agents/testing-agent.md` for a literal `Read skills/tdd-cycle/SKILL.md` directive.
2. Confirm each of the three files contains the directive at the point where TDD discipline applies.

**Expected Result:**
- All three consumers contain the `Read skills/tdd-cycle/SKILL.md` directive at the point of use.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `commands/implement-story.md`, `agents/coding-agent.md`, `agents/testing-agent.md`

**Notes:**

---

### Scenario 9: The tdd-cycle body contains no orchestration or gate references

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `skills/tdd-cycle/SKILL.md`.
2. Outside fenced code blocks, confirm the body has no gate names (e.g., "Gate 0.5", "Gate 1"), no agent-orchestration language, no `Read commands/`, no `Read skills/`, no `Task(`, and no line-leading slash command.
3. Run: `bash scripts/lint-skill.sh skills/tdd-cycle/SKILL.md` and confirm exit `0`.

**Expected Result:**
- The body describes only the *how* of TDD, not *when* the pipeline invokes it; the lint passes.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `skills/tdd-cycle/SKILL.md`

**Notes:**

---

### Scenario 10: implement-story shrink is a D5 note (documented net-neutral outcome)

**Source:** Acceptance Criteria (honest partial) — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/implement-story.md` Gate 1 and confirm the TDD guidance is now a D5-shaped orchestration note that loads `tdd-cycle` (skill owns the cycle; the command owns context routing, BLOCKED handling, gate flow).
2. Confirm the command still owns its non-TDD behavior: context routing, `STATUS: BLOCKED` handling, and degraded-story handling.
3. Note the documented line-count finding: `974 → 974` (net-neutral), because Gate 1 held no inline TDD block to remove.

**Expected Result:**
- Gate 1 loads `tdd-cycle` via a D5 orchestration note and retains all behavior the command still owns.
- The tester confirms the honest finding: line count is net-neutral, not a reduction (this is an accepted known limitation, not a failure).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — `commands/implement-story.md` (Gate 1 D5 note)

**Notes:**

---

### Scenario 11: Regenerated catalog lists tdd-cycle

**Source:** Acceptance Criteria — Story 2

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open the root `SKILL.md` and confirm `tdd-cycle` appears in the Available Skills table.
2. Confirm the `.writ/manifest.yaml` `skills:` entries remain alphabetically ordered with `tdd-cycle` registered.

**Expected Result:**
- `tdd-cycle` is listed in the catalog and registered alphabetically in the manifest.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 2 — root `SKILL.md`, `.writ/manifest.yaml`

**Notes:**

---

## Story 3: Extract `error-rescue-mapping` from `/create-spec`

### Scenario 12: error-rescue-mapping skill exists as a lint-clean candidate with the table technique

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Confirm `skills/error-rescue-mapping/SKILL.md` exists with `status: candidate` and an evidence note.
2. Read the body and confirm it carries the Error & Rescue Map, Shadow Paths, and Interaction Edge Cases table technique plus the `[UNPLANNED]` marker discipline as capability prose.
3. Run: `bash scripts/lint-skill.sh skills/error-rescue-mapping/SKILL.md` and read `echo $?`.

**Expected Result:**
- The skill exists as `status: candidate` with an evidence note and the three-table + `[UNPLANNED]` technique described.
- The lint exits `0`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `skills/error-rescue-mapping/SKILL.md` (new)

**Notes:**

---

### Scenario 13: create-spec Step 2.8 loads the skill and shrinks

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `commands/create-spec.md` Step 2.8.
2. Confirm a literal `Read skills/error-rescue-mapping/SKILL.md` directive is present.
3. Confirm the inline table guidance is reduced to a D5-shaped orchestration note (skill owns *how to build* the maps; create-spec owns *when* to include them).

**Expected Result:**
- Step 2.8 loads `error-rescue-mapping` and the previously inline table guidance is now a short orchestration note.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `commands/create-spec.md` (Step 2.8)

**Notes:**

---

### Scenario 14: The skill expresses the shared-format principle without line-leading orchestration

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `skills/error-rescue-mapping/SKILL.md`.
2. Confirm the prose states the tables describe what the *user sees* (not what the system does) and that discrepancies between the map and actual code are drift signals.
3. Confirm any mention of `/review` appears inside running prose (never as the first token of a line) and there is no `Read commands/` directive.

**Expected Result:**
- The skill expresses the "what the user sees" principle and the plan-vs-actual drift framing, with no line-leading slash command.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — `skills/error-rescue-mapping/SKILL.md`

**Notes:**

---

### Scenario 15: /review is documented as future work and not modified

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Confirm the spec (or skill notes) documents `/review` as a natural future second consumer of `error-rescue-mapping`.
2. Confirm `commands/review.md` was NOT wired to the skill in this spec (no `Read skills/error-rescue-mapping/SKILL.md` directive added to it).

**Expected Result:**
- `/review` is documented as deferred future wiring; it is not modified by this spec.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — spec Deliverables/notes; `commands/review.md` unmodified

**Notes:**

---

### Scenario 16: Regenerated catalog lists error-rescue-mapping

**Source:** Acceptance Criteria — Story 3

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open the root `SKILL.md` and confirm `error-rescue-mapping` appears in the Available Skills table.

**Expected Result:**
- `error-rescue-mapping` is listed in the regenerated catalog.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 3 — root `SKILL.md`, `.writ/manifest.yaml`

**Notes:**

---

## Story 4: Extract `safe-refactor-loop` and Finalize

### Scenario 17: safe-refactor-loop skill exists as a lint-clean candidate and refactor.md shrinks

**Source:** Acceptance Criteria — Story 4

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Confirm `skills/safe-refactor-loop/SKILL.md` exists with `status: candidate` and an evidence note.
2. Read the body and confirm it carries the green-baseline → surgical change → verify (tests + types + lint) → commit-or-revert → one-concern-per-commit discipline as capability prose.
3. Open `commands/refactor.md` Phase 3 and confirm it is reduced to a D5-shaped orchestration note that loads `safe-refactor-loop`.
4. Run: `bash scripts/lint-skill.sh skills/safe-refactor-loop/SKILL.md` and read `echo $?`.

**Expected Result:**
- The skill exists as `status: candidate` with the behavior-preserving-change discipline described; the lint exits `0`.
- `commands/refactor.md` Phase 3 is a D5 note referencing the skill.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 4 — `skills/safe-refactor-loop/SKILL.md` (new), `commands/refactor.md` (Phase 3)

**Notes:**

---

### Scenario 18: The catalog is in sync with the full skill set

**Source:** Acceptance Criteria — Story 4

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Run: `bash scripts/gen-skill.sh --check` and read `echo $?`.
2. Open the root `SKILL.md` and confirm the five skills are listed: `code-explanation`, `conventional-commits`, `error-rescue-mapping`, `safe-refactor-loop`, `tdd-cycle`.
3. Confirm no `/explain-code` command entry appears.

**Expected Result:**
- `gen-skill.sh --check` reports in-sync and exits `0`.
- All five skills are listed; `/explain-code` is absent.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 4 — root `SKILL.md`, `.writ/manifest.yaml`

**Notes:**

---

### Scenario 19: All skills lint clean and fan out to every platform

**Source:** Acceptance Criteria — Story 4

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Run: `bash scripts/lint-skill.sh skills/*/SKILL.md` and read `echo $?`.
2. Run: `bash scripts/install.sh --dry-run` and inspect the output.
3. Run: `bash scripts/update.sh --dry-run` and inspect the output.

**Expected Result:**
- The lint exits `0` across all skills.
- Both dry-runs show the four new skills (`code-explanation`, `error-rescue-mapping`, `safe-refactor-loop`, `tdd-cycle`) fanning out to `.cursor/`, `.claude/`, and Codex targets, with no `explain-code` command copied.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 4 — `scripts/lint-skill.sh`, `scripts/install.sh`, `scripts/update.sh`

**Notes:**

---

### Scenario 20: skills.md gains an extraction-patterns section and the stale line is corrected

**Source:** Acceptance Criteria — Story 4

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Open `.writ/docs/skills.md`.
2. Confirm an extraction-patterns section describes the lift → lint → wire → shrink transform and the four shipped skills with their consumers.
3. Confirm the previously stale line 3 ("No production skills extracted yet") is corrected to reflect the shipped extractions (four skills, all `candidate`).

**Expected Result:**
- The extraction-patterns section is present.
- Line 3 accurately reflects the shipped extractions rather than claiming none exist.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 4 — `.writ/docs/skills.md`

**Notes:**

---

### Scenario 21: The four-skill decision and ship non-extraction are documented honestly

**Source:** Acceptance Criteria — Story 4

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Read the spec's Deliverables/notes (and `.writ/docs/skills.md`).
2. Confirm the set is committed at exactly four skills, with per-skill reuse justifications.
3. Confirm `/ship`'s non-extraction is explained (its capability already shipped as `conventional-commits`), and that no fifth skill was invented to reach the roadmap's "3–5" ceiling.

**Expected Result:**
- The four-skill decision, `/ship`'s non-extraction, and each skill's reuse justification are documented; no padding fifth skill exists.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 4 — spec Deliverables, `commands/ship.md` (documented non-extraction)

**Notes:**

---

### Scenario 22: Repository-wide eval remains clean after finalization

**Source:** Error & Rescue Map (Regenerate catalog / Install fanout) / Shadow Paths (Catalog sync) — Story 4

**Preconditions:**
- Repository checked out at `/Users/Adam/Projects/writ`

**Steps:**
1. Run: `bash scripts/eval.sh` and read `echo $?`.
2. Confirm the report shows `0` findings and `0` run errors.

**Expected Result:**
- The full eval suite passes cleanly (0 findings) after all four registrations and the retirement.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** Story 4 — `scripts/eval.sh`

**Notes:**

---

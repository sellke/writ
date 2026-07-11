# UAT Plan: GBrain Compatibility Recipe

> **Generated:** 2026-07-11
> **Spec:** `.writ/specs/2026-07-11-gbrain-compatibility-recipe/`
> **Stories Covered:** 2 of 2 completed
> **Total Scenarios:** 12

## How to Use This Plan

1. Work through scenarios in order (grouped by story).
2. For each scenario, follow the steps exactly as written.
3. Mark Pass or Fail — add notes for any unexpected behavior.
4. Scenarios marked Fail should be filed as issues or fed back to the spec.
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations).

All commands assume the repository root `/Users/Adam/Projects/writ` as the working directory unless a scenario says otherwise. Read exit codes with `echo $?`.

> **Environment split — read first.** Scenarios 1–8 are **artifact/accuracy checks** that run with no external tooling. Scenarios 9–12 are **live GBrain checks** that require you to install GBrain yourself (`github.com/garrytan/gbrain`); they are the roadmap's "GBrain-equipped project" criteria and are handed off for manual execution — Writ ships no GBrain, so they cannot run in CI.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: `gbrain-interop` skill + registration | ✅ Covered | 5 | AC: 4, Shadow: 1 |
| Story 2: `gbrain-recipe.md` user-facing recipe | ✅ Covered | 4 | AC: 3, Accuracy: 1 |
| Live GBrain (handoff) | ⚑ Manual | 3 | Roadmap criteria 1–2 |

---

## Story 1: `gbrain-interop` Skill + Registration

### Scenario 1: The skill is lint-clean and born `candidate`

**Source:** Acceptance Criteria — Story 1

**Steps:**
1. Run `bash scripts/lint-skill.sh skills/gbrain-interop/SKILL.md`.
2. Inspect the frontmatter of `skills/gbrain-interop/SKILL.md`.

**Expected Result:**
- Lint reports clean (exit 0).
- Frontmatter has a verb-phrase `description:`, `disable-model-invocation: true`, and `status: candidate`; the body has an `## Evidence` section (0 entries valid).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `skills/gbrain-interop/SKILL.md`

**Notes:**

---

### Scenario 2: Detection routes on health, not PATH

**Source:** Acceptance Criteria — Story 1

**Steps:**
1. Read the skill's "Detect" section.

**Expected Result:**
- Detection uses `gbrain doctor --json` status (`ok`/`warnings` = present; `error`/missing = absent), explicitly **not** a bare `command -v gbrain`.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `skills/gbrain-interop/SKILL.md` → Detect

**Notes:**

---

### Scenario 3: Brain-first retrieval cites the canonical markdown path

**Source:** Acceptance Criteria — Story 1

**Steps:**
1. Read the "Route" and "Cite" sections.

**Expected Result:**
- When a brain is detected, the skill prefers `gbrain search` / `mcp__gbrain__search` for semantic knowledge/spec/ADR queries, and every result cites the canonical markdown path so a human can verify the source.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `skills/gbrain-interop/SKILL.md` → Route, Cite

**Notes:**

---

### Scenario 4: Registered in manifest and catalog, idempotently

**Source:** Acceptance Criteria — Story 1

**Steps:**
1. Grep `.writ/manifest.yaml` for a `gbrain-interop` skills entry.
2. Run `bash scripts/gen-skill.sh`, then `git diff --exit-code SKILL.md`.

**Expected Result:**
- `gbrain-interop` appears in the manifest `skills:` list with `status: candidate` and in the root `SKILL.md` catalog.
- A regeneration produces no diff (idempotent).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `.writ/manifest.yaml`, `SKILL.md`

**Notes:**

---

### Scenario 5 (Shadow): The skill never makes GBrain a write target

**Source:** Shadow Path — markdown-first writes

**Steps:**
1. Read the "Write" section.

**Expected Result:**
- Durable knowledge is written to `.writ/` markdown first, then `gbrain sync` re-indexes; the skill explicitly forbids writing durable knowledge only into GBrain (`gbrain put` without a backing markdown file).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `skills/gbrain-interop/SKILL.md` → Write

**Notes:**

---

## Story 2: `gbrain-recipe.md` User-Facing Recipe

### Scenario 6: Source registration uses real commands

**Source:** Acceptance Criteria — Story 2

**Steps:**
1. Read the "Register `.writ/` as a source" section of `.writ/docs/gbrain-recipe.md`.

**Expected Result:**
- Registration uses `gbrain sources add <repo-or-path>` + `gbrain sync`, documents the `.gbrain-source` pin file and recommends gitignoring it.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `.writ/docs/gbrain-recipe.md` → Step 1

**Notes:**

---

### Scenario 7: Artifact→page tag mapping is documented

**Source:** Acceptance Criteria — Story 2

**Steps:**
1. Read the page-type mapping section.

**Expected Result:**
- A table maps Writ artifacts to tags: `spec`, `adr`, `knowledge-decision`, `knowledge-convention`, `knowledge-glossary`, `knowledge-lesson`, framed as a tagging convention (not a Writ-run importer).

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `.writ/docs/gbrain-recipe.md` → Step 2

**Notes:**

---

### Scenario 8: Round-trip guarantee + removal path are stated

**Source:** Acceptance Criteria — Story 2

**Steps:**
1. Read the "Round-trip guarantee" section.

**Expected Result:**
- The guarantee (removing GBrain loses zero canonical data) is stated with a concrete removal path, and MCP registration (`gbrain serve`, `claude mcp add gbrain -- gbrain serve`) is documented.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `.writ/docs/gbrain-recipe.md` → Round-trip guarantee, Step 3

**Notes:**

---

### Scenario 9 (Accuracy): No fabricated GBrain commands

**Source:** Business Rule 8 — version boundary

**Steps:**
1. Cross-check every `gbrain …` command cited in the recipe and skill against current GBrain / GStack docs.

**Expected Result:**
- Every cited command is real; version-sensitive details (engine init flags, embedding keys, `sources remove`, local-state paths) are labeled "verify against current GBrain docs" rather than asserted.

**Status:** [ ] Pass  [ ] Fail

**Implementation Reference:** `.writ/docs/gbrain-recipe.md` → Version-tracking boundary

**Notes:**

---

## Live GBrain (Handoff — requires a GBrain install)

> These realize the roadmap's "GBrain-equipped project" and "round-trip" criteria. Install GBrain per its own tooling first (`gbrain init --pglite` is the fastest local path).

### Scenario 10: A GBrain-equipped project answers a retrieval query against `.writ/`

**Source:** Roadmap Phase 8 Success Criterion 1

**Steps:**
1. With GBrain installed and healthy (`gbrain doctor --json` → `ok`), run `gbrain sources add .` then `gbrain sync` in the repo.
2. Run `gbrain search "markdown canonical, indexes disposable"`.

**Expected Result:**
- The search returns ADR-011 (or the relevant knowledge/spec entry) and the result traces to its canonical markdown path.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 11: Live round-trip — removing GBrain loses zero canonical data

**Source:** Roadmap Phase 8 Success Criterion 2

**Steps:**
1. Note the git state of `.writ/` (`git status --short .writ/`).
2. Follow the recipe's removal path (drop the source, delete the local store, remove `.gbrain-source`).
3. Re-check `git status --short .writ/`.

**Expected Result:**
- `.writ/` is byte-for-byte unchanged; no canonical data was lost. Writ continues to function with grep retrieval.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 12: Graceful absence on a machine without GBrain

**Source:** Business Rule 2 — opt-in, gracefully absent

**Steps:**
1. On a machine where `gbrain` is not installed, use Writ normally and exercise a retrieval-style task.

**Expected Result:**
- No command references GBrain, prompts for it, or errors; behavior is identical to Writ without this spec.

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Sign-Off

- [ ] Scenarios 1–9 (artifact/accuracy) pass in CI/local — no external tooling
- [ ] Scenarios 10–12 (live GBrain) executed manually on a GBrain-equipped machine, or accepted as handed-off
- Overall UAT status: ______________________

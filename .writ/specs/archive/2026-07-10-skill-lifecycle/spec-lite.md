# Skill Lifecycle (Lite)

> Source: `.writ/specs/2026-07-10-skill-lifecycle/spec.md`
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Add a required `status:` field (`candidate → proven → promoted`) plus an `evidence:` block to skill frontmatter, where each non-`candidate` state is *earned* by evidence. Wire `/new-skill`, `lint-skill.sh`, `gen-skill.sh`, the manifest schema, `skills.md`, and a new ADR-014. Set `conventional-commits` to `proven`.

**Implementation Approach:**
- State is a function of evidence — the lint proves earned state from frontmatter alone (no git, no network).
- `candidate` = 0+ entries; `proven` = ≥3 well-formed entries; `promoted` = proven bar + ≥1 `type: promotion` entry.
- Each evidence entry: `date` (YYYY-MM-DD), `type` (`usage|transcript|eval|promotion`), `ref`, `note`.
- One validator (`scripts/lint-skill.sh`) serves `/new-skill`, `/refresh-command --lint-skills`, and `eval.sh`.
- Manifest `status:` is a render mirror; `SKILL.md` frontmatter is authoritative.
- Write failing fixtures BEFORE editing `lint-skill.sh`.

**Files in Scope:**
- `skills/<name>/SKILL.md` (schema), `skills/conventional-commits/SKILL.md` (→ proven)
- `commands/new-skill.md`, `scripts/lint-skill.sh`, `scripts/gen-skill.sh`, `scripts/eval.sh`
- `.writ/manifest.yaml`, `.writ/docs/skills.md`, `.writ/decision-records/adr-014-skill-lifecycle.md`

**Error Handling:**
- Missing/invalid `status:` → L1/L2 violation (exit 1).
- Unearned state (`proven`<3, `promoted` no promotion) → L3/L4 with the shortfall.
- Malformed evidence entry → L5 naming the missing field.
- Catalog drift → regenerate `SKILL.md` in the same story.

**Integration Points:**
- `/refresh-command --lint-skills` already runs `lint-skill.sh skills/*/SKILL.md` — DO NOT edit `refresh-command.md`.
- `gen-skill.sh` reads manifest `status:` into a `Status` catalog column.
- `eval.sh` gains one `check_skill_lifecycle` function + one `CHECKS` array entry (append-only).

---

## For Review Agents

**Acceptance Criteria:**
1. Every product `SKILL.md` carries a `status:` in the closed three-state vocabulary; omission fails the lint.
2. `proven`<3 entries or `promoted` without a promotion record fails with an "unearned state" finding.
3. A malformed evidence entry fails naming the missing/invalid field.
4. `/new-skill` scaffolds `status: candidate` (temp lint file, written file, manifest entry).
5. `/refresh-command --lint-skills` surfaces lifecycle findings with `refresh-command.md` unedited.
6. Catalog shows a `Status` column; `gen-skill.sh --check` clean.
7. `conventional-commits` is `proven` with three usage entries.

**Business Rules:**
- `status:` is required; vocabulary is closed to `candidate|proven|promoted`.
- State is earned from evidence, never asserted; the ladder is monotone (no skipping).
- Three-success threshold ports GStack's quarantine → active model.
- Demotion is a manual, unenforced maintainer edit.
- Manifest `status:` mirrors the authoritative frontmatter (like `description:`).
- Schema is finalized here for `2026-07-10-skill-extraction` to consume unchanged.

**Experience Design:**
- Entry: `/new-skill <name>` → born `candidate`; reviewer runs `/refresh-command --lint-skills`.
- Happy path: candidate → accrue evidence → proven at 3 → promoted on `required_skills:` declaration.
- Moment of truth: catalog `Status` column distinguishes provisional / load-bearing / depended-upon skills.
- Error: lint blocks unearned or malformed states with a specific shortfall.

**Drift Anchors:**
- Editing `commands/refresh-command.md`, extracting new skills, or fixing the stale "No production skills extracted yet" line is OUT of scope.
- Reading git/transcripts/network to verify evidence truth is contract drift — the lint checks shape and thresholds only.

---

## For Testing Agents

**Success Criteria:**
1. All eight lifecycle fixtures produce their expected lint exit codes.
2. `skill-lifecycle` eval check passes within full `eval.sh`.
3. `lint-skill.sh skills/*/SKILL.md`, `gen-skill.sh --check`, and `install.sh --dry-run` are clean.

**Shadow Paths to Verify:**
- **Happy path:** valid candidate/proven/promoted → exit 0.
- **Nil input:** no frontmatter → L1 missing-status.
- **Empty input:** `evidence: []` valid on candidate, L3 unearned on proven.
- **Upstream error:** `status: shipped` → L2; malformed entry → L5.

**Edge Cases:**
- `proven` with 2 entries → L3; `promoted` with usages but no promotion → L4.
- Reordered evidence keys → valid (key-based parse).
- Manifest omits `status:` → catalog renders `candidate`.

**Coverage Requirements:**
- Every lifecycle rule (L1–L5) has a failing fixture and a passing fixture.
- Fixtures written before the `lint-skill.sh` edits.

**Test Strategy:**
- Failing-first fixtures driven through `lint-skill.sh`.
- `scripts/eval.sh --check=skill-lifecycle`, then full `eval.sh`, `gen-skill.sh --check`, install dry run.

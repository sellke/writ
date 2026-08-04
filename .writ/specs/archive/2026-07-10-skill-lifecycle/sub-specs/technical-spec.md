# Technical Specification: Skill Lifecycle

> **Parent:** `../spec.md`
> **Status:** Complete
> **Stories:** 1–3

## Architecture Summary

The lifecycle adds a declarative `status:` field (and an `evidence:` block) to skill frontmatter and a stateless validator that proves the declared state is *earned* by the evidence present. There is one validator — `scripts/lint-skill.sh` — invoked by every path: `/new-skill` at authoring time, `/refresh-command --lint-skills` at review time, and `scripts/eval.sh` in CI. The manifest and generated catalog carry a rendered mirror of the state, never a competing source of truth.

```text
        skills/<name>/SKILL.md frontmatter  (authoritative)
        ┌───────────────────────────────────────────────┐
        │ status: candidate | proven | promoted          │
        │ evidence:                                       │
        │   - { date, type, ref, note }                   │
        └───────────────────────────────────────────────┘
                        │
        ┌───────────────┼─────────────────────────────┐
        ▼               ▼                             ▼
 lint-skill.sh    manifest.yaml status:        (author records
 earned-state     (render mirror)               evidence as the
 validation            │                        skill sees use)
        │              ▼
        │        gen-skill.sh ──► SKILL.md catalog "Status" column
        │
        ├──► /new-skill (authoring)
        ├──► /refresh-command --lint-skills (review)
        └──► scripts/eval.sh skill-lifecycle check (CI)
```

## Design Decisions

### D1 — Status Is a Closed Three-State Vocabulary

Skill frontmatter gains a required `status:` field:

```yaml
---
name: conventional-commits
description: "Write Conventional Commits messages ..."
disable-model-invocation: true
status: proven
---
```

Rules:

- Value is exactly one of `candidate`, `proven`, `promoted`.
- The field is required on every Writ-authored `SKILL.md`; absence is a violation.
- `candidate` is the born state and the `/new-skill` default.
- The vocabulary is closed — any other value is an "invalid status" violation.

### D2 — Evidence Is a YAML List of Typed Entries

Non-`candidate` states carry an `evidence:` block:

```yaml
status: proven
evidence:
  - date: 2026-05-06
    type: usage
    ref: commands/ship.md
    note: "Cited as the commit-message authority in /ship's commit phase."
  - date: 2026-05-12
    type: usage
    ref: commands/release.md
    note: "Release changelog grouping consumes the type vocabulary."
  - date: 2026-06-01
    type: usage
    ref: agents/coding-agent.md
    note: "coding-agent authors story commits through this skill."
```

Each entry requires all four fields:

| Field | Format | Meaning |
|---|---|---|
| `date` | `YYYY-MM-DD` | When the evidence was recorded |
| `type` | `usage \| transcript \| eval \| promotion` | Class of evidence |
| `ref` | repo-relative path or transcript UUID | Pointer to the evidence |
| `note` | one line | Human-readable justification |

`type` semantics: `usage` = a consumer file wields the skill; `transcript` = a recorded agent-transcript UUID shows a successful application; `eval` = a passing eval check exercises the skill; `promotion` = a consumer declares the skill in `required_skills:`. This schema is **finalized by this spec** and consumed unchanged by `2026-07-10-skill-extraction`.

### D3 — State Is Earned From Evidence (Static Transition Legality)

The lint sees one file at a time — no git history. "Legal transition" is reframed as "the declared state is earned by the evidence present":

| State | Evidence bar |
|---|---|
| `candidate` | 0+ entries (none required) |
| `proven` | ≥3 well-formed entries |
| `promoted` | `proven` bar **and** ≥1 entry with `type: promotion` |

Because each bar is a strict superset of the one below, the ladder is monotone: a valid `promoted` statically implies the `proven` and `candidate` bars were met, so `candidate → promoted` skipping is unrepresentable. The three-entry threshold ports GStack's "active after three successes" quarantine model. Demotion is a manual maintainer edit the lint does not police — it only proves the *current* declared state.

### D4 — Lint Is the Single Validator

`scripts/lint-skill.sh` gains a `lint_lifecycle` step invoked from `lint_file`, running after the existing description-shape and body-shape checks. It reuses the frontmatter-extraction approach already in the script (an `awk` pass bounded by the `---` fences).

Per-file lifecycle checks:

| ID | Check | Finding category |
|---|---|---|
| L1 | `status:` present | `Lifecycle-missing` |
| L2 | value ∈ vocabulary | `Lifecycle-invalid` |
| L3 | non-`candidate` meets its evidence-count threshold | `Lifecycle-unearned` |
| L4 | `promoted` carries a `type: promotion` entry | `Lifecycle-unearned` |
| L5 | each evidence entry has all four well-formed fields | `Lifecycle-evidence` |

Findings use the existing shape (`❌ <file>: <category> — <detail>` + `Remediation:`), increment the shared `violations` counter, and preserve exit codes `0`/`1`/`2`. No lifecycle logic touches `commands/refresh-command.md`; its Phase 5 `--lint-skills` flag already runs `bash scripts/lint-skill.sh skills/*/SKILL.md`.

### D5 — Evidence Parsing Without a YAML Library

Bash + `awk` parse the `evidence:` block by: (a) locating the `evidence:` key inside the frontmatter, (b) collecting subsequent lines indented under it, (c) counting `- ` list-item starts as entries, (d) for each entry, asserting the four required keys appear before the next list item or block end. Edge cases the parser must survive: absent block (valid for `candidate`), `evidence: []` inline empty list, entries with reordered keys, quoted vs unquoted `note`, and trailing blank lines. Fixtures cover each.

### D6 — Manifest Carries a Render Mirror

The `.writ/manifest.yaml` skills entry gains an optional `status:` field used only for catalog rendering, mirroring how `description:` is already duplicated between frontmatter and manifest. The `SKILL.md` frontmatter is authoritative; the manifest value is metadata for `gen-skill.sh`. The schema comment (lines ~215–223) documents the field; the generator defaults a missing manifest `status:` to `candidate` so the skill-extraction spec's appended entries render even before evidence accrues.

### D7 — Catalog Gains a Status Column

`scripts/gen-skill.sh` adds a `SKILL_STATUSES` array parallel to `SKILL_NAMES`/`SKILL_FILES`/`SKILL_DESCRIPTIONS`, populated in both the `yq` path (line ~152–159) and the fallback line-parser path (line ~369–398). The Available Skills table (line ~640–648) becomes:

```markdown
## Available Skills

| Skill | Status | File | Description |
|-------|--------|------|-------------|
| `conventional-commits` | `proven` | `skills/conventional-commits/SKILL.md` | Write Conventional Commits ... |
```

Adding the column changes generated `SKILL.md`; regeneration and `gen-skill.sh --check` land in the same story (Story 3).

### D8 — ADR-014 Extends ADR-009

`adr-014-skill-lifecycle.md` records: the earned-state model, the evidence schema, the three-success threshold and its GStack provenance, static transition legality, and the manifest-mirror decision. It cites ADR-009 as the boundary it extends (classification unchanged; lifecycle is a new orthogonal axis), not a supersession. Date `2026-07-10`, Status `Accepted`.

## File × Story Matrix

| File | S1 | S2 | S3 |
|---|---:|---:|---:|
| `skills/<name>/SKILL.md` (schema definition) | ✓ |  |  |
| `.writ/decision-records/adr-014-skill-lifecycle.md` | ✓ |  |  |
| `.writ/manifest.yaml` | ✓ |  | ✓ |
| `skills/conventional-commits/SKILL.md` | ✓ |  |  |
| `scripts/lint-skill.sh` |  | ✓ |  |
| `scripts/eval.sh` |  | ✓ |  |
| lifecycle lint fixtures |  | ✓ |  |
| `commands/new-skill.md` |  |  | ✓ |
| `scripts/gen-skill.sh` |  |  | ✓ |
| `.writ/docs/skills.md` |  |  | ✓ |
| `SKILL.md` (regenerated catalog) |  |  | ✓ |

`.writ/manifest.yaml` appears in S1 (schema comment + `conventional-commits` status mirror) and S3 (no further edit expected, but the catalog regen in S3 reads it — listed for traceability). `scripts/eval.sh` and `.writ/docs/skills.md` are SHARED-ADDITIVE with `2026-07-10-skill-extraction`; edits are append-only in distinct regions.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Parse skill frontmatter | Missing/garbled `---` fences or no frontmatter | Reuse existing extractor; missing `status:` becomes an L1 violation, not a crash | Fixture with no frontmatter and with only `name`/`description` |
| Validate status value | Absent or out-of-vocabulary `status:` | L1/L2 violation with expected vocabulary in the finding | Fixtures: missing status, `status: shipped`, empty value |
| Enforce earned state | `proven` with <3 entries; `promoted` with no promotion record | L3/L4 "unearned state" finding naming the shortfall and count | Fixtures: proven-with-2, promoted-without-promotion |
| Parse evidence block | Malformed entry, reordered keys, `evidence: []`, indentation drift | L5 finding naming the missing/invalid field; empty block valid only for `candidate` | Fixtures: missing `ref`, bad `type`, empty inline list, reordered keys |
| Manifest schema mismatch | Manifest `status:` disagrees with frontmatter, or manifest omits `status:` | Frontmatter is authoritative; generator defaults missing manifest status to `candidate`; drift is a documented author responsibility (same as `description:`) | Manifest entry without status → catalog renders `candidate`; note drift in ADR/docs |
| Catalog regen | `gen-skill.sh --check` drift after adding the column | Run `gen-skill.sh` to regenerate `SKILL.md`; commit the generated file in the same story | `gen-skill.sh --check` clean gate in Story 3 verification |
| Eval registration | `skill-lifecycle` check added to function but not `CHECKS`, or vice versa | Register both the `check_skill_lifecycle` function and the `CHECKS` array line; `--check=skill-lifecycle` resolves | Run `bash scripts/eval.sh --check=skill-lifecycle` and full `eval.sh` |
| Refresh-command leakage | Lifecycle logic mistakenly added to `commands/refresh-command.md` | Keep all logic in `lint-skill.sh`; verify via targeted search that refresh-command is unedited | Search `commands/refresh-command.md` for lifecycle strings — must be absent |

No `[UNPLANNED]` operations remain. The lint validates evidence *shape and thresholds* only; it never fetches or verifies that a cited transcript UUID or path is genuine — that is out of scope by design.

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Status validation | Valid state word → pass | No frontmatter → L1 missing-status violation | `status:` present but empty value → L2 invalid | `status: shipped` → L2 invalid with vocabulary |
| Evidence parsing | 3 well-formed entries → proven passes | No `evidence:` block on `candidate` → valid | `evidence: []` on `candidate` → valid; on `proven` → L3 unearned | Malformed entry → L5 names missing field |
| Earned-state | proven+3 / promoted+promotion → pass | candidate (no evidence) → pass | proven+0 → L3 unearned | promoted with 3 usage but no promotion → L4 unearned |
| `/new-skill` scaffold | Writes `status: candidate`, lint clean | Interactive name prompt still yields candidate default | No tags → candidate scaffold unaffected | Lint of temp file fails only on description shape, never on missing status |
| Catalog render | `Status` column shows earned state | `skills: []` → no Skills section (unchanged) | Manifest entry without `status:` → renders `candidate` | `gen-skill.sh --check` drift → regenerate in same story |
| Eval check | Fixtures pass → `skill-lifecycle` green | No fixtures dir → check errors loudly, not silently | Empty fixture set → check reports zero scenarios | Lint exit-code mismatch → check adds a finding |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Author sets `proven` before recording evidence | Lint blocks with L3 "unearned state" naming the count shortfall |
| Author claims `promoted` with 3 usage entries but no `required_skills:` consumer | L4 blocks; promotion needs a `type: promotion` entry |
| Evidence entry keys in a different order | Parser is key-based, not position-based; valid |
| `evidence: []` on a `candidate` | Valid — candidate needs no evidence |
| Manifest `status:` lags the frontmatter after a promotion | Frontmatter authoritative; catalog shows manifest value; author syncs the mirror (documented, same discipline as `description:`) |
| Skill-extraction appends a manifest entry with `status: candidate` | Renders correctly; generator default also covers omission |
| A future demotion (`proven → candidate`) | Allowed as a manual edit; lint validates only the new current state |
| Non-Writ community skill without `status:` | Writ lint targets `skills/*/SKILL.md` product source; community skills follow their own catalogs and are not linted here |

## Fixture Design

Disposable lint fixtures (temp directory or a fixtures path excluded from product discovery), written **before** the `lint-skill.sh` edits:

1. `valid-candidate` — `status: candidate`, no evidence → exit 0.
2. `valid-proven` — `status: proven`, 3 well-formed entries → exit 0.
3. `valid-promoted` — `status: promoted`, 3 entries incl. one `type: promotion` → exit 0.
4. `unearned-proven` — `status: proven`, 2 entries → exit 1, L3.
5. `unearned-promoted` — `status: promoted`, 3 usage entries, no promotion → exit 1, L4.
6. `invalid-status` — `status: shipped` → exit 1, L2.
7. `malformed-evidence` — `status: proven`, one entry missing `ref` → exit 1, L5.
8. `missing-status` — frontmatter without `status:` → exit 1, L1.

The `skill-lifecycle` eval check drives these fixtures through `lint-skill.sh` and asserts each expected exit code, then uses `require_literal` to confirm the lint script and `.writ/docs/skills.md` document the earned-state contract.

## Verification Commands

```bash
bash scripts/lint-skill.sh skills/*/SKILL.md
bash scripts/eval.sh --check=skill-lifecycle
bash scripts/eval.sh
bash scripts/gen-skill.sh --check
bash scripts/install.sh --dry-run
```

Also search `commands/refresh-command.md` to confirm no lifecycle logic leaked into it, and confirm the stale "No production skills extracted yet" line in `.writ/docs/skills.md` is untouched by this spec.

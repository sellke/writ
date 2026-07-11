# Skill Lifecycle

> **Status:** Not Started
> **Created:** 2026-07-10
> **Owner:** @AdamSellke
> **Phase:** 7 — Compounding Layer
> **Dependencies:** []
> **Source:** `.writ/product/roadmap.md` Phase 7 — feature "Skill lifecycle"
> **Governing ADRs:** `adr-009-command-agent-skill-boundary.md` (extended), `adr-014-skill-lifecycle.md` (new, authored by this spec)

---

## Specification Contract

**Deliverable:** Add a `status:` lifecycle field to skill frontmatter with three earned states — `candidate → proven → promoted` — where every non-`candidate` state is backed by a recorded evidence block. Wire `/new-skill` to scaffold at `status: candidate`, teach `scripts/lint-skill.sh` to enforce lifecycle hygiene (surfaced through the existing `/refresh-command --lint-skills` path), render lifecycle state in the generated `SKILL.md` catalog, extend the `.writ/manifest.yaml` skills schema, document the lifecycle in `.writ/docs/skills.md`, record `adr-014-skill-lifecycle.md`, and mark the one shipped skill (`conventional-commits`) as `status: proven` with its real-use evidence.

**Origin:** Phase 7 — Compounding Layer in `.writ/product/roadmap.md`, feature "Skill lifecycle." Extends the command/agent/skill boundary set in ADR-009, which has no lifecycle concept.

**Must Include:** A statically-checkable schema in which the declared `status:` is a *function of the evidence present* — a skill cannot claim a state it has not earned. The lint proves earned state from the frontmatter alone, with no dependence on git history or network access.

**Hardest Constraint:** Finalize the `status:` schema and the `lint-skill.sh` lifecycle rules precisely enough that the downstream `2026-07-10-skill-extraction` spec can consume them unchanged. Every skill that spec extracts is born `status: candidate`; this spec is the single writer of the schema and lint contract it will depend on.

### Experience Design

- **Entry point:** A skill author runs `/new-skill <name>` and receives a scaffold that already carries `status: candidate`. A reviewer runs `/refresh-command --lint-skills`, which routes through `scripts/lint-skill.sh`.
- **Happy path:** Scaffold at `candidate` → accumulate recorded evidence as the skill sees real use → promote to `proven` at the three-success threshold → promote to `promoted` when a consumer declares it in `required_skills:`.
- **Moment of truth:** A maintainer reading the generated `SKILL.md` catalog can see, at a glance, which skills are provisional (`candidate`), load-bearing (`proven`), and structurally depended upon (`promoted`) — and the lint guarantees each label was earned.
- **Feedback model:** The lint prints per-file lifecycle findings with the offending field, the earned-vs-claimed gap, and a remediation. The catalog shows a `Status` column.
- **Error experience:** A skill claiming `proven` with two evidence entries, or `promoted` with no promotion record, fails the lint with an "unearned state" finding naming the exact shortfall. A malformed evidence entry names the missing field.

### Business Rules

1. `status:` is a **required** frontmatter field on every Writ-authored `SKILL.md`. Its value is exactly one of `candidate`, `proven`, `promoted`.
2. `/new-skill` scaffolds every new skill at `status: candidate` with an empty (or absent) evidence block.
3. State is **earned from evidence**, not asserted. The lint validates the declared state against the evidence present in the same frontmatter — no git history, no network.
4. `candidate` requires no evidence. Fewer than three recorded evidence entries is a valid `candidate`.
5. `proven` requires **at least three** well-formed evidence entries (the "active after three successes" threshold, borrowed from GStack's domain-skill quarantine model).
6. `promoted` requires everything `proven` requires **plus** at least one evidence entry of `type: promotion` citing a consumer that declares the skill in `required_skills:`.
7. Because `promoted`'s evidence bar is a strict superset of `proven`'s, and `proven`'s a superset of `candidate`'s, the ladder is monotone: a valid higher state statically implies the lower states were passed. Skipping (`candidate → promoted` without meeting the `proven` bar) is unrepresentable.
8. Each evidence entry is well-formed only with all of: `date` (`YYYY-MM-DD`), `type` (`usage | transcript | eval | promotion`), `ref` (repo-relative path or transcript UUID), and `note` (one line).
9. The lint treats a missing `status:`, an out-of-vocabulary value, an unearned state, or a malformed evidence entry as a **violation** (exit `1`), consistent with the existing description-shape and body-shape violation model.
10. Demotion (editing a skill from `proven` back to `candidate`) is a manual maintainer action outside lint enforcement; the lint only ever proves the *current* declared state is earned.
11. The `.writ/manifest.yaml` skills entry carries a mirrored `status:` for catalog rendering, exactly as `description:` is mirrored today. The `SKILL.md` frontmatter is the authoritative source; the manifest value is render metadata.
12. `conventional-commits` ships at `status: proven` with three `type: usage` evidence entries citing `/ship`, `/release`, and `coding-agent`.

### Success Criteria

1. Every Writ-authored `SKILL.md` carries a `status:` field whose value is one of the three states, and the lint fails any file that omits it or uses an out-of-vocabulary value.
2. A skill declaring `proven` with fewer than three evidence entries, or `promoted` without a promotion record, fails the lint with a specific "unearned state" finding.
3. A malformed evidence entry (missing `date`, `type`, `ref`, or `note`, or an out-of-vocabulary `type`) fails the lint naming the missing or invalid field.
4. `/new-skill` scaffolds new skills at `status: candidate`, and the scaffold passes the lint unchanged.
5. `/refresh-command --lint-skills` surfaces every lifecycle finding without any edit to `commands/refresh-command.md` (the flag already invokes `scripts/lint-skill.sh skills/*/SKILL.md`).
6. The generated `SKILL.md` catalog renders a `Status` column, and `bash scripts/gen-skill.sh --check` is clean after regeneration.
7. `conventional-commits` is `status: proven` with three real-use evidence entries and passes the lint.
8. `bash scripts/eval.sh` includes a `skill-lifecycle` check that passes; `bash scripts/lint-skill.sh skills/*/SKILL.md`, `bash scripts/gen-skill.sh --check`, and `bash scripts/install.sh --dry-run` are clean.
9. `adr-014-skill-lifecycle.md` records the lifecycle semantics and cites ADR-009 as the boundary it extends.

### Scope Boundaries

**Included:**
- The `status:` frontmatter field contract and the evidence-block schema.
- Lifecycle-hygiene rules in `scripts/lint-skill.sh` (state presence, vocabulary, earned-state thresholds, evidence well-formedness).
- A `skill-lifecycle` eval check registered in `scripts/eval.sh` with valid and invalid fixtures.
- `/new-skill` scaffolding at `status: candidate`.
- A `Status` column in the generated `SKILL.md` catalog via `scripts/gen-skill.sh`.
- The `.writ/manifest.yaml` skills-schema comment and the `status:` mirror on `conventional-commits`.
- A lifecycle section in `.writ/docs/skills.md`.
- `adr-014-skill-lifecycle.md`.
- Setting `conventional-commits` to `status: proven` with evidence.

**Excluded:**
- Extracting any new skills (owned by `2026-07-10-skill-extraction`).
- Editing `commands/refresh-command.md` — lifecycle checks flow through the existing `--lint-skills` path automatically.
- A `/promote-skill` or demotion command, or any automated state transition.
- Reading git history, agent transcripts, or the network to *verify* cited evidence — the lint checks well-formedness and thresholds, not evidence truth.
- Fixing the stale "No production skills extracted yet" line in `.writ/docs/skills.md` (owned by `2026-07-10-skill-extraction`).
- Per-platform install-fanout changes (skills already fan out; no new mechanism).

### Technical Concerns

- **Static transition legality.** The lint sees one file at a time, not history. "Legal transition" is reframed as "the declared state is earned by the evidence present." Making each state's evidence bar a strict superset of the state below makes the ladder monotone and the check purely static.
- **Manifest/frontmatter drift.** `status:` lives in both `SKILL.md` (authoritative) and the manifest entry (render mirror), exactly like `description:`. The error map covers the mismatch; the authoritative source is always the frontmatter.
- **Bash frontmatter parsing.** `lint-skill.sh` already parses YAML frontmatter with `awk`. The evidence block is a YAML list of maps — the lint must parse nested list items without a YAML library. Fixtures must cover indentation and empty-block edge cases.
- **Catalog regen is a generated-file change.** Adding a `Status` column changes `SKILL.md`; regeneration and `gen-skill.sh --check` belong to the same story as the generator edit.
- **Shared-additive files.** `.writ/manifest.yaml`, `.writ/docs/skills.md`, and `scripts/eval.sh` are also touched by the skill-extraction spec. This spec appends to distinct regions; sequential phase execution keeps the additions conflict-free.

### Recommendations

- Encode the three-success threshold as an evidence-count rule rather than a separate flag, so the schema stays declarative and the lint stays stateless.
- Model promotion as an evidence `type: promotion` entry rather than a second status axis — it keeps the ladder one-dimensional and the catalog column simple.
- Keep the manifest `status:` optional-with-`candidate`-default in the generator so the skill-extraction spec's appended entries render even before they carry evidence.
- Author `adr-014` as an extension of ADR-009 (same boundary, new lifecycle axis), not a supersession — ADR-009's classification rules are untouched.
- Write failing fixtures before touching `lint-skill.sh`, mirroring the repo's contract-and-script verification discipline.

### Cross-Spec Review

`2026-07-10-skill-extraction` is the sole downstream consumer and has **no reciprocal dependency back onto this spec's runtime** — it depends only on the finalized schema and lint contract. This spec owns the schema, lint rules, catalog column, `/new-skill` scaffold, ADR, and the `conventional-commits` status. The extraction spec owns new skill files, the stale skills-doc line, and its own manifest and doc appends. `2026-07-09-phase6-autonomy-ceiling` (complete) established the `scripts/eval.sh` check-registration pattern this spec reuses. No competing writer touches the `status:` schema.

---

## Experience Design

### Primary User Journey

1. An author runs `/new-skill retro-facilitation`. The scaffold is written with `status: candidate` and no evidence block. It passes the lint.
2. Over subsequent work, the skill is wielded by a command and an agent. The author (or a reviewer) records evidence entries citing those consumers.
3. Once three well-formed entries exist, the author edits `status: proven`. `/refresh-command --lint-skills` confirms the state is earned.
4. When a consumer adds the skill to its `required_skills:` frontmatter, the author adds a `type: promotion` evidence entry and edits `status: promoted`. The lint confirms the promotion record exists.
5. The maintainer regenerates the catalog; `SKILL.md` shows each skill's `Status` column so provisional and load-bearing skills are distinguishable at a glance.

### State Catalog

| State | User-visible behavior |
|---|---|
| Missing `status:` | Lint violation — "missing lifecycle status"; skill is not shippable |
| `candidate` | Provisional; no evidence required; born state from `/new-skill` |
| `candidate` with 1–2 evidence entries | Valid; accumulating toward the proven threshold |
| `proven` with ≥3 evidence entries | Valid; skill is in real use across consumers |
| `proven` with <3 evidence entries | Lint violation — "unearned state: proven requires ≥3 evidence entries (found N)" |
| `promoted` with proven bar + promotion record | Valid; a consumer structurally depends on the skill |
| `promoted` without a promotion record | Lint violation — "unearned state: promoted requires a type: promotion evidence entry" |
| Out-of-vocabulary status | Lint violation — "invalid status 'X'; expected candidate\|proven\|promoted" |
| Malformed evidence entry | Lint violation naming the missing/invalid field |

### Interaction and Output Rules

- Output stays terminal-oriented Markdown; no new UI.
- Lifecycle findings match the existing lint finding shape: `❌ <file>: <category> — <detail>` plus a `Remediation:` line.
- The catalog `Status` column shows the bare state word; no evidence is inlined into the catalog.
- Missing evidence is distinct from malformed evidence — the finding text names which.
- The lint never asserts that cited evidence is *true*; it validates presence, vocabulary, thresholds, and shape only.

---

## Detailed Requirements

### R1 — Lifecycle Status Field

- Every Writ-authored `SKILL.md` frontmatter includes `status: <candidate|proven|promoted>`.
- The field is required; its absence is a violation.
- The value vocabulary is closed to exactly three states.
- `candidate` is the born state and the `/new-skill` default.

### R2 — Evidence Block Schema

- Non-`candidate` states carry an `evidence:` block: a YAML list of entries.
- Each entry has `date` (`YYYY-MM-DD`), `type` (`usage | transcript | eval | promotion`), `ref` (repo-relative path or transcript UUID), and `note` (one line).
- `type: usage` cites a consumer command or agent file that wields the skill.
- `type: transcript` cites an agent-transcript UUID demonstrating a successful application.
- `type: eval` cites a passing eval check that exercises the skill.
- `type: promotion` cites a consumer whose `required_skills:` declares the skill.
- The schema is finalized by this spec; the skill-extraction spec consumes it unchanged.

### R3 — Earned-State Transition Rules

- `candidate → proven` is earned when the evidence block holds ≥3 well-formed entries.
- `proven → promoted` is earned when, in addition, ≥1 entry has `type: promotion`.
- The ladder is monotone: each higher state's evidence bar is a strict superset of the lower state's, so a valid state statically implies the states below were earned. `candidate → promoted` skipping is unrepresentable.
- Demotion is a manual, unenforced maintainer action; the lint validates only the current declared state.

### R4 — Lifecycle Hygiene Lint

- `scripts/lint-skill.sh` gains lifecycle checks that run per file alongside the existing description-shape and body-shape checks.
- Checks: (a) `status:` present, (b) value in vocabulary, (c) non-`candidate` states meet their evidence threshold, (d) `promoted` carries a promotion record, (e) each evidence entry is well-formed.
- Each failed check emits a finding in the existing format and increments the violation count; exit codes stay `0` (clean), `1` (violations), `2` (usage error).
- No lifecycle logic is added to `commands/refresh-command.md`; its Phase 5 `--lint-skills` flag already invokes `scripts/lint-skill.sh skills/*/SKILL.md`, so the new checks flow through automatically.

### R5 — Lifecycle Eval Check

- `scripts/eval.sh` gains a `skill-lifecycle` check: one `check_skill_lifecycle` function plus one entry appended to the `CHECKS` array (SHARED-ADDITIVE with the skill-extraction spec; distinct regions; sequential execution keeps it conflict-free).
- The check runs `lint-skill.sh` against valid and invalid fixtures and asserts the expected exit codes, and uses `require_literal` to assert the lint script and `.writ/docs/skills.md` document the lifecycle contract.
- Fixtures are written **first** (failing) and cover: valid candidate, valid proven, valid promoted, unearned proven, unearned promoted, invalid status value, malformed evidence entry, missing status.

### R6 — Authoring Scaffold

- `commands/new-skill.md` scaffolds the frontmatter with `status: candidate` (and no evidence block) in both the lint-candidate temp file (Phase 2) and the written `skills/<name>/SKILL.md` (Phase 3).
- The manifest entry appended by `/new-skill` includes `status: candidate`.
- The Core Rules and Completion sections name the lifecycle default so authors understand the born state.

### R7 — Catalog Rendering

- `scripts/gen-skill.sh` renders a `Status` column in the Available Skills table: `| Skill | Status | File | Description |`.
- The generator parses `status:` from each manifest skills entry (adding a parallel `SKILL_STATUSES` array), defaulting a missing value to `candidate`.
- The root `SKILL.md` is regenerated in the same story, and `bash scripts/gen-skill.sh --check` is clean.

### R8 — Schema, Docs, and ADR

- `.writ/manifest.yaml` skills-schema comment documents the `status:` field and the earned-state rule; the `conventional-commits` entry gains `status: proven`.
- `.writ/docs/skills.md` gains a lifecycle section (states, thresholds, evidence schema, worked example) in a region distinct from the skill-extraction spec's edits. The stale "No production skills extracted yet" line is *not* touched here.
- `.writ/decision-records/adr-014-skill-lifecycle.md` records the lifecycle semantics, the evidence-as-state rationale, the three-success threshold provenance (GStack), and cites ADR-009 as the extended boundary.
- `skills/conventional-commits/SKILL.md` frontmatter gains `status: proven` and three `type: usage` evidence entries citing `/ship`, `/release`, and `coding-agent`.

---

## Implementation Approach

### Architecture

The lifecycle is a **declarative schema plus a stateless validator**. The `status:` field and its `evidence:` block live in `SKILL.md` frontmatter. `scripts/lint-skill.sh` is the single validator; every consumer path (`/new-skill` authoring, `/refresh-command --lint-skills` review, `scripts/eval.sh` CI) invokes that one script. The manifest and catalog carry a rendered mirror of the state, never a second source of truth.

```text
SKILL.md frontmatter (authoritative)
   status: + evidence:
        │
        ├──► lint-skill.sh ──► earned-state validation ──► /new-skill, /refresh-command, eval.sh
        │
        └──► manifest.yaml status: (render mirror) ──► gen-skill.sh ──► SKILL.md catalog Status column
```

### Earned-State Model

The lint never sees history, so "transition legality" is expressed as evidence thresholds:

- `candidate`: 0+ evidence entries.
- `proven`: ≥3 well-formed evidence entries.
- `promoted`: `proven` bar + ≥1 `type: promotion` entry.

Each state's bar is a strict superset of the one below, so the declared state is provably earned from the frontmatter alone.

### Validation Strategy

This repository has no application test suite. Verification is contract-and-script based:

- failing-first fixtures for each lifecycle rule, driven through `lint-skill.sh`
- `bash scripts/lint-skill.sh skills/*/SKILL.md`
- `bash scripts/eval.sh --check=skill-lifecycle` and `bash scripts/eval.sh`
- `bash scripts/gen-skill.sh --check`
- `bash scripts/install.sh --dry-run`
- targeted searches confirming no lifecycle logic leaked into `commands/refresh-command.md`

---

## Files in Scope

### Primary

- `skills/<name>/SKILL.md` — the `status:` field and `evidence:` block contract (schema definition)
- `commands/new-skill.md` — scaffold `status: candidate`
- `scripts/lint-skill.sh` — lifecycle hygiene checks
- `scripts/gen-skill.sh` — `Status` column in the catalog
- `.writ/manifest.yaml` — skills-schema comment + `status:` on `conventional-commits` (SHARED-ADDITIVE registry)
- `.writ/docs/skills.md` — lifecycle section (SHARED-ADDITIVE; distinct region)
- `.writ/decision-records/adr-014-skill-lifecycle.md` (new)
- `skills/conventional-commits/SKILL.md` — set `status: proven` with evidence

### Supporting Validation

- `scripts/eval.sh` — `skill-lifecycle` check (one function + one `CHECKS` entry; SHARED-ADDITIVE)
- lifecycle lint fixtures (disposable, under a temp/fixtures path)
- `SKILL.md` (regenerated catalog)
- `.writ/specs/2026-07-10-skill-lifecycle/uat-plan.md` (generated after implementation)

---

## Story Plan

1. **Skill lifecycle schema + ADR** — Dependencies: None
2. **Lifecycle hygiene lint** — Dependencies: Story 1
3. **Authoring + catalog wiring** — Dependencies: Stories 1, 2

---

## Deliverables

- [ ] `status:` field contract defined with a closed three-state vocabulary
- [ ] `evidence:` block schema finalized (date/type/ref/note) for downstream consumption
- [ ] Earned-state thresholds documented (candidate/proven/promoted; three-success rule)
- [ ] `adr-014-skill-lifecycle.md` recorded, extending ADR-009
- [ ] `.writ/manifest.yaml` skills-schema comment updated; `conventional-commits` mirror set to `proven`
- [ ] `scripts/lint-skill.sh` enforces status presence, vocabulary, thresholds, promotion record, and evidence shape
- [ ] `scripts/eval.sh` `skill-lifecycle` check registered with failing-first fixtures
- [ ] `/new-skill` scaffolds `status: candidate` in temp lint file, written file, and manifest entry
- [ ] `scripts/gen-skill.sh` renders a `Status` column; catalog regenerated and `--check` clean
- [ ] `.writ/docs/skills.md` lifecycle section added (stale extraction line left untouched)
- [ ] `skills/conventional-commits/SKILL.md` set to `status: proven` with three usage evidence entries
- [ ] Schema and lint contract stable enough for `2026-07-10-skill-extraction` to consume unchanged

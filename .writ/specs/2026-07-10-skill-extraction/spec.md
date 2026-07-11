# Skill Extraction from High-Traffic Commands

> **Status:** Completed ✅
> **Created:** 2026-07-10
> **Owner:** @AdamSellke
> **Phase:** 7 — Compounding Layer
> **Dependencies:** [2026-07-10-skill-lifecycle]
> **Source:** `.writ/product/roadmap.md` Phase 7 — feature "Skill extraction from high-traffic commands"
> **Governing ADRs:** `adr-009-command-agent-skill-boundary.md`

---

## Specification Contract

**Deliverable:** Extract a committed set of four reusable capabilities out of Writ's heaviest commands into standalone skills (`skills/<name>/SKILL.md`), shrink those commands toward orchestration that loads each skill via `Read skills/<name>/SKILL.md`, and retire the weak `/explain-code` command — its ~10 durable lines (the explanation template) become one of the four skills. Every newly extracted skill is born `status: candidate` per the skill-lifecycle schema and is boundary-lint-clean under `scripts/lint-skill.sh`.

**Origin:** Phase 7 — Compounding Layer in `.writ/product/roadmap.md`, feature "Skill extraction from high-traffic commands," which explicitly also resolves the weak content in `/explain-code` (retire the command; its durable lines become a skill). Governed by ADR-009's command/agent/skill boundary.

**Must Include:** Four extracted skills — `code-explanation` (from the retired `/explain-code`), `tdd-cycle` (from `commands/implement-story.md`), `error-rescue-mapping` (from `commands/create-spec.md`), and `safe-refactor-loop` (from `commands/refactor.md`). Each has at least one wired consumer that loads it explicitly, is registered in `.writ/manifest.yaml`, appears in the regenerated root `SKILL.md`, and passes the boundary lint. `/explain-code` is deleted and absent from every active surface.

**Hardest Constraint:** This spec must not redefine the skill lifecycle. The `status:` frontmatter field, its allowed values, and the lint's lifecycle rules are owned by `2026-07-10-skill-lifecycle`. Extracted skills *consume* that schema by declaring `status: candidate` with an initial evidence note. If skill-lifecycle has not landed the `status` field, this spec cannot begin — the extracted skills would be born without a lifecycle state.

### Experience Design

- **Entry point:** The maintainer runs the extraction as a sequence of stories; there is no new user-invoked command. The user-visible surface change is that `/explain-code` disappears and its capability is available as a skill the agent loads on demand.
- **Happy path:** For each source command, isolate the durable capability prose → author `skills/<name>/SKILL.md` (`status: candidate`) → lint clean → wire the consumer to `Read` it → shrink the command to a `Read`-and-orchestrate reference → regenerate the catalog → verify no dangling references.
- **Moment of truth:** A high-traffic command shrinks measurably, its extracted capability lints clean, its consumer loads the skill deterministically, and `scripts/gen-skill.sh --check` reports the catalog is in sync.
- **Feedback model:** `bash scripts/lint-skill.sh skills/*/SKILL.md` proves boundary hygiene; `bash scripts/gen-skill.sh --check` proves catalog sync; targeted greps prove `/explain-code` is absent from active surfaces; `bash scripts/install.sh --dry-run` proves the new skills fan out to all three platforms.
- **Error experience:** A skill whose body contains orchestration (`Read commands/`, `Read skills/`, `Task(`, or a line starting with `/command`) fails the lint and blocks its story until the body is pure capability prose. A stale catalog fails `--check` and blocks finalization. A dangling `/explain-code` reference fails the retirement grep.
- **Scope-degradation decisions:** Padding the set to five skills without a genuine second consumer is a scope violation, not a bonus. If a candidate extraction has no reuse and no shrink value, the honest outcome is to leave it in its command and say so.

### Business Rules

1. The extraction set is exactly four skills. `/ship` is named in the roadmap as a high-traffic candidate but has already been extracted (`conventional-commits`); no further extraction is warranted, and that finding is documented rather than padded.
2. Every extracted skill declares `status: candidate` and an initial evidence note in its frontmatter, consuming the schema owned by `2026-07-10-skill-lifecycle`. This spec never defines, renames, or reorders lifecycle states.
3. Every extracted skill body is capability prose only — it must pass `scripts/lint-skill.sh` with zero violations. Skills do not invoke commands, chain other skills, spawn subagents, or start a line with a slash command.
4. Every extracted skill is loaded explicitly (`disable-model-invocation: true`) by at least one wired consumer via `Read skills/<name>/SKILL.md`. A skill with no consumer is not shippable in this spec.
5. "In real use" is satisfied for this spec by wiring live consumers to load the skill. Promotion from `candidate` to `proven` requires transcript evidence and is owned by the lifecycle spec, not this one.
6. `/explain-code` is deleted, not archived in place. It is removed from `.writ/manifest.yaml`, the regenerated root `SKILL.md`, both `commands/status.md` allowlists, `README.md`, all adapters, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, and `commands/new-command.md`, and its capability is redirected to `skills/code-explanation/SKILL.md`.
7. Command shrink must preserve every behavior the command still owns. Extraction moves *how to do the capability well* into the skill; the command retains *when to invoke it and with what data*.
8. `.writ/manifest.yaml` `skills:` entries remain alphabetically ordered and additive — this spec shares that registry with `2026-07-10-skill-lifecycle` and runs after it, so it sees the `status`-aware schema.
9. The root `SKILL.md` catalog is generated, never hand-edited. Any catalog change lands via `bash scripts/gen-skill.sh` and is proven with `--check`.
10. Retirement verification uses allowlisted greps: historical specs, ADRs, changelog history, and roadmap history may still name `/explain-code`; active product surfaces may not.

### Success Criteria

1. Four skills exist under `skills/` (`code-explanation`, `tdd-cycle`, `error-rescue-mapping`, `safe-refactor-loop`), each with `status: candidate`, and `bash scripts/lint-skill.sh skills/*/SKILL.md` exits clean.
2. Each of the four skills has at least one consumer wired to `Read skills/<name>/SKILL.md`, and the source command is measurably shorter than its pre-extraction line count.
3. `/explain-code` is absent from every active surface: `commands/`, `.writ/manifest.yaml`, generated `SKILL.md`, `commands/status.md` allowlists, `README.md`, adapters, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, and `commands/new-command.md`. Allowlisted historical references remain.
4. `bash scripts/gen-skill.sh --check` reports the root catalog is in sync with the manifest after all four skills are registered and `/explain-code` is removed.
5. `bash scripts/install.sh --dry-run` shows all four new skills fanning out to `.cursor/`, `.claude/`, and Codex install targets alongside `conventional-commits`.
6. `.writ/docs/skills.md` gains an extraction-patterns section, and its stale line 3 ("No production skills extracted yet") is corrected to reflect the shipped extractions.
7. The four-skill decision is documented honestly: the set is committed at four, ship's non-extraction is explained, and each skill's reuse justification is recorded.

### Scope Boundaries

**Included:**
- Four `skills/<name>/SKILL.md` capability files, each `status: candidate` and lint-clean
- Retirement and deletion of `commands/explain-code.md` and every active reference
- Consumer wiring: `Read skills/<name>/SKILL.md` in the commands and agents that use each capability
- Command shrink for `create-spec`, `implement-story`, and `refactor` toward orchestration
- `.writ/manifest.yaml` skill registration (additive) and `/explain-code` removal
- Root `SKILL.md` regeneration and `--check` verification
- `.writ/docs/skills.md` extraction-patterns section and stale-line correction
- Install/update dry-run fanout verification and boundary-lint verification

**Excluded:**
- Defining, renaming, or reordering skill lifecycle states (owned by `2026-07-10-skill-lifecycle`)
- Promoting any skill from `candidate` to `proven` (requires transcript evidence; later work)
- Extracting a fifth skill purely to hit the roadmap's "3–5" upper bound
- New extraction from `/ship` (already extracted as `conventional-commits`)
- Evidence-bound `/refresh-command` refinement (separate Phase 7 feature)
- Knowledge consolidation (separate Phase 7 feature)
- Any change to `scripts/lint-skill.sh` grammar or `scripts/gen-skill.sh` logic
- New user-invoked commands or platform APIs

### Technical Concerns

- **Lifecycle dependency is hard, not soft.** Without the `status:` field from `2026-07-10-skill-lifecycle`, extracted skills cannot be born `candidate`. If that spec slips, this spec blocks — it must not invent a placeholder schema.
- **`code-explanation` has no command wrapper after retirement.** Because Writ standardizes on `disable-model-invocation: true`, a skill nothing loads is dead. The retirement must wire a genuine consumer (`commands/research.md`) so the capability remains reachable, not orphaned.
- **Catalog drift is silent until `--check`.** Registering a skill in the manifest without regenerating `SKILL.md` produces a catalog that lies. Every story that touches the manifest must end with regeneration; finalization runs `--check`.
- **The boundary lint is unforgiving of orchestration prose.** Source-command language often says "then run `/review`" or "`Read commands/…`". Extraction must rewrite those into capability prose (referencing the command by name in running text, never as a line-leading slash command or a `Read` directive) or the lint fails.
- **`ship` is a trap for padding.** The roadmap names it as a candidate. The honest reading is that its extraction already happened. Documenting the non-extraction is a deliverable, not a gap.

### Recommendations

- Follow the `conventional-commits` precedent exactly: body sections `# Title` → `## Purpose` → `## When to Use` → `## How to Apply` → `## Examples`, `disable-model-invocation: true`, verb-phrase description.
- Sequence the three independent extractions (Stories 1–3) first, then land the fourth skill plus all finalization (catalog, docs, dry-runs) in Story 4 so the catalog is regenerated once, authoritatively, at the end.
- For each command shrink, replace the extracted section with a one-paragraph `Read skills/<name>/SKILL.md` orchestration note stating what data the command supplies and what the skill owns — mirroring `commands/ship.md` line ~275.
- Keep `error-rescue-mapping`'s second consumer (`/review`) as a documented future wiring, not an in-scope change, to avoid scope creep beyond the owned command set.
- Verify retirement the way Ralph retirement was verified in the phase6 spec: allowlisted greps over active surfaces, catalog `--check`, and install/update dry-runs.

### Cross-Spec Review

`2026-07-10-skill-lifecycle` is a **binding prerequisite**. It owns the `status:` frontmatter schema (`candidate` / `proven` / `promoted`), the initial-evidence-note convention, and any lifecycle-hygiene checks added to `scripts/lint-skill.sh`. This spec consumes that schema and must run *after* it. Both specs write to `.writ/manifest.yaml` `skills:` entries — that registry is **shared and additive**: lifecycle establishes the `status`-aware schema and `/new-skill` default; this spec appends four `status: candidate` entries under it. There is no ordering conflict on the manifest because both changes are additive and alphabetical, but this spec must see the lifecycle schema first. The `2026-05-03-skills-foundation` spec (shipped) established the primitive, the lint, the catalog generator, and the `conventional-commits` pilot — it is an implementation reference, not competing work.

---

## Experience Design

### Primary User Journey

1. The maintainer confirms `2026-07-10-skill-lifecycle` has landed the `status:` field, then begins the extraction stories.
2. For each source command, the durable capability prose is identified and lifted into `skills/<name>/SKILL.md` with `status: candidate` and an initial evidence note.
3. `scripts/lint-skill.sh` is run on the new skill; it must pass before the story proceeds.
4. The consuming command or agent is rewired to `Read skills/<name>/SKILL.md`, and the source section shrinks to an orchestration note.
5. The skill is registered in `.writ/manifest.yaml` and the catalog is regenerated.
6. `/explain-code` is deleted and every active reference is rerouted or removed.
7. Finalization regenerates the catalog once more, runs `--check`, the lint over all skills, and the install/update dry-runs, and fixes the stale `skills.md` line.

### State Catalog

| State | User-visible behavior |
|---|---|
| Lifecycle schema absent | Block: extraction cannot start until `status:` exists; report the missing prerequisite |
| Capability identified | Show the source section, the target skill name, and the consumer to wire |
| Skill lints dirty | Block the story with the exact lint violation and remediation until the body is capability prose |
| Skill lints clean | Proceed to consumer wiring and command shrink |
| Consumer unwired | A `candidate` skill nothing loads is flagged as not shippable |
| `/explain-code` still referenced | Retirement grep fails and names the surviving active reference |
| Catalog stale | `gen-skill.sh --check` fails; regenerate before finalization |
| All green | Four skills registered, catalog in sync, dry-runs clean, `/explain-code` gone |

### Interaction and Output Rules

- No new UI or command surface is introduced. The only user-facing change is the disappearance of `/explain-code`.
- Every skill load is explicit and traceable in transcripts (`Read skills/<name>/SKILL.md`).
- Command shrink notes name the skill and the data the command supplies; they never duplicate the skill's prose.
- Verification output is terminal-oriented: lint results, `--check` status, dry-run diffs, and grep results.
- Missing lifecycle schema is a hard block, distinct from a lint failure — the former stops the spec, the latter stops one story.

---

## Detailed Requirements

### R1 — Committed Extraction Set

- The set is exactly four skills: `code-explanation`, `tdd-cycle`, `error-rescue-mapping`, `safe-refactor-loop`.
- Each skill has a documented source command, a reuse justification, and at least one wired consumer.
- `/ship` is explicitly out of scope for new extraction; its prior `conventional-commits` extraction is the documented precedent.
- No fifth skill is added solely to reach the roadmap's "3–5" upper bound.

### R2 — Lifecycle Schema Consumption

- Every extracted skill declares `status: candidate` and an initial evidence note in its frontmatter, using the exact field and value vocabulary defined by `2026-07-10-skill-lifecycle`.
- This spec does not define, rename, reorder, or lint-enforce lifecycle states.
- If the `status:` field is unavailable, extraction does not begin.

### R3 — Retire `/explain-code` into `code-explanation`

- Author `skills/code-explanation/SKILL.md` (`status: candidate`) carrying the Purpose → How It Works → Context → Diagrams (conditional) → Complexity Notes (conditional) explanation template, rewritten as capability prose.
- Delete `commands/explain-code.md`.
- Wire `commands/research.md` to `Read skills/code-explanation/SKILL.md` as the redirect target for the retired command's capability, so the skill has a live consumer despite `disable-model-invocation: true`.
- Remove `/explain-code` from `.writ/manifest.yaml`, both `commands/status.md` allowlists, `README.md`, `adapters/cursor.md`, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, and `commands/new-command.md`.
- Regenerate root `SKILL.md`; prove `/explain-code`'s absence from active surfaces with allowlisted greps.

### R4 — Extract `tdd-cycle` from `/implement-story`

- Author `skills/tdd-cycle/SKILL.md` (`status: candidate`) carrying the red → green → refactor discipline as capability prose.
- Wire consumers to `Read skills/tdd-cycle/SKILL.md`: `commands/implement-story.md` (Gate 1), `agents/coding-agent.md`, and `agents/testing-agent.md`.
- Shrink the Gate 1 TDD guidance in `commands/implement-story.md` to an orchestration note that names the skill and the context it passes.
- The skill body must not reference gates, agents, or command orchestration — those stay in the consumers.

### R5 — Extract `error-rescue-mapping` from `/create-spec`

- Author `skills/error-rescue-mapping/SKILL.md` (`status: candidate`) carrying the Error & Rescue Map + Shadow Paths + Interaction Edge Cases tables and the `[UNPLANNED]` marker technique as capability prose.
- Wire `commands/create-spec.md` Step 2.8 to `Read skills/error-rescue-mapping/SKILL.md`; shrink the inline table guidance to an orchestration note.
- Document `/review` as a natural future second consumer (identical table structures) without wiring it in this spec.
- The skill must express the "describe what the user sees, not what the system does" principle and the plan-vs-actual drift-signal framing.

### R6 — Extract `safe-refactor-loop` from `/refactor`

- Author `skills/safe-refactor-loop/SKILL.md` (`status: candidate`) carrying the green-baseline → surgical change → verify (tests + types + lint) → commit-or-revert → one-concern-per-commit discipline as capability prose.
- Wire `commands/refactor.md` Phase 3 to `Read skills/safe-refactor-loop/SKILL.md`; shrink the execution-cycle prose to an orchestration note.
- Record honestly that `safe-refactor-loop` is the extraction with the thinnest current reuse (one consumer): the justification is the durable, transferable behavior-preserving-change discipline plus command shrink, and `/prototype` is named as a plausible future consumer.

### R7 — Consumer Wiring and Command Shrink

- Every consumer loads its skill with a literal `Read skills/<name>/SKILL.md` directive at the point of use, following the `commands/ship.md` line ~275 pattern.
- Each shrink note states: which skill is loaded, what the skill owns (*how*), and what the command retains (*when/with what data*).
- Source commands are measurably shorter after extraction; the shrink is a deliverable, not a side effect.
- No consumer duplicates the skill's prose; the skill is the single source of truth for its capability.

### R8 — Catalog, Manifest, and Reference Integrity

- `.writ/manifest.yaml` gains four alphabetical `skills:` entries (`code-explanation`, `error-rescue-mapping`, `safe-refactor-loop`, `tdd-cycle`) and loses the `explain-code` command entry.
- Root `SKILL.md` is regenerated via `bash scripts/gen-skill.sh`; `bash scripts/gen-skill.sh --check` passes at finalization.
- `bash scripts/lint-skill.sh skills/*/SKILL.md` exits clean across all skills.
- `bash scripts/install.sh --dry-run` and `bash scripts/update.sh --dry-run` show the four skills fanning out and no `explain-code` command copied.
- `.writ/docs/skills.md` gains an extraction-patterns section and its stale line 3 is corrected.
- Allowlisted greps confirm `/explain-code` survives only in historical specs, ADRs, changelog, and roadmap history.

---

## Implementation Approach

### Architecture

Extraction is a mechanical, repeatable transform applied per source command:

```text
source command section
        │
        ▼
identify durable capability prose  (the "how", reusable across consumers)
        │
        ▼
author skills/<name>/SKILL.md  (status: candidate, verb-phrase desc)
        │
        ▼
lint-skill.sh  ──► clean? ──no──► rewrite orchestration prose into capability prose
        │ yes
        ▼
wire consumer:  Read skills/<name>/SKILL.md   (the "when/with what data" stays here)
        │
        ▼
shrink source section to an orchestration note
        │
        ▼
register in manifest (alphabetical) → regenerate catalog
```

`code-explanation` is the one variant: instead of shrinking a section, the entire `commands/explain-code.md` is deleted and its references are rerouted, with `commands/research.md` adopting the capability as its consumer.

### Skill Body Convention

All four skills follow the shipped `conventional-commits` shape: YAML frontmatter (`name`, `description` as a verb-phrase, `disable-model-invocation: true`, plus the lifecycle `status: candidate` and an evidence note), then `# Title` → `## Purpose` → `## When to Use` → `## How to Apply` → `## Examples`. Bodies are capability prose; code blocks may show whatever examples need (they are exempt from the body lint).

### Validation Strategy

This repository has no application test suite. Verification is lint-, catalog-, and grep-based:

- `bash scripts/lint-skill.sh skills/*/SKILL.md` — boundary hygiene for every skill
- `bash scripts/gen-skill.sh --check` — catalog in sync with manifest
- `bash scripts/install.sh --dry-run` and `bash scripts/update.sh --dry-run` — fanout and no orphaned command
- `bash scripts/eval.sh` — repository-wide checks remain clean
- allowlisted greps — `/explain-code` absent from active surfaces; each skill referenced by its wired consumer

---

## Files in Scope

### New Skills

- `skills/code-explanation/SKILL.md` (new)
- `skills/tdd-cycle/SKILL.md` (new)
- `skills/error-rescue-mapping/SKILL.md` (new)
- `skills/safe-refactor-loop/SKILL.md` (new)

### Source Commands (extract + shrink)

- `commands/create-spec.md` — Step 2.8 extraction, wire `error-rescue-mapping`
- `commands/implement-story.md` — Gate 1 extraction, wire `tdd-cycle`
- `commands/refactor.md` — Phase 3 extraction, wire `safe-refactor-loop`
- `commands/ship.md` — no new extraction; documented non-extraction (already yielded `conventional-commits`)

### Consumer Wiring

- `commands/research.md` — wire `code-explanation` (retirement redirect target)
- `agents/coding-agent.md` — wire `tdd-cycle`
- `agents/testing-agent.md` — wire `tdd-cycle`

### Retirement (`/explain-code`)

- `commands/explain-code.md` — DELETE
- `.writ/manifest.yaml` — remove `explain-code`; add four `skills:` entries (SHARED-ADDITIVE with skill-lifecycle)
- `SKILL.md` (root catalog) — regenerated via `gen-skill.sh`
- `commands/status.md` — remove `/explain-code` from both allowlists (lines ~184, ~344)
- `README.md` — remove `/explain-code` row (line ~145)
- `adapters/cursor.md` — remove `/explain-code` tree entry (line ~48)
- `claude-code/CLAUDE.md` — remove `/explain-code` row (line ~28)
- `codex/AGENTS.md.template` — remove `/explain-code` row (line ~65)
- `commands/new-command.md` — remove `explain-code` from the example category list (line ~146)

### Documentation

- `.writ/docs/skills.md` — extraction-patterns section; correct stale line 3

### Supporting Validation

- `scripts/lint-skill.sh` (invoked, not modified)
- `scripts/gen-skill.sh` (invoked with `--check`, not modified)
- `scripts/install.sh`, `scripts/update.sh` (invoked `--dry-run`, not modified)
- `scripts/eval.sh` (invoked, not modified)

---

## Story Plan

1. **Retire `/explain-code` into a skill** — Dependencies: None (within spec)
2. **Extract `tdd-cycle` from `/implement-story`** — Dependencies: None (within spec)
3. **Extract `error-rescue-mapping` from `/create-spec`** — Dependencies: None (within spec)
4. **Extract `safe-refactor-loop` and finalize** — Dependencies: Stories 1–3

All four stories share the binding cross-spec prerequisite `2026-07-10-skill-lifecycle`.

---

## Deliverables

- [x] `skills/code-explanation/SKILL.md` authored (`status: candidate`), lint-clean, consumed by `commands/research.md`
- [x] `skills/tdd-cycle/SKILL.md` authored (`status: candidate`), lint-clean, consumed by `implement-story` + coding/testing agents
- [x] `skills/error-rescue-mapping/SKILL.md` authored (`status: candidate`), lint-clean, consumed by `commands/create-spec.md`
- [x] `skills/safe-refactor-loop/SKILL.md` authored (`status: candidate`), lint-clean, consumed by `commands/refactor.md`
- [x] `commands/explain-code.md` deleted and absent from every active surface
- [~] Source commands measurably shrunk toward orchestration — `create-spec` 912 → 890, `refactor` 205 → 186, `/explain-code` deleted entirely; `implement-story` net-neutral (974 → 974, an orchestrator with no inline TDD block — see Story 2 note)
- [x] `.writ/manifest.yaml` carries four alphabetical `skills:` entries and no `explain-code` command
- [x] Root `SKILL.md` regenerated; `gen-skill.sh --check` passes
- [x] `lint-skill.sh skills/*/SKILL.md` clean; `install.sh`/`update.sh` dry-runs behave as baseline (source-repo guard, no new failures); `eval.sh` clean (0 findings)
- [x] `.writ/docs/skills.md` extraction-patterns section added; stale line 3 corrected
- [x] Four-skill decision, ship non-extraction, and per-skill reuse justifications documented

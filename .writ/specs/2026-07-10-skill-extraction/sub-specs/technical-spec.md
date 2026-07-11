# Technical Specification: Skill Extraction from High-Traffic Commands

> **Parent:** `../spec.md`
> **Status:** Completed ✅
> **Stories:** 1–4

## Architecture Summary

This spec applies one repeatable transform — *lift a durable capability out of a command into a `SKILL.md`, wire the consumer to load it, shrink the command* — across four sites, plus a retirement variant that deletes `/explain-code` and reroutes its references. No scripts are modified; the existing boundary lint (`scripts/lint-skill.sh`) and catalog generator (`scripts/gen-skill.sh`) are the guardrails.

```text
2026-07-10-skill-lifecycle  (prerequisite: status: field exists)
          │
          ▼
   per-command extraction transform
          │
   ┌──────┼───────────────┬───────────────┐
   ▼      ▼               ▼               ▼
code-   tdd-cycle    error-rescue-   safe-refactor-
explan.  (S2)         mapping (S3)    loop (S4)
 (S1)                                     │
   │      │               │               │
   └──────┴───────┬───────┴───────────────┘
                  ▼
   register (manifest, alphabetical) → regenerate SKILL.md
                  ▼
   S4 finalize: gen-skill.sh --check · lint-skill.sh · install/update --dry-run · docs
```

## Design Decisions

### D1 — The Extraction Set Is Committed at Four

The roadmap says "3–5 skills." This spec commits to **four**, named and sourced:

| Skill | Source | Primary consumer(s) | Reuse justification |
|---|---|---|---|
| `code-explanation` | retired `commands/explain-code.md` (Step 3 template) | `commands/research.md` | The Purpose → How It Works → Context → Diagrams → Complexity-Notes template is a general explanation capability any agent can wield |
| `tdd-cycle` | `commands/implement-story.md` Gate 1 | `implement-story`, `coding-agent`, `testing-agent` | Strongest reuse: three live consumers share the red→green→refactor discipline (ADR-009 names it) |
| `error-rescue-mapping` | `commands/create-spec.md` Step 2.8 | `create-spec` (now); `/review` (future) | Error & Rescue / Shadow Path / edge-case tables are shared with `/review`'s output by design |
| `safe-refactor-loop` | `commands/refactor.md` Phase 3 | `refactor` (now); `/prototype` (future) | Thinnest reuse; justified by durable behavior-preserving-change discipline + command shrink |

`/ship` is **not** a source: its high-traffic capability was already extracted as `conventional-commits`. Documenting that non-extraction is a deliverable (R1), not a gap. No fifth skill is invented to reach five.

### D2 — Lifecycle Schema Is Consumed, Never Redefined

Frontmatter for every extracted skill:

```yaml
---
name: <kebab-case-name>
description: "<verb-phrase>"
disable-model-invocation: true
status: candidate
status_evidence: "Extracted <date> from <source command>; candidate until consumer transcripts prove reuse."
---
```

The `status` field, its allowed values, the evidence-note key, and any lifecycle-hygiene lint rule are owned by `2026-07-10-skill-lifecycle`. This spec references that schema and matches its exact key names. If the field is unavailable at implementation time, extraction does not begin (Shadow Paths → *Lifecycle prerequisite* → Nil Input).

### D3 — Skill Bodies Are Capability Prose Only

`scripts/lint-skill.sh` rejects, outside code blocks and within the first 200 non-indented characters of a paragraph:

- `Read commands/` — command invocation
- `Read skills/` — skill chaining
- `Task(` — subagent dispatch
- a line **starting** with `/command` — slash-command invocation

Extraction rewrites orchestration language accordingly. Examples:

| Source prose (orchestration) | Skill prose (capability) |
|---|---|
| "then send errors back to the coding agent" | "when a check fails, feed the specific failures back into the next change" |
| "`Read commands/review.md` for drift format" | "these tables mirror the reviewer's output, enabling plan-vs-actual comparison" |
| "`/review` compares this to code" | "a reviewer compares this map to the code's actual handling; gaps are drift signals" |

The consumer keeps the orchestration; the skill keeps the craft. Code blocks in examples are lint-exempt, so worked examples may show tables, commit sequences, or diagrams freely.

### D4 — Explicit Load, Explicit Consumer

All skills are `disable-model-invocation: true`, so platforms never ambient-load them. Each is reachable only through a literal `Read skills/<name>/SKILL.md` in a consumer, placed at the point of use, mirroring `commands/ship.md` line ~275 and `agents/coding-agent.md` line ~111. A skill with no consumer is dead weight and fails R4. This is why retiring `/explain-code` must adopt `commands/research.md` as `code-explanation`'s consumer — deleting the command would otherwise orphan the capability.

### D5 — Command Shrink Note Shape

Each shrunk section becomes a short orchestration note of the form:

> **`<Capability>`:** `Read skills/<name>/SKILL.md` for `<what the skill owns — the "how">`. This command owns `<what stays — when to invoke, what data to pass>`.

The note names the skill, states the *how/when* split, and never restates the skill's prose. The source command's line count drops; the drop is recorded per story as evidence of shrink (R7).

### D6 — Retirement Is Deletion Plus Reroute

`/explain-code` retirement differs from the other three (which shrink in place):

1. Delete `commands/explain-code.md`.
2. Lift its Step 3 template into `skills/code-explanation/SKILL.md`.
3. Wire `commands/research.md` to `Read` the skill.
4. Reroute/remove every active reference (manifest, root catalog, status allowlists ×2, README, adapters, CLAUDE.md, AGENTS.md.template, new-command.md).
5. Regenerate the catalog; prove absence with allowlisted greps.

Allowlist for the retirement grep — these may still name `/explain-code`:

- `.writ/specs/**` (historical specs, e.g. `2026-03-22-suite-quality-polish`)
- `.writ/decision-records/**`
- `.writ/product/roadmap.md` history and `CHANGELOG.md` history
- `.writ/explanations/**`

### D7 — Manifest Is Shared-Additive; Catalog Is Generated

Both this spec and `2026-07-10-skill-lifecycle` append to `.writ/manifest.yaml` `skills:`. The registry is additive and alphabetical; lifecycle establishes the `status`-aware schema and `/new-skill` default, this spec appends four entries under it. The `explain-code` **command** entry is removed here. The root `SKILL.md` is regenerated with `bash scripts/gen-skill.sh` and never hand-edited; `--check` is the sync gate at finalization (Story 4).

Final alphabetical `skills:` order after this spec: `code-explanation`, `conventional-commits`, `error-rescue-mapping`, `safe-refactor-loop`, `tdd-cycle`.

## File × Story Matrix

| File | S1 | S2 | S3 | S4 |
|---|---:|---:|---:|---:|
| `skills/code-explanation/SKILL.md` (new) | ✓ |  |  |  |
| `skills/tdd-cycle/SKILL.md` (new) |  | ✓ |  |  |
| `skills/error-rescue-mapping/SKILL.md` (new) |  |  | ✓ |  |
| `skills/safe-refactor-loop/SKILL.md` (new) |  |  |  | ✓ |
| `commands/explain-code.md` (DELETE) | ✓ |  |  |  |
| `commands/research.md` (wire consumer) | ✓ |  |  |  |
| `commands/implement-story.md` (shrink + wire) |  | ✓ |  |  |
| `agents/coding-agent.md` (wire) |  | ✓ |  |  |
| `agents/testing-agent.md` (wire) |  | ✓ |  |  |
| `commands/create-spec.md` (shrink + wire) |  |  | ✓ |  |
| `commands/refactor.md` (shrink + wire) |  |  |  | ✓ |
| `commands/ship.md` (document non-extraction) |  |  |  | ✓ |
| `.writ/manifest.yaml` | ✓ | ✓ | ✓ | ✓ |
| `SKILL.md` (regenerate) | ✓ | ✓ | ✓ | ✓ |
| `commands/status.md` (allowlists ×2) | ✓ |  |  |  |
| `README.md` | ✓ |  |  |  |
| `adapters/cursor.md` | ✓ |  |  |  |
| `claude-code/CLAUDE.md` | ✓ |  |  |  |
| `codex/AGENTS.md.template` | ✓ |  |  |  |
| `commands/new-command.md` | ✓ |  |  |  |
| `.writ/docs/skills.md` |  |  |  | ✓ |

## Error & Rescue Map

Scripts and parsing are touched (catalog regeneration, manifest edits, lint). Planned handling:

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Read lifecycle `status:` schema | Field not yet defined by prerequisite spec | Hard block; report missing prerequisite; do not invent a placeholder schema | Confirm `status:` present in `conventional-commits` or lifecycle artifact before Story 1 |
| Author skill body | Orchestration prose trips the lint (`Read`, `Task(`, slash-command line) | Block story; rewrite as capability prose per D3; re-run `lint-skill.sh` | Run `lint-skill.sh <new>` on each skill before wiring |
| Parse manifest after edit | Malformed YAML, duplicate `name`, non-alphabetical order | `gen-skill.sh` fails to parse or emits wrong catalog; fix entry; re-run | `gen-skill.sh --check` after each manifest edit |
| Regenerate catalog | Manifest edited but `SKILL.md` not regenerated | `--check` reports drift; regenerate before finalization | `gen-skill.sh --check` at Story 4 |
| Delete `commands/explain-code.md` | A live reference survives (allowlist too broad/narrow) | Retirement grep fails and names the path; reroute or add to allowlist deliberately | Allowlisted grep over active surfaces |
| Wire consumer | Skill referenced by wrong path or not at point of use | `Read` path grep finds no match for the skill; add the directive | Grep each skill's path in its consumer |
| Shrink command | Removed prose the command still owns (behavior loss) | Restore the *when/with-what-data* orchestration; only *how* moves to the skill | Diff review against D5 note shape |
| Install fanout | New skill folder not copied to a platform target | `install.sh --dry-run` omits the skill; verify overlay logic covers `skills/*` | `install.sh`/`update.sh --dry-run` at Story 4 |

No `[UNPLANNED]` operations remain. No external services are touched; all failure modes are local file, parse, or lint failures.

## Shadow Paths

Focus on retirement risk: broken refs, catalog drift, install fanout.

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Lifecycle prerequisite | `status:` field present → extraction proceeds | Prerequisite spec not landed → hard block, no skills authored | `status_evidence` empty → author requires an initial note | Schema fields renamed upstream → match new names; never fork the schema |
| Extraction transform | Capability lifted → lint clean → consumer wired → command shrunk | No durable capability found → leave in command, document non-extraction | Section already thin → still may extract for reuse (tdd-cycle) | Lint dirty → rewrite orchestration prose, re-lint |
| `/explain-code` retirement | Deleted; `code-explanation` consumed by `/research`; refs rerouted | No consumer wired → skill orphaned under `disable-model-invocation`; block | No new-command example list entry → skip that reroute | Surviving active reference → grep fails with the path |
| Catalog sync | Manifest additive → regenerate → `--check` passes | Empty `skills:` (not our case) → generator skips section | Skill added, catalog stale → `--check` fails | Duplicate/misordered `name` → generator error; fix and re-run |
| Install fanout | Four skill folders overlay to all three platforms | No skills (not our case) → clean no-op | Sidecar-less skill → `SKILL.md` only, still copied | `explain-code` command still copied → dry-run shows it; complete deletion |
| Docs correction | `skills.md` extraction section added; line 3 corrected | No extractions (not our case) → line 3 stays honest | Partial extraction → line 3 states count accurately | Stale line left uncorrected → success criterion 6 fails |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Two specs edit `.writ/manifest.yaml` `skills:` | Both additive and alphabetical; this spec runs after lifecycle and appends four entries |
| Skill name collides with a command/agent name | Names are unique across all primitives; `code-explanation` avoids colliding with the (deleted) `explain-code` command |
| Consumer already reads another skill | Additive `Read` directive at the new point of use (e.g. `coding-agent` already reads `conventional-commits`) |
| Reviewer sees a one-consumer skill (`safe-refactor-loop`) | Acceptable and documented; reuse is future (`/prototype`), shrink is present-tense value |
| `code-explanation` invoked with no target | Capability prose covers interactive target selection; orchestration stays in the consumer |
| History still names `/explain-code` | Not a failure; allowlist (D6) protects specs, ADRs, changelog, roadmap, explanations |

## Verification Commands

```bash
bash scripts/lint-skill.sh skills/*/SKILL.md
bash scripts/gen-skill.sh --check
bash scripts/install.sh --dry-run
bash scripts/update.sh --dry-run
bash scripts/eval.sh
```

Also grep active product surfaces for `/explain-code`, excluding `.writ/specs/`, `.writ/decision-records/`, `.writ/explanations/`, `CHANGELOG.md`, and roadmap history; and grep each skill's path in its wired consumer(s).

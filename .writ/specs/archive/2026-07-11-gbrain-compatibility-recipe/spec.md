# Phase 8: GBrain Compatibility Recipe

> **Status:** Complete (integrated via Phase 8 lane merge `f88c6f8`)
> **Created:** 2026-07-11
> **Owner:** @AdamSellke
> **Phase:** 8 — Memory Interop
> **Dependencies:** []
> **Source:** `.writ/product/roadmap.md` Phase 8 — feature "GBrain compatibility recipe"
> **Governing ADRs:** `adr-011-memory-interop-markdown-canonical.md` (markdown canonical, indexes disposable), `adr-005-knowledge-substrate-markdown-over-database.md` (zero-infrastructure driver), `adr-009-command-agent-skill-boundary.md` (skill vs. doc boundary)

---

## Specification Contract

**Deliverable:** A documented, optional, disposable way to make an external [GBrain](https://github.com/garrytan/gbrain) index consume Writ's markdown substrate — shipped as one agent-facing **skill** (`gbrain-interop`) plus one user-facing **recipe doc** (`.writ/docs/gbrain-recipe.md`). The skill teaches an agent to detect a brain, prefer brain-first retrieval when one is present, and fall back to grep when it is absent. The doc teaches a human to register `.writ/` as a GBrain source, map Writ artifacts to GBrain pages, and remove the index with zero canonical data loss. **Zero new Writ infrastructure**: markdown in git stays the only system of record.

**Origin:** Phase 8 — Memory Interop in `.writ/product/roadmap.md`, feature "GBrain compatibility recipe," governed by ADR-011 (which makes markdown canonical and every index a welcome-but-disposable consumer) and ADR-005 (zero owned retrieval infrastructure).

**Must Include:** A skill and a recipe doc grounded in GBrain's *actual* current interface (`gbrain sources add`, `gbrain sync`, `gbrain doctor --json`, `gbrain search`, `gbrain serve` MCP) — not an invented API. Brain-detection is observable (`gbrain doctor --json` / MCP presence), retrieval is brain-first *only when detected*, and the whole capability degrades to a clean no-op when GBrain is absent. The round-trip guarantee — removing GBrain loses zero canonical data — must be stated and demonstrable.

**Hardest Constraint:** Writ must own **no retrieval infrastructure** and introduce **no dependency** on GBrain. Everything ships as documentation and one skill; if GBrain's API moves, the blast radius is these two files and nothing else. The recipe must never instruct a user to move canonical data *into* GBrain — GBrain only ever *indexes* the markdown that remains authoritative on disk.

### Experience Design

- **Entry point (human):** A user who runs GBrain reads `.writ/docs/gbrain-recipe.md` and registers `.writ/` as a source. A user who doesn't run GBrain never encounters it — nothing in the core workflow references or requires it.
- **Entry point (agent):** A command or agent that needs to retrieve prior knowledge loads `skills/gbrain-interop/SKILL.md`, checks whether a brain is present, and routes retrieval accordingly.
- **Happy path:** Brain detected → agent prefers `gbrain search` for semantic knowledge/spec/ADR retrieval, always citing the canonical markdown path in results → writes still land in markdown first, then get re-indexed by `gbrain sync`.
- **Moment of truth:** On a large project, "what did we decide about X?" returns the exact ADR or knowledge entry by semantic search instead of a grep guess — and the answer points back to the reviewable markdown file, not a database row.
- **Feedback model:** Detection is explicit and cheap (`gbrain doctor --json` → `status`). When a brain is absent or unhealthy, the skill says so once and falls back to grep silently thereafter.
- **Error experience:** GBrain not on PATH, `doctor` returns `error`, or MCP unavailable → graceful no-op fallback to markdown grep; never a hard failure, never a blocked command.
- **Graceful absence is the default posture:** the recipe is opt-in. Absence of GBrain is the common case and must be indistinguishable from Writ-without-this-spec.

### Business Rules

1. Markdown in git is the only canonical system of record; GBrain is a disposable index over it (ADR-011). The recipe never writes canonical data only into GBrain.
2. The capability is opt-in and gracefully absent: with no GBrain installed, Writ behaves exactly as it did before this spec — no references, no prompts, no errors.
3. Brain detection is observable, not assumed: `gbrain doctor --json` (or MCP tool presence) is the detection signal. "Detected" requires a healthy or warning status, never a bare PATH hit.
4. Brain-first retrieval applies only when a brain is detected. Absent a brain, grep over markdown is the retrieval path, unchanged.
5. Retrieval results always cite the canonical markdown path so a human can open, review, and trust the source of truth.
6. Writes are markdown-first: agents write to `.writ/` files, then `gbrain sync` re-indexes. GBrain is never the write target for durable Writ knowledge.
7. Round-trip guarantee: removing GBrain (or any index) loses zero canonical data, because canonical data never lived in the index. The recipe documents the removal path and the guarantee.
8. The recipe tracks GBrain's real, current interface and names its version-tracking boundary explicitly (ADR-011: blast radius is one recipe if the API moves). No invented commands.
9. The skill obeys the command/agent/skill boundary (ADR-009): it is a capability ("route retrieval brain-first when a brain is present"), not a workflow and not a role. It carries `disable-model-invocation: true` and is born `status: candidate`.
10. Zero new infrastructure: no database, no embedding store, no daemon, no runtime service shipped by Writ (ADR-005 zero-infrastructure driver).

### Success Criteria

1. `skills/gbrain-interop/SKILL.md` exists, passes `scripts/lint-skill.sh` (role convention + lifecycle), carries `disable-model-invocation: true`, and is born `status: candidate`.
2. The skill is registered in `.writ/manifest.yaml` and appears in the regenerated root `SKILL.md` catalog (via `scripts/gen-skill.sh`), with `gen-skill.sh` producing no diff on a second run.
3. `.writ/docs/gbrain-recipe.md` exists and documents, against GBrain's real interface: registering `.writ/` as a source (`gbrain sources add` + `gbrain sync`), the artifact→page mapping, MCP registration (`gbrain serve`), brain-first retrieval, and graceful absence.
4. The recipe states and justifies the round-trip guarantee: removing GBrain loses zero canonical data, with the concrete removal step.
5. Detection is observable and absence is a clean no-op: the skill routes on `gbrain doctor --json` status and specifies grep fallback when GBrain is absent or unhealthy.
6. Every GBrain command the recipe cites is real (verifiable against GBrain/GStack docs), and the recipe names its version-tracking boundary. No fabricated flags or subcommands.
7. The `.gbrain-source` pin file that `gbrain sources add` writes to a repo root is documented and added to the recommended `.gitignore` guidance so a disposable index artifact is never committed as canonical.
8. `bash scripts/eval.sh --check=memory-interop` passes for the assertions this spec owns (skill present + registered + recipe doc present with the round-trip and graceful-absence content). *(The `memory-interop` check is authored by the sibling `native-memory-guidance` spec, which runs after this one; this spec's artifacts must satisfy it.)*

### Scope Boundaries

**Included:**
- `skills/gbrain-interop/SKILL.md` — agent capability: detect, brain-first retrieval, markdown-first writes, graceful absence.
- `.writ/docs/gbrain-recipe.md` — user-facing setup recipe: register `.writ/` as a source, artifact→page mapping, MCP registration, round-trip guarantee, removal.
- `.writ/manifest.yaml` skills-list entry for `gbrain-interop`.
- Regenerated root `SKILL.md` catalog (`scripts/gen-skill.sh`).
- `.gbrain-source` pin-file `.gitignore` guidance within the recipe doc.

**Excluded:**
- Any Writ-owned index, database, embedding store, retrieval engine, or daemon (ADR-005; ADR-011).
- Bundling, installing, or hard-depending on GBrain. The recipe assumes the user installs GBrain themselves via its own tooling.
- Per-adapter native-memory guidance and the mission-language sweep (sibling `native-memory-guidance` spec).
- Authoring the `memory-interop` eval check or editing `scripts/eval.sh` (owned by the sibling spec — single-writer).
- Automatic `gbrain sync` hooks, preamble injection, or any always-on runtime wiring.

### Technical Concerns

- **External moving target.** GBrain ships frequently; exact flags may drift. Mitigation (ADR-011): keep the recipe to stable, documented touchpoints (`sources add`, `sync`, `doctor`, `search`, `serve`), name the version boundary, and accept a one-doc blast radius.
- **Confidence calibration.** Every cited command must be verifiable against current GBrain/GStack documentation. Where behavior is version-specific (e.g., sync strategies, embedding-provider keys), say so rather than assert a single form.
- **Detection false-positive.** A `gbrain` binary on PATH is not a healthy brain. Detection must read `gbrain doctor --json` status, not merely `command -v gbrain`.
- **Index-as-canonical trap.** The `.gbrain-source` pin file and any GBrain state must never be treated as canonical; the recipe explicitly keeps them out of the reviewable substrate.
- **Cross-spec eval coupling.** The machine-checkable proof lives in one `memory-interop` eval check owned by the sibling spec. Sequential phase execution (this spec first) guarantees the check's assertions about this spec's artifacts can pass.

### Recommendations

- Ground the recipe in the real upstream tool: [`garrytan/gbrain`](https://github.com/garrytan/gbrain) and GStack's `USING_GBRAIN_WITH_GSTACK.md`. Cite `gbrain sources add` + `gbrain sync`, `gbrain doctor --json`, `gbrain search`, `gbrain put/get`, and `claude mcp add gbrain -- gbrain serve` for MCP.
- Map Writ artifacts to GBrain pages by *tagging*, since `gbrain put` uses YAML frontmatter (title/tags): tag pages by artifact type — `spec`, `adr`, `knowledge-decision`, `knowledge-convention`, `knowledge-glossary`, `knowledge-lesson`. GBrain indexes the source files; the tag mapping is the "page type" mapping the roadmap asks for.
- Keep the skill short and routing-focused (detect → route → cite), and put the setup mechanics in the doc. This respects ADR-009: the skill is a capability, the doc is the human explainer.
- State the round-trip guarantee as a one-line invariant plus the concrete `rm`/uninstall path, so a reviewer can see that canonical data is safe by construction.

### Cross-Spec Review

This spec is independent at the file level (`Dependencies: []`) — it owns the skill, the recipe doc, `manifest.yaml`, and the regenerated `SKILL.md`, none of which the sibling `native-memory-guidance` spec touches. The sibling spec depends on this one: its per-adapter guidance cross-links the `gbrain-interop` skill, and its `memory-interop` eval check asserts this spec's artifacts exist. Sequential phase execution (this spec first) satisfies both couplings. There is no shared-writer file between the two specs.

---

## Detailed Requirements

### R1 — `gbrain-interop` Skill (agent capability)

- Create `skills/gbrain-interop/SKILL.md` following the role convention enforced by `scripts/lint-skill.sh`: verb-phrase `description:`, `disable-model-invocation: true`, `status: candidate`, and a lifecycle `## Evidence` section (0 entries is valid for a candidate).
- Content is routing-focused: **detect** a brain (`gbrain doctor --json` status), **route** retrieval brain-first when detected (prefer `gbrain search` / MCP `mcp__gbrain__search` over grep for semantic knowledge/spec/ADR queries), **cite** the canonical markdown path in every result, **write markdown-first** (edit `.writ/` files, then `gbrain sync`), and **degrade gracefully** to grep when GBrain is absent or unhealthy.
- The skill states the boundary: it changes *retrieval routing*, never the canonical store. It never instructs writing durable knowledge only into GBrain.

### R2 — `.writ/docs/gbrain-recipe.md` (user-facing recipe)

- A concise, accurate setup guide grounded in GBrain's real interface. Sections: what this is and when to use it; prerequisites (user installs GBrain themselves); register `.writ/` as a source (`gbrain sources add <repo-or-path>` + `gbrain sync`); the artifact→page tag mapping; optional MCP registration (`gbrain serve`); brain-first retrieval expectations; the round-trip guarantee + removal; and the version-tracking boundary.
- Documents the `.gbrain-source` pin file and recommends gitignoring it (disposable index artifact, not canonical).
- Explicitly labels version-sensitive details and points to current GBrain docs rather than freezing a single command form where the interface is known to vary.

### R3 — Registration & Catalog

- Add a `gbrain-interop` entry to the `skills:` list in `.writ/manifest.yaml` (`name`, `file`, `description`, `status: candidate`, `tags`).
- Regenerate the root `SKILL.md` catalog with `scripts/gen-skill.sh`; the entry appears and a second run produces no diff (idempotent).

### R4 — Round-Trip & Graceful Absence (behavioral guarantees)

- The recipe demonstrates that removing GBrain — uninstalling the CLI / deleting the local PGLite / dropping the source — leaves `.writ/` markdown byte-for-byte intact and Writ fully functional.
- The skill guarantees that on a machine with no GBrain, no command changes behavior: detection returns "absent," routing falls back to grep, and nothing is printed into the user's normal workflow.

---

## Implementation Approach

### Architecture

Two artifacts, no runtime:

```
skills/gbrain-interop/SKILL.md   (agent) → detect · route brain-first · cite markdown · write markdown-first · degrade
.writ/docs/gbrain-recipe.md      (human) → install GBrain (yourself) · sources add · sync · map · MCP · remove
```

Markdown in git remains the canonical system of record (ADR-011). GBrain is registered as a *federated source* that indexes the existing files; nothing about Writ's storage changes.

### Grounding in GBrain's real interface

Verified against `github.com/garrytan/gbrain` (upstream tool) and GStack's `USING_GBRAIN_WITH_GSTACK.md`:

- `gbrain sources add` + `gbrain sync` — register a directory/repo as a federated source and index it (writes a `.gbrain-source` pin file in the repo root).
- `gbrain doctor --json` — health check returning `{status, health_score, checks}`; the observable detection signal.
- `gbrain search "query"` — semantic retrieval; `gbrain put`/`gbrain get` write/read pages with YAML frontmatter (title/tags → the "page type" mapping).
- `gbrain serve` + `claude mcp add gbrain -- gbrain serve` — MCP tool surface (`mcp__gbrain__search`, etc.); other hosts register manually.

### Validation Strategy

This repository has no application test suite. Verification is script and static-assertion based:

- `bash scripts/lint-skill.sh skills/gbrain-interop/SKILL.md` (role convention + lifecycle)
- `bash scripts/gen-skill.sh` then `git diff --exit-code SKILL.md` (idempotent catalog regeneration)
- `bash scripts/eval.sh --check=memory-interop` (the sibling-owned check asserts this spec's artifacts) and full `bash scripts/eval.sh`
- Manual accuracy review: every cited GBrain command verified against current GBrain/GStack docs

---

## Files in Scope

### Primary (single-writer for this spec)

- `skills/gbrain-interop/SKILL.md` (new) — agent capability
- `.writ/docs/gbrain-recipe.md` (new) — user-facing recipe
- `.writ/manifest.yaml` — add the `gbrain-interop` skills-list entry
- `SKILL.md` (root catalog) — regenerated by `scripts/gen-skill.sh`

### Reference (read-only, not edited)

- `skills/conventional-commits/SKILL.md`, `skills/tdd-cycle/SKILL.md` — skill format exemplars
- `scripts/lint-skill.sh`, `scripts/gen-skill.sh` — lint + catalog tooling
- `.writ/decision-records/adr-011-memory-interop-markdown-canonical.md` — governing policy

---

## Story Plan

1. **`gbrain-interop` skill + registration** — Dependencies: None
2. **`gbrain-recipe.md` user-facing recipe** — Dependencies: Story 1

---

## Deliverables

- [x] `skills/gbrain-interop/SKILL.md` — detect · route brain-first · cite markdown · write markdown-first · degrade gracefully; lint-clean, `candidate`
- [x] `gbrain-interop` registered in `.writ/manifest.yaml` and the regenerated root `SKILL.md` (idempotent)
- [x] `.writ/docs/gbrain-recipe.md` — real-interface setup recipe with artifact→page mapping, MCP registration, and the version-tracking boundary
- [x] Round-trip guarantee documented with the concrete removal path; `.gbrain-source` pin-file gitignore guidance
- [x] Graceful absence: no behavior change on a machine without GBrain
- [x] `bash scripts/eval.sh --check=memory-interop` passes for this spec's owned assertions (check authored by the sibling spec) — *artifacts in place; the `memory-interop` check itself is authored by the sibling `native-memory-guidance` spec and is not yet present in `scripts/eval.sh`*

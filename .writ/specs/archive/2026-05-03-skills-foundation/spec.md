# Skills Foundation — The Third Primitive

> **Status:** Complete
> **Created:** 2026-05-03
> **Completed:** 2026-05-04
> **Owner:** Adam Sellke
> **ADR:** `.writ/decision-records/adr-009-command-agent-skill-boundary.md`

---

## Specification Contract

**Deliverable:** Add the `skills/` primitive to Writ as a peer to `commands/` and `agents/` per ADR-009. Ship the foundation infrastructure only — directory layout, manifest schema extension, install fanout, adapter docs, authoring command, and the `Required skills:` frontmatter convention. No production skills extracted in this spec; integration verified end-to-end via a hello-world smoke skill that's authored, installed across all platforms, and **deleted before merge**. Pilot extraction (`tdd-cycle`, `conventional-commits`, `adr-writing`) is deferred to follow-up specs per ADR-009's "pilot proves integration before broader extraction" sequencing.

**Origin:** Implements ADR-009 — `Command, Agent, Skill — Three Primitives with Distinct Roles`.

**Must Include:** A path from `skills/<name>/SKILL.md` in product source to a working install at `.cursor/skills/<name>/SKILL.md` and `.claude/skills/<name>/SKILL.md` on consumer projects, with manifest tracking, three-way overlay update logic, and authoring discoverability via `/new-skill`.

**Hardest Constraint:** The boundary the ADR draws (capability ≠ workflow ≠ role) is enforceable only by review and tooling. If `/new-skill` doesn't lint for it and `/refresh-command` doesn't check for drift, the boundary will erode within ~10 contributions. Foundation must ship with both gates active *before* the first real skill is extracted.

### Experience Design

- **Entry point (contributor):** Writ contributor runs `/new-skill <name>` to scaffold a new capability following the role convention.
- **Entry point (user):** Writ user runs `bash scripts/install.sh` (or `update.sh`) and skills fan out alongside commands and agents.
- **Happy path (contributor):** `/new-skill conventional-commits` → prompted for verb-phrase description → boundary lint passes → `skills/conventional-commits/SKILL.md` scaffolded with `disable-model-invocation: true` frontmatter → manifest entry appended.
- **Happy path (user):** Run `install.sh` → terminal shows `📜 Skills: N` row alongside Commands/Agents counts → on next session, `Read skills/<name>/SKILL.md` from any agent or command works because the file is at the platform-native path.
- **Moment of truth:** A user opens `.cursor/skills/`, sees the catalog, and reads one to learn how to do something well — without ever invoking a workflow or assuming a role.
- **Feedback model:** Install summary ends with `Skills: N new, M updated, K preserved` — same overlay summary shape as commands/agents. The familiarity of the format is intentional; muscle memory carries.
- **Error experience:** Boundary lint failure on `/new-skill` shows the offending phrase ("Run the full…", "Acts as…") with a one-line remediation; install.sh skill copy failure surfaces alongside command/agent copy failures with the same overlay format.
- **Empty state:** A fresh install with `skills:` empty in the manifest renders "No skills installed yet" instead of an empty Skills section in `SKILL.md`. The `gen-skill.sh --check` mode treats the empty case as valid.
- **First-use state:** If `skills/` directory does not exist in product source, `install.sh` skips the skills step silently (consistent with how it handles missing optional directories today).

### Business Rules

- **Skills source layout is flat.** `skills/<name>/SKILL.md` (plus optional supporting files within the skill folder). No nesting by category. Categories live in the manifest.
- **All Writ-authored SKILL.md files set `disable-model-invocation: true`** in frontmatter. Boundary lint enforces.
- **Skills do not invoke commands or other skills.** Boundary lint rejects skill bodies that contain `Read commands/`, `Read skills/`, slash-prefixed command names (`/command-name`), or `Task(` invocations. Skills can describe *how* to do something with tools the agent already has, but they don't dispatch other workflows.
- **Skill descriptions begin with a verb-phrase.** Boundary lint rejects descriptions starting with "Acts as", "Is responsible for", "The X agent", "Run the full", "Execute the entire". These are role/workflow shapes, not capability shapes.
- **Manifest schema is additive.** Existing `metadata`, `categories`, `commands`, `agents` keys are unchanged. New `skills:` list is optional but conventional; `gen-skill.sh --check` passes whether the list is present or empty.
- **Install fanout mirrors commands/agents semantics.** Three-way overlay (upstream / local / baseline), preserves user modifications, supports `--force` reset.
- **Skills overlay is scoped at the `SKILL.md` granularity inside each skill folder**, not the folder itself. A user customizing `.cursor/skills/foo/SKILL.md` does not have their non-SKILL.md sidecar files (e.g. helper scripts within the skill folder) touched by overlay updates. Overlay tracks the SKILL.md hash; sidecar files are copied on first install only and never overwritten.
- **`Required skills:` frontmatter convention is reserve-only in this spec.** The schema is defined, documented, and harness-aware (commands and agents *may* declare it), but no existing agent/command file is modified to add the field. That happens during pilot skill extraction.
- **Boundary lint scope.** Description-shape checks scan only the `description:` frontmatter value. Body-shape checks scan only the rendered markdown body (post-frontmatter), and only the first 200 characters of paragraphs (not code blocks or example sections).
- **Smoke skill lifecycle.** The `hello-writ` smoke skill is authored in Story 3 and deleted in Story 3's final task. It is never present in `main` branch on PR merge.

## Current State

- `commands/` and `agents/` are first-class primitives with full install/update fanout, manifest entries, and `gen-skill.sh` table rendering.
- `.writ/manifest.yaml` has `metadata`, `categories`, `commands`, `agents` sections — no `skills:` section.
- `scripts/install.sh` and `scripts/update.sh` fan out commands and agents only; skills are unknown.
- `scripts/gen-skill.sh` (despite its name, generates the *root* `SKILL.md` catalog) renders Commands and Agents tables; no Skills table.
- `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/openclaw.md` document command/agent install paths and platform mappings; none mention skills.
- ADR-009 is accepted and explicitly carves the pilot skill extraction (`tdd-cycle`, `conventional-commits`, `adr-writing`) into a separate follow-up spec.
- No `commands/new-skill.md` exists.
- No `Required skills:` frontmatter convention is documented or wired into any harness.

## Expected Outcome

- Writ contributors can scaffold new skills via `/new-skill <name>` with boundary lint enforcement at authoring time.
- Writ users running `install.sh` or `update.sh` see `Skills` fan out alongside commands and agents, with the same overlay semantics they already know.
- Root `SKILL.md` regenerates from `.writ/manifest.yaml` to include a `## Available Skills` table; CI `--check` mode catches drift.
- All three platform adapters (`cursor.md`, `claude-code.md`, `openclaw.md`) include a parallel-shaped `## Skills` section documenting install paths, loading mechanism, and explicit-vs-auto invocation behavior.
- `Required skills:` frontmatter convention is documented in `system-instructions.md`, `.writ/docs/skills.md` (new), and all three adapter files — ready for pilot specs to consume.
- `/refresh-command` includes a boundary-check section that lints existing skills against the role convention.
- The `hello-writ` smoke skill validated end-to-end install on at least Cursor and Claude Code platforms during Story 3, then was deleted from `skills/` and from manifest before merge.
- The repo state at PR merge contains zero production skills — pilot extraction is reserved for follow-up specs.

## Success Criteria

1. `mkdir -p skills/hello-writ && bash scripts/install.sh --dry-run` against a sandbox project lists `Skills: 1 new` and identifies the destination `.cursor/skills/hello-writ/SKILL.md`.
2. `bash scripts/install.sh` against the sandbox actually places `SKILL.md` at the platform-native path with frontmatter intact, including `disable-model-invocation: true`.
3. `bash scripts/gen-skill.sh --check` exits 0 against a manifest with a populated `skills:` list (root `SKILL.md` includes a Skills table); CI parity with commands/agents drift detection holds.
4. `/new-skill foo` scaffolds `skills/foo/SKILL.md`, appends manifest entry, and rejects malformed inputs (workflow-shaped description, role-shaped description, illegal body content) with a clear remediation message.
5. `/refresh-command` includes a boundary-check section that runs the same lint against existing skills (zero false positives on the throwaway hello-writ smoke skill).
6. `Required skills:` frontmatter convention is documented in `system-instructions.md`, `.writ/docs/skills.md`, and all three adapter docs — with no agent/command file modified yet.
7. Hello-writ smoke skill is deleted from `skills/` and from manifest before merge; final repo state ships zero production skills.
8. Skills three-way overlay preserves user modifications to `.cursor/skills/<name>/SKILL.md` exactly the way it does for commands/agents (verified via overlay smoke test in Story 2).

## Scope Boundaries

**Included:**

- `skills/` directory at product source root
- `.writ/manifest.yaml` `skills:` schema
- `scripts/gen-skill.sh` Skills table rendering and `--check` mode parity
- `scripts/install.sh` + `scripts/update.sh` skills fanout with three-way overlay
- `commands/new-skill.md` (new command)
- `commands/refresh-command.md` boundary-check section addition
- `Required skills:` frontmatter convention — defined and documented (no agent/command files modified to declare it yet)
- Skills sections in `adapters/cursor.md`, `adapters/claude-code.md`, `adapters/openclaw.md`
- New `.writ/docs/skills.md` explainer with verb/noun/tool framing
- Updates to root `README.md`, root `SKILL.md` (regenerated), `AGENTS.md`, and `.writ/docs/self-dogfooding.md`

**Excluded:**

- Pilot skill extraction (`tdd-cycle`, `conventional-commits`, `adr-writing` — deferred to per-skill follow-up specs)
- `adapters/codex.md` (separate platform-adapter spec)
- Modifying any existing agent or command to declare `Required skills:` (deferred to pilot specs)
- Skill discovery UI or CLI search
- Community skill installation flow (e.g. `clawhub`, `agentskills.io` ingestion)
- Skill versioning beyond what `install.sh`'s overlay already provides
- Migration of community-installed skills already present in users' `.cursor/skills/` from external installers — those continue to be governed by whatever installer placed them; Writ overlay tracks only Writ-authored skills

## Implementation Approach

### Manifest Schema (additive)

```yaml
skills:
  - name: hello-writ
    file: skills/hello-writ/SKILL.md
    description: "Demonstrates the skill loading path end-to-end. Throwaway smoke artifact."
    tags: [smoke, internal]
```

Required fields: `name`, `file`, `description`. Optional: `tags`, `aliases`. Validation matches commands/agents pattern: file exists, name is unique, description is non-empty.

### Install/Update Fanout

`install.sh` gains a Skills step (Step 3) parallel to the existing Commands and Agents steps. Three-way overlay (`overlay_scan`) generalized to recurse into subdirectories *only at the `SKILL.md` granularity* — each skill folder is treated as a unit, but only its `SKILL.md` is hash-tracked in the manifest.

Manifest file format (`.cursor/.writ-manifest`) gains `skills/<name>/SKILL.md` entries alongside `commands/*.md` and `agents/*.md` entries.

### `gen-skill.sh` Skills Table

Both YAML parser branches (`parse_with_yq` and `parse_with_bash`) extended with a `parse_skills` block. Body generation adds a `## Available Skills` section after `## Available Agents`. Empty `skills:` list produces no table (silent skip), not an empty section. `--check` mode validates skill files exist and renders match.

### `/new-skill` Command

Scaffolder with three phases:

1. **Capture:** Skill name (kebab-case, validated), description (verb-phrase), category (optional), tags (optional).
2. **Lint:** Boundary check on description and body. Rejects role/workflow shapes with one-line remediation. See Business Rules for the rejection grammar.
3. **Write:** Creates `skills/<name>/SKILL.md` with `disable-model-invocation: true` frontmatter, scaffolded sections (Purpose, When to Use, How to Apply, Examples), and appends to `.writ/manifest.yaml`.

### `Required skills:` Convention

Documented schema in agent/command frontmatter:

```yaml
---
name: example-agent
required_skills:
  - tdd-cycle
  - conventional-commits
---
```

Harness behavior (documented but not yet wired): when a command or agent declares `required_skills`, the platform adapter pre-loads each named skill via `Read skills/<name>/SKILL.md` before the work begins. Without the field, agents/commands continue to inline `Read skills/<name>/SKILL.md` instructions in their prompts.

### Boundary Lint Implementation

Single shared script (`scripts/lint-skill.sh` or inline in `/new-skill` and `/refresh-command`) with the rejection grammar:

- **Description-shape rejections:** `^(Acts as|Is responsible for|The .* agent|Run the full|Execute the entire)`
- **Body-shape rejections (first 200 chars per paragraph, code blocks excluded):** `Read commands/`, `Read skills/`, `\bTask\(`, `^/[a-z-]+`

Rejections produce: line number, offending phrase, suggested rewrite (when known) or generic remediation ("Skills describe a capability; rephrase as a verb-phrase about what to do.").

## Stories Plan

| # | Story | Dependencies |
|---|---|---|
| 1 | Manifest schema + Skills table generation in `gen-skill.sh` | None |
| 2 | `install.sh` + `update.sh` skills fanout with three-way overlay | None |
| 3 | Hello-writ smoke verification (skill deleted in final task) | Story 1, Story 2 |
| 4 | Adapter Skills sections (cursor, claude-code, openclaw) | None |
| 5 | `Required skills:` frontmatter convention — schema + docs only | None |
| 6 | `/new-skill` command + `/refresh-command` boundary check | Story 1 |
| 7 | Documentation pass — root `SKILL.md`, `README.md`, `.writ/docs/skills.md`, `self-dogfooding.md`, `AGENTS.md` | Stories 1, 2, 4, 5, 6 |

Stories 1, 2, 4, 5 may run in parallel batches. Story 3 gates on 1 + 2. Story 6 gates on 1. Story 7 is the final synthesis story.

## Technical Decisions

- **Skills overlay at `SKILL.md` granularity, not folder granularity.** Avoids the complexity of recursive overlay diff while preserving user customization on the SKILL.md text itself. Sidecar files inside a skill folder are install-once.
- **Boundary lint is description + body-shape regex, not deep semantic analysis.** Cost vs value: deep analysis would catch more drift but adds a dependency (NLP model or ML classifier) the project has no other use for. Regex catches the obvious failures and gets sharper with each false-negative we observe.
- **Smoke skill is in-spec, not in-product.** Deleting `hello-writ` before merge means the foundation ships clean. If a future contributor wants to ship a "minimal skill" example, that's a separate spec with proper review.
- **`Required skills:` documented but not wired.** Defining the schema now lets pilot specs consume it on Day 1 without a schema-change negotiation. Wiring without consumers risks dead code; documentation without schema risks pilot specs reinventing the convention. Defining + documenting hits the right balance.
- **No new platform adapter (`adapters/codex.md`) in this spec.** ADR-009 references it; we're consciously deferring. The Skills sections in existing adapters cover the three platforms the install script supports today (cursor, claude). OpenClaw adapter gets the same Skills section for consistency with prior infrastructure work.

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `parse_with_bash` fallback in `gen-skill.sh` becomes unmaintainable after adding skills section | Medium | Medium | Keep skill schema minimal (3 required fields, 2 optional). Resist tag/alias/category sprawl until pilot specs prove need. |
| Boundary lint produces false positives on legitimate skill content | High | Low | Scope description-shape lint to frontmatter only; scope body-shape lint to first 200 chars of paragraphs (not code blocks). Lint failures must include explicit remediation, not just rejection. |
| Three-way overlay logic regression on commands/agents while generalizing for skills | Medium | High | Keep `overlay_scan` flat; add a new `overlay_scan_skills` function rather than generalizing the existing one. Existing tests remain green; skills tests are new. |
| `Required skills:` documented but never used | Medium | Low | Mark "reserve-only until pilot specs land" in docs with a 90-day review trigger (matches ADR-009 review date). If unused at review, deprecate. |
| Smoke skill (`hello-writ`) accidentally committed to `main` | Low | Low | Story 3 explicitly includes "delete smoke skill" as final task with both file and manifest cleanup. Verify via `git diff` in Story 3 DoD. |
| Skills documentation contradicts ADR-009 boundary | Low | High | Story 7 cross-references ADR-009 directly. `.writ/docs/skills.md` opens with the verb/noun/tool framing in the same words the ADR uses. |

## References

- ADR-009 — `.writ/decision-records/adr-009-command-agent-skill-boundary.md` (this spec implements it)
- ADR-001 — AskQuestion vs Plan Mode in Commands (interaction precedent — used `AskQuestion` for scope decisions in this spec's discovery)
- ADR-008 — Spec as Team Contract Moat (contract-first ethos this spec extends)
- Spec 2026-04-24-phase4-production-grade-substrate — shipped `manifest.yaml` + `gen-skill.sh` foundation this extends
- AgentSkills open standard — file format compatibility target

## Out of Scope (Reserved for Follow-Up Specs)

- **Skill pilot 1: `conventional-commits`** — extract from `coding-agent` and (eventually) `/release` / `/ship`
- **Skill pilot 2: `tdd-cycle`** — extract from `coding-agent` and `/prototype`
- **Skill pilot 3: `adr-writing`** — extract from `/create-adr` and `/knowledge`
- **`adapters/codex.md`** — first-class Codex adapter, including (but not limited to) Skills section
- **Wiring `required_skills:` into existing agents and commands** — happens organically as pilot skills are extracted and consumed

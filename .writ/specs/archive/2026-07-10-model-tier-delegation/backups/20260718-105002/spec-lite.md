# Model-Tier Delegation (Lite)

> Source: .writ/specs/2026-07-10-model-tier-delegation/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** A portable `model_tier` convention. Agents carry an ENFORCED tier (`orchestration` → anchor/`inherit`, `capability` → floor/`fast`), resolved per-platform via native primitives. Skills and commands carry ADVISORY-ONLY tier. No maintained model ranking; relative semantics only; graceful degradation (warn → fall back to parent).

**Implementation Approach:**
- Story 1: define `model_tier` vocabulary (2 named tiers + reserved ordinal-offset form); document in `system-instructions.md` + `cursor/writ.mdc` (byte-identical); write ADR-014.
- Story 2: add `model_tier` to all 7 agents (frontmatter + `manifest.yaml`), mapped from today's `model:` with ZERO behavior change.
- Story 3: adapter tier→native-resolution tables + graceful degradation (cursor/codex/openclaw).
- Story 4: `/new-command` + `/new-skill` scaffold advisory `model_tier:`; lint validates values; `.writ/docs/model-tiers.md`; README/AGENTS refs.
- Keep `model:` as concrete-override escape hatch; `model:` takes precedence over `model_tier:`.

**Files in Scope:**
- New: `.writ/decision-records/adr-014-model-tier-delegation.md`, `.writ/docs/model-tiers.md`
- Modified: `.writ/manifest.yaml`, `agents/*.md` (all 7), `adapters/cursor.md`, `adapters/codex.md`, `adapters/openclaw.md`, `system-instructions.md`, `cursor/writ.mdc`, `commands/new-command.md`, `commands/new-skill.md`, `scripts/lint-skill.sh`, `README.md`, `AGENTS.md`

**Agent tier mapping (no regression):**
- `capability` (→ fast/floor): `architecture-check-agent`, `user-story-generator` (both `fast` today)
- `orchestration` (→ inherit/anchor): `coding`, `review`, `testing`, `documentation` (`default` today), `visual-qa` (`inherit` today)

**Error Handling:**
- Unset `model_tier` → inherit parent/default (today's behavior)
- Unknown/unhonorable tier → WARN, fall back to parent/default; never hard-fail
- `model_tier` value outside allowed set on `/new-*` → lint rejects with remediation, no file written

**Integration Points:**
- Extends ADR-009 verb/noun/tool boundary and the `required_skills:` reserve-only pattern
- `cursor/writ.mdc` mirrors `system-instructions.md` tiering content (Phase 4 parity)

**Line Budget Constraints:** N/A (markdown framework; lint additions stay minimal bash)

---

## For Review Agents

**Acceptance Criteria:**
1. `rg "model_tier:" agents/` returns a valid tier for all 7 agents, each matching its `manifest.yaml` entry.
2. Mapping preserves current behavior — each agent resolves to the same concrete model it runs today (verified via adapter resolution table review).
3. cursor/codex/openclaw adapters each have a tier→native-resolution table + documented graceful-degradation rule.
4. `system-instructions.md` + `cursor/writ.mdc` document the convention; tiering content byte-identical between them.
5. `/new-command` + `/new-skill` scaffold advisory `model_tier:`; lint rejects invalid values.
6. `adr-014` exists with agent-carrier + relative + staged-resolver decision and rejected alternatives.
7. `.writ/docs/model-tiers.md` exists; README + AGENTS reference it.

**Business Rules:**
- Enforced tier lives ONLY on agents (the spawn boundary with a `model` param).
- Commands (session model) + skills (caller's context) → advisory-only, must be labeled as such everywhere.
- Two tiers ship: `orchestration`=anchor, `capability`=floor. Relative, not absolute.
- No maintained model ranking in this spec. Ordinal offsets reserved (inert, 2-band resolution today).
- Graceful degradation: warn → fall back to parent. No behavioral regression from the mapping.

**Experience Design:**
- Entry: contributor sets `model_tier:` in agent frontmatter + manifest
- Happy path: `capability` agent → floor model, cheaper, no quality drop; `orchestration` agent → anchor model
- Moment of truth: a phase run spends top-tier tokens only where reasoning demands
- Feedback: greppable, self-documenting; adapter table shows tier→model
- Error: unhonorable tier warns + inherits, never fails

**Drift Analysis Anchors:**
- Building the model ranking, N-step resolution, anchor detection, or eval harness → OUT OF SCOPE; do not absorb
- Enforcing tier on commands/skills → mis-scoped; advisory only
- Any agent changing its effective concrete model → regression; flag high drift

---

## For Testing Agents

**Success Criteria:**
1. All 7 agents declare a valid `model_tier`; frontmatter and manifest agree (`rg`/diff check).
2. Each agent's resolved concrete model is unchanged from today (adapter-table walkthrough per platform).
3. Lint rejects an out-of-set `model_tier` value with remediation; accepts valid ones.
4. Tiering content in `system-instructions.md` and `cursor/writ.mdc` is byte-identical (`diff`).

**Shadow Paths to Verify:**
- **Happy path:** `orchestration` agent spawns at `inherit`; `capability` agent spawns at `fast` — resolution table matches.
- **Nil input:** agent with no `model_tier:` → resolves to parent/default (today's behavior), no warning noise.
- **Empty input:** command/skill with advisory `model_tier:` → documented, never used to select a model.
- **Upstream error:** platform lacks a fast model / unknown tier value → warn + fall back to parent, no hard-fail.

**Edge Cases:**
- Both `model:` and `model_tier:` present → `model:` wins (documented precedence).
- Reserved ordinal offset (e.g. `-1`) declared → accepted by lint, resolved as 2-band (clamped) today.
- `manifest.yaml` tier ≠ agent frontmatter tier → flagged as inconsistency in review.

**Coverage Requirements:**
- Verification = `rg`/`diff`/manual adapter-table walkthrough (markdown+bash project — no test framework)
- Critical paths (mapping preserves model, lint validation, parity mirror): manual sign-off in story DoD

**Test Strategy:**
- Story 2: build the tier→concrete-model table per platform; confirm each agent lands on today's model.
- Story 3: walk graceful-degradation path per adapter (no fast model / unknown value).
- Story 4: feed lint a bad `model_tier` value → rejected; a valid one → accepted; `diff` the two root files.

# Skill Extraction from High-Traffic Commands (Lite)

> Source: `.writ/specs/2026-07-10-skill-extraction/spec.md`
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Extract four skills from Writ's heaviest commands and retire `/explain-code` into one of them. Each skill is born `status: candidate` (schema owned by `2026-07-10-skill-lifecycle`) and lints clean.

**The four skills → source → consumer:**
- `code-explanation` ← retired `/explain-code` → `commands/research.md`
- `tdd-cycle` ← `commands/implement-story.md` Gate 1 → implement-story + `agents/coding-agent.md` + `agents/testing-agent.md`
- `error-rescue-mapping` ← `commands/create-spec.md` Step 2.8 → create-spec
- `safe-refactor-loop` ← `commands/refactor.md` Phase 3 → refactor

**Implementation Approach:**
- Confirm `status:` field exists (hard prerequisite) before starting.
- Follow the `conventional-commits` shape: frontmatter (`name`, verb-phrase `description`, `disable-model-invocation: true`, `status: candidate` + evidence note) → `# Title` → `## Purpose` → `## When to Use` → `## How to Apply` → `## Examples`.
- Skill bodies are capability prose only — no `Read commands/`, no `Read skills/`, no `Task(`, no line starting with a slash command.
- Wire each consumer with a literal `Read skills/<name>/SKILL.md` (see `commands/ship.md` ~275).
- Shrink each source section to an orchestration note; delete `commands/explain-code.md` entirely.
- Register skills alphabetically in `.writ/manifest.yaml` (additive, shared with lifecycle spec); regenerate `SKILL.md`.

**Files in Scope:**
- `skills/{code-explanation,tdd-cycle,error-rescue-mapping,safe-refactor-loop}/SKILL.md` (new)
- `commands/{create-spec,implement-story,refactor,research,new-command,status}.md`, `commands/explain-code.md` (DELETE)
- `agents/{coding-agent,testing-agent}.md`
- `.writ/manifest.yaml`, root `SKILL.md`, `README.md`, `adapters/cursor.md`, `claude-code/CLAUDE.md`, `codex/AGENTS.md.template`, `.writ/docs/skills.md`

**Error Handling:**
- Missing `status:` schema → hard block; do not invent a placeholder.
- Lint violation → block the story; rewrite orchestration prose as capability prose.
- Stale catalog → `gen-skill.sh --check` fails; regenerate before finalizing.
- Surviving `/explain-code` active reference → retirement grep fails.

---

## For Review Agents

**Acceptance Criteria:**
1. Four skills exist, each `status: candidate`, and `lint-skill.sh skills/*/SKILL.md` is clean.
2. Each skill has ≥1 wired consumer (`Read skills/<name>/SKILL.md`); each source command is shorter.
3. `/explain-code` is gone from all active surfaces; allowlisted history may keep it.
4. `gen-skill.sh --check` passes; `install.sh --dry-run` fans out four skills, no orphan command.
5. `skills.md` has an extraction section and the stale line 3 is fixed.

**Business Rules:**
- The set is exactly four; `/ship` is a documented non-extraction (already yielded `conventional-commits`).
- This spec consumes the lifecycle `status:` schema; it never defines or reorders states.
- "In real use" = wired live consumers now; `candidate → proven` promotion is out of scope.
- Skills load explicitly (`disable-model-invocation: true`); a consumerless skill is not shippable.
- No fifth skill added just to reach the roadmap "3–5" ceiling.

**Experience Design:**
- No new command surface; the only user-facing change is `/explain-code` disappearing.
- Command shrink notes name the skill and the data supplied; they never duplicate skill prose.
- `code-explanation` must have a live consumer (`/research`) or it is orphaned under `disable-model-invocation`.

**Drift Anchors:**
- A skill body containing orchestration (`Read`, `Task(`, slash-command line) is contract drift.
- Padding to five skills, or a hand-edited root catalog, is contract drift.
- Redefining lifecycle `status` values here is a boundary violation of the seam.

---

## For Testing Agents

**Success Criteria:**
1. `lint-skill.sh skills/*/SKILL.md` exits 0 across all four new skills.
2. `gen-skill.sh --check` reports the catalog in sync after registration + retirement.
3. `install.sh --dry-run` / `update.sh --dry-run` show four skills fanned out, no `explain-code` command.

**Shadow Paths to Verify:**
- **Happy path:** skill authored → lint clean → consumer wired → command shrunk → catalog regenerated.
- **Nil input:** `status:` schema absent → hard block, extraction never begins.
- **Empty input:** skill with no consumer → flagged not shippable.
- **Upstream error:** dangling `/explain-code` reference → retirement grep fails with the surviving path.

**Edge Cases:**
- Manifest registered but catalog not regenerated → `--check` fails.
- Orchestration prose left in a skill body → lint fails with remediation.
- Allowlisted history naming `/explain-code` → not a failure.

**Coverage Requirements:**
- All four skills lint-clean: mandatory.
- Every wired consumer references its skill: verified by grep.
- `candidate → proven` promotion: explicitly out of scope, tracked by the lifecycle spec.

**Test Strategy:**
- `lint-skill.sh`, `gen-skill.sh --check`, `install.sh`/`update.sh --dry-run`, `eval.sh`, allowlisted greps.

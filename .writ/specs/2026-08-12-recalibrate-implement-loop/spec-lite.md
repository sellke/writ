# Recalibrate the implement-spec / implement-story Loop (Lite)

> Source: .writ/specs/2026-08-12-recalibrate-implement-loop/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Fix 5 evidenced friction points from a real 6-story
`/implement-spec` run: 3 bookkeeping/clarity amendments to
`implement-spec.md`, and 2 new skills referenced from `implement-story.md`.

**Implementation Approach:**
- Story 1 amends `implement-spec.md` only (Step 3.2, 3.3, completion step)
- Stories 2/3 each author one new `skills/*/SKILL.md` and reference it from
  `implement-story.md` — follow the file's existing convention exactly:
  `` `Read skills/<name>/SKILL.md` for *how*... This gate owns *when*...; the
  skill owns *how*. ``
- No existing gate's PROCEED/CAUTION/ABORT or PASS/FAIL/PAUSE contract
  changes — additive only

**Files in Scope:**
- `commands/implement-spec.md` — Step 3.2, 3.3, completion step
- `commands/implement-story.md` — skill references at Gate 0/1/3/4/4.5
- `skills/subagent-result-completeness/SKILL.md` — new
- `skills/subagent-worktree-integration/SKILL.md` — new

**Error Handling:**
- N/A — this is a documentation/process spec, no runtime error paths

**Integration Points:** `implement-story.md`'s Pipeline table (Skill column);
`/refresh-command`'s Tier-2 structural allowlist (implement-story.md is on it).
**Out of scope:** concurrent peer-session editing risk, `agents/*.md`,
`commands/implement-phase.md`, rewriting any existing gate's result contract.

---

## For Review Agents

**Acceptance Criteria:**
1. Step 3.2's spawn-mechanism note is present and matches the ambiguity
   actually observed (inline load vs. backgrounding)
2. Completion step updates `spec.md`'s own header, not just story files/README
3. Step 3.3's state write reads as required, not optional
4. Both skills pass `scripts/lint-skill.sh` and are referenced from
   `implement-story.md` using its exact existing phrasing convention
5. `bash scripts/eval.sh` green, including implement-story.md's Tier-2 check

**Business Rules:**
- Skills describe capabilities, not workflows (ADR-009)
- Skill references must match the existing "this gate owns *when*; the skill
  owns *how*" phrasing exactly — not a paraphrase
- No existing gate's result contract changes
- `Phase-Orchestrated Lane Mode` in implement-spec.md is untouched

**Experience Design:**
- Entry: a maintainer running `/implement-spec` or `/implement-story`
- Happy path: spawned agent returns complete verdict first try; worktree
  output (if any) integrates via a documented procedure
- Moment of truth: orchestrator no longer manually judges "real verdict or
  mid-task narration?"
- Feedback: the skill names the next action, not invented per-story
- Error: a mid-task stop is itself the named condition, with a resume step

**Design note:** the concurrent peer-session command-file-editing risk
(another session refactored `implement-story.md` mid-run) was considered and
explicitly deferred — see spec.md § Business Rules item 5. Do not re-litigate.

---

## For Testing Agents

**Success Criteria:**
1. `bash scripts/lint-skill.sh skills/subagent-result-completeness/SKILL.md skills/subagent-worktree-integration/SKILL.md` exits clean
2. `bash scripts/eval.sh` full suite green
3. Both skills are referenced from `implement-story.md`, verified by grep
4. `implement-spec.md`'s frontmatter and `## Completion` heading unchanged

**Shadow Paths to Verify:**
- **Happy path:** both skills lint clean, both referenced, eval.sh green
- **Edge case:** a skill reference added but the skill file boundary-lint
  fails — must not ship a broken reference

**Edge Cases:**
- Story 3 lands after Story 2 (dependency) — confirm no concurrent-edit
  conflict in `implement-story.md`'s adjacent inserted sections

**Coverage Requirements:** N/A — no executable code in this spec's scope.

**Test Strategy:** `scripts/lint-skill.sh` for both new skills;
`bash scripts/eval.sh` for the Tier-2 structural check on `implement-story.md`
and general suite health; manual grep/read-through for phrasing-convention
match.

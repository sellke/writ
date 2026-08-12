# Story 2: Extract the Lane / Merge / Quarantine Mechanics to a Skill

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** maintainer who needs `/implement-phase` to stay under the 24,960-byte budget without weakening the machinery that keeps failed work off the phase branch
**I want to** move the 5,225 bytes of lane, merge, quarantine, and reconcile *narrative* into a capability file while the *invariants* stay in the command
**So that** the mechanics are documented once and reusable, and a skill that fails to load can never be the reason an unverified result gets merged

## Acceptance Criteria

- [ ] Given `skills/` is a shared namespace shared with six sibling specs, when this story starts, then the name is reconciled against `2026-08-12-disclosure-implement-story` and every other `2026-08-12-*` spec's claimed skill names (checked clear at authoring time, 2026-08-12 — re-check, do not assume), and the finding is recorded in the story notes
- [ ] Given Business Rule 9, when the skill is created, then it is authored via `/new-skill`, `bash scripts/lint-skill.sh` exited 0 on the description before any file was written, and the file carries `disable-model-invocation: true` and `status: candidate`
- [ ] Given the source prose names `scripts/phase-state.py` subcommands, `/implement-spec`, and `/create-uat-plan` directly, when the skill is written, then it reads as a portable capability — *how to run a unit of work in a fresh isolated git lane and dispose of its result* — with no command, slash-command, skill, or subagent invocation in the body, and `bash scripts/lint-skill.sh skills/<name>/SKILL.md` exits 0
- [ ] Given Business Rule 3 forbids redesign, when the skill is written, then it carries: how the lane's base is verified clean before creation; how a fresh worker is seeded from artifact paths only with no conversational transcript forwarded; the pass-through of caller flags; the inherited-answer precedence (contract → story files → technical spec → roadmap); the classify → bounded-retry → quarantine sequence; the block-dependents / continue-independents rule; and read-only reconciliation before resume — compressed in wording, unchanged in meaning
- [ ] Given Business Rule 2 keeps the safety contract in the command, when this story lands, then the skill does **not** claim to be the authority on the four invariants; it describes mechanics and defers the normative statements to its consumer, so a reader of the skill alone cannot conclude that merging an unverified result is permitted
- [ ] Given ten eval anchors have their only surviving occurrence inside this story's source range, when this story lands, then `git diff --name-only` shows **zero** changes to `commands/implement-phase.md` — the anchors cannot break here because this story does not touch that file, and Story 4 owns re-stating them
- [ ] Given Business Rule 4 requires reachability, when this story lands, then the skill is registered in `.writ/manifest.yaml` and `bash scripts/gen-skill.sh --check` reports no delta
- [ ] Given this skill sits on the **always-taken** path — every run that executes a single spec reaches it — when this story lands, then its measured byte size is recorded and checked against Business Rule 1's second capped figure: projected floor (46,255) + this skill must stay **below 54,096**, the monolith. It is the one of the three whose size is still bound, because its bytes are conditional in form and unconditional in practice
- [ ] Given Business Rule 8, when this story lands, then `git diff --name-only` lists only `skills/<name>/SKILL.md`, `.writ/manifest.yaml`, and `SKILL.md`

## Implementation Tasks

- [ ] 2.1 Read `commands/implement-phase.md` lines 186–226 in full, plus `.writ/docs/phase-execution-state-format.md` for the `phase-execution-v2` / `phase-spec-result-v1` contracts the prose refers to, and `scripts/phase-state.py`'s `cmd_create_lane`, `validate_result`, `cmd_integrate`, `cmd_quarantine`, `cmd_reconcile` — the skill describes what these do, and describing them wrong is a drift the eval suite will not catch
- [ ] 2.2 Reconcile the skill name (Business Rule 10) across all `2026-08-12-*` sibling specs. Record the finding either way — "no overlap" is evidence, not an absence of work
- [ ] 2.3 Run `/new-skill <name>` — description, pre-write lint, file, manifest entry, `gen-skill.sh --check`
- [ ] 2.4 Author the body from lines 186–226, rewriting orchestration references out and keeping the mechanics: lane creation preconditions, fresh-worker seeding, result validation, merge-on-success disposal, non-success preservation, bounded retry, quarantine, dependent blocking, reconcile-before-resume
- [ ] 2.5 Explicitly **do not** carry into the skill: the *Iteration bound* paragraph (lines 202–203) and the four Business Rule 2 invariant statements. Both are retained in the command by Story 4. Note in the skill where its consumer holds the authority
- [ ] 2.6 Verify: `bash scripts/lint-skill.sh` exits 0; byte size recorded and summed with Story 1's against the budget; `gen-skill.sh --check` no delta
- [ ] 2.7 Confirm ownership: `git diff --name-only` shows no `scripts/` or `commands/` path

## Notes

**Technical considerations:**

- This is the story where the extraction is most likely to go wrong, because the source is simultaneously the densest prose in the file, the location of ten of the twenty eval anchors, and the entire safety machinery of the phase pipeline. The split is deliberate and mechanical: **normative statements stay, mechanics move.** "Only a verified result merges" is normative. "The merge is `--no-ff`, after which the worktree is removed and the merge commit recorded" is mechanics.
- The skill will be read by nobody at authoring time except its one consumer. That is not a reason to write it loosely — ADR-014's promotion path requires three consumers, and the `implement-spec` sibling is a plausible second. Writing it as a general capability rather than as `/implement-phase`'s Step 3.2 in disguise is what makes that possible.
- `scripts/phase-state.py` subcommand names may appear as *nouns describing a reducer's operations* without violating `lint-skill.sh` — the lint rejects `Read commands/`, `Read skills/`, `Task(`, and body lines beginning with a slash command. Naming a script is not invocation. Verify against the lint rather than guessing.

**Risks / challenges:**

- **Softening an invariant into mechanics.** The failure is subtle: "the phase branch is never touched by failed work" reworded as "failed lanes are normally preserved rather than merged" reads like the same sentence and is not. Task 2.5 exists to draw the line explicitly, and Story 4's acceptance criteria re-check it from the other side.
- **Writing this as `/implement-phase`'s Step 3.2 in disguise.** `implement-spec` is **not** among the programme's six extracted files, so there is no live counterparty for ADR-021 §4's "one shared skill, not two copies" rule today — and that is exactly why the temptation to write a command-specific skill is unchecked here. When `implement-spec` is eventually extracted, a general capability is a reuse and a disguised transcript is a rewrite.
- **Budget pressure still lands hardest here, but for a different reason.** The pre-ruling cap demanded 5,225 bytes of source into roughly 2,600 — a ~50% compression, the steepest of the three. **That cap is retired** (2026-08-12 ruling); the target is ≈4,400 B, authored to the source. What replaces the pressure is Business Rule 1's always-taken-path bound: this is the only skill of the three that every real run loads, so floor + this skill must stay under 54,096. At ≈4,400 B that clears by ≈3,441 bytes. If it will not fit without dropping a rule, that is a finding to escalate, not a licence to trim the rule.
- **Do not treat this skill's bytes as a conditional win.** `measure-invocation.py` books them under `conditional_bytes` because the load is inline, but the path that skips them is the path that executes no specs. Story 5 reports it as the always-taken path for exactly this reason.

**Integration points:**

- Story 4 loads this skill with one inline `Read skills/<name>/SKILL.md` at the start of the per-spec iteration, and authors the retained **Lane & Failure Invariants** block that this story deliberately leaves behind. Business Rule 2 is *stronger* under the inline mechanism, not weaker: non-load is now the design rather than an accident, the `Read` can fail mid-step with no harness warning, and no governor check resolves an inline read at all. Task 2.5's line is the one that matters most in the spec.
- Story 5 measures this skill's bytes and re-runs the full anchor grep against the rewritten command.
- `.writ/docs/phase-execution-state-format.md` carries its own eval-required literals (`Isolation Begins Before Work`, `never forwards`, `os.replace`, `## Quarantine and Resume`) and is **not** edited by this spec.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] `bash scripts/lint-skill.sh skills/<name>/SKILL.md` exits 0
- [ ] `bash scripts/gen-skill.sh --check` reports no delta
- [ ] Running byte total (Stories 1 + 2) recorded against the ≈7,841-byte budget, with any overrun escalated before Story 3
- [ ] Skill-name reconciliation across all `2026-08-12-*` sibling specs recorded either way
- [ ] `git diff --name-only` shows zero changes to `commands/implement-phase.md` and no path under `scripts/`

## Context for Agents

- **Business rules:** [BR1 path-dependent ceiling — this skill is the always-taken path and the second capped figure, BR2 safety invariants stay in the command (strengthened), BR3 relocate-not-redesign, BR4 precise placement, BR8 ownership, BR9 lint, BR10 name reconciliation] — from spec.md → 📋 Business Rules
- **Mechanism ruling:** [inline `Read` replaces `required_skills:`; `phase-lane-execution` is only nominally conditional] — from spec.md → ## Approved Scope Changes, ## Technical Concerns
- **Detailed requirements:** [What extracts, and where → `skills/phase-lane-execution/SKILL.md`] — from spec.md → ## Detailed Requirements
- **Technical spec:** [Section Byte Ledger (lines 186–226); The 20 Blocking Anchors — ten at risk in this range; The Retained Lane & Failure Invariants Block] — from sub-specs/technical-spec.md
- **Technical concerns:** [19 blocking eval literals pin prose inside a file this spec is rewriting] — from spec.md → ## Technical Concerns

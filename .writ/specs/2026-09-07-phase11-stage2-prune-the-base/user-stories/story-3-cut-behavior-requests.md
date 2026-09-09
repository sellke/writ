# Story 3: Cut Behavior Requests — Line-by-Line Classification to a 10,000-Byte Base, Batching Line to Adapters

> **Status:** Completed ✅ (2026-09-07)
> **Commit:** 2fc26f935c26bf0da8281b714be4b805f848add1
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer pruning the shared base under a Goal Card that caps it at 10,000 bytes, **I want to** classify every remaining line of `system-instructions.md` and `commands/_preamble.md` as an environment fact, a human boundary, or a behavior request, remove the behavior requests and the duplicate `File Organization` section with a dated ledger reason for each, and move the Fable 5.1 batching line to each adapter file, **so that** the base lands at or under the cap with nothing but facts, boundaries, and untouched hard constraints left in it, and `prune-ledger.py check --cap-blocking` proves it.

## Acceptance Criteria

> **AC IDs assigned through:** AC-3.5

- [x] Given Story 2's closing base byte count, when the classification table in this story's What Was Built is read, then every remaining line of `system-instructions.md` and `commands/_preamble.md` appears in it with columns file, section, line count, class, and action, and the three classes used are exactly environment-fact, human-boundary, and behavior-request per the research test in `.writ/research/2026-09-05-goldilocks-harness-research.md` `[AC-3.1]`
- [x] Given the cut candidates named in technical-spec §4 (Identity & Approach, Command Execution Protocol, Judgment Principles, Prose, Interaction Tool Selection beyond the tool-naming rule, Session Auto-Orientation, Skills, the duplicate File Organization, preamble Tool Selection, Knowledge Context, Adapter Neutrality), when each is removed, then every removed line has a corresponding row in `.writ/decision-records/pruned-instructions-ledger.md` of class `behavior-request` (reason ≤ 120 chars stating why Fable 5.1-class models do it unprompted) or, for the duplicate `## File Organization` section, class `duplicate` (reason naming where the surviving copy lives) `[AC-3.2]`
- [x] Given the sections named as kept verbatim (Hard Constraints, the Recommended Delivery Exception's rule, Plan Mode Integrity, User Challenge's four-part shape, Autonomy Gate Classes, Artifact Integrity), when they are diffed against the pinned commit `cf84742`, then they are byte-identical with no reflow, rewrap, or reword `[AC-3.3]`
- [x] Given the Fable 5.1 batching line currently in `system-instructions.md`, when it is moved, then each of `adapters/claude-code.md`, `adapters/cursor.md`, `adapters/codex.md`, and `adapters/openclaw.md` carries exactly one Fable 5.1 line under a `## Model-specific` heading, proved by `grep -c "Fable 5.1" adapters/<file>.md` returning `1` for each, and `cursor/writ.mdc`'s Prime Directive mirror stays byte-identical to `system-instructions.md`'s `[AC-3.4]` — *met for the `## Model-specific` section of all four (section-scoped count 1); the whole-file count is 3 for `adapters/cursor.md`, whose 2026-09-03 verification record names the model twice (DEV-009)*
- [x] Given the base at or under 10,000 bytes, when `python3 scripts/prune-ledger.py check --repo . --cap-blocking` runs, then it exits 0, the ledger file carries the `<!-- cap: blocking -->` marker line, and `bash scripts/eval.sh` reports 0 findings `[AC-3.5]`

## Implementation Tasks

- [x] 3.1 Write the classification table (file, section, line count, class, action) for every remaining line of `system-instructions.md` and `commands/_preamble.md` in this story's What Was Built, as the record against which the cut is executed and verified `[AC-3.1]`
- [x] 3.2 Remove the duplicate `## File Organization` section and the preamble restatements (`## Tool Selection`, `## Knowledge Context`, `## Adapter Neutrality` where they restate adapter files), each removal's ledger rows landing in the same commit `[AC-3.2]`
- [x] 3.3 Cut `## Identity & Approach`, `## Command Execution Protocol` coaching, `### Judgment Principles`, and `### Prose`, with ledger rows in the same commit `[AC-3.2]`
- [x] 3.4 Cut `## Interaction Tool Selection` beyond the tool-naming rule, `## Session Auto-Orientation`, and the Skills explainer, with ledger rows in the same commit `[AC-3.2]`
- [x] 3.5 Move the Fable 5.1 batching line out of `system-instructions.md` into each `adapters/*.md` file under its own `## Model-specific` heading, one line per file `[AC-3.4]`
- [x] 3.6 Measure bytes with `prune-ledger.py measure`, stop cutting once the total is at or under 10,000 (do not cut past the cap for its own sake), append `<!-- cap: blocking -->` to the ledger, and sync `cursor/writ.mdc`'s Prime Directive mirror to match `system-instructions.md` `[AC-3.1, AC-3.3, AC-3.5]`
- [x] 3.7 Verify all acceptance criteria: `python3 scripts/prune-ledger.py check --repo . --cap-blocking` exits 0, `bash scripts/eval.sh` shows 0 findings, `grep -c "Fable 5.1" adapters/<file>.md` returns `1` for all four adapters, `check_prime_directive_sync` and `check_anti_sycophancy` stay green, and append the decision-log line `{date} stage-2: Story 3 — behavior requests cut, base at <bytes> bytes, cap flipped to blocking` to the story's completion commit `[AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5]`

## Notes

**Technical considerations.** The cap is the finish line, not the goal (Business Rule 1) — stop cutting once `prune-ledger.py measure` reports at or under 10,000 bytes, even if candidate sections remain uncut. A line that is half constraint, half coaching is split at the sentence boundary and only the coaching half is removed, never dropped as a whole line to save the trouble of splitting it. The reason column for every `behavior-request` row is capped at 120 characters and must name *why* Fable 5.1-class models do the thing unprompted, not just restate the removed text. Kept sections are diffed against `cf84742`, not against Story 2's closing commit, per Business Rule 5.

**Risks.** A behavior request that turns out to be load-bearing for Fable 5.1 will not surface until Story 5's baseline re-run — this story cannot verify that risk itself, only minimize it by following the constraint test from the research doc line by line rather than by byte-count pressure. Cutting the wrong half of a split line (constraint half instead of coaching half) silently weakens a hard boundary; the diff-against-`cf84742` check in AC-3.3 is the only guard, so the kept-sections list must be checked, not assumed, after every cut commit.

**Integration with later stories.** Story 4 works on `implement-story.md` frontmatter and does not touch the base files this story cuts. Story 5 reverts Stories 2 and 3 as one commit range if the baseline re-run falls short of 8/8 (Business Rule 10) — every commit in this story must therefore be independently revertible as part of that range, which is why ledger rows land in the same commit as their removal (Business Rule 4) rather than being batched at story close.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows** [technical-spec.md → ## 1. `scripts/prune-ledger.py` (Story 1) → Findings table: `removed_not_in_ledger`, `over_cap`] [technical-spec.md → ## 3. Move targets (Story 2) → cross-reference for the base byte count entering this story]
- **Shadow paths** [spec.md → 🎯 Experience Design → Error experience → "A kept line accidentally reflowed"] [spec.md → 🎯 Experience Design → Error experience → "A removal without a ledger line"]
- **Business rules** [spec.md → 📋 Business Rules → 1 (constraint test is the rule, bytes are the finish line)] [spec.md → 📋 Business Rules → 3 (removed includes moved; reason classes)] [spec.md → 📋 Business Rules → 4 (ledger rows land in the removal commit)] [spec.md → 📋 Business Rules → 5 (kept lines byte-identical against cf84742)] [spec.md → 📋 Business Rules → 7 (one model-specific line per model per adapter)] [spec.md → 📋 Business Rules → 8 (Prime Directive mirror stays byte-identical)] [spec.md → 📋 Business Rules → 12 (decision-log line)]
- **Experience** [spec.md → 🎯 Experience Design → Happy path, step 3] [spec.md → 🎯 Experience Design → State catalog → "cuts in progress" / "cap reached"]
- **Requirements** [spec.md → Detailed Requirements → Story 3 — Cut behavior requests]
- **Codebase** [technical-spec.md → ## 4. Cut candidates (Story 3) → classification table columns, candidate sections and bytes, kept-verbatim list, needed cut arithmetic] [technical-spec.md → ## 2. Ledger format (Story 1) → row format and class vocabulary] [.writ/research/2026-09-05-goldilocks-harness-research.md → the constraint-vs-behavior-request test] [system-instructions.md, commands/_preamble.md → the two files being cut] [adapters/claude-code.md, adapters/cursor.md, adapters/codex.md, adapters/openclaw.md → destination for the batching line] [cursor/writ.mdc → Prime Directive mirror to keep in sync]

---

## What Was Built

**Implementation Date:** 2026-09-07

### Classification table

Every line of both base files as they stood at Story 2's close (`f8daec1`; `system-instructions.md` 181 lines, `commands/_preamble.md` 95 lines), classified by ADR-026's three-way test — environment fact / human boundary stay, behavior request leaves — and the research doc's F2 rule (a line that names a fact about the world is durable; a line that names a fact about the model is not). Line count is non-blank lines; blank lines need no ledger row (DEV-002). Action names the commit that cut the rows. 62 + 58 = 120 non-blank lines kept; 74 + 11 = 85 non-blank lines cut = 85 ledger rows (67 `behavior-request`, 18 `duplicate`), rows 103–187 of the ledger.

| File | Section | Lines (f8daec1) | Line count | Class | Action |
|---|---|---|---|---|---|
| `system-instructions.md` | (before first heading) — frontmatter, title | 1–6 | 4 (+2 blank) | environment-fact | keep |
| `system-instructions.md` | ## Identity & Approach | 7–17 | 7 (+4 blank) | behavior-request | cut (11f590b) |
| `system-instructions.md` | ## Command Execution Protocol — heading | 18–19 | 1 (+1 blank) | behavior-request | cut (11f590b) |
| `system-instructions.md` | ## Command Execution Protocol — item 1, welcome greetings | 20–30 | 11 (+0 blank) | behavior-request | cut (11f590b) |
| `system-instructions.md` | ## Command Execution Protocol — item 2, parallel tool execution | 31–31 | 1 (+0 blank) | behavior-request | cut (11f590b); Fable 5.1 line in adapters/*.md (99c1b0e) |
| `system-instructions.md` | ## Command Execution Protocol — item 3, follow the Prime Directive | 32–33 | 1 (+1 blank) | behavior-request | cut (11f590b) |
| `system-instructions.md` | ## Prime Directive — heading | 34–35 | 1 (+1 blank) | environment-fact | keep (anchor read by check_prime_directive_sync) |
| `system-instructions.md` | ## Prime Directive — first-obligation sentence | 36–37 | 1 (+1 blank) | human-boundary | keep |
| `system-instructions.md` | ### Hard Constraints | 38–54 | 14 (+3 blank) | human-boundary | keep verbatim |
| `system-instructions.md` | ### Recommended Delivery Exception | 55–82 | 26 (+2 blank) | human-boundary | keep verbatim |
| `system-instructions.md` | ### Recommendation Semantics — labeling rule | 83–90 | 6 (+2 blank) | environment-fact | keep verbatim (the `(Recommended)` suffix contract) |
| `system-instructions.md` | ### Recommendation Semantics — pointer | 91–92 | 1 (+1 blank) | environment-fact | keep (Story 2 pointer) |
| `system-instructions.md` | ### Judgment Principles | 93–108 | 13 (+3 blank) | behavior-request | cut (11f590b) |
| `system-instructions.md` | ### Prose | 109–116 | 4 (+4 blank) | behavior-request | cut (11f590b) |
| `system-instructions.md` | ## File Organization | 117–132 | 13 (+3 blank) | duplicate | cut (f6fa3af); survives in commands/_preamble.md |
| `system-instructions.md` | ## Interaction Tool Selection — heading | 133–134 | 1 (+1 blank) | environment-fact | keep |
| `system-instructions.md` | ## Interaction Tool Selection — intro, AskQuestion and Plan Mode example lists | 135–148 | 11 (+3 blank) | behavior-request | cut (ece8cc5) |
| `system-instructions.md` | ## Interaction Tool Selection — the principle (names AskQuestion, Plan Mode, ADR-001) | 149–150 | 1 (+1 blank) | environment-fact | keep |
| `system-instructions.md` | ## Interaction Tool Selection — typical contract-first flow | 151–156 | 5 (+1 blank) | behavior-request | cut (ece8cc5) |
| `system-instructions.md` | ## Startup Update Awareness — heading, trigger, pointer | 157–162 | 3 (+3 blank) | environment-fact | keep (Story 2 state) |
| `system-instructions.md` | ## Session Auto-Orientation | 163–172 | 6 (+4 blank) | behavior-request | cut (ece8cc5) |
| `system-instructions.md` | ## Skills — heading | 173–174 | 1 (+1 blank) | environment-fact | keep |
| `system-instructions.md` | ## Skills — three-primitives explainer | 175–176 | 1 (+1 blank) | duplicate | cut (ece8cc5); survives in .writ/docs/skills.md |
| `system-instructions.md` | ## Skills — pointer | 177–178 | 1 (+1 blank) | environment-fact | keep (Story 2 pointer) |
| `system-instructions.md` | ## Model Tiers — heading, pointer | 179–181 | 2 (+1 blank) | environment-fact | keep (Story 2 pointer) |
| `commands/_preamble.md` | (before first heading) — frontmatter, title | 1–8 | 6 (+2 blank) | environment-fact | keep |
| `commands/_preamble.md` | (before first heading) — what this file is | 9–11 | 2 (+1 blank) | environment-fact | keep |
| `commands/_preamble.md` | ## Plan Mode Integrity | 12–17 | 4 (+2 blank) | human-boundary | keep verbatim |
| `commands/_preamble.md` | ### Narrow Recommended-Delivery Exception | 18–28 | 9 (+2 blank) | human-boundary | keep verbatim |
| `commands/_preamble.md` | ## User Challenge — heading, trigger definition | 29–35 | 5 (+2 blank) | human-boundary | keep verbatim |
| `commands/_preamble.md` | ## User Challenge — four required parts | 36–39 | 3 (+1 blank) | environment-fact | keep verbatim (contract shape) |
| `commands/_preamble.md` | ## User Challenge — select-or-pause, validator path | 40–48 | 8 (+1 blank) | human-boundary | keep verbatim |
| `commands/_preamble.md` | ## Autonomy Gate Classes — heading, table | 49–60 | 9 (+3 blank) | human-boundary | keep verbatim |
| `commands/_preamble.md` | ## Autonomy Gate Classes — reversibility precondition | 61–62 | 1 (+1 blank) | human-boundary | keep verbatim |
| `commands/_preamble.md` | ## Autonomy Gate Classes — stakes triage (ADR-023) | 63–64 | 1 (+1 blank) | human-boundary | keep verbatim (in a kept section; coaching-shaped, see decision 7) |
| `commands/_preamble.md` | ## File Organization | 65–71 | 5 (+2 blank) | environment-fact | keep (the surviving copy) |
| `commands/_preamble.md` | ## Artifact Integrity — heading, verify Required Artifacts | 72–74 | 2 (+1 blank) | environment-fact | keep verbatim |
| `commands/_preamble.md` | ## Artifact Integrity — HALT / never auto-run a mutating repair / degraded mode | 75–77 | 2 (+1 blank) | human-boundary | keep verbatim |
| `commands/_preamble.md` | ## Artifact Integrity — creating commands, never inspect .writ/state/ | 78–79 | 1 (+1 blank) | environment-fact | keep verbatim (trailing blank line went with the file end) |
| `commands/_preamble.md` | ## Tool Selection — heading, AskQuestion, Plan Mode | 80–83 | 3 (+1 blank) | duplicate | cut (f6fa3af); survives as the Interaction Tool Selection rule |
| `commands/_preamble.md` | ## Tool Selection — todo_write | 84–84 | 1 (+0 blank) | duplicate | cut (f6fa3af); survives in adapters/*.md tool-mapping tables |
| `commands/_preamble.md` | ## Tool Selection — parallel tool calls | 85–86 | 1 (+1 blank) | behavior-request | cut (f6fa3af); Fable 5.1 line in adapters/*.md (99c1b0e) |
| `commands/_preamble.md` | ## Knowledge Context | 87–91 | 3 (+2 blank) | behavior-request | cut (f6fa3af) |
| `commands/_preamble.md` | ## Adapter Neutrality | 92–95 | 3 (+1 blank) | behavior-request | cut (f6fa3af) |

### Per-cut commits and bytes

`prune-ledger.py measure --repo .` totals; `check --repo .` exit 0 at every commit (verified in a detached worktree: `removed: n, re-added: 0` at each).

| Task | Commit | What left | Rows | Base after |
|---|---|---|---|---|
| — | `f8daec1` (Story 2 close) | — | 102 | 15,713 |
| 3.2 | `f6fa3af7` | `system-instructions.md` `## File Organization` (13 rows, `duplicate`); `_preamble.md` `## Tool Selection` (4 `duplicate` + 1 `behavior-request`), `## Knowledge Context` (3), `## Adapter Neutrality` (3) | 126 | 14,437 |
| 3.3 | `11f590b` | `## Identity & Approach` (7), `## Command Execution Protocol` (14: heading, greeting list, parallel item, follow-PD item), `### Judgment Principles` (13), `### Prose` (4); `cursor/writ.mdc` took the Judgment Principles + Prose cut in the same commit | 164 | 11,713 |
| 3.4 | `ece8cc5` | `## Interaction Tool Selection` beyond its rule line (16) → 10,649; `## Session Auto-Orientation` (6) → 10,090; `## Skills` explainer (1, `duplicate`) → 9,704 | 187 | **9,704** |
| 3.5 | `99c1b0e` | nothing from the base; `## Model-specific` + one Fable 5.1 line appended to each of the four adapters | 187 | 9,704 |
| 3.6 | `8596281` | nothing from the base; `<!-- cap: blocking -->` appended to the ledger; `cursor/writ.mdc` re-synced to the pruned base | 187 | 9,704 |

**Per file and section (`measure`, before → after):** `system-instructions.md` 10,061 → **4,600**: before-first-heading 57 → 57; Identity & Approach 663 → 0; Command Execution Protocol 827 → 0; Prime Directive 112 → 112; Hard Constraints 1,064 → 1,064; Recommended Delivery Exception 1,778 → 1,778; Recommendation Semantics 655 → 655; Judgment Principles 816 → 0; Prose 418 → 0; File Organization 728 → 0; Interaction Tool Selection 1,241 → 177; Startup Update Awareness 417 → 417; Session Auto-Orientation 559 → 0; Skills 550 → 164; Model Tiers 176 → 176. `commands/_preamble.md` 5,652 → **5,104**: before-first-heading 343; Plan Mode Integrity 270; Narrow Recommended-Delivery Exception 635; User Challenge 1,189; Autonomy Gate Classes 1,773; File Organization 320 (all unchanged); Artifact Integrity 575 → 574 (its trailing blank line is now the file's end); Tool Selection 244 → 0; Knowledge Context 122 → 0; Adapter Neutrality 181 → 0. **Total 15,713 → 9,704 bytes**, 296 under the cap; the cap was reached with the last candidate the spec named and nothing outside that list was cut.

### Files Created

[None created]

### Files Modified

- **`system-instructions.md`** (nine sections)
  - 99 lines removed (74 non-blank), 0 added. Remaining: frontmatter and title, `## Prime Directive` → `### Recommendation Semantics` verbatim, `## Interaction Tool Selection` (heading + the one rule line), `## Startup Update Awareness` (Story 2 state), `## Skills` and `## Model Tiers` (heading + pointer). 82 lines.
- **`commands/_preamble.md`** (three sections)
  - 17 lines removed (11 non-blank), 0 added; the file now ends at `## Artifact Integrity`. 78 lines (cap 95). Shared by symlink with `.claude/commands/` and `.cursor/commands/`.
- **`.writ/decision-records/pruned-instructions-ledger.md`** (rows 103–187, marker)
  - 85 rows dated 2026-09-07, class `behavior-request` (67; every reason ≤ 120 chars, longest 120, naming why Fable 5.1-class models do the thing unprompted or where the model-specific nudge now lives) or `duplicate` (18; reason names the surviving copy). `<!-- cap: blocking -->` appended as the last line. Header and rows 1–102 untouched.
- **`adapters/claude-code.md`, `adapters/cursor.md`, `adapters/codex.md`, `adapters/openclaw.md`** (new `## Model-specific` section at the end)
  - One line each: *Claude Fable 5.1 may serialize independent tool calls: issue independent reads, searches, and checks as one batched message, not one at a time (the only model-specific line this adapter carries — ADR-026; see ADR-024 for delegation).* Counts: `grep -c "Fable 5.1"` → claude-code 1, cursor 3, codex 1, openclaw 1; `awk '/^## Model-specific/,0' <file> | grep -c "Fable 5.1"` → 1, 1, 1, 1 (DEV-009).
- **`cursor/writ.mdc`** (whole file)
  - Commit `11f590b`: Judgment Principles and Prose removed in lockstep with the base (Business Rule 8). Commit `8596281`: the file becomes `cp system-instructions.md cursor/writ.mdc` — 20,885 → 4,600 bytes, `cmp` clean (DEV-011).
- **`.writ/specs/2026-09-07-phase11-stage2-prune-the-base/spec-lite.md`** (Files in Scope → adapters row)
  - DEV-010 Small-drift auto-amend; pre-edit SHA-256 `af035cf7b19bd3424bb2854c48f6a6b84c8b370ac6bd2b93ef746b44b39517c9`.
- **`.writ/specs/2026-09-07-phase11-stage2-prune-the-base/drift-log.md`** — DEV-009, DEV-010, DEV-011.
- **`.writ/decision-log.md`** — one `2026-09-07 stage-2:` line (Business Rule 12).
- **`user-stories/README.md`** — Story 3 row and totals.

### Implementation Decisions

1. **The classification table was written before the first cut and the cut executed against it.** Line ranges are `f8daec1` numbers; each cut commit's row count equals the table's non-blank count for those ranges (13 + 11 = 24 in 3.2, 38 in 3.3, 23 in 3.4), so the table is the record the ledger was checked against, not a description written afterwards.
2. **Whole lines only; no line was split.** Every candidate line was either wholly a behavior request/duplicate or wholly kept, so the "removal + addition" path for a mixed line was never needed; `git diff -U0 cf84742` adds exactly Story 2's four pointer lines and nothing from this story.
3. **The Interaction Tool Selection rule is the blockquote line.** *Use AskQuestion when you know the option space. Use Plan Mode when you need to discover it. See ADR-001* names both tools and the decision; the intro sentence, the two example lists, and the four-step flow are the tutorial around it. `SwitchMode` leaves with the Plan Mode header line; the six commands that use Plan Mode name `SwitchMode` themselves.
4. **`todo_write` and `.writ/knowledge/` leave the base as instructions, stay as facts.** The four adapters' tool-mapping tables carry `todo_write`; the preamble's `## File Organization` still lists `knowledge/`; eight commands and all four adapters name the knowledge scan where it happens. The base no longer tells the model to use either.
5. **The greeting list is cut on the keep-rule, not the unprompted-rule.** A greeting names no environment fact and no human boundary, so ADR-026 says it leaves; its rows' reason says so (*persona flourish naming no fact or boundary*) rather than claiming the model would produce Writ's greetings on its own. It is the only cut where "why the model does it unprompted" is not the whole reason.
6. **`cursor/writ.mdc` is re-synced whole** (DEV-011): it is the rule Cursor loads on every session, and it was a byte copy of the base at `cf84742`. Leaving 16 KB of moved-and-cut text in it would have exempted Cursor from the cut Story 5 measures.
7. **Two kept lines are flagged, not cut.** `_preamble.md` line 63 (*Stakes triage*, ADR-023) is coaching-shaped but sits inside `## Autonomy Gate Classes`, which the spec keeps verbatim, and its last sentence (*Safety gates are never capped by count*) is a boundary; it is the first candidate for the agent-prompt pass ADR-026 defers. The Startup Update Awareness trigger still says *before session auto-orientation*, a section that no longer exists; Business Rule 5 forbids rewording a kept line while the cut is open, so the dangling reference waits for the freeze to lift.
8. **No governor pin was retargeted.** Every `require_literal` on the base (`check_autonomy_governance` 6 + `writ.mdc` 1, `check_recommendation_semantics` 3 + `writ.mdc` 2, `check_recommended_spec_implementation`, `check_phase_lanes`/User Challenge, `check_artifact_integrity` 4 on `_preamble.md`) and every test docstring reference (`test_governor_enforcement.py`, `test_governor_mutation.py`, `test_measure_invocation.py`, `test_eval_length_caps.sh`) points at kept lines; grepping `scripts/eval.sh`, `scripts/tests/`, `.writ/eval/` for 30 literals from the cut lines found only `scripts/gen-skill.sh`'s paraphrase of the personality bullets (a generated-catalog summary, not a pin; left as is).

### Test Results

**Verification:** `python3 scripts/prune-ledger.py check --repo .` exit 0 at each of `f6fa3af`, `11f590b`, `ece8cc5`, `99c1b0e`, and with `--cap-blocking` at `8596281` (126 / 164 / 187 / 187 / 187 rows, `re-added: 0`, verified in a detached worktree per commit); `uv run --python 3.9 pytest -q` — 1075 passed, 1 skipped; all 14 `scripts/tests/test_*.sh` green; `bash scripts/eval.sh` (sandbox off, all checks) → `Findings: 0`, `Run errors: 0`, exit 0, `pruned-base` note `base: 9704 bytes (cap 10000), ledger: 187 rows, removed: 187, re-added: 0` with `--cap-blocking` in force and no `over_cap` note; `python3 scripts/build-smoke.py check --project .` → `unverifiable` (unsupported stack; markdown repo).
- ✅ After every cut commit, one `--check` per invocation: `prime-directive-sync`, `anti-sycophancy`, `autonomy-governance`, `recommendation-semantics`, `preamble`, `required-sections`, `referenced-paths`, `pruned-base` — each exit 0, `Findings: 0`; `broken-refs` and `length` also 0 after the adapter edit
- ✅ AC-3.3: `## Prime Directive` → `### Hard Constraints`, `### Recommended Delivery Exception`, `## Plan Mode Integrity` + `### Narrow Recommended-Delivery Exception`, `## User Challenge`, `## Autonomy Gate Classes`, `## File Organization`, `## Artifact Integrity` extracted from `cf84742` and HEAD and `diff`ed: identical (Artifact Integrity differs only by the trailing blank line that became the file end — whitespace, DEV-002); every non-blank line of both files at HEAD exists verbatim in `cf84742` except Story 2's four pointers
- ✅ AC-3.4: `cmp system-instructions.md cursor/writ.mdc` clean; adapter counts as recorded above
- ✅ AC-3.5: `python3 scripts/prune-ledger.py check --repo . --cap-blocking` exit 0; `grep -Fxq '<!-- cap: blocking -->'` true
- ✅ `commands/_preamble.md` 78 lines against the 95-line cap (`test_eval_length_caps.sh` scenario 7)
- ✅ Leanness warnings all pre-existing (commands/skills/scripts/adapters ceilings); adapters +16 lines on a surface already past its 2026-09-03 ceiling before this story; `COMMAND_BYTE_BUDGET` note now reports the live base at 9,704 against the 24,960 pin — a report, not a finding
- ✅ No new scripts; no coverage claim (documentation-only story)

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Medium (DEV-009, DEV-011); Small (DEV-010)
- **Security:** None — markdown removals, one appended line per adapter, a file copy
- **Boundary Compliance:** owned set (`system-instructions.md`, `commands/_preamble.md`, the ledger, four adapters, `cursor/writ.mdc`, spec bookkeeping); no cross-boundary edits — `scripts/eval.sh` and `scripts/tests/` read only

### Deviations from Spec

- **[DEV-009] `grep -c "Fable 5.1" adapters/cursor.md` cannot return 1** — Severity: Medium
  - Spec said: AC-3.4's proof is `grep -c` returning `1` for each adapter
  - Reality: `adapters/cursor.md`'s 2026-09-03 verification record already names the model on two lines; whole-file count 3, `## Model-specific` section count 1; Business Rule 7 and the Goal Card's instruction-line rule hold
  - Resolution: ⚠️ flagged; pipeline PASS; both counts recorded; `spec.md` unchanged
- **[DEV-010] The base carried no literal Fable 5.1 batching line** — Severity: Small
  - Spec said: move "the Fable 5.1 batching line currently in `system-instructions.md`"
  - Reality: the base named only generic parallel-execution nudges (three lines); they left as `behavior-request` rows and the model-specific line was authored in the adapters
  - Resolution: logged; `spec-lite.md` amended
- **[DEV-011] `cursor/writ.mdc` re-synced whole** — Severity: Medium
  - Spec said: `writ.mdc` is the Prime Directive mirror (Business Rule 8 governs that block only; DEV-007 deferred the rest)
  - Reality: the file is a byte copy of the pruned base, because it is the `alwaysApply` rule Cursor sessions load
  - Resolution: ⚠️ flagged; pipeline PASS; `spec.md` unchanged

### For Story 5

- The pruned base is **9,704 bytes** (`system-instructions.md` 4,600 + `commands/_preamble.md` 5,104); the ledger has 187 rows and the cap is blocking. The revert range for Business Rule 10 is contiguous: `25518d0` (Story 2's first move) through this story's completion and SHA-record commits — Story 2's four moves and two bookkeeping commits, then this story's five cut/move commits and two bookkeeping commits; no other story's commit sits inside it (`git log --oneline 25518d0~1..HEAD`).
- `cursor/writ.mdc` is in that range too (`11f590b`, `8596281`); a revert restores the full pre-move rule.
- The eight runs load the same base on every platform now; nothing model-specific remains in the base, and the only model-specific line is the adapters' `## Model-specific` one.

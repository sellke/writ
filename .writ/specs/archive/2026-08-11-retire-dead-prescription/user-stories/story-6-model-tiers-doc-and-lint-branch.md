# Story 6: Retire the Prose-Note Carrier in the Explainer and the Lint

> **Status:** Complete
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer who has just corrected the root contract's frontmatter claim
**I want to** `.writ/docs/model-tiers.md` and `scripts/lint-skill.sh` to describe and enforce the carrier that actually exists, instead of the prose-note workaround the false claim justified
**So that** the user-facing explainer and the only validator of `model_tier` values agree with `system-instructions.md` rather than outliving it

> **Approved scope addition, 2026-08-11.** This story is not part of the original locked contract's clauses (a)–(e). The maintainer added it after the Story 1 sweep found the same *"commands have no frontmatter mechanism / verified 0/31 files"* claim in two further live prescribing artifacts. See `spec.md` → Detailed Requirements → "(f) Approved scope addition".

## Acceptance Criteria

- [x] Given `.writ/docs/model-tiers.md` § "Where `model_tier` Lives", when the Command row (line 45) is read, then its Carrier column names `---` YAML frontmatter — carried by 32/32 files in `commands/` (31 commands + `_preamble.md`) — its Example column shows a frontmatter field rather than a prose note, and the row contains no claim that commands carry no frontmatter mechanism and no "verified 0/31 files" figure.
- [x] Given the literals `verified 0/31 files`, `no frontmatter mechanism`, and `carry no frontmatter mechanism`, when `.writ/docs/model-tiers.md` and `scripts/lint-skill.sh` are grepped, then zero hits are returned in either file.
- [x] Given `.writ/docs/model-tiers.md` line 95 (`/new-command` emission) and line 97 (`lint-skill.sh` validation description), when each is read after the edit, then each states what the named artifact actually does as measured at implementation time — not what this spec intends it to do.
- [x] Given `scripts/lint-skill.sh`'s `lint_model_tier()`, when a file declares `model_tier: orchestration` or `model_tier: capability` in YAML frontmatter or in an agent's fenced configuration block, then the value is still captured and validated; and when the function is read, then it carries no branch matching the `**Model tier (advisory only):** <value>` prose shape.
- [x] Given `scripts/lint-skill.sh`'s `usage()` text and the `lint_model_tier()` comment block, when read after the edit, then neither describes a command prose note as a recognized carrier, and both remain consistent with the narrowed allow-list Story 2 left behind.
- [x] Given `bash scripts/eval.sh --check=skill-lifecycle`, when run after the lint edit, then it reports PASS — the check's four `require_literal` assertions against `scripts/lint-skill.sh` (`candidate|proven|promoted`, `State is EARNED from evidence`, `Lifecycle-unearned`, `Lifecycle-evidence`) all live outside `lint_model_tier()` and must remain intact.
- [x] Given `.writ/decision-records/adr-016-model-tier-delegation.md`, `CHANGELOG.md`, and `commands/new-command.md`, when diffed before and after this story, then all three are byte-unchanged.
- [x] Given the full validation suite, when `bash scripts/eval.sh` runs, then it reports `Findings: 0` with no new `eval-exempt:` marker introduced by this story.

## Implementation Tasks

- [x] 6.1 Re-measure before editing (Business Rule 1): `ls commands/*.md | wc -l` and a per-file `head -1` frontmatter check (expected 32/32, of which 31 are commands and 1 is `_preamble.md`); `grep -rn -F "Model tier (advisory only)" commands/ agents/ skills/ .writ/docs/ scripts/ system-instructions.md cursor/` to record the live occurrence set at story start. Read `system-instructions.md` § Model Tiers as Story 1 left it — the explainer must restate the root contract, not diverge from it.
- [x] 6.2 Rewrite `.writ/docs/model-tiers.md`'s Command row (line 45) in the "Where `model_tier` Lives" table: Carrier becomes the existing `---` YAML frontmatter that already holds `name:` and `description:`; Example becomes `model_tier: orchestration   # advisory only`, matching the Skill row's shape. Leave the Skill and Agent rows and the umbrella-term sentence beneath the table (line 47) untouched — both are accurate as measured.
- [x] 6.3 Verify line 95 against the file it describes before rewriting it. It claims `/new-command` emits the locked prose note. `commands/new-command.md` is owned by the sibling spec `2026-08-11-component-contract` (its Story 1) and is **not** edited here. If that spec has landed and `new-command.md` now emits a frontmatter field, describe that. If it has not, and `new-command.md` still emits the prose note, do **not** write a claim that it emits frontmatter — record the divergence per Task 6.6 instead. Replacing one false claim with another fails this spec's premise.
- [x] 6.4 Rewrite `.writ/docs/model-tiers.md` line 97 to describe what `lint_model_tier()` recognizes after Task 6.5: `model_tier: <value>` in skill frontmatter, command frontmatter, or an agent's Agent Configuration block. Drop "or a command's prose note". Story 2 will already have narrowed the allow-list on this line to `^(orchestration|capability)$` — confirm that, do not re-narrow it.
- [x] 6.5 Remove the prose-note branch from `scripts/lint-skill.sh`'s `lint_model_tier()`: the `elif` at line 279 and its `value=` assignment at line 280. The `if` at line 277 stays and is sufficient — its regex is unanchored and the function reads every raw line of the file, so a command frontmatter `model_tier: capability` is already captured by it. Then update the comment block (lines 253–265) to describe one recognized shape instead of two, and the `usage()` text (line 27) to stop naming a command prose note. Story 2 owns the ordinal half of both blocks — edit only the prose-note half and locate by literal, not by line number.
- [x] 6.6 Record, in "What Was Built", the cross-spec state this story leaves behind: whether `commands/new-command.md` still prescribes the prose note at implementation time, and that a prose note written after this story is no longer validated by any lint. Zero shipped commands carry the note today (Task 6.1's grep), so the removal orphans no live validation — state the measured count rather than asserting it.
- [x] 6.7 Verify: `bash scripts/lint-skill.sh skills/*/SKILL.md` exits 0; the same script over all 7 `agents/*.md` still captures and validates their fenced `model_tier` values; a synthetic file carrying only `> **Model tier (advisory only):** bogus` produces no `model_tier` finding (proving the branch is gone) while a synthetic `model_tier: bogus` still does. Then `bash scripts/eval.sh --check=skill-lifecycle` PASS, `bash scripts/eval.sh` → `Findings: 0`, `bash scripts/gen-skill.sh --check` exit 0, and a diff proving `adr-016-model-tier-delegation.md`, `CHANGELOG.md`, and `commands/new-command.md` are unchanged.

## Notes

**Technical considerations:**

- **Remove, do not retarget.** `lint_model_tier()` (`scripts/lint-skill.sh:268-290`) reads the entire raw file line by line and its first branch is `[[ "$line" =~ model_tier:[[:space:]]*([A-Za-z0-9-]+) ]]` — unanchored, not fence-gated (the function's own comment at lines 255–257 says it is "format-agnostic and scans the ENTIRE raw file"). A `model_tier:` line in command frontmatter is therefore already matched by branch 1. There is no second frontmatter shape to retarget the `elif` to; retargeting would produce a duplicate of a branch that already exists. The `elif` at line 279 matches only `**Model tier (advisory only):** <value>`, which is the prose form this spec retires.
- **The `skill-lifecycle` eval check is currently PASSING and must stay that way.** `check_skill_lifecycle()` (`scripts/eval.sh:2476`) drives fixtures through `lint-skill.sh` via `scripts/eval-skill-lifecycle.py` and then asserts four literals in the lint script: `candidate|proven|promoted`, `State is EARNED from evidence`, `Lifecycle-unearned`, `Lifecycle-evidence`. All four sit in `lint_lifecycle()`, not `lint_model_tier()`. Measured: `grep -n "model_tier\|Model tier" scripts/eval-skill-lifecycle.py` returns **zero lines** — the fixture generator has no `model_tier` case at all. The removal has no path to that check, but Acceptance Criterion 6 requires proving it rather than assuming it.
- `.writ/docs/model-tiers.md` line 97 is a **shared line** with Story 2: it carries both the prose-note phrase this story removes and the `^(orchestration|capability|-[0-9]+)$` allow-list Story 2 narrows. Depending on Story 2 is what makes the two edits sequential instead of colliding.
- No eval check reads `.writ/docs/model-tiers.md` — `grep -n "model-tiers" scripts/eval.sh scripts/*.py` returns nothing. The suite will stay green regardless of what this story writes into it, so the acceptance criteria, not the gate, are the verification. The same is true of Story 5 and for the same reason.
- `.writ/docs/*.md` ships to installed projects through `install.sh`'s doc fan-out. This explainer is read by Writ *users*, not only by this repo's maintainer — the corrected row is user-facing documentation, not an internal note.

**Risks / challenges:**

- **A live producer may survive the removal.** `commands/new-command.md` still instructs every generated command to carry the prose note (lines 148 and 171), and the sibling spec that owns that file states the prose-note *format* stays locked. If that spec lands unchanged, `/new-command` will emit a note that no lint validates. This is an accepted consequence, not an oversight: zero shipped commands carry the note today, so nothing currently validated stops being validated. Task 6.6 exists to put the state on the record instead of leaving it to be discovered.
- Over-broad grep. `Model tier (advisory only)` contains regex metacharacters — use `grep -F`. A plain `grep -rn "Model tier (advisory only)"` silently misses most hits because BRE treats the parentheses as literals in some positions and not others; the measured set at story-writing time was 6 live occurrences, found only with `-F`.
- The temptation to "helpfully" fix the historical records. See Business Rule 8 — `.writ/decision-records/adr-016-model-tier-delegation.md:76` and `CHANGELOG.md:143` both carry the same "no frontmatter mechanism / verified 0/31 command files" wording. Both are correct descriptions of what was true when written and are explicitly out of scope.

**Integration points:**

- **Depends on Story 2** for file overlap in both of its files. Story 2 edits `.writ/docs/model-tiers.md` (lines 75, 82, 86, 97, 103) and `scripts/lint-skill.sh` (`usage()` lines 26–27, the `lint_model_tier()` comment block at 253–265, and the allow-list at 285–286). This story edits the prose-note half of the same two blocks and the same line 97. Nothing in this story's *content* depends on the ordinal deprecation — the dependency is single-writer-per-file serialization, the same reason Stories 1–3 are chained.
- **Not dependent on Story 3.** Story 3 edits `system-instructions.md` § Skills, `.writ/docs/skills.md`, and `adapters/`. Zero file overlap with this story, so Stories 3 and 6 can run in parallel once Story 2 has landed.
- **Story 1 no longer owns these two artifacts.** Story 1's original Tasks 1.5 and 1.6 covered `.writ/docs/model-tiers.md` lines 45/95/97 and the `lint-skill.sh` prose branch; both were transferred here on 2026-08-11 so that a single story owns the decision rather than leaving it optional. Story 1 retains `system-instructions.md` line 277 and its `cursor/writ.mdc` mirror.
- **`commands/new-command.md` is owned by the sibling spec `2026-08-11-component-contract`, Story 1** (`.writ/specs/2026-08-11-component-contract/user-stories/story-1-contract-schema-and-authoring-template.md`, Task 1.6). That spec declares `2026-08-11-retire-dead-prescription` as its dependency and lands after it. This story does not edit `new-command.md` and must not, even to keep line 95 of the explainer true — the fix for a divergence there is a recorded finding, not a cross-spec edit.
- **`.writ/decision-records/adr-016-model-tier-delegation.md:76` and `CHANGELOG.md:143` are historical records and are not edited.** ADR-016 originates the prose-note carrier and correctly states the constraint as it stood on 2026-07-10; the changelog entry correctly records what shipped in that release. Business Rules 3 and 8 both forbid rewriting them. An implementer who "fixes" either has broken the spec.

## What Was Built

**Implementation Date:** 2026-08-11

### Files Modified

- **`.writ/docs/model-tiers.md`**
  - **Carrier table, Command row** — Carrier is now "The existing `---` YAML frontmatter that already holds `name:` and `description:` — carried by 32/32 files under `commands/` (31 commands + `_preamble.md`)"; Example is now `model_tier: orchestration   # advisory only`, matching the Skill row's shape. The "verified 0/31 files" figure and the no-frontmatter-mechanism claim are gone. Skill and Agent rows and the umbrella-term sentence untouched.
  - **`/new-command` emission** — now states that it emits `model_tier: <tier>` into the generated command's `---` frontmatter alongside `name:` and `description:`. Verified against the file first (see Task 6.3 below), not assumed.
  - **lint-validation sentence** — "or a command's prose note" replaced by "in command frontmatter"; the allow-list Story 2 narrowed to `^(orchestration|capability)$` was confirmed, not re-narrowed.
- **`scripts/lint-skill.sh`**
  - `lint_model_tier()`'s prose-note `elif` branch and its `value=` assignment **removed**. The `if` at the top of the loop, and the `else` / `continue` / `fi` beneath, survive intact; `bash -n` clean.
  - The `lint_model_tier()` comment block collapsed from "it recognizes two shapes" to the single key-value shape, naming skill frontmatter, command frontmatter, and agent Agent Configuration/Specification blocks as its sites.
  - `usage()` no longer names a command prose note: "Any declared model_tier value (skill or command frontmatter, or an agent config block) must be 'orchestration' or 'capability'".

### Task 6.1 — re-measured before editing (Business Rule 1)

- `ls commands/*.md | wc -l` → **32**; `head -1` frontmatter check → **32/32**.
- `grep -rn -F "Model tier (advisory only)"` across `commands/ agents/ skills/ .writ/docs/ scripts/ system-instructions.md cursor/` at story start → **3** live occurrences remaining (`.writ/docs/model-tiers.md:45`, `:84`, `scripts/lint-skill.sh:260`) — down from the 7 measured at spec-writing time, because Story 1 had already cleared `system-instructions.md`, `cursor/writ.mdc`, and both `commands/new-command.md` hits. `grep -F` was used throughout; the literal contains regex metacharacters.

### Task 6.3 — line 84 verified against the artifact it describes

`commands/new-command.md` was measured, not assumed. Under the ownership ruling recorded in Story 1's Notes (2026-08-11), this spec — not the sibling `2026-08-11-component-contract` — owns that file's Model tier note, and the sibling was amended to make zero changes there. At Story 6's implementation time the file's Step 2.1 emits a `---` frontmatter block containing `model_tier: <tier>` and its Step 2.2 checklist requires declaring that field in frontmatter. The explainer therefore describes frontmatter emission because that is what the file actually does. **No divergence to record.** This story made zero edits to `commands/new-command.md`.

### Task 6.6 — the state this story leaves behind

- **Zero shipped commands carry the prose note.** After this story, `grep -rn -F "Model tier (advisory only)"` across `commands/ agents/ skills/ .writ/docs/ scripts/ system-instructions.md cursor/ adapters/` returns **0 hits**. Nothing that was previously validated stopped being validated.
- **No lint validates a `> **Model tier (advisory only):** <value>` note any more.** This is the accepted consequence of removing rather than retargeting the branch. The risk the story anticipated — a live producer surviving the removal — did not materialize: `/new-command`'s producer was converted to frontmatter by Story 1, so the retired carrier now has neither a producer nor a consumer.
- **Removal, not retargeting, was correct.** `lint_model_tier()` reads every raw line of the file and its surviving branch (`model_tier:[[:space:]]*([A-Za-z0-9-]+)`) is unanchored and not fence-gated, so a command's frontmatter `model_tier:` is already captured by it. Retargeting the `elif` would have duplicated branch 1.

### Task 6.7 — verification

- `bash scripts/lint-skill.sh skills/*/SKILL.md` → all 6 clean, exit 0.
- Agent fenced values still captured and validated: an unmodified `agents/architecture-check-agent.md` copy → 0 `model_tier` findings; the same file with its value tampered to `bogus` → 1 finding. Capture through the agent config block survives the removal.
- Synthetic file carrying only `> **Model tier (advisory only):** bogus` → **0** `model_tier` findings, proving the branch is gone. Synthetic `model_tier: bogus` in frontmatter → **1** finding, proving branch 1 still works.
- The four `require_literal` assertions `check_skill_lifecycle()` makes against this script are all still present (`candidate|proven|promoted` ×2, `State is EARNED from evidence` ×1, `Lifecycle-unearned` ×2, `Lifecycle-evidence` ×1) — all live in `lint_lifecycle()`, none in `lint_model_tier()`.
- `bash scripts/eval.sh --check=skill-lifecycle` → **PASS** (report `.writ/state/eval-20260811-212318.md`).
- `grep -F -e "verified 0/31 files" -e "no frontmatter mechanism" -e "carry no frontmatter mechanism" -e "Model tier (advisory only)" .writ/docs/model-tiers.md scripts/lint-skill.sh` → **0 hits**.
- `git diff --stat` for `.writ/decision-records/adr-016-model-tier-delegation.md`, `CHANGELOG.md`, and `commands/new-command.md` over this story's changes → **empty**. All three byte-unchanged by Story 6 (Business Rules 3 and 8).
- `bash scripts/eval.sh` → `Findings: 0`, `Run errors: 0` (report `.writ/state/eval-20260811-212336.md`). `bash scripts/gen-skill.sh --check` → exit 0.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] `bash scripts/eval.sh` reports `Findings: 0`
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 1 (measured, not asserted — re-count the frontmatter files and re-grep the prose string), Rule 3 (active surface only — ADR-016 and `CHANGELOG.md` untouched), Rule 4 (`Findings: 0` per story, no self-serving exemptions), Rule 5 (no new contract fields — this documents the carrier, it does not populate it), Rule 8 (single-writer-per-file across Phase 10; historical records are never "corrected")] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [(f) Approved scope addition, 2026-08-11 — `.writ/docs/model-tiers.md` and `scripts/lint-skill.sh`, with the ownership boundaries for `commands/new-command.md`, ADR-016, and `CHANGELOG.md`] — from spec.md → ## Detailed Requirements
- **Technical concerns:** [Why the lint branch is removed rather than retargeted; the `skill-lifecycle` check's four `require_literal` assertions; the shared line 97] — from sub-specs/technical-spec.md → "(f) Explainer and lint carrier retirement — Story 6"
- **Contract:** [This story is outside the locked contract's clauses (a)–(e) and does not alter them. It extends clause (a)'s deliverable — "The prose-note workaround for advisory `model_tier` is replaced by frontmatter" — into the two live artifacts that clause names nowhere. Hardest constraint applies unchanged: every edit leaves the full suite at `Findings: 0`] — from spec.md → ## Contract (Locked)

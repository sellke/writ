# Story 2: /create-uat-plan Drafts the Recipe and Binds Scenarios to Feature IDs

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1, Story 3

## User Story

**As a** developer using Writ on my own project
**I want to** have `/create-uat-plan` draft my app's verification recipe once, bind every UAT scenario to a feature ID, and run the project's own checks for the scenarios a machine can decide
**So that** a scenario reads "passed — evidence: `evidence/uat/<id>/result.json`" instead of "human, please check", and anything a machine cannot decide stays an honest human step with a stated reason

## Acceptance Criteria

> **AC IDs assigned through:** AC-2.5

- [ ] Given a spec with at least one completed story and no `.writ/docs/app-verification.md`, when `/create-uat-plan` runs, then a new Step 1.3 drafts the recipe in the Story 1 format from the project's test harness (Playwright, Cypress, pytest, `package.json` test scripts), dev or start command, readiness URL or port, and environment files that name a database; each feature with an existing check gets a backticked `Check` command and every other feature `human-only: no check yet` (no harness detected → every feature `human-only: no check yet`); the command shows the draft and asks exactly one AskQuestion with options save / edit / skip, exactly one labelled `(Recommended)`; skip writes no recipe and produces today's populated all-human plan; an existing recipe gets no draft and no question; the zero-completed-stories stub and `--check` (which saves nothing and runs nothing) are unchanged `[AC-2.1]`
- [ ] Given a recipe that was just saved or already existed, when the command validates it with `python3 scripts/app-verify.py validate --recipe .writ/docs/app-verification.md`, then a non-zero exit prints `app-verify: recipe invalid — <first finding>`; a drafted recipe that fails validation is never saved and returns to the edit option; a pre-existing invalid recipe is not rewritten by the command, every scenario falls back to `**Verification:** human — recipe invalid`, and the report suggests fixing the recipe and re-running `[AC-2.2]`
- [ ] Given a valid recipe, when scenarios are generated, then every scenario carries `**Feature:** <id>` and either `**Verification:** machine — evidence: evidence/uat/<id>/result.json` or `**Verification:** human — <reason>` directly under its `**Source:**` line; the ID is chosen from the IDs `python3 scripts/app-verify.py touched --recipe .writ/docs/app-verification.md --changed <files>` prints for the story's "What Was Built" files (when several IDs are printed, the scenario binds the one whose `Feature` text describes the scenario's behavior, and each other touched ID gets at least one scenario of its own; this is an authoring choice, and the verdict still comes from the script); a feature whose `Check` is `human-only: <reason>` binds as human with that reason; a scenario with no touched feature reads `**Feature:** none` and `**Verification:** human — no mapped feature`; with no recipe (skipped) every scenario reads `**Verification:** human — no recipe` `[AC-2.3]`
- [ ] Given one or more machine scenarios, when the command runs `python3 scripts/app-verify.py run --recipe .writ/docs/app-verification.md --spec .writ/specs/<spec-folder> --run-label uat --features <id,…>` once with every distinct machine ID, then each machine scenario's Status is ticked Pass only when its `evidence/uat/<id>/result.json` verdict is `pass` and Fail otherwise (exit 1, including launch failure or `not_ready`, marks every machine scenario Fail and its Notes cite `evidence/uat/_launch/`); exit 2 with `refused` rewrites those scenarios to `**Verification:** human — refused` with Status unticked; the verdict comes only from the script's exit code and `result.json`, never from agent judgment; the script's `app-verify:` line and machine/human scenario counts appear in the Step 5.3 report `[AC-2.4]`
- [ ] Given the edited `commands/create-uat-plan.md`, when the new hook test and the suites run, then the command states it never writes test code or check scripts (features without a check stay `human-only: no check yet`; authoring checks is the coding agent's job), its `exit_criteria` gains one criterion requiring every scenario in a populated plan to carry `**Feature:**` and `**Verification:**` lines, `scripts/tests/test_uat_plan_verification_hooks.sh` pins every new literal named in AC-2.1 through AC-2.4, the file stays under the 24,960-byte `COMMAND_BYTE_BUDGET`, no `commands/create-uat-plan.lean.md` is created, and no `.writ/docs/app-verification.md` appears in the Writ repo `[AC-2.5]`

## Implementation Tasks

- [ ] 2.1 Write failing `scripts/tests/test_uat_plan_verification_hooks.sh` (pattern: `test_spec_analyze_command_hooks.sh`; header comment naming `2026-10-01-behavioral-verification` Story 2 and the AC IDs) pinning: the Step 1.3 heading ordered after Step 1.2; the four drafting sources; `human-only: no check yet`; the save / edit / skip AskQuestion with one `(Recommended)`; the `validate`, `touched`, and `run … --run-label uat` invocations; the `**Feature:**` and both `**Verification:**` template lines; the `refused`, `recipe invalid`, `no recipe`, and `no mapped feature` reasons; the never-writes-test-code sentence; the new `exit_criteria` line; byte size below 24,960; absence of a `.lean` twin and of `.writ/docs/app-verification.md` `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`
- [ ] 2.2 Add `#### Step 1.3: Verification Recipe` to `commands/create-uat-plan.md` after the zero-stories exit in Step 1.2: detect an existing recipe, otherwise draft it from the four sources, show it, and ask the single save / edit / skip AskQuestion (save `(Recommended)` when a launch command was detected, otherwise skip); skip continues with an all-human plan; `--check` previews the draft without saving `[AC-2.1]`
- [ ] 2.3 In Step 1.3, validate the saved or existing recipe with `python3 scripts/app-verify.py validate --recipe .writ/docs/app-verification.md`: a failing draft returns to edit and is never saved; a failing pre-existing recipe prints `app-verify: recipe invalid — <first finding>`, is left untouched, and sets the plan-wide reason `recipe invalid` `[AC-2.2]`
- [ ] 2.4 Extend the Phase 3 Step 3.1 scenario template with the `**Feature:**` and `**Verification:**` lines under `**Source:**`, and add a binding step after Phase 4's "What Was Built" load that calls `app-verify.py touched` with each story's files and applies the machine / `human — <reason>` / `none` rules; keep Step 3.2's no-jargon rule by treating these two lines as metadata, not tester steps `[AC-2.3]`
- [ ] 2.5 Add a run step before Phase 5 assembly: one `app-verify.py run --run-label uat --features <id,…>` call; tick Status from each `result.json` verdict, handle exit 1 (launch/`not_ready` → Fail, cite `evidence/uat/_launch/`) and exit 2 (`refused` → `human — refused`, unticked); add the `app-verify:` line and machine/human counts to the Step 5.3 report `[AC-2.4]`
- [ ] 2.6 Add the never-writes-test-code sentence next to the Terminal constraint, the new `exit_criteria` frontmatter line, and Error Handling entries for no harness detected, recipe invalid, and safety refused, each one line ending in the human fallback; trim adjacent prose where meaning is unchanged to limit growth `[AC-2.2, AC-2.4, AC-2.5]`
- [ ] 2.7 Verify: `bash scripts/tests/test_uat_plan_verification_hooks.sh` passes; `wc -c commands/create-uat-plan.md` is below 24,960; `uv run --python 3.9 pytest` and the bash suite are green; `bash scripts/eval.sh` reports Findings 0; walk the four Shadow Path cells of the `/create-uat-plan` row against the command text `[AC-2.1, AC-2.2, AC-2.3, AC-2.4, AC-2.5]`

## Notes

- **Planning command boundary.** `/create-uat-plan` writes the recipe (after confirmation) and `uat-plan.md`, and starts checks only through `app-verify.py`. It never writes test code. Business Rule 2's check authoring belongs to the coding agent, which Story 4 wires.
- **Populated-plan invariant.** `exit-criteria.py` (`implement-phase.c2`) rejects a stub `uat-plan.md` for merged specs. The skip, invalid-recipe, and refused paths must therefore still produce a full plan with human scenarios. Only the existing zero-completed-stories path writes a stub.
- **Feature selection.** Gate 4.5 can't learn features from the UAT plan (spec ⚠️ Technical Concerns), so both consumers use the same mechanical path-intersection through `touched`. Choosing which of several touched IDs a given scenario exercises is a binding choice, not a verdict. The verdict always comes from the script.
- **One launch.** A single `run` call with every machine ID starts the app once. Calling `run` per feature would relaunch the app for each one and could trip the pre-launch probe's `instance_already_running` refusal.
- **Stale evidence.** If a scenario is marked Fail after a launch failure, its `evidence/uat/<id>/result.json` either doesn't exist or doesn't say `pass`. Story 5's evidence check will then report `unmet`, which is the intended outcome. A failed run must never be rewritten as human to dodge that check.
- **Dogfooding hazard.** Running `/create-uat-plan` with save on the Writ repo itself would create `.writ/docs/app-verification.md`, which Story 1's guard forbids (install's overlay would collide with project recipes). For this repo, choose skip.
- **Out of scope.** `scripts/recommend-state.py` renders its own UAT scenarios for the `--recommend` path. It is not touched here (see the out-of-scope note in `.writ/docs/acceptance-criteria-ids.md`). Story 5 treats plans without `**Verification:**` lines as `legacy plan`.
- **Integration.** Story 1 supplies the recipe grammar and `validate`. Story 3 supplies `touched`, `run`, exit codes 0/1/2, and the `result.json` schema. End-to-end execution against the fixture app is proven by Story 5's eval check. This story's test pins command prose only.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [`/create-uat-plan` draft, Read recipe, Validate recipe, Resolve safety variable, Launch, Readiness, Run check] — from sub-specs/technical-spec.md → ## Error & Rescue Map
- **Shadow paths:** [`/create-uat-plan`] — from sub-specs/technical-spec.md → ## Shadow Paths
- **Business rules:** [1 Recipe sections and `check` / `human-only` entries, 2 Machine decides and the agent never grades, 3 Safety refuses by default, Expanded 1 Recipe shape, Expanded 2 Machine verdicts only, Expanded 7 Evidence under `evidence/uat/`, Expanded 8 Evidence check reads the cited path] — from spec.md → 📋 Business Rules and ## 📋 Business Rules (Expanded)
- **Experience:** [Entry point (draft + confirm), Moment of truth (passed — evidence line), Feedback model (`pass` / `fail` / `human-only: <reason>`), Error experience (one line, fall back), State Catalog rows No recipe / Recipe invalid / Safety refused / Human-only feature, Interaction Patterns (one confirmation; `app-verify:` prefix)] — from spec.md → ## 🎯 Experience Design
- **Technical:** sub-specs/technical-spec.md → ## Files in Scope (`commands/create-uat-plan.md`), ## Run Contract, ## Recipe Grammar; spec.md → ## Detailed Requirements → UAT scenario lines

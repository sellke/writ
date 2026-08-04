# Story 3: Loop Script, Handoff Artifacts, and Configuration

> **Status:** Completed ✅
> **Priority:** High
> **Dependencies:** Stories 1, 2

## User Story

**As a** Writ developer switching from Cursor planning to CLI execution  
**I want** a checked-in `scripts/ralph.sh` loop template, project-tailored handoff files from `/ralph plan` (including `PROMPT_build.md` and an initialized Ralph state file), and documented Ralph keys in `.writ/config.md`  
**So that** I can run a predictable bash loop in the terminal (plan vs build, bounded iterations, git push) with settings and stop conditions that match my repo and the CLI pipeline from Story 2

## Acceptance Criteria

- [ ] **Given** a project where `/ralph plan` has run (Stories 1–2 deliverables exist) and `.writ/config.md` includes the new Ralph keys, **when** the developer runs `./ralph.sh` with optional numeric max-iteration argument, **then** the script selects plan or build mode (documented interface, e.g. flag or env), respects max iterations and default branch from config where applicable, pipes the correct PROMPT file into the configured CLI agent invocation, and performs `git push` after a successful iteration per the spec’s playbook pattern
- [ ] **Given** `/ralph plan` completes successfully, **when** the developer inspects the repo root (or paths documented in the command), **then** handoff artifacts include a tailored `PROMPT_build.md`, a `ralph.sh` (or `scripts/ralph.sh`) customized for the project (default branch, agent command placeholders filled or clearly parameterized from config), and an initialized `.writ/state/ralph-*.json` consistent with `.writ/docs/ralph-state-format.md` (Story 1)
- [ ] **Given** `.writ/docs/config-format.md` after this story, **when** a maintainer reads Supported Keys, **then** Ralph configuration is documented: max iterations default, stop conditions (e.g. escalation, all complete), CLI agent selection / invocation pattern, and autonomy level (what the loop may do without human confirmation), with read order rules aligned with existing Conventions/Paths sections
- [ ] **Given** the developer stops the loop with Ctrl+C, **when** they run `./ralph.sh` again, **then** behavior matches the **Paused → resume** rule: state on disk is preserved and the next iteration continues from authoritative state (no silent reset of progress)
- [ ] **Given** the loop script template in `scripts/`, **when** compared to `scripts/install.sh` / `update.sh` style, **then** it uses portable bash patterns, clear comments for adopters, and does not assume Cursor-only tools

## Implementation Tasks

- [x] 3.1 Author validation scenarios (checklist or fixture-driven dry-run steps) for: `./ralph.sh` vs `./ralph.sh N`, plan vs build mode, branch detection / default branch usage, `git push` ordering, behavior when max iterations reached, and presence of handoff files after `/ralph plan`
- [x] 3.2 Add `scripts/ralph.sh` as the loop script template: wrap CLI agent invocation in a loop; support plan/build mode selection; honor max iterations (argument overrides config default); read Ralph-related settings from `.writ/config.md` where specified in `config-format.md`; invoke the appropriate PROMPT file for the mode; run `git push` after each iteration as in the Ralph Playbook reference loop
- [x] 3.3 Update `commands/ralph.md` **plan** workflow (Story 1 baseline): emit project-tailored `PROMPT_build.md`, generate or overwrite the project’s loop entrypoint (`ralph.sh` and/or `scripts/ralph.sh`) with values derived from the plan and config, and initialize the Ralph state file to **Planned** (or equivalent) per the state catalog — aligned with Story 1 schema and Story 2 PROMPT templates
- [x] 3.4 Extend `.writ/docs/config-format.md` with a **Ralph** subsection under the format example, document new keys in **Supported Keys**, and state how commands should parse them (case-insensitive read, Title Case write — consistent with existing rules)
- [x] 3.5 Wire mode selection to Story 2 artifacts: document which PROMPT file is used in plan mode vs build mode (`PROMPT_plan.md` / `PROMPT_build.md` or names fixed in Story 2) so the loop script and `/ralph plan` outputs stay consistent
- [x] 3.6 Cross-check `.writ/docs/ralph-state-format.md` (Story 1): if initialization fields or filenames differ from what the loop expects, update docs and command output in lockstep (single source of truth for state file naming)
- [x] 3.7 Run validation scenarios from 3.1 against a multi-spec fixture (or temporary specs under `.writ/specs/`), confirm all acceptance criteria, and update `SKILL.md` or install surfaces only if new user-facing paths or commands are introduced

## Notes

**Technical considerations**

- Deliverables are markdown commands, docs, and bash — no automated test runner in this repo; “tests” are explicit validation scenarios and manual dry-runs (see `AGENTS.md`).
- Keep the loop script a **thin wrapper**: intelligence stays in PROMPT templates (Story 2) and state (Story 1). The script should mirror the playbook idea (`while …; cat PROMPT | cli-agent; git push; done`) while adding mode, bounds, and config-driven invocation.
- **Branch detection:** use `Default Branch` from `.writ/config.md` when the workflow needs to push or base work; fall back to documented detection if the key is missing (same read order as other commands).
- **Security / autonomy:** document in config what “autonomy level” means for v1 (e.g. flags passed to CLI agent); avoid baking secrets into generated `ralph.sh`.

**Integration points**

- **Story 1:** state file path, schema, and **Planned / Executing / Paused** semantics — spec.md → 🎯 Experience Design → State Catalog
- **Story 2:** PROMPT templates and CLI pipeline wording consumed each iteration — spec.md → Implementation Approach → CLI Pipeline
- **`.writ/config.md`:** Ralph keys consumed by `ralph.sh` and referenced by `/ralph plan` when generating handoff files — spec.md → Integration Points → With `.writ/config.md`
- **`commands/ralph.md`:** plan phase owns regeneration of handoff artifacts; avoid contradicting Story 1 task 1.6 — Story 3 completes and hardens the loop script + config + initialization behavior

**Risks**

- **Overlap with Story 1 handoff stub:** if Story 1 already emits placeholder `ralph.sh` / PROMPT, Story 3 must replace or upgrade with full behavior and document migration for early adopters.
- **CLI divergence:** different agents use different flags — mitigate with a single documented “invocation pattern” key in config and comments in `scripts/ralph.sh`.
- **Push failures:** network or auth errors should not corrupt state; document exit behavior and whether the loop retries or stops (prefer stop with clear message for v1).

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Validation scenarios executed successfully
- [ ] `scripts/ralph.sh` committed as template (matches spec Files in Scope)
- [ ] `.writ/docs/config-format.md` updated with Ralph section and Supported Keys
- [ ] `/ralph plan` generates tailored `PROMPT_build.md`, customized loop script, and initialized state file
- [ ] Documentation cross-links consistent (ralph command ↔ state format ↔ config format)
- [ ] Review completed (peer or self-review against spec)

## Context for Agents

- **Error map rows:** [Loop stops on environment/build breakage — spec.md → 🎯 Experience Design → Error Experience — “Build/test environment broken”]
- **Shadow paths:** [Happy Path Flow — step 5 (`./ralph.sh` / `./ralph.sh 20`); step 6 (CLI loop: fresh context, next story, pipeline, commit, loop)] — spec.md → 🎯 Experience Design → Happy Path Flow
- **Business rules:** [One Story Per Iteration; Platform Separation — Cursor plan vs CLI loop; State as Single Source of Truth — `.writ/state/ralph-*.json`] — spec.md → 📋 Business Rules
- **Experience:** [State Catalog — Planned (handoff ready), Executing (per-iteration updates), Paused (resume via `./ralph.sh`)] — spec.md → 🎯 Experience Design → State Catalog
- **Integration:** [`.writ/config.md` — Ralph configuration + project conventions for pipeline] — spec.md → Implementation Approach → Integration Points → With `.writ/config.md`
- **Files in scope:** [`scripts/ralph.sh` created; `.writ/docs/config-format.md` modified] — spec.md → Files in Scope

---

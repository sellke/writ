# Story 4: Build Smoke — Booting the Framework, Honestly

> **Status:** Not Started
> **Priority:** Medium
> **Dependencies:** Story 1

## User Story

**As a** developer whose tests import route handlers as plain functions and never boot the
framework
**I want** a check that actually builds the project and distinguishes a compiler failure from
an unreachable database
**So that** the class of defect that passes every unit test and breaks every deployment is
caught in the gate that already runs, and the check does not get disabled the first time
someone runs it without a dev database

## Acceptance Criteria

> **AC IDs assigned through:** AC-4.5

- [ ] Given a project whose source contains a framework-level structural error that typechecking cannot see — the reference fixture is two sibling dynamic route segments with different slug names — when `build-smoke.py check` runs, then it reports `build_failed_source` as blocking, includes the build tool's own error text, and exits 1. `[AC-4.1]`
- [ ] Given a build that fails because a database is unreachable, an env var is unset, or a dependency is not installed, when the check runs, then it reports `build_failed_environment` as informational, the verdict is `unverifiable`, and the exit code is 0 — an unavailable environment is never a code defect. `[AC-4.2]`
- [ ] Given a project whose build script chains database migration and seeding before the compiler — the reference fixture is `pnpm verify-db && pnpm prisma:deploy && prisma generate && tsx scripts/seed-preview-test-user.ts && next build` — when the check runs, then it invokes the narrowest build step that exercises the framework rather than the full composite script, and records which command it chose in `inspected.method`. `[AC-4.3]`
- [ ] Given a build that exceeds the timeout, or a project with no recognized build command, when the check runs, then the verdict is `unverifiable` with reason `timeout` or `unsupported_stack` respectively — never `fail`. `[AC-4.4]`
- [ ] Given the classification rules cannot be made reliable on the Node/TypeScript fixture set, when this story closes, then it closes either shipping a checker that prefers `unverifiable` over `fail`, or as `Closed — Not Implemented` with the measurement recorded — and in neither case does it ship a check that reports `fail` on environment failures. `[AC-4.5]`

## Implementation Tasks

- [ ] 4.1 Write `scripts/tests/test_build_smoke.py` first — `unittest`, imported by path; fixtures for source failure, each environment-failure class, timeout, and absent build command, with the classifier tested directly on captured build output rather than by running real builds `[AC-4.1, AC-4.2, AC-4.4]`
- [ ] 4.2 Implement build-command selection: prefer the narrowest invocation that boots the framework, decline the full composite script when it chains non-compiler steps, and record the choice in `inspected.method` `[AC-4.3]`
- [ ] 4.3 Implement the failure classifier over build output and exit status, with an explicit enumerated list of environment-failure signatures and a default of `unverifiable` for anything unrecognized `[AC-4.1, AC-4.2]`
- [ ] 4.4 Implement the timeout and unsupported-stack paths, both resolving to `unverifiable` `[AC-4.4]`
- [ ] 4.5 Write `scripts/eval-build-smoke.py` fixture scenarios — driving the classifier over recorded build output, never invoking a real toolchain in CI — and register `build-smoke` in `scripts/eval.sh` with finding-code bindings against both the checker and Story 1's doc `[AC-4.1, AC-4.2, AC-4.4]`
- [ ] 4.6 Measure the classifier against a real yuss checkout in both states — with and without a reachable database — and record both outputs verbatim in What Was Built `[AC-4.2, AC-4.3]`
- [ ] 4.7 Make the AC-4.5 disposition call on the recorded evidence and record the reasoning, whether that means shipping or closing the story unimplemented `[AC-4.5]`

## Notes

**Technical considerations:** This is the only checker that executes rather than reads, and
the only one whose correctness depends on classifying failures it did not produce. It is
exempt from the read-only subprocess ban that Stories 2 and 3 carry, but must still never
write a file itself.

The reference defect is real and documented. From
`.writ/specs/archive/2026-07-23-quick-split-single-transaction/drift-log.md` DEV-004 in the
yuss repository: `Error: You cannot use different slug names for the same dynamic path
('id' !== 'token')` — build-breaking, deployment-blocking, and invisible to Gate 1 through
Gate 5 because "every test in this repo imports route handlers as plain functions … none of
Story 1's tests, nor its own Gate 2 `tsc --noEmit`/lint pass, ever actually booted the Next.js
framework router". That entry also names the fix this story implements, at the position it
implements it: "add a cheap `next build` (or at least a route-manifest check) to Gate 2".

Note the parenthetical. If a route-manifest check turns out to be sufficient and dramatically
cheaper than a full build, take it — the goal is booting the router, not producing a
deployable artifact.

**Risks:** This story is the most likely of the six to be cut, and AC-4.5 makes that an
explicit, honest outcome rather than a silent failure. A build gate that reports `fail`
because Postgres is down will be disabled within a week, and will take Stories 2, 3, 5 and 6
down with it by association. When the classifier is uncertain, `unverifiable` is always the
correct answer.

Second risk: build latency. A full `next build` on a large project is minutes, per story.
Selecting the narrowest framework-booting invocation (task 4.2) is a correctness requirement
for adoption, not an optimization.

**Integration:** Story 5 wires this into Gate 2. Gate 2 today has no BLOCKED handler, no
iteration cap, and no FAIL verdict in the pipeline's control-flow line — a blocking finding
here therefore routes through the existing shared BLOCKED escalation rather than inventing new
control flow. Adding an iteration cap would require a `loop.nested` frontmatter unit *and*
matching prose or `scripts/eval-loop-bounds.py` fails; this story adds neither.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** Run build (source-attributable / environment-attributable / timeout /
  build tool absent) — from `sub-specs/technical-spec.md` → `## Error & Rescue Map`
- **Shadow paths:** Happy, Nil input, Empty input, Upstream error — from
  `sub-specs/technical-spec.md` → `## Shadow Paths`
- **Business rules:** "environment failure is never code failure", the verdict trichotomy —
  from `spec.md` → `## 📋 Business Rules`
- **Ground truth fixture:** `spec.md` → `## Evidence Base` §4 quotes DEV-004 in full,
  including the exact error string and the process-gap recommendation this story implements
- **Precedent to mirror:** `scripts/ac-trace.py` (CLI, JSON, exit codes); for the
  disposition path in AC-4.5, the Phase 10 progressive-disclosure specs that closed
  `Closed — Not Implemented` on measured evidence with contracts kept as design records

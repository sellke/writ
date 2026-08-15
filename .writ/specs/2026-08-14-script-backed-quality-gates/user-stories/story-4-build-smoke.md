# Story 4: Build Smoke — Booting the Framework, Honestly

> **Status:** Completed ✅
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

- [x] Given a project whose source contains a framework-level structural error that typechecking cannot see — the reference fixture is two sibling dynamic route segments with different slug names — when `build-smoke.py check` runs, then it reports `build_failed_source` as blocking, includes the build tool's own error text, and exits 1. `[AC-4.1]`
- [x] Given a build that fails because a database is unreachable, an env var is unset, or a dependency is not installed, when the check runs, then it reports `build_failed_environment` as informational, the verdict is `unverifiable`, and the exit code is 0 — an unavailable environment is never a code defect. `[AC-4.2]`
- [x] Given a project whose build script chains database migration and seeding before the compiler — the reference fixture is `pnpm verify-db && pnpm prisma:deploy && prisma generate && tsx scripts/seed-preview-test-user.ts && next build` — when the check runs, then it invokes the narrowest build step that exercises the framework rather than the full composite script, and records which command it chose in `inspected.method`. `[AC-4.3]`
- [x] Given a build that exceeds the timeout, or a project with no recognized build command, when the check runs, then the verdict is `unverifiable` with reason `timeout` or `unsupported_stack` respectively — never `fail`. `[AC-4.4]`
- [x] Given the classification rules cannot be made reliable on the Node/TypeScript fixture set, when this story closes, then it closes either shipping a checker that prefers `unverifiable` over `fail`, or as `Closed — Not Implemented` with the measurement recorded — and in neither case does it ship a check that reports `fail` on environment failures. `[AC-4.5]`

## Implementation Tasks

- [x] 4.1 Write `scripts/tests/test_build_smoke.py` first — `unittest`, imported by path; fixtures for source failure, each environment-failure class, timeout, and absent build command, with the classifier tested directly on captured build output rather than by running real builds `[AC-4.1, AC-4.2, AC-4.4]`
- [x] 4.2 Implement build-command selection: prefer the narrowest invocation that boots the framework, decline the full composite script when it chains non-compiler steps, and record the choice in `inspected.method` `[AC-4.3]`
- [x] 4.3 Implement the failure classifier over build output and exit status, with an explicit enumerated list of environment-failure signatures and a default of `unverifiable` for anything unrecognized `[AC-4.1, AC-4.2]`
- [x] 4.4 Implement the timeout and unsupported-stack paths, both resolving to `unverifiable` `[AC-4.4]`
- [x] 4.5 Write `scripts/eval-build-smoke.py` fixture scenarios — driving the classifier over recorded build output, never invoking a real toolchain in CI — and register `build-smoke` in `scripts/eval.sh` with finding-code bindings against both the checker and Story 1's doc `[AC-4.1, AC-4.2, AC-4.4]`
- [x] 4.6 Measure the classifier against a real yuss checkout in both states — with and without a reachable database — and record both outputs verbatim in What Was Built `[AC-4.2, AC-4.3]`
- [x] 4.7 Make the AC-4.5 disposition call on the recorded evidence and record the reasoning, whether that means shipping or closing the story unimplemented `[AC-4.5]`

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

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

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

---

## What Was Built

**Implementation Date:** 2026-08-14

### Files Created

1. **`scripts/build-smoke.py`** (449 lines)
   - Build-command selection, the failure classifier, and the `check` verdict
   - The only checker that executes rather than reads
2. **`scripts/tests/test_build_smoke.py`** (52 tests)
   - Written before the implementation, per task 4.1; the classifier is tested
     on captured build output, never by running real builds
3. **`scripts/eval-build-smoke.py`** (23 scenarios)

### Files Modified

- **`scripts/eval.sh`** (`CHECKS` array + new `check_build_smoke()`)
  - Binds both finding codes against the checker and the classification doc,
    and pins the environment-before-source ordering and the
    `unverifiable`-by-default rule as literals

### Implementation Decisions

1. **AC-4.5 disposition: ship.** The classifier is reliable on the Node/TS
   fixture set, measured against real captured output rather than invented
   strings — see the evidence run below. It ships preferring `unverifiable`
   over `fail`: two enumerated signature lists, environment checked first, and
   anything matching neither list resolving to `unverifiable`.
2. **Environment is decided before source, and mixed output resolves to
   environment.** Pinned by a test and by a `require_literal` in `eval.sh`. The
   trade-off is deliberate and asymmetric: a missed source failure costs one
   escaped defect, while a false `fail` on a developer without a database
   costs the whole check — and, by association, the other three.
3. **The composite build script is declined, and the decline is recorded.**
   `inspected.method` carries both the command actually invoked and the reason,
   naming which chained steps were skipped, so an operator can see why the
   check did not run their `build` script.
4. **The build is injected, not hard-wired.** `check()` takes a `runner`
   callable defaulting to the real subprocess. That is what lets the entire
   test suite and every CI scenario exercise the verdict logic without a
   JavaScript toolchain — the story's own note that CI must never invoke a real
   build made this a design requirement rather than a testing convenience.
5. **No iteration cap, no new control flow.** Per the story's Integration note,
   adding one would require a `loop.nested` frontmatter unit *and* matching
   prose or `scripts/eval-loop-bounds.py` emits `drift-*`. This story adds
   neither; a blocking finding routes through the existing shared BLOCKED
   escalation, which Story 5 wires.

### Test Results

**Verification:** Automated

- ✅ 52 unit tests, 0 failures
- ✅ 23/23 eval scenarios
- ✅ `bash scripts/eval.sh` — 0 findings, 0 run errors
- ✅ `build_failed_source` blocking with the build tool's own error text,
  exit 1 `[AC-4.1]`
- ✅ `build_failed_environment` informational, verdict `unverifiable`,
  exit 0 `[AC-4.2]`
- ✅ Composite script declined; narrowest framework invocation chosen and
  recorded in `inspected.method` `[AC-4.3]`
- ✅ Timeout and absent build command both `unverifiable`, never `fail` `[AC-4.4]`
- ✅ Disposition made on recorded evidence `[AC-4.5]`

**Coverage:** 99.1% of body statements (112/113). The single uncovered line is
`sys.exit(main())` under the `__main__` guard.

### Task 4.6 — Verbatim yuss Evidence Run

Checkout `ff3ad2e` (2026-08-14).

**Command selection.** The project's own build script is:

```
pnpm verify-db && pnpm prisma:deploy && prisma generate && tsx scripts/seed-preview-test-user.ts && next build
```

Selection output:

```
argv  : ['pnpm', 'exec', 'next', 'build']
reason: declined the composite build script — it chains prisma, seed, verify-db before the compiler
```

All four database-dependent steps declined; `packageManager: pnpm@10.33.0`
honoured in the runner prefix.

**State A — build run with the narrowed command.**
`python3 scripts/build-smoke.py check --project ~/Projects/yuss --timeout 600`

```
verdict: pass    exit: 0
method : pnpm exec next build — declined the composite build script —
         it chains prisma, seed, verify-db before the compiler
findings: []     unverifiable: []
```

A real `next build` completed. This is the load-bearing result for AC-4.3: the
project has no `.env` and the narrowed command still built, where the composite
script would have run migrations and a seed script first.

**State B — database unreachable.** Captured from the real toolchain with
`DATABASE_URL` pointed at a dead port
(`pnpm exec prisma migrate status`, read-only, exit 1):

```
Prisma schema loaded from prisma/schema.prisma
Datasource "db": PostgreSQL database "nodb", schema "public" at "127.0.0.1:59999"
Error: P1001: Can't reach database server at `127.0.0.1:59999`

Please make sure your database server is running at `127.0.0.1:59999`.
```

Classifier results on real captured output:

| Input | Classification | Matched signature |
|---|---|---|
| Real Prisma `P1001` block above | `environment` | `can't reach database server` |
| Real DEV-004 slug-collision error | `source` | `you cannot use different slug names for the same dynamic path` |
| Both concatenated | `environment` | environment wins, as specified |
| `Error: something nobody enumerated` | `unverifiable` | — (never `fail`) |

**Why State B was measured this way.** Running the project's actual composite
`build` script to force the environment failure would have executed
`prisma:deploy` (migrations) and a seed script against a real database
reachable through `.env.local`. That is a mutating action on a repository this
spec only has read authority over, and the classifier's input — the toolchain's
own `P1001` output — was obtainable from a read-only command instead. The
recorded output is real, not synthesized; only the way it was provoked is
narrower. Noted here because the difference is the kind of thing a later reader
would otherwise have to reconstruct.

### Review Outcome

**Result:** PASS

- **Iteration count:** 2 iterations — the importlib/dataclass loader, and an
  over-strict assertion about the recorded method string
- **Drift:** None
- **Security:** Executes one build command derived from the project's own
  declared framework dependency and `packageManager`; never interpolates a
  shell string (`subprocess.run` with an argv list, no `shell=True`), never
  writes a file, and never runs the project's `build` script when that script
  chains other steps. Declining the composite script is a security property as
  well as a correctness one: it is what keeps the check from running arbitrary
  chained commands, including migrations and seeds, from a project it is only
  inspecting.
- **Boundary Compliance:** Exempt from the subprocess ban and asserted still
  bound by the write ban, both in `eval.sh` and by a test that snapshots the
  project tree before and after a run.

### Deviations from Spec

None.

### Lessons Learned

1. **The story most likely to be cut was the one whose contract made it
   shippable.** AC-4.5's explicit permission to close `Closed — Not
   Implemented` removed the incentive to overclaim, which made it easy to
   design for `unverifiable` as the default rather than treating it as an
   admission of failure. The check ships more conservative than it could be,
   and that is the disposition the AC was written to make legitimate.
2. **Injecting the runner was what made the whole story testable.** The
   requirement that CI never invoke a real toolchain looked like a constraint
   on the test suite; it was actually a constraint on the module's shape. A
   `check()` that called `subprocess.run` directly would have been untestable
   without a JavaScript toolchain, and the 23 CI scenarios would not exist.
3. **The narrowest-invocation rule paid off immediately on real code.** The
   reference project's build script is four database steps deep, and the
   narrowed `next build` succeeded on a machine with no `.env` at all. The
   naive implementation would have reported FAIL on the first run — the exact
   failure mode the risk note predicted, observable on the very first real
   measurement.

### Next Story

**Story 5:** Gate wiring — extending Gate 2 and Gate 4 in place, with no new
gate number.

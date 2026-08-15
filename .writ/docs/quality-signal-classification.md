# Quality-Signal Classification

> Parent spec: [`2026-08-14-script-backed-quality-gates`](../specs/2026-08-14-script-backed-quality-gates/spec.md)
> Produced by: Story 1 (`user-stories/story-1-classification-doc.md`)
> Consumed by: Stories 2, 3 and 4, which implement `scripts/quality-config-audit.py`,
> `scripts/test-integrity.py` and `scripts/build-smoke.py` against exactly this vocabulary —
> no code here, no finding there.

## Purpose

Writ states four quality guarantees that, until this spec, had no executable behind them:
coverage at or above a threshold, tests that actually test the code, a project that still
builds, and a project whose own gates are switched on. Three read-only checkers now decide
those claims from disk and tool output rather than from a field an agent types.

This document is the specification those checkers implement against — the same relationship
[`acceptance-criteria-ids.md`](acceptance-criteria-ids.md) has to `scripts/ac-trace.py` and
[`exit-criteria-classification.md`](exit-criteria-classification.md) has to
`scripts/exit-criteria.py`. It defines the finding vocabulary, the verdict rules, the
parse-failure rule, the stack-support matrix, and the baseline format, precisely enough that
an implementer decides nothing new.

### How this document binds to the checkers

Two models were available and the choice is deliberate. `exit-criteria.py` **parses** its
classification doc at runtime, which makes drift impossible but makes the doc a hard runtime
dependency — a missing or renamed doc stops the checker. `ac-trace.py` is merely **bound** to
its grammar doc by `require_literal` assertions in `scripts/eval.sh`, which is simpler and
keeps the checker self-contained.

**These three checkers use the `ac-trace.py` model: bound, not parsed.** The reason is that
the finding vocabulary here is a fixed, small, code-shaped table — thirteen codes and two
severities — not an open registry of project-specific identifiers that grows per spec. Making
it a runtime input would buy nothing and would add a failure mode to instruments whose entire
value is that they still work in a degraded project. `scripts/eval.sh` binds every code below
as a `require_literal` against **both** the checker and this document, so a code renamed in one
place and not the other fails eval. That is the intended coupling.

## Verdict Rules

### The trichotomy

Every check, on every stack, returns exactly one of three verdicts.

| Verdict | Means | Pipeline behavior |
|---|---|---|
| `pass` | The check ran, examined something, and found no blocking finding | Continue |
| `fail` | The check ran and found at least one blocking finding | Blocks |
| `unverifiable` | The check ran and honestly could not decide | Surfaces in the story report; does **not** block |

`unverifiable` is a first-class outcome, not an error and not a soft pass. The rule it exists
to enforce: **a check may not launder "could not tell" into either "fine" or "broken".** A
check that reports `fail` when it means "could not tell" gets muted within a week and takes
the true findings with it; a check that reports `pass` when it means the same thing is the
exact defect this spec is named for.

### `unverifiable` is reachable only through an enumerated cause

A checker may emit `unverifiable` for these reasons and no others. Each appears verbatim in
the `unverifiable[].reason` field.

| Reason | Emitted when |
|---|---|
| `could_not_parse` | A config or source file was found but no bounded answer could be extracted from it |
| `unsupported_stack` | No first-class or best-effort handler matched the project |
| `no_coverage_report` | No machine-readable coverage report was found where one was expected |
| `unknown_report_format` | A coverage report was found but its format is not recognized |
| `truncated_report` | A coverage report was found and recognized but is structurally incomplete |
| `environment` | A build failed for a reason attributable to the machine, not the source |
| `timeout` | An executed check exceeded its time budget |
| `nothing_inspected` | The check ran against a project offering nothing in its domain to examine |

An implementer who finds a genuine cause not on this list adds it **here first**, then to the
checker — this document is authoritative, and a checker emitting an unregistered reason is a
defect in the checker.

### `unverifiable` never exits 2

The exit-code ladder matches `scripts/ac-trace.py` exactly:

| Code | Meaning |
|---|---|
| 0 | Ran correctly, no blocking findings — informational findings and `unverifiable` verdicts may be present |
| 1 | Ran correctly, at least one blocking finding |
| 2 | Could not run correctly — usage error, missing project root, unreadable input, malformed baseline |

**Exit 2 belongs to the checker being unable to operate at all**, not to the checker being
unable to decide. A check that ran, read what it could, and honestly reported that the answer
is unavailable has done its job correctly and exits 0 with `verdict: "unverifiable"`. Exit 2
means the invocation itself was broken: a `--project` path that does not exist, a baseline
file that is malformed, an unreadable input. Conflating the two would make every unsupported
stack look like a broken tool.

### Mapping onto `/status`'s existing health vocabulary

`/status` already renders a categorical verdict from `scripts/phase-state.py health`, where
missing or stale evidence is a `Warning` — "never a silent pass" — and `Attention` requires an
affirmative current failure. That is the same trichotomy under different names, and this spec
reuses it rather than inventing a fourth way to say the same thing:

| This document | `/status` |
|---|---|
| `pass` | `Healthy` |
| `unverifiable` | `Warning` |
| `fail` | `Attention` |

### The vacuous-pass guard

Every checker's JSON carries an `inspected` object recording what it actually examined — the
house rule `scripts/ac-trace.py` implements as `scanned_files` / `ignore_filter`, and
`scripts/eval.sh` states as governor-instrumentation Business Rule 8.

**"0 findings" and "0 things inspected" must not read the same.** A report with
`findings: []` and `inspected.files: 0` is `unverifiable` with reason `nothing_inspected`,
never `pass`. A vacuous pass is the failure mode these instruments are most likely to die of:
it is indistinguishable from success at a glance, it never fires, and it degrades silently as
the project it points at moves underneath it.

## Finding Vocabulary

Thirteen codes. Every checker transcribes the codes it owns exactly; a code invented in a
checker before it exists here fails eval by design.

Severity is `blocking` or `informational`. **There is no third, permanently-warning severity**,
deliberately: Writ has already run that experiment — four byte instruments shipped
non-blocking, one sat breached for months, and the apparatus trained the dismissal it was
built to prevent. A finding nobody must act on is a finding nobody reads. Every finding here
is blocking by default or explicitly waived with a recorded reason in the baseline.

### `quality-config-audit`

| Code | Severity | Fires when |
|---|---|---|
| `build_gate_disabled` | blocking | Typecheck or lint errors are configured not to fail the build |
| `coverage_threshold_absent` | blocking | A coverage tool is configured with no enforced threshold, or one set to zero |
| `coverage_scope_gap` | informational | Coverage collection excludes a source directory that contains shipped code |
| `tests_excluded_from_typecheck` | informational | The typechecker's or linter's include/exclude omits the test tree |
| `duplicate_lockfile` | informational | Two package-manager lockfiles coexist |
| `could_not_parse` | informational | A config file was found but not parseable — **downgrades every finding that file would have decided to `unverifiable`** |

**`build_gate_disabled`** — worked example, from `yuss.app`'s `next.config.js:7–12`:

```js
eslint: { ignoreDuringBuilds: true },
typescript: { ignoreBuildErrors: true },
```

That project's `tsconfig.json` sets `strict: true`. It cannot fail a build. Writ spent a year
running Gate 2's `tsc --noEmit` on top of a harness whose native equivalent was disabled. Both
keys fire independently: two findings, at `next.config.js:8` and `next.config.js:11`.

**`coverage_threshold_absent`** — worked example, `jest.config.js:30–36`:

```js
collectCoverageFrom: [
  'lib/**/*.{js,jsx,ts,tsx}',
  'components/**/*.{js,jsx,ts,tsx}',
  'utils/**/*.{js,jsx,ts,tsx}',
],
```

`collectCoverageFrom` is present, `coverageThreshold` is absent entirely. Coverage is measured
and reported and enforces nothing. **A `coverageThreshold` set to `0` fires the same finding**
— a zero bar and an absent bar are the same bar, and setting zero is the obvious way to
launder the check.

**`coverage_scope_gap`** — in the same config, `app/` is absent from `collectCoverageFrom`
while containing roughly eighty API routes. Shipped source excluded from collection is
invisible to the measurement rather than counted against it, which inflates the reported
number without any single file appearing under-covered.

**`tests_excluded_from_typecheck`** — worked example, a `lint` script reading
`next lint --ignore-pattern '**/__tests__/**' --ignore-pattern 'tests/**'`. The tree most
likely to accumulate dead assertions is the tree the linter is told to skip.

**`duplicate_lockfile`** — worked example: `bun.lock` and `pnpm-lock.yaml` present in the same
directory alongside `"packageManager": "pnpm@10.33.0"`. Two lockfiles means two possible
dependency graphs and no guarantee CI resolves the one the developer tested. When
`packageManager` is present it decides which toolchain to invoke; the finding stands
regardless.

**`could_not_parse`** — see *The Parse-Failure Rule* below. This code is informational in
itself but is never *only* informational: it always carries a downgrade of the findings that
file would have decided.

### `test-integrity`

| Code | Severity | Fires when |
|---|---|---|
| `coverage_below_threshold` | blocking | Measured coverage on a new file is under the declared bar |
| `coverage_regression` | blocking | Coverage on a modified file decreased against the baseline |
| `coverage_report_absent` | informational | No machine-readable coverage report was produced |
| `test_imports_no_source` | blocking | A test file resolves zero module specifiers into project source |

**`coverage_below_threshold`** — the claim being verified is `agents/testing-agent.md:133`,
`- **Coverage threshold met:** [YES/NO]`, a field the agent types and nothing recomputes. The
checker re-derives per-file line coverage from the coverage tool's own machine-readable output.
Where the two disagree, **the checker wins** — the same relationship `scripts/exit-criteria.py`
has to a self-reported COMPLETE.

**`test_imports_no_source`** — worked example, `yuss.app`'s
`app/api/user/password/__tests__/password-change.test.ts`, 351 lines whose only import is
`bcryptjs`, and which at `:21` defines its own `function validatePasswordStrength(password:
string)` — a copy annotated "matches implementation" — then asserts against the copy. It
cannot fail when the route changes. It passed review and testing gates for months.

**A test that legitimately tests only types or only constants will trip this code.** That is a
waiver case, recorded in the baseline, not a bug. But if the waiver list grows past a handful
on a real project, the heuristic is wrong and should be narrowed rather than waived around.

**Severity note, recorded honestly:** `coverage_regression` is specified as blocking on the
non-degrading principle ([ADR-006](../decision-records/adr-006-non-degrading-destination.md))
applied to a number. It has not yet fired against a real project, because it requires two runs
with a stored baseline between them. If first contact shows it firing on file renames or
refactors that move covered lines between files, the correct response is to narrow its firing
condition here — not to downgrade it to informational, which would create exactly the
permanent-warning instrument this document forbids.

### `build-smoke`

| Code | Severity | Fires when |
|---|---|---|
| `build_failed_source` | blocking | The build failed for a reason attributable to source |
| `build_failed_environment` | informational | The build failed on a missing dependency, service, or credential |

**`build_failed_source`** — worked example, recorded in the field before this spec existed.
From `yuss.app`'s `2026-07-23-quick-split-single-transaction` drift log, entry DEV-004:

```
Error: You cannot use different slug names for the same dynamic path ('id' !== 'token')
```

Build-breaking, deployment-blocking, and invisible to every gate that does not boot the
framework — because "every test in this repo imports route handlers as plain functions … and
invokes them directly", so neither the unit tests nor `tsc --noEmit` ever started the router.

**`build_failed_environment`** — worked example: `yuss.app`'s own build script is
`pnpm verify-db && pnpm prisma:deploy && prisma generate && tsx
scripts/seed-preview-test-user.ts && next build` — four database-dependent steps before the
compiler runs. A smoke check that ran that script naively would report `fail` on every machine
without a Postgres branch. **An unavailable environment is never a code defect.** This finding
is informational, the verdict is `unverifiable`, and the exit code is 0.

### Shared

| Code | Severity | Fires when |
|---|---|---|
| `unsupported_stack` | informational | No first-class or best-effort handler matched |

Owned by all three checkers. Always accompanies verdict `unverifiable`, never `pass`.

## The Parse-Failure Rule

**Unparseable is not absent.** When a checker finds a config file and cannot extract a bounded
answer from it, every finding that file would have decided becomes `unverifiable` — never
absent, and never a clean result.

This is the single largest technical risk in this spec. Writ has no dependencies and no build
step, so the standard library gives us `json` and `tomllib` and nothing that reads executable
JavaScript or JSONC. Detection is therefore heuristic, and a heuristic that fails to find
`ignoreBuildErrors` has learned **nothing** about whether the gate is on.

### What a bounded regex heuristic may and may not conclude

| From | It may conclude | It may **not** conclude |
|---|---|---|
| A match | The pattern is present — report the finding, with file and line | — |
| A non-match, in a file it fully read and recognized the shape of | Nothing about the gate's state; emit `could_not_parse` and downgrade | That the gate is enabled |
| A non-match, in a file it could not read at all | Nothing; emit `could_not_parse` and downgrade | That the file is irrelevant |

**The forbidden outcome is a clean report produced by a parser that gave up.** Treating
"pattern not found" as "gate enabled" converts every unparseable config into a clean bill of
health and reproduces, exactly, the defect these checks exist to catch.

The evidence for taking this seriously is in the parent spec's own measurement. Three passes
over the same 147 test files, asking one question:

| Method | Files flagged | Verdict |
|---|---|---|
| Careful human hand-audit | 6 | over-counted by 50% |
| Naive single-line `import … from` regex | 22 | over-counted by 450% — 18 false positives |
| Multi-line-aware module-specifier extraction | **4** | ground truth |

The obvious implementation was wrong by a factor of five, and the careful human read was wrong
by half. Bound every heuristic; where it cannot be bounded, say `unverifiable`.

### The three known-unparseable shapes

| File | Why stdlib cannot read it | Required heuristic |
|---|---|---|
| `next.config.js` | Executable JavaScript — may compute values, wrap in `withBundleAnalyzer(...)`, read `process.env` | Bounded pattern match for `ignoreBuildErrors` / `ignoreDuringBuilds` against a truthy literal. A match reports; a non-match emits `could_not_parse` |
| `jest.config.js` | Executable JavaScript — commonly wrapped in `createJestConfig(...)`, and `coverageThreshold` may be assembled programmatically | Bounded pattern match for the `coverageThreshold` key and for `collectCoverageFrom` entries. A non-match on `coverageThreshold` **within a file whose `collectCoverageFrom` was found** is informative — coverage is configured, the threshold key is not there. A non-match on both emits `could_not_parse` |
| `tsconfig.json` | JSONC — permits `//` and `/* */` comments and trailing commas, which `json.loads` rejects | A comment-and-trailing-comma stripping pass, then `json.loads`. If the stripped text still does not parse, emit `could_not_parse` |

The `jest.config.js` row is the one asymmetry worth stating explicitly, because it is the only
place a non-match is allowed to be informative: finding `collectCoverageFrom` proves the file
was read and its shape understood, which makes the absence of `coverageThreshold` a fact about
the config rather than a fact about the parser. Absent both anchors, the parser learned
nothing and must say so.

Every inspection records which files it parsed, which it could not, and by what method, in the
`inspected` object — `inspected.method` names the technique, `inspected.unparsed` names every
file that defeated it.

## Stack Support Matrix

**Stack support is declared, not inferred.** A checker must never guess at a toolchain it has
no fixture for.

| Stack | Support | Basis |
|---|---|---|
| Node / TypeScript | **First-class** | Every finding in the parent spec derives from one Node/TypeScript/Next.js project. This is the only stack with ground-truth fixtures |
| Python | Best-effort | Writ's own scripts are Python and `coverage.py` XML is a stable, documented format. No project-scale fixture exists, so findings degrade to `unverifiable` more readily |
| Everything else | `unsupported_stack` | No handler, no fixture, no evidence |

### The evidence basis, stated rather than assumed

This ordering is not a judgement about which stacks matter. It is a record of where the
evidence came from. All four findings that motivated these checks come from **one** project,
**one** developer, and **one** stack. The *mechanism* they demonstrate — a guarantee with no
executable behind it decays without anyone noticing — is general. The *numbers* are not.

The four fixtures pinned in the parent spec (57.2% statements, exactly 4 inauthentic test
files, the specific config findings, the environment-versus-source build split) are ground
truth about `yuss.app`, not about software. A checker that generalized from them to a stack it
has never been measured against would be making precisely the unevidenced claim this spec
exists to eliminate.

When a stack gains first-class support, it gains it by acquiring a fixture set, and this table
is updated in the same change.

## The Baseline: `.writ/quality-baseline.md`

**Baseline, then ratchet.** On `/initialize`, existing findings in a brownfield project are
recorded as acknowledged debt and do not block. Findings **not** in the baseline block.

Any real brownfield project will light up on first contact. The baseline is what makes
adoption survivable — and it is also the mechanism most likely to hollow these checks out
entirely. A baseline that grows on every run is a disabled check wearing a costume.

### Format

The file is reviewable markdown, not a machine-generated blob. One `##` section per finding
code, one `- ` entry per waived instance. Prose before the first `##` section is preamble and
carries no entries.

```markdown
# Quality Baseline

> Created: 2026-08-14 by `/initialize`
> Entries: 4

Findings recorded here were present when Writ was adopted and are acknowledged debt. They do
not block. Any finding not listed here is new and blocks.

## build_gate_disabled

- `next.config.js:8` — 2026-08-14 — `eslint.ignoreDuringBuilds` predates Writ adoption;
  roughly 400 lint errors stand between here and enabling it. Tracked for Phase 3.
- `next.config.js:11` — 2026-08-14 — `typescript.ignoreBuildErrors` predates Writ adoption.

## coverage_threshold_absent

- `jest.config.js` — 2026-08-14 — no `coverageThreshold` key. `/initialize` wrote the measured
  floor of 57%; this entry retires when that write is confirmed in CI.

## duplicate_lockfile

- `bun.lock` — 2026-08-14 — stray Bun lockfile from an experiment; `packageManager` names pnpm.
  Delete on next dependency change.
```

### Entry grammar

Each entry is a single list item with three fields separated by ` — ` (spaced em dash):

```
- `<file>[:<line>]` — <YYYY-MM-DD> — <rationale>
```

- **Locator** — backticked file path, optionally `:line`. This plus the enclosing `##` code
  is the identity a later run matches against.
- **Date** — ISO `YYYY-MM-DD`, the date the entry was written. Not the date it was reviewed,
  not a range.
- **Rationale** — free prose, required, non-empty. It states why this finding is acknowledged
  rather than fixed, and ideally what would retire it.

**All three fields are mandatory.** An entry missing its date or its rationale is malformed.

### Malformed is exit 2, never ignored

A baseline file that exists but does not parse is **exit 2**, naming the offending line. It is
never treated as empty and never partially applied.

The reasoning is that both failure modes of a silently-ignored baseline are unacceptable in
opposite directions. Treating a malformed baseline as empty floods the developer with findings
they already acknowledged, which trains dismissal. Treating it as suppressing everything hides
real findings behind a typo. Refusing to run until it is fixed is the only honest option, and
it is loud enough to actually get fixed.

An **absent** baseline is different and is not an error: it is treated as empty, every finding
is new, and the report says so.

### No automatic re-baselining

**Nothing but a human, running `/initialize`, ever writes this file.** The three checkers are
read-only in the strict sense and never touch it.

Specifically prohibited:

- A checker adding a finding it just discovered to the baseline.
- Any command refreshing the baseline as a side effect of a run that found something new.
- A `--update-baseline` or `--accept` flag on any of the three checkers.

A baseline that silently re-baselines is just a disabled check with extra steps. Re-baselining
is a deliberate, dated, human act: the developer edits the file, writes a rationale, and
commits it under review like any other change.

The number of baseline entries should only ever decrease. An entry count that grows run over
run is the signal that this mechanism has been captured, and it is worth watching more closely
than any individual finding.

## Coverage Thresholds Are Written at the Measured Floor

When `/initialize` writes a coverage threshold into a project's config, the value is
`floor(current measured coverage)` — never 80%, never any other aspiration.

Writing 80% into a project measuring 57% breaks its build on the first run and teaches the
developer to delete the key, which costs both the threshold and the trust. Writing 57% makes
57% the new minimum and lets it only go up. That is [ADR-006](../decision-records/adr-006-non-degrading-destination.md)'s
non-degrading principle applied to a number instead of a document.

The nominal 80% bar stays in `agents/testing-agent.md` as the target for **new** files in a
story, which is a different question from what an existing codebase's aggregate is allowed to
be. A project can require 80% of code written today while its 2019 modules sit at 40%.

## Read-Only Discipline

`quality-config-audit` and `test-integrity` never write a file and never invoke a mutating
subprocess — the same discipline `scripts/exit-criteria.py` and `scripts/ac-trace.py` document
about themselves, and asserted the same way, by `forbid_literal` in `scripts/eval.sh`.

`build-smoke` executes a build and is therefore exempt from the subprocess ban. It is **not**
exempt from the write ban: it never writes a file itself. Artifacts the build tool produces in
its own output directory are the build tool's, not the checker's.

Only `/initialize` writes — the baseline file and the coverage-floor config — and it does so
inside a command the user ran expressly to set a project up.

## Adoption Posture

- **No new gate, no new command, no new flag.** These checks fire inside Gate 2 and Gate 4,
  which developers already run. The gate set is unchanged from Gate 0 through Gate 5.
- **`unverifiable` is not `⚠️ DEGRADED`.** DEGRADED means a gate could not be cleared;
  `unverifiable` means a check could not be run. A story is never marked DEGRADED on an
  `unverifiable` verdict alone. Conflating them either floods DEGRADED until it stops meaning
  anything or hides real gate failures.
- **Existing projects are not retroactively blocked.** The baseline is written once, at
  `/initialize`, and everything in it is acknowledged from that moment.
- **A first run that finds a great deal is working correctly.** The failure mode to watch is
  not a noisy first run — it is a baseline that grows on the second one.

## Not This Document's Job

This document specifies the finding vocabulary, verdict rules, parse-failure rule, stack
matrix, and baseline format. It does not specify the CLI surface, JSON schema field layout,
subcommand names, or determinism guarantees of the checkers themselves — those belong to the
scripts and to
[`sub-specs/technical-spec.md`](../specs/2026-08-14-script-backed-quality-gates/sub-specs/technical-spec.md).

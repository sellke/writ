# Script-Backed Quality Gates

> **Status:** Complete (2026-08-14)
> **Created:** 2026-08-14
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Origin:** Recommendations 1–4 of [`2026-08-14-writ-dogfooding-quality-assessment-research.md`](../../research/2026-08-14-writ-dogfooding-quality-assessment-research.md)

## Specification Contract

**Deliverable:** Four quality guarantees Writ currently states as instructions to a
language model — coverage ≥80%, tests that actually test the code, an app that still
builds, and a project whose own gates are switched on — become read-only scripts whose
verdicts override the self-report, each validated against a real application codebase
before it ships.

**Must Include:** Validation against real application code, as an acceptance criterion
rather than a follow-up. Every check here exists because a prompt-level version of it
already failed silently for a year in a real project. Shipping a replacement that has only
ever run against this markdown repo would reproduce the exact defect the spec is named for.

**Hardest Constraint:** Telling a code defect apart from an environment defect. These
checks inspect and execute *other projects'* toolchains, where a missing database, an unset
env var, or an unsupported stack are all normal. A check that reports FAIL when it means
"could not tell" gets muted within a week, and takes the true findings with it.

**Success Criteria:** Run against `yuss.app` — the codebase whose year of use produced this
evidence — the four checks reproduce the four defects the research found by hand, at the
measured numbers: 57.2% coverage against a `Coverage threshold met: YES` claim, exactly 4
test files importing zero production source, `ignoreBuildErrors` + `ignoreDuringBuilds` +
absent `coverageThreshold` + dual lockfiles, and a build verdict that separates
`next build` failing from Postgres being unreachable.

**Scope Boundaries:**

- **Included:** a classification doc defining the finding vocabulary and severities;
  `scripts/quality-config-audit.py`, `scripts/test-integrity.py`, `scripts/build-smoke.py`
  with unit tests and eval registration; Gate 2 and Gate 4 wiring in `/implement-story`;
  `/initialize` baseline + coverage-floor writing; the `/status` health line.
- **Excluded:** performance, accessibility, and observability gates (research Option C —
  explicitly not recommended); manual-tail expiry and the cross-project feedback channel
  (research recommendations 6–7, separate specs); doc-drift lint (recommendation 8); making
  `DEGRADED` a durable machine-checkable status (contradicts a recorded exclusion — see
  *Business Rules*); any **new** gate number; TDD-order verification (recommendation 7 of
  the research is *test authenticity*, not test-first proof — see *Deliberate Omissions*).

## Evidence Base

Four findings, each measured rather than argued. All yuss line references are to the
repository at its 2026-08-10 head.

### 1. The coverage mandate has no mechanism behind it

`agents/testing-agent.md` states the bar three times — `:26` "Minimum 80% line coverage on
new files", `:148–149` "**≥80% line coverage on new files is MANDATORY**", and an exit
criterion at `:19` binding PASS to *"Coverage threshold met reads YES"*. The value it binds
to is `:133`:

```markdown
- **Coverage threshold met:** [YES/NO]
```

That is a field the agent types. Nothing recomputes it. In yuss, `jest.config.js:30–36`
declares `collectCoverageFrom` over `lib/`, `components/`, `utils/` and **no
`coverageThreshold` key at all**, so the project enforces nothing either; `app/` — all ~80
API routes — is excluded from collection outright. Measured with `jest --coverage`:
**57.23% statements**, with `lib/settlement-utils.ts` (the 1,273-line money core) at 46.9%
and `lib/auth-middleware.ts`, `lib/api-schemas.ts`, `lib/stripe-webhooks.ts` at 0%.
Meanwhile mature-era yuss commit bodies claim "Coverage 90–100% on all new files."

### 2. Tests that import nothing they claim to test

`app/api/user/password/__tests__/password-change.test.ts` is 351 lines. Its only import is
`bcryptjs`; at `:21` it defines `function validatePasswordStrength(password: string)` inside
the test file — a copy annotated "matches implementation" — and asserts against the copy.
It cannot fail when the route changes. It passed Gate 3 review and Gate 4 testing for
months.

**The measurement is itself evidence for how the check must be built.** Three passes over
the same 147 unit-test files:

| Method | Files flagged | Verdict |
|---|---|---|
| The research doc's own hand-audit | 6 | over-counted — `CompactActionBar.test.tsx:15` and `EventSelector.test.tsx:13` do import their components |
| Naive single-line `import … from` regex | 22 | 18 false positives — misses multi-line `import {\n…\n} from` (`quick-split-utils.test.ts:1`) and dynamic `await import('@/…')` (`Toast.test.tsx:262`) |
| Multi-line-aware module-specifier extraction | **4** | ground truth |

An 82% false-positive rate from the obvious implementation, and a 50% over-count from a
careful human read. This finding is the reason Story 3 specifies specifier extraction
rather than line matching, and the reason the count `4` is pinned as a fixture.

### 3. The project's own build gate was switched off, and nothing looked

`next.config.js:7–12`:

```js
eslint: { ignoreDuringBuilds: true },
typescript: { ignoreBuildErrors: true },
```

`tsconfig.json` sets `strict: true`. It cannot fail a build. Writ spent a year running
Gate 2's `tsc --noEmit` on top of a harness whose native equivalent was disabled, and no
command in the framework reads a target project's quality configuration to notice. Also
present: `bun.lock` **and** `pnpm-lock.yaml` alongside `"packageManager": "pnpm@10.33.0"`,
and a `lint` script that excludes `**/__tests__/**` and `tests/**`.

### 4. The field already filed this request

`.writ/specs/archive/2026-07-23-quick-split-single-transaction/drift-log.md`, entry
**DEV-004**, written by the project during a real story:

> It went undetected through Story 1's entire pipeline (Gates 1-5, all passing) because
> every test in this repo imports route handlers as plain functions … and invokes them
> directly — none of Story 1's tests, nor its own Gate 2 `tsc --noEmit`/lint pass, ever
> actually booted the Next.js framework router, which is the only place this class of error
> surfaces.

> **Process gap flagged:** No gate in this pipeline actually starts the Next.js server
> before Gate 4.5, and Gate 4.5 itself is normally skipped for stories with no visual
> mockups … Recommend a future process change: add a cheap `next build` (or at least a
> route-manifest check) to Gate 2 for any story that adds new `app/api/**` dynamic route
> folders, regardless of whether that story has UI mockups.

The bug was `Error: You cannot use different slug names for the same dynamic path ('id' !==
'token')` — build-breaking, deployment-blocking, and invisible to every gate that does not
boot the framework. Story 4 implements the recommendation this entry made, at the position
it named.

**Recorded caveat.** All four findings come from **one** project, one developer, one stack
(Node/TypeScript/Next.js). The *mechanism* — a guarantee with no executable behind it decays
without anyone noticing — is general. The *numbers* are not, and the four fixtures pinned in
this spec are ground truth about yuss, not about software. Story 2–4 checks must therefore
degrade honestly on stacks where they cannot compute an answer, rather than generalizing
from the one stack that produced the evidence.

## The Load-Bearing Idea

`scripts/exit-criteria.py` already establishes the pattern this spec generalizes. Per
`commands/implement-spec.md:261–265`, a run may report COMPLETE and be published as
`unmet`, because a read-only script re-derives the verdict from disk state and the script
wins. That is the only place in Writ where a self-report is checked rather than trusted.

Four more places need it. This spec adds no new gate, no new pipeline stage, and no new
command — it puts an executable behind claims that already exist.

**No new gate number, deliberately.** Gate numbers are free-text strings with no registry,
pinned by literal in five places in `scripts/eval.sh:2232–2236`, mirrored in
`scripts/eval-leanness.py:257`, `skills/subagent-result-completeness/SKILL.md:41–45`, and an
ASCII pipeline diagram at `agents/visual-qa-agent.md:149`. Extending Gate 2 and Gate 4 in
place costs a Pipeline-table cell rename; inserting Gate 2.6 or Gate 4.6 costs all of the
above plus a `--quick` policy decision. The cheaper edit is also the more honest one: these
are not new stages, they are the missing halves of two existing ones.

## 📋 Business Rules

**Verdict trichotomy — every check, every stack.** `PASS` / `FAIL` / `UNVERIFIABLE`. A
check that cannot compute an answer emits `UNVERIFIABLE` with a machine-readable reason and
never silently returns 0. Mapping to pipeline behavior: `FAIL` blocks; `UNVERIFIABLE`
surfaces in the story report and does not block. This is the *hardest constraint* made
operational — the checks may not launder "could not tell" into either "fine" or "broken".

**Stack support is declared, not inferred.** Node/TypeScript is first-class (it is the
stack the entire evidence base comes from). Python is best-effort. Every other stack emits
`UNVERIFIABLE: unsupported_stack`. A check must never guess at a toolchain it has no
fixture for.

**Environment failure is never code failure.** `build-smoke` classifies a non-zero build as
`FAIL` only when the failure is attributable to source; unreachable databases, missing env
vars, absent dependencies, and network failures are `UNVERIFIABLE: environment`. yuss's own
`build` script is `pnpm verify-db && pnpm prisma:deploy && prisma generate && tsx
scripts/seed-preview-test-user.ts && next build` — four database-dependent steps before the
compiler runs. A smoke gate that ran that script naively would report FAIL on every machine
without a Postgres branch, which is the failure mode that gets gates disabled.

**Unparseable is not absent.** `next.config.js` and `jest.config.js` are executable
JavaScript; `tsconfig.json` is JSONC, with comments and trailing commas. Writ has no
dependencies and no build step, so stdlib gives us `json` and `tomllib` and nothing that
reads any of those three. Detection is therefore heuristic — and a heuristic that fails to
find `ignoreBuildErrors` has learned nothing about whether the gate is on. Every inspection
records which files it parsed, which it could not, and by what method; a file that could not
be read emits `could_not_parse` and the affected findings become `UNVERIFIABLE`. The
forbidden outcome is a clean report produced by a parser that gave up. This is the same
error the naive test-authenticity regex made in *Evidence Base* §2, and it is the single
largest technical risk in this spec.

**"0 findings" and "0 things inspected" must not read the same.** Every checker's JSON
carries what it actually examined — the house rule `scripts/ac-trace.py` implements as
`scanned_files` / `ignore_filter`, and `scripts/eval.sh` states as *governor-instrumentation
Business Rule 8*. A vacuous pass is the failure mode these instruments are most likely to
die of.

**Baseline, then ratchet.** On `/initialize`, existing findings in a brownfield project are
recorded to `.writ/quality-baseline.md` as acknowledged debt and do not block. Findings not
in the baseline block. The baseline is a reviewable markdown file with a dated rationale per
entry — never auto-refreshed, because a baseline that silently re-baselines is just a
disabled check.

**Coverage thresholds are written at the measured floor, never at the aspiration.**
`/initialize` writes `coverageThreshold` at `floor(current measured coverage)`, not at 80%.
Writing 80% into a project measuring 57% breaks its build on the first run and teaches the
developer to delete the key. Writing 57% makes 57% the new minimum and lets it only go up —
the non-degrading principle ([ADR-006](../../decision-records/adr-006-non-degrading-destination.md))
applied to a number instead of a document.

**No permanent-warning instruments.** Every finding is blocking-by-default or explicitly
waived with a recorded reason. Writ has already run this experiment: per the 2026-08-13
research Finding 7, four byte instruments shipped non-blocking, one sat breached, and the
apparatus trained the dismissal it was built to prevent. A finding nobody must act on is a
finding nobody reads.

**`DEGRADED` semantics are consumed, not redefined.**
`.writ/docs/exit-criteria-classification.md:301–320` records `implement-story.c3` as
`Scope: excluded`, on the ground that the What Was Built record it reads from is allowed to
be incomplete by design. This spec does not reopen that. Gate 2 and Gate 4 additions route
through the **existing** BLOCKED escalation at `commands/implement-story.md:307–324` and its
existing `⚠️ DEGRADED` wording. No new status token, no `Status: DEGRADED` header, no
change to `scripts/spec-status.py`'s vocabulary.

**Read-only, in the strict sense.** The three checkers never write a file, matching
`scripts/exit-criteria.py` and `scripts/ac-trace.py`. Only `/initialize` writes — the
baseline file and the coverage-floor config — and it does so in a command a user ran
expressly to set a project up.

## 🎯 Experience Design

- **Entry point:** invisible. No new command, no new flag, no new question. The checks fire
  inside gates the developer already runs.
- **Happy path:** Gate 2 and Gate 4 emit one extra line each. Nothing else changes.
- **Moment of truth:** the first time `TEST_RESULT: PASS` arrives with
  `Coverage threshold met: YES` and the pipeline prints the coverage the tool actually
  measured, contradicting it — and the story does not close.
- **Feedback model:** one line per check in the story report, naming the finding code, the
  measured value, and the file that produced it.
- **Error experience:** `UNVERIFIABLE` reads as *"this check could not run here, and here is
  the reason"* — never as a failure, never as a pass, and never as silence.

## Implementation Approach

Six stories. Story 1 writes the specification the checkers implement against — the same
relationship `.writ/docs/acceptance-criteria-ids.md` has to `scripts/ac-trace.py`, and
`.writ/docs/exit-criteria-classification.md` has to `scripts/exit-criteria.py`. Stories 2–4
are three independent read-only checkers, each with unit tests, an eval registration, and a
yuss-fixture validation task. Stories 5 and 6 wire them into commands.

Stories 2, 3 and 4 touch disjoint files and can run as one parallel batch. Story 5
(`commands/implement-story.md`, `agents/testing-agent.md`) and Story 6 (`commands/initialize.md`,
`commands/status.md`) also touch disjoint files and can run as a second parallel batch.

**Where each check runs:**

| Check | Position | Consumes |
|---|---|---|
| `build-smoke` | Gate 2, inside the existing block (`commands/implement-story.md:183–191`) | — |
| `test-integrity coverage` | Gate 4, after the testing agent returns | its `Coverage threshold met` field |
| `test-integrity authenticity` | Gate 4, same invocation | the story's `test_files` |
| `quality-config-audit` | `/initialize` (baseline write) and `/status` (health line) | `.writ/quality-baseline.md` |

**`/status` compatibility is a hard constraint, not a preference.** Its third exit criterion
reads *"every execution state file under `.writ/state/` was read without being written, and
no build, test or git-mutating command ran"*, restated as a terminal constraint at
`commands/status.md:477`. `quality-config-audit` is pure file reads and satisfies this;
`test-integrity coverage` and `build-smoke` execute tooling and therefore **never** appear in
`/status`. Story 6 surfaces only the config audit there.

**Verdict vocabulary aligns with the existing health reducer.** `/status` already renders a
categorical `Healthy` / `Warning` / `Attention` from `scripts/phase-state.py health`, where
missing or stale evidence is a Warning — "never a silent pass" — and `Attention` requires an
affirmative current failure. This spec's `PASS` / `UNVERIFIABLE` / `FAIL` maps onto those
three exactly. Reuse the vocabulary rather than inventing a fourth way to say the same thing.

**Fixture strategy.** yuss cannot be vendored — it is a separate private repository, and a
gate validated only against a snapshot would rot the moment either side moved. Each checker
gets two fixture layers: synthetic tempdir fixtures in `scripts/tests/` reproducing the
*shape* of each finding (the blocking, CI-runnable layer), and a documented one-shot
validation run against a real yuss checkout whose measured output is recorded verbatim in
the story's What Was Built record (the evidence layer, run once by the implementer). The
four numbers in *Success Criteria* are what that run must reproduce.

## Deliberate Omissions

**TDD-order verification is not in scope.** The research listed "TDD is instructed, never
verified" as gap 7, and the tempting fix — check that the test commit precedes the
implementation commit — does not survive contact with how these stories are actually
committed (one commit per story, tests and code together, per yuss's mature-era convention).
A check that demands a commit ordering the house style does not produce would fail every
story and be disabled within a day. Test *authenticity* (Story 3) is the part of that gap
that is mechanically decidable; test *order* is left as an instruction, honestly labeled.

**Gate 4.5 stays conditional on mockups.** The research recommended making its launch step
unconditional. Story 4 makes that redundant: once Gate 2 boots the framework on every story,
the DEV-004 class of defect is caught earlier and cheaper than a screenshot pass would catch
it, and Gate 4.5 keeps its single job of comparing rendered UI against mockups.

## Risks

**The checks find so much on first contact that they get waived wholesale.** Any real
brownfield project will light up. Mitigated by the baseline rule — first run records, it
does not block — but the failure mode to watch is a baseline that grows on every run instead
of shrinking.

**`build-smoke` is the story most likely to be cut.** It is the only check that executes
rather than reads, the only one whose runtime is measured in minutes, and the only one whose
correctness depends on classifying failure causes it did not produce. If the environment/code
classification cannot be made reliable on the Node/TS fixture set, the honest outcome is to
ship it emitting `UNVERIFIABLE` more often than `FAIL`, or to close the story
`Closed — Not Implemented` with the measurement recorded — the disposition Phase 10's
progressive-disclosure specs already established as legitimate.

**Six stories, three new scripts, and six modified product files is at the upper end of a
single spec.** Run `/assess-spec` before `/implement-spec`; if it recommends decomposition,
the clean seam is Stories 1–3 + 6 (the read-only, file-inspecting half) as one spec and
Stories 4–5 (the executing half) as another.

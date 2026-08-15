# Writ Dogfooding Quality Assessment — Evidence from yuss.app

> Created: 2026-08-14
> Status: Complete
> Method: Four parallel codebase investigations — (1) process evidence in yuss.app's `.writ/` workspace and 462-commit git history, (2) functional code quality of yuss (tests executed, coverage measured), (3) non-functional code quality of yuss, (4) Writ framework current state (v0.32.0). Synthesis cross-correlates framework mechanisms against product outcomes.
> Evidence base: https://github.com/sellke/yuss (cloned at commit head, 2025-08-12 → 2026-08-10 history) and this repo at v0.32.0.

## Research Questions

1. What development process did Writ *actually* facilitate on yuss.app, per artifact and git evidence — and does it refute the "Writ isn't dogfooded" criticism?
2. What is the resulting code quality on functional axes (correctness, tests, edge cases) and non-functional axes (architecture, security, performance, maintainability)?
3. Where does the evidence show Writ causing quality, and where does it show ceremony without quality payoff — or gaps that let defects through?
4. What modifications would most advance the mission (durable contract layer, non-degrading artifacts, repeatable quality)?

## Executive Summary

**The "not dogfooded" criticism is factually wrong.** yuss.app is a year of continuous dogfooding: 113 spec folders, 385 story files (377 with real acceptance criteria), 37 releases, drift logs that caught severe bugs pre-ship, and a commit history whose discipline visibly tracks the framework's maturity — from vague 4,700-line "enhance UX" mega-commits in the Code Captain era to fully traceable issue → spec → story-commit → drift-log → verify → CHANGELOG-linked-release loops by mid-2026. The pipeline demonstrably caught real defects: a build-breaking route collision that passed Gates 1–5 (caught at Visual QA), a dead-code race guard exposed by mutation testing at Gate 4, and a silent money regression reverted same-day off a CI integration failure. Writ's own 2026-08-13 research concluded its code-facing gates "never fired against application code" — true of *this repo*, but yuss shows they fired for months on a real product. The evidence just lived in a repo the inward-looking research never examined.

**The sharper finding is a clean natural experiment: yuss's quality is strong exactly where Writ's guarantees are mechanical, and weak exactly where they are prompt-level or absent.** Where a script, CI job, or checklist enforced the bar, the results are excellent — 3,053 genuinely passing unit tests in under 9 seconds with near-zero snapshot filler, systematic ownership-checking auth on all ~80 API routes, verified Stripe webhooks, disciplined DB-branch protection born from a production data-loss incident. Where the guarantee was an instruction to an LLM, it silently failed: the "MANDATORY ≥80% coverage" gate coexists with a jest config that has **no coverage threshold at all** (measured: 57% overall, with `app/` excluded from collection and the 633-line core money function ~47% covered); a handful of **fake tests reimplement the logic they claim to test** (including password validation) and passed every review gate; and `next.config.js` ships `typescript: { ignoreBuildErrors: true }` — the product's own build gate is neutered and no Writ mechanism ever looks at harness configuration. Where Writ has *no* gate, the corresponding defect class simply exists: money stored as `Float` throughout a settlement app (patched with a $0.51 drift-tolerance epsilon), client-side N+1 fetches ×4 in the hottest page, zombie root docs describing an application that no longer exists.

**Recommendation in one line: stop adding process breadth; convert existing prompt-level guarantees into script-backed ones, and add the two missing gates (runtime smoke, foundational data-model review) that yuss's own drift log already asked for.** Writ's proven pattern — `exit-criteria.py` overriding a run's self-reported completion — is the template; it should be applied to coverage, test authenticity, build/boot verification, and project quality-config integrity. That is the shortest path to the mission's "repeatable quality — not brilliant one day and embarrassing the next."

## Key Findings

### Finding 1 — Dogfooding is real, and it shows a maturity curve, not steady-state discipline

yuss's year splits into eras (story/spec-referencing commits per era: **0 → 6 → 21 → 37**):

| Era | Character |
|---|---|
| 2025-08–10 (Code Captain early) | Spec theater: elaborate "track" spec folders coexisting with vague mega-commits (`048fb51`: 29 files, +4,699), zero commit↔spec linkage, zero releases |
| 2025-11–2026-01 | First story-tagged commits; whole-spec-in-one-commit still common (`1014e06`: 63 files, +7,545); **production data-loss incident** (2025-12-01, unprotected `/api/migrate` wiped prod DB) |
| 2026-02–04 (Writ migration, `3aeb57a`) | Conventional commits, PR numbers, `[Story N/M]` convention, first release tags (37 total from here), **the April test-gate reckoning** |
| 2026-05–08 | Full pipeline: per-story commits with recorded SHAs, drift logs, verify-spec closeouts, same-day bug→spec→fix→release (v0.19.0, 2026-08-10) |

The turn is causal, not coincidental: each discipline arrived with the framework feature that enforced it (traceability IDs → commit-SHA recording; verify-spec → status normalization commits; the restored jest gate → real CI backstop). Framework improvements measurably improved process outcomes. (Evidence: yuss git history; `.writ/specs/archive/` ledger; era table from process investigation.)

### Finding 2 — The gates caught real, severe bugs (process working as designed)

- **DEV-004** (`archive/2026-07-23-quick-split-single-transaction/drift-log.md`): a build-breaking Next.js sibling-dynamic-route collision "went undetected through Story 1's entire pipeline (Gates 1–5, all passing)" because unit tests import route handlers directly and never boot the router. Caught at Gate 4.5 Visual QA — which only runs when mockups exist. The drift log explicitly recommends adding `next build` to Gate 2. **That recommendation never propagated to the framework** (Gate 2 today is still lint/typecheck/format only).
- **DEV-007** (same log): mutation testing at Gate 4 exposed a double-tap guard as dead code; fixed pre-merge with a same-tick `act()` test.
- **`1fa24ed`** (2026-05-13): CI integration test caught a silent money regression ("Expected: youOwe=15 … Got: youOwe=0") from a rework that exceeded its filed scope — reverted same day, follow-up spec next day.
- **The April 2026 test-gate reckoning**: the first real run of the integration suite found **75/405 tests failing** — releases had been shipping with `--skip-gate`. The response was a five-spec triage campaign in one day, ending with a canonized integration-triage methodology. The process detected and repaired its own decay — but the decay happened because the gate was skippable.

### Finding 3 — Prompt-level guarantees silently failed; mechanical ones held

This is the central correlation of the whole assessment:

| Writ guarantee | Enforcement character | Outcome in yuss |
|---|---|---|
| "≥80% coverage on new files is MANDATORY" (testing-agent) | LLM self-reported | **No `coverageThreshold` in any jest config.** Measured: 57.2% statements; `app/` (all API routes) excluded from collection; `lib/settlement-utils.ts` (the money core) 46.9%; `lib/auth-middleware.ts`, `lib/api-schemas.ts`, `lib/stripe-webhooks.ts` 0% unit. Commit bodies claiming "Coverage 90–100% on all new files" are unverifiable |
| TDD "write the failing test first" | Instructed, never verified | Mixed by era; ~half of mature-era feature commits include tests. Worse: **6 unit suites import no source code at all** — `app/api/user/password/__tests__/password-change.test.ts` (351 lines) reimplements `validatePasswordStrength` inside the test file and tests the copy. A fake test on a security path, passing every gate for months |
| Review gate (Gate 3) checks quality/security/tests | LLM verdict, read-only agent | Passed the fake tests, the `Float` money model, and `ignoreBuildErrors: true` repeatedly; review depth degrades by an LLM-classified change surface |
| Lint/typecheck (Gate 2), CI unit gate, DB-branch protection, Stripe signature verification, dependency graphs | **Script/tool-backed** | All held. 3,053/3,053 unit tests pass in 8.7s, deterministic, zero skips; CI enforces typecheck+lint+unit on every PR; `prisma:push` literally banned in package.json; prod-DB guards in integration setup |
| Drift logging, exit-criteria re-derivation | Structured artifact + script | The two drift logs that exist are excellent and caught real bugs (Finding 2) — but only 2 of 113 specs have one; the mechanism existed for ~2 of 12 months |

The product also contains the single most corrosive quality fact found anywhere: **`next.config.js` sets `eslint: { ignoreDuringBuilds: true }` and `typescript: { ignoreBuildErrors: true }`** — `strict: true` in tsconfig is decorative at build time. No Writ command inspects the project's own quality configuration, so the framework spent a year enforcing gates on top of a harness whose native gates were switched off.

### Finding 4 — Where Writ has no gate, the defect class exists; where it has one, it mostly doesn't

Writ's NFR coverage matrix (from the framework survey) predicts yuss's defect map almost exactly:

| NFR axis | Writ mechanism | yuss outcome |
|---|---|---|
| Security | Strongest axis: review category ("never Minor"), `/security-audit`, drift rule | **Adequate/Strong**: systematic HOF auth middleware with ownership checks on every sampled route, privacy-preserving 404s, verified webhooks, targeted rate limiting, clean secrets. The one production disaster (data loss via `/api/migrate`) predates the mature process; the disciplined response (DB-branch validation spec, Neon-branch CI isolation) came through the process |
| Performance | **No command, no gate** (two discovery-prompt bullets) | **Weak**: settlement-status N+1 fetch loop repeated 4× in `app/events/[id]/page.tsx`; `canAccessEvent` loads the full event graph for every yes/no check; awaited-writes-in-loops; essentially zero caching; 1,055–1,358-line `"use client"` page monoliths. (Counterpoint: Prisma indexes are genuinely good — likely architecture-check influence) |
| Data-model correctness | Checklist bullets only; no schema review gate | **Serious**: money as `Float` in every table of an expense-splitting product, epsilon patchwork (`0.01`, `0.011`, and a **$0.51** `AMOUNT_DRIFT_TOLERANCE`), two contradictory rounding strategies (event splits drift-correct to exact totals; quick-splits deliberately let a cent evaporate: $100/3 → $99.99), dates stored as `String`, unguarded denormalized aggregates. Also: expense-split inputs unvalidated — no sum-equals-total check, no sign check, no event-membership check on `paidById`/split participants; an authenticated user can write inconsistent money data |
| Runtime verification | **No smoke gate**; Gate 4.5 conditional on mockups; UAT plans manual | DEV-004 build-break passed Gates 1–5; e2e suite carries flake scar tissue (`retries: 3`, `waitForTimeout` sleeps); integration suite (703 cases) runs only on path-filtered CI and needs a live Neon branch |
| Maintainability / doc hygiene | Nothing outside `.writ/` | **Weak**: README claims Next 14.2.16 (actual: 16.1.6) and diagrams a LocalStorage architecture that hasn't existed for months; 11 zombie root docs (`ROADMAP.md` shows unchecked boxes for auth shipped 2025-10); a committed 528KB unused Tailwind template (`pocket-js/`), dual lockfiles, committed `dev.log`, a 1-byte `create-favicon.js`; 470 `console.*` calls; 1,480-line component. Counter-signals: only 8 TODO/FIXME in production code, and in-schema documentation of invariants is exceptional |

Functional quality, by contrast — the axis Writ's pipeline actually targets — is genuinely good: high-volume behavioral tests with real edge cases (empty states, null emails, zero-weight ratios, rounding quirks explicitly locked with rationale), optimistic UI with tested rollback, consistent structured error handling, almost no swallowed errors, correct Stripe integer-cent boundary conversion.

### Finding 5 — Degradation happened everywhere no command routinely touched

The mission claims "non-degrading by construction." The evidence says: non-degrading *where a command's write-path covers it*, degrading everywhere else.

- `.writ/` needed a **one-day retroactive bulk sweep** (2026-08-10: all 107 archive-ledger entries dated the same day; ~40 specs' statuses assigned retroactively; every entry "no knowledge evidence yet").
- `state.json` stale for 11 months (`project_name: "ioyoux"`, last updated 2025-09-10).
- 4 of 6 active specs stuck for 3–6 months on **manual-verification tails** ("Manual Smoke Pending", "Story 3 UI verification pending", "ops pending") — the same failure signature as this repo's 1/265 (0.4%) UAT execution rate. **Human-manual steps are where the process goes to die, in both repos.**
- Root-level docs were never reconciled with `.writ/product/` — only text-swept during the rebrand. Two systems of record; one alive, one zombie.
- Meanwhile the artifacts commands *do* touch each run — `context.md`, `CHANGELOG.md`, spec statuses post-verify-spec — stayed accurate.

### Finding 6 — Learning loops work locally but there is no channel from consumer projects back to the framework

yuss's refresh-log shows the evidence-bound loop functioning (e.g., `/prototype`'s Quick Contract questions removed after transcript evidence showed defaults chosen 5/6 times). But yuss's drift logs contain *framework-level* findings — most concretely DEV-004's "add `next build` to Gate 2" — that never reached this repo. `/refresh-command` reads local transcripts only; the cross-project learning corpus sits in the parking lot. The framework's richest source of improvement evidence (a year of real product usage) was structurally invisible to it — which is also exactly why the 2026-08-13 inward-looking research concluded the gates had "never fired."

## Overall Assessment

**Process quality: strong at maturity, and the maturity was framework-driven.** The mature loop (issue → spec → story commits with drift references → gates → verify → linked release) is traceable end-to-end and demonstrably caught severe bugs before ship. Grade: **B+**, docked for skippable gates having actually been skipped for months (April reckoning) and manual tails never closing.

**Functional code quality: good, with two serious domain-core exceptions.** The test culture Writ instilled is real and unusually healthy for AI-built code. But the float-money model with epsilon forgiveness and the unvalidated split-integrity writes are latent correctness bugs *in the product's core domain* — precisely the "expensive thinking before code" that contract-first was supposed to force, missed at the foundational-decision layer and never revisited. Grade: **B** overall; **C−** for the money core specifically.

**Non-functional code quality: mixed, tracking Writ's gate coverage almost perfectly.** Security B+, performance C−, maintainability/doc hygiene D+. The framework gets what it inspects.

**Net verdict on the framework:** Writ demonstrably raises the floor of AI-assisted development — the mature-era yuss is far better engineered than typical solo AI-built products, and the paper trail proves *why*. But its ceiling is set by enforcement character: every guarantee that lives in a prompt eventually got faked, skipped, or drifted, and every axis without a gate accumulated exactly the debt you'd predict. The mission's differentiators (non-degrading, repeatable quality) are earned today only inside the mechanically-enforced perimeter.

## Options Analysis

### Option A — Harden existing guarantees: prompt → script (recommended core)

Apply the `exit-criteria.py` pattern (machine re-derivation overriding self-report) to the pipeline's self-reported gates.

- **Pros:** Directly targets the proven failure mode (Finding 3); no new ceremony — same gates, real enforcement; the pattern is already validated in-repo and rated ahead of the SDD field; each check is small and independently shippable.
- **Cons:** Per-stack tooling variance (coverage output formats differ); some checks need project-side config writes at `/initialize`.
- **Effort:** Medium (a handful of small scripts + gate wiring). **Risk:** Low.

### Option B — Add the two missing gates yuss's evidence demands (runtime smoke + foundational data review)

Gate 2 gains build/boot verification (`next build` or stack equivalent, boot + health-route hit); `/create-spec`/architecture-check gains a blocking foundational-decision review for data-shaped features (money types, date types, denormalization, enum discipline) with an ADR trigger.

- **Pros:** Runtime smoke was *literally requested by a yuss drift log* and closes the tests-pass-but-app-doesn't-run gap without depending on mockups; the data review would have caught the single worst defect (Float money) at contract time for the cost of one checklist gate; both are cheap relative to payoff.
- **Cons:** Build step adds per-story latency on large projects; data review adds ceremony to small specs (mitigable via change-surface classification, which already exists).
- **Effort:** Small–Medium. **Risk:** Low.

### Option C — Broaden NFR coverage with new commands (perf gate, a11y gate, observability gate, doc-hygiene linter)

- **Pros:** Addresses the weakest measured axes (performance, maintainability, docs).
- **Cons:** Contradicts the "thin" mandate and the project's own "stop building Writ" finding; new prompt-level gates would reproduce the Finding-3 failure mode unless script-backed first; performance/a11y gates are hard to make mechanical and cheap.
- **Effort:** Large. **Risk:** Medium — process bloat, low compliance. **Not recommended as a package**; cherry-pick only the mechanical subset (doc-drift lint, quality-config audit) into A/B.

### Option D — Close the loops (manual-tail expiry, cross-project feedback channel, production→spec intake)

- **Pros:** Targets the two degradation signatures found in *both* repos (manual steps never closing; framework blind to consumer-project evidence); the cross-project channel has now-concrete evidence justifying its promotion from the parking lot.
- **Cons:** Feedback-channel design has real surface-area questions (what's exported, how it's consumed); production intake risks scope creep toward observability tooling Writ deliberately doesn't build.
- **Effort:** Medium. **Risk:** Medium.

## Recommendations

**Primary: A + B as one hardening campaign, then D's cheapest slice. Explicitly defer C.**

Concretely, in priority order:

1. **Coverage becomes machine-verified.** The testing gate's script parses the coverage tool's actual output (lcov/coverage.py/etc.) and re-derives PASS/FAIL; `/initialize` writes real `coverageThreshold` config into the project so the project enforces its own bar even when Writ isn't running. *(Kills: unverifiable "90–100%" claims over a thresholdless config.)*
2. **Test-authenticity check.** A mechanical gate check: every test file must import at least one symbol from production source (trivially scriptable per-stack). *(Kills: the fake-test pattern — reimplemented password validation passing gates for months.)*
3. **Runtime smoke in Gate 2.** Build + boot + health check, stack-detected, with Gate 4.5 no longer conditional on mockups existing for its launch step. *(Kills: DEV-004-class escapes; honors yuss's own drift-log recommendation.)*
4. **Project quality-config audit** in `/initialize` and the `/status` health line: detect neutered gates (`ignoreBuildErrors`, `ignoreDuringBuilds`), missing thresholds, dual lockfiles, tests excluded from typechecking. *(Kills: enforcing process on top of a switched-off harness.)*
5. **Foundational-decision review at contract time** for data-shaped specs: money/date/enum/denormalization types are contract items requiring an explicit ADR or an explicit waiver. *(Would have caught: Float money, String dates, at the only moment they were cheap to fix.)*
6. **Manual-tail expiry semantics.** `/verify-spec` flags any manual-verification step pending > N days as a blocking finding with three exits: execute it, convert it to an automated check, or explicitly waive it with rationale. UAT plans default to executable (Playwright) form where a UI exists. *(Kills: specs frozen "Manual Smoke Pending" for months; 0.4% UAT execution.)*
7. **Cross-project feedback channel (minimal form).** A convention + tiny script: consumer-project drift-log entries tagged `process-gap` are exportable/greppable, and `/refresh-command` in the Writ repo lists them as candidate evidence. Promote the parked cross-project learning corpus with this as its first concrete increment. *(Kills: framework-improvement evidence dying in consumer repos.)*
8. **Doc-drift lint (cheapest C item, folded into hygiene):** flag root-level docs contradicting manifest facts (version claims vs package.json) and unreconciled duplicate systems of record. Advisory, not blocking.

**Rationale:** Every recommendation above is (a) evidenced by a specific yuss defect or degradation, (b) mechanical rather than prompt-level, honoring the single clearest lesson of the whole assessment, and (c) thin — scripts and gate wiring, no daemons, no new pipeline stages. This is also the direction the repo's own ADR-023 admission points ("all governance is ex ante… nothing observes whether a run honored it"): these are the *ex post* observers, applied at the highest-value points.

## Risks & Mitigation

| Risk | Mitigation |
|---|---|
| Per-stack variance makes script-backed gates brittle (coverage formats, build commands) | Start with the stacks Writ demonstrably serves (Node/TS first — yuss's stack); adapter-style detection with graceful degradation to today's advisory behavior, never silent skip — emit `DEGRADED: unverifiable` |
| Runtime smoke slows every story on large apps | Cache builds per batch; run boot-check once per batch rather than per story; change-surface classification already exists to scope it |
| New mechanical gates train dismissal if they warn without blocking (Finding: the governor-ratchet failure, ADR-021/Finding 7) | Ship each check blocking-by-default with an explicit waiver syntax, never permanent-warning mode |
| Foundational-decision review re-bloats `/create-spec` ceremony | Trigger only on data-shaped change surfaces (new schema/models/money/dates), not every spec |
| Single-project evidence base (one product, one developer, one stack) over-fits recommendations | The recommendations are enforcement-character changes, not stack features; still, validate the top 3 on a second consumer project before promoting beyond candidate status |

## Further Research

- **Integration-suite ground truth:** yuss's 703 integration test cases could not be executed here (require a live Neon branch); their real pass state — and whether the CI path filters leave DB-logic changes untested in practice — is unverified.
- **Counterfactual quality:** no baseline exists for what this developer would have shipped without Writ; the maturity-curve correlation is strong but the causal magnitude is unmeasurable from one project.
- **E2E reliability:** the flake scar tissue (`retries: 3`, sleeps) suggests the 188 e2e tests overstate reliable signal; a flake-rate measurement would say whether Gate 4.5-style checks can be trusted as blocking.
- **Second consumer project:** every finding here derives from one repo. The framework survey's own primary recommendation ("stop building Writ and use it") now has a sharper form: *use it on a second real codebase with the hardened gates from this document, and measure whether the Finding-3 failure modes disappear.*

## Sources

All evidence is first-party repository artifacts examined 2026-08-14:

- **yuss.app repo** (https://github.com/sellke/yuss): git history (462 commits, tags v0.2.0–v0.19.0); `.writ/specs/` + `archive/` (113 spec folders, `LEDGER.md`); `archive/2026-07-23-quick-split-single-transaction/drift-log.md` (DEV-004, DEV-007); `archive/2026-04-27-restore-jest-gate/`; commits `3aeb57a`, `048fb51`, `1014e06`, `1fa24ed`, `a927023`, `32fc8e1`; `next.config.js`; `jest.config.js`; `prisma/schema.prisma`; `lib/settlement-utils.ts`, `lib/quick-split-utils.ts`, `lib/expense-recalc.ts`, `lib/auth-middleware.ts`, `lib/api-schemas.ts`; `app/api/user/password/__tests__/password-change.test.ts`; `app/events/[id]/page.tsx`; `middleware.ts`; root docs (`README.md`, `ROADMAP.md`, `TECHNICAL_PRINCIPLES.md`, `SIMPLICITY_GUIDELINES.md`); measured test run: 147 suites / 3,053 tests passing, coverage 57.23% statements.
- **Writ repo** (this repo, v0.32.0): `commands/implement-story.md`, `commands/ship.md`, `commands/verify-spec.md`, `commands/review.md`, `commands/security-audit.md`; `agents/testing-agent.md`, `agents/review-agent.md`, `agents/coding-agent.md`; `scripts/exit-criteria.py`, `scripts/ac-trace.py`, `scripts/eval.sh`; `.writ/product/mission.md`; `.writ/decision-records/adr-022-autonomy-gate-classes.md`, `adr-023-stakes-proportional-diligence.md`; `.writ/research/2026-08-13-writ-vs-gstack-gastown-research.md` (Findings 4, 7, 8, 10).

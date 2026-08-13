# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.31.0] - 2026-08-13

**Machine-Evaluable Exit Criteria + Implement-Loop Recalibration** — `/implement-phase`, `/implement-spec`, and `/implement-story` gain a read-only stop-time checker that turns their `exit_criteria` frontmatter into verdicts (`met`/`unmet`/`unknown`/`impossible`) instead of self-reported completion. A full 6-story run of that spec then surfaced real orchestration friction, fixed in the same release: an ambiguous spawn-mechanism note, two completion-bookkeeping gaps, and two undocumented sub-agent-integration failure modes.

### Added

- **`scripts/exit-criteria.py`** — a read-only checker classifying each of the 10 `exit_criteria` across the three implement commands into evaluable-now, needs-run-record, or structurally-unobservable, with the full classification recorded in `.writ/docs/exit-criteria-classification.md`. Additive run-record fields (`exitCriteria[]`, `terminalStatus`, `haltReported`) land in `scripts/phase-state.py`, wired into `scripts/eval.sh` (18 fixture scenarios) and the adapters' `/goal` Stop hook.
- **`skills/subagent-result-completeness`** — how to tell a spawned gate agent's complete verdict (the exact shape each of Gate 0/1/3/4/4.5 requires) apart from a mid-task stop, and the resume-and-ask-again recovery step. Directly evidenced: nearly every spawned agent in the run that produced this spec stopped mid-synthesis at least once.
- **`skills/subagent-worktree-integration`** — how to reconcile a spawned agent's isolated git worktree with the orchestrator's own checkout (recognize → scoped diff → copy → re-verify → cleanup), including the stale-worktree-behind-main failure mode. Every gate agent in that same run — including nominally read-only ones — ran in its own isolated worktree with no documented reconciliation procedure.

### Changed

- **`commands/implement-phase.md` / `commands/implement-spec.md`** — completion reports now carry the checker's verdict and per-criterion evidence; `implement-spec.md`'s own `✅ Specification Complete` banner is gated on a `met` verdict rather than the run's self-report.
- **`commands/implement-spec.md`** — Step 3.2 states explicitly what "spawn ... concurrently" means on a harness that loads `/implement-story` inline rather than backgrounding it; Step 3.3's execution-state write is now a required disk write, not an optional log line; the completion step syncs `spec.md`'s own `> **Status:**` header on a `met` verdict, closing a gap `/verify-spec` had to catch by hand.
- **`commands/implement-story.md`** — two new cross-cutting blockquote notes under the Step 3 pipeline intro point at the skills above, applying to every gate that spawns a sub-agent (Gate 0, 1, 3, 4, 4.5).
- **README.md** — the Skills table was six releases stale (listed 6, 16 exist); now lists all 16, and the "six skills are live today" claim is corrected.

### Why

Both specs came from the same real run: `2026-08-12-machine-evaluable-exit-criteria` built the checker across 6 stories, and running that spec end-to-end — architecture-check, coding, and review agents spawned roughly 18 times — is what surfaced the orchestration gaps `2026-08-12-recalibrate-implement-loop` fixes. Neither is speculative hardening; both are named, evidenced friction from one execution, not a generic "commands could be better" pass.

## [0.30.3] - 2026-08-12

**Product Docs Reconciled to the Phase 10 Closure** — `/plan-product --reconcile` caught the framing layers of `mission.md`/`roadmap.md` still describing Phase 10 as "planned, in flight" after it closed, plus two stale-truth defects the pass surfaced. One `/release` fix ships to installed projects; the rest is this repo's product layer catching up to its own closure record.

### Fixed

- **`/release` Step 3.1 now maintains `.writ/manifest.yaml` `metadata.version`** alongside the other version files, guarded to the indented key (the top-level `version:` is the manifest schema version and never moves). The value had drifted 15 minor versions before Phase 10's one-time fix, then drifted again to `0.29.0` against `v0.30.2` within a day — because the fix was a value, not a maintainer. Hand-corrected to current in the same commit that gives it an owner; this release is the step's first live run.
- **The roadmap closure's "Scenario 20 not yet run" claim was false by a few commits.** The manual criterion — one real `/implement-story` run with progressive disclosure active — ran and passed later the same day (`uat/disclosure-harness-probe`, story-1 of the dirty-tree-guard spec): all eight applicable skill reads fired lazily at their own steps, so the −35.9% floor reduction is real, not paper. The closure and the success criterion now cite the pass and name what stays open — the `--quick` path and the missing-skill degradation probe (Scenario 20 steps 5 and 7).

### Changed

- **`mission.md`** — the falsified "thin is a target, Phase 10 closes the gap" blockquote rewritten to the closure's findings (the 516KB alarm was a measurement artifact; worst real invocation ~19.4k tokens, 7.2× smaller; efficiency governed by ADR-023's stakes-proportional diligence with deliberately no mechanical constraint); the Key Features Phase 10 block moved from plan to outcome; Next Horizon states plainly that **no phase is currently committed**; the parking-lot blockquote aligned with the roadmap's authoritative list; Phases 8–9 labeled with their release versions.
- **`roadmap.md`** — header status and Phase 10 heading aligned to the closure section in the same file; four closure-status sentences claiming "pending `/release`" corrected (Phases 6–9 shipped in v0.19.0/v0.20.0/v0.23.0 — stale through eleven tagged releases); the Phase 9 release caveat marked resolved; Leanness Guardian annotated with its v0.24.0 full-surface successor (ADR-019); five inter-phase infrastructure specs recorded in the condensed history so no Complete spec lacks a roadmap home; two revision-log rows record the pass.
- **Derivatives regenerated** — `mission-lite.md` and `.writ/context.md` now reflect the revised authoritative docs (no active spec; all 55 specs archived).

### Why

The reconcile posture exists for exactly this: the closure record and ADR-023 were honest the day they were written, but nothing re-read the summaries that frame them. `/verify-spec --product` confirms the layer is now consistent (P1 parity clean, P2 all ADR references resolve, P3 derivatives fresh); `eval.sh` reports 0 findings with a warning set identical to the pre-change baseline.

## [0.30.2] - 2026-08-12

**Stakes-Proportional Diligence** — Writ stops optimizing bytes, and adopts no number in their place. [ADR-023](.writ/decision-records/adr-023-stakes-proportional-diligence.md) supersedes ADR-021: diligence is decided per decision, by stakes, because no universal exchange rate between a decision and its cost exists.

### Added

- **A stakes triage in `commands/_preamble.md`**, beside ADR-022's gate-class table — the only change that reaches installed projects. Before spending diligence on any decision: *does the answer change what happens?* (if no, it is not a decision — drop it) and *how bad if it's wrong?* (reversible → decide, act, record; irreversible or wide → full rigor). The triage must cost less than the decision it governs; if answering it needs investigation, that *is* the answer. **Safety gates are never capped by count** — rarity is not irrelevance.

### Changed

- **The byte budget is demoted from design constraint to reported drift signal.** ADR-021's per-command cap (24,960) and 400-line tripwire still compute and still name every violator with its overage; only their authority is removed. `eval-leanness.py`'s cap had shipped non-blocking for a *circumstantial* reason — "blocking once a future decision converts the remaining commands." That decision came and went the other way, so the demotion is now recorded as permanent, with a guard: never flipped to blocking without a recorded derivation linking the threshold to measured harm.
- **ADR-021 is `Superseded`**, with reciprocal cross-references and an explicit note on what survives — every measurement, the extraction technique, the `required_skills:` eager-pre-load correction, and the five archived spec contracts as design records.
- **The roadmap's two Phase 10 byte/line success criteria are struck as void**, not deleted, with a postscript stating the goal is *withdrawn, not merely unmet*.

### Why

The goal is economy of *steps and ruminations to reach exit criteria*, especially as autonomy grows. Bytes measure file size. Where the two diverge, bytes point the wrong way: extraction cut `implement-story`'s floor 35.9% **while adding eight decision points, five of which fire unconditionally and buy nothing**. No byte instrument can see that trade — it counts what is loaded, never what must be decided.

Replacing bytes with a step or decision-count threshold was attempted and abandoned. Inlining the five dead reads would raise the floor 17,376 B on every run to save 4,750 on the worst run — about 3,475 bytes of permanent floor per decision removed. Pricing that needs an exchange rate that is not merely unmeasured but **not a stable quantity**: a decision's cost is a function of its stakes. There is no denominator making a load-a-skill decision commensurable with a merge-to-main decision.

Writ therefore has **no mechanically enforced efficiency constraint** as of this release. That is a deliberate cost, not an oversight — an unenforceable true rule was judged better than an enforceable wrong one. Reviewed 2026-11-11 alongside ADR-021 and the `required_skills:` trigger.

## [0.30.1] - 2026-08-12

**The same bug, one layer up.** v0.30.0 shipped a fix for a vocabulary that was declared and referenced nowhere. Two questions about that release — *why wasn't the completed spec archived?* and *why are never-executed specs in the archive?* — found the identical defect in `spec-status.py`, the file v0.30.0's spec had explicitly scoped out as "already correct."

### Fixed

- **The spec status vocabulary was decorative.** `spec-status.py` matched `Closed` as a **bare prefix**, so any subtype passed silently — which is how `Closed — Not Implemented` accumulated across five specs while `.writ/docs/spec-lifecycle.md` still instructed authors not to introduce a fourth prefix. Nothing compared the doc to the detector because nothing could. `CANONICAL_STATUS_HEADS` is now declared in code, `spec-status.py validate` reports any non-canonical head, and the new `spec-vocabulary` eval check asserts doc/script agreement. **Detection stays tolerant** — an off-vocabulary value is still complete-family, so enforcement never silently reclassifies an existing spec or strands it out of the archive.
- **`/release`'s post-merge archival hook was structurally blind to Writ's own commit convention.** It fed the resolver `messageHeadline` only, while Writ commits carry the spec path in the *body* (`Story N of .writ/specs/<id>`) — so it could match only when a branch name happened to contain the spec id. It had fired **exactly once** (`5a9a2d2`, PR #33) against 40+ archived specs; every other spec was swept by hand. The hook now feeds headline **and** body, verified on the case that exposed it.

### Added

- **`spec-status.py validate`** — reports every spec whose status head is off-vocabulary, scanning `archive/` as well, since an archived spec's status is the permanent record of *how* it ended and archived specs are most of the corpus. Never mutates; separates a missing header (a documented, intentional state) from actual drift.
- **`Closed — Not Implemented` as a canonical fourth value.** It carries what `Abandoned` does not: the decision was made *on evidence gathered after the spec was written* — a measured pilot, a changed premise, a subsuming spec — rather than the work lapsing.
- **`spec-vocabulary` eval check** with a **mutation proof**: an off-vocabulary value is injected into a disposable fixture and must be reported. A validator nothing has ever seen fail is decorative in exactly the way this release exists to fix, so a clean `ok: true` was not accepted as evidence on its own.

### Changed

- **Both layers now use the same words.** The phase-layer enum `closed_unimplemented` is renamed **`closed_not_implemented`** to match the spec-layer prose, which is the incumbent across five specs. Live surfaces only — the v0.30.0 changelog entry, the refresh log, the archived spec, and the source issue are historical records of what shipped and are left intact. `phase-execution-v2` stays at schema version 2; read-tolerance means a state file carrying the old value still reports.
- `.writ/docs/spec-lifecycle.md` documents the enforcement mechanism and the spec ↔ phase layer mapping, and no longer forbids the prefix five specs already used.

## [0.30.0] - 2026-08-12

**Closure by Decision** — Writ could record that work was *completed*, but not that it was deliberately *never built*. Both layers that needed the distinction got it: the spec archive ledger now carries terminal status, and `phase-execution-v2` gains a `closed_unimplemented` state written by a new `close-spec` reducer subcommand. The gap was found by `/refresh-command`, which rejected it as out of its own scope and filed it instead — the loop closing on itself. `/status` no longer reports a finished phase as five specs of work in flight.

### Added

- **`closed_unimplemented` and `close-spec`** — a terminal status for a spec a maintainer decided against, distinct from `failed`/`quarantined` (nothing failed) and `skipped_blocked` (nothing blocked it). `close-spec --reason` is mandatory because the phase report is obliged to print it; the reason is validated before the state file is read and before any git call, so a refused closure leaves the file byte-identical. Mid-run closure frees the lane worktree but **retains** the lane branch under `writ/phase/…` — `writ/quarantine/…` asserts a failure that did not happen.
- **`phase-closure` eval check** — `scripts/eval-phase-closure.py`, 39 disposable-repository scenarios plus 10 static contract assertions. Its bypass detector walks the AST rather than grepping: a line-based check found 5 of 8 status-mutation sites and missed every `record.update({"status": …})` form.
- **Terminal status on the archive ledger line** — a closed spec's ledger entry records *how* it ended, not just that it did. All 13 Phase 10 specs swept, roadmap glyphs normalized.
- **`safe-refactor-loop`'s checkpoint is now executable.** It previously said "note the current clean git state so a revert is one step" — an assumption, not an instruction. It now captures the commit as the revert target and asserts a clean tree at the top of *every* iteration. Step 4's red branch reverts to that target including files the change created; without it a reverted module split leaves untracked files behind and the next checkpoint stops on the loop's own leftovers.

### Changed

- **`SPEC_STATUSES` is load-bearing rather than documentary.** It was declared and referenced nowhere — no validation, no membership test — so adding a value to it would have changed zero behaviour. Every spec-status write now routes through one `_set_status` guard, and `cmd_progress` seeds its counts from the same set so the two cannot drift again. Validation is on **write** only: a status written by a newer reducer must still report, never crash, or the schema's forward-compatibility promise breaks.
- **`blockedBy` now means "upstream reached a terminal status without delivering"** — a quarantine *or* a closure — because closure cascades through `skipped_blocked`. Left implicit this would mislead, so `progress` reports the cause per blocked spec and both the schema doc and `/status` require naming it. The cascade skips dependents already in a terminal status; quarantine cascades unconditionally, but closure must not, or closing a spec would flip an `integrated` dependent and discard its merge commit.
- **`/implement-phase` exit criterion 1 admits `closed_unimplemented`,** and its completion report carries a **mandatory** "Closed by decision" section. A phase may report `COMPLETE` with closed specs only because that section names what was dropped and why; omitting it would make the verdict a false claim of delivered scope.
- **`/implement-phase` refreshed with three amendments evidenced by two live runs** — phase branches must not be named `writ/phase/{id}` (every `create-lane` fails on a git ref D/F conflict against the lane namespace); a lane brief seeds context and never new scope (one run's out-of-scope brief edit silently invalidated a UAT plan already generated for an earlier spec); and a truncated subagent report is indistinguishable from a completed one unless checked — four of five reports were dropped in a single run.

### Fixed

- **`challenge_required` was written by the reducer but absent from both the status vocabulary and the progress counts.** It had been uncounted since the status was introduced; enforcement would have started rejecting a write the reducer already performed.
- **The live Phase 10b state reported five closed specs as `pending`.** `progress` now reports `pending: 0, closed_unimplemented: 5, integrated: 2`, each closure carrying the measured evidence that closed it, with `reconcile` consistent and no `Attention` attributable to the closures.

## [0.29.0] - 2026-08-12

**Component Contract, Bounded Loops & a Governor That Bites** — every command and agent now declares the problem it addresses, the outcome it produces, and machine-checkable exit criteria; every loop declares a bound calibrated against a recorded run; and the contract checks are enforced as blocking findings rather than advisory warnings. Phase 10's token half was measured, found to be largely an artefact of the wrong metric, and stopped after one conversion — the evidence is recorded rather than the goal restated.

### Added

- **Component contract (ADR-020)** — `problem:` / `outcome:` / `exit_criteria:` in all 31 commands' frontmatter and all 7 agents' config blocks; `## Completion` in all 31 commands (was 13). 94 criteria, authored against a swap test and a restatement test rather than templated. `.writ/docs/component-contract.md` documents the schema; `/new-command` now mandates it.
- **Loop bounds** — `loop.max_iterations` + `on_exhaustion` on the five loop-bearing commands (was 0 of 5), each citing the run it was calibrated against *with its evidence quality stated in-file*. `scripts/eval-loop-bounds.py` enforces correctness across 38 scenarios and cross-reads `phase-state.py`'s `attempts < 2` guard, so a declaration cannot drift from the code it transcribes.
- **Autonomy gate classes (ADR-022)** — five-row gate-class table plus a two-condition reversibility precondition in `commands/_preamble.md`.
- **`scripts/measure-invocation.py`** — per-invocation load measurement. Reports floor (base + command + eagerly declared skills) and ceiling (plus inline-read skills) separately, flags hoisted reads, and labels tokens an estimate rather than a measurement. Writ ships no tokenizer, so the ratio is recorded and overridable rather than asserted.
- **Governor enforcement** — four contract checks flipped to blocking `structural`, proven by mutation. An absolute per-invocation byte budget ships measured and non-blocking, naming every over-budget command. `MAX_SKILLS` re-derived 12 → 45. `contract_compliance`, `required_skills_declarations` and `inline_skill_reads` now reach the eval report.
- **Eight extracted skills** from `commands/implement-story.md`, loaded by inline `Read` at the point of need.
- **`/refactor` dirty-tree guard** — `Step 1.1b` HALTs before any mutation, mirroring `/revert`'s discipline, with a `--dry-run` exemption and a `git ls-files --error-unmatch` rule so an untracked `--dead-code` target is reported rather than deleted.

### Changed

- **`commands/implement-story.md` 52,709 → 24,837 bytes** (989 → 340 lines) with zero behavioural drift, verified across a 281-row inventory with 75 literals machine-checked.
- **`check_length`'s command limit 2000 → 400, and non-binding.** Bytes-per-line varies 2.6x across commands, so a line cap selects the wrong files — it misses `implement-phase`, the densest file in the repo.
- **The command byte budget is pinned by decision, not derived.** As a live derivation it had a perverse incentive: growing `system-instructions.md` — the most expensive surface, paid on every invocation — would have *raised* every command's allowance. `BASE_BYTE_CAP` now governs the base directly and tighter.

### Fixed

- **The leanness `justification` field silenced a whole surface at any magnitude, forever.** Read once per surface outside the metric loop, it skipped both `lines` and `chars` on every future run, while the warning's own remediation told you to write one and then run the command that erases it. Justifications are now per-metric and bound to a recorded ceiling.
- **ADR-020's premise was false.** `new-command.md` never mandated `## Completion`; it was an emergent convention in 13 files. Amended — the contract was *missing*, not unenforced.
- **`required_skills:` adoption reversed.** Its 2026-08-03 review resolved *revisit → adopt* on one named future consumer, which then evaluated the mechanism and did not adopt it: the field is an eager pre-load, so extraction under it moves bytes into the floor every invocation pays. Corrected in `system-instructions.md`, all three adapters and `.writ/docs/skills.md`; review trigger restored to 2026-11-11.
- Stale root-contract claims retired — the false *"commands have no frontmatter (verified 0/31 files)"* (32/32 carry it), `model_tier` negative ordinal offsets deprecated, `.writ/manifest.yaml` reconciled to 0.28.0, `.writ/product/decisions.md` deprecated with its "Override Priority: Highest" precedence claim removed.

### Measured, and not what was assumed

- **The token alarm was largely a measurement artefact.** `commands/` measured 560,772 chars — a directory no invocation loads. The worst *real* invocation is 77,669 bytes (~19.4k tokens), 7.2x smaller, and 24,960 of it is a shared base no restructuring reduces.
- **Progressive disclosure costs ~1,017 bytes of overhead per extracted skill.** The pilot removed 27,872 bytes from a command and added 36,005 as 8 skills. Floor fell 35.9%; the worst path rose 9.7%. **Five sibling specs were closed unimplemented on this evidence**, contracts kept intact as the design record.
- **Loading is genuinely lazy** — verified by a live `/implement-story` run. Eight applicable skills read at their own step; the inapplicable one never opened. The caveat stands: laziness is a convention the command states, not a mechanism that enforces it.
- **`per_surface.commands.chars` did not drop.** Phase 10's headline token criterion is unmet, and Phase 10 closes `PARTIALLY COMPLETE`.

## [0.28.0] - 2026-08-10

**Full Install Fanout & Post-Merge Archival** — installed projects now receive the complete Writ runtime surface (all command-invoked scripts and upstream reference docs) on install and update, not just `recommend-state.py`. `/release` can also auto-archive a spec immediately after its PR merges, when the resolver finds an unambiguous match.

### Added

- **Full runtime fanout on install/update** — `install.sh`, `update.sh`, `unlink.sh`, and `/update-writ` three-way overlay all shippable runtime scripts (`story-context.py`, `spec-deps.py`, `phase-state.py`, `lint-skill.sh`, `gen-skill.sh`, and 10 others) plus upstream `.writ/docs/*.md` reference docs; lifecycle installers, eval tooling, and internal modules are excluded ([PR #34](https://github.com/sellke/writ/pull/34))
- **Post-merge archival hook** — `/release` Step 1.3c resolves the merged PR's spec via `scripts/resolve-spec-reference.py` and calls `scripts/archive-sweep.py archive-one` when unambiguous; silent no-op on miss or ambiguity ([spec: 2026-08-04-post-merge-archival-hook](.writ/specs/archive/2026-08-04-post-merge-archival-hook/spec.md))
- **`scripts/resolve-spec-reference.py`** — shared branch+commit resolver for `/ship` Spec Reference and `/release` archival hook ([Story 1](.writ/specs/archive/2026-08-04-post-merge-archival-hook/user-stories/story-1-shared-spec-reference-resolution.md))
- **`archive-sweep.py archive-one`** — single-spec archive entry point with complete-family, collision, and ledger checks ([Story 2](.writ/specs/archive/2026-08-04-post-merge-archival-hook/user-stories/story-2-single-spec-archive-entry-point.md))

### Changed

- Lifecycle scripts use shared `overlay_scan_flat_dir` with `is_shippable_script` exclusion filter instead of hardcoded `recommend-state.py` + one doc paths

### Internal

- Archived completed specs: `2026-08-04-post-merge-archival-hook`, `2026-08-04-spec-lifecycle-archival`
- Eval coverage for post-merge archival hook, spec-reference resolver, and archive-one CLI boundary

## [0.27.0] - 2026-08-04

**Status-Alone Archive Eligibility** — amends the archive lifecycle shipped in 0.26.0: eligibility no longer requires a knowledge-evidence citation alongside a complete-family status. In practice the two-signal bar left 36 of 39 completed specs stranded in the active directory, defeating the point of the archival feature. Knowledge evidence is still recorded per-spec in the ledger, but as enrichment, not a gate.

### Changed

- **Archive eligibility is status-alone** — `scripts/archive-sweep.py` now archives any complete-family spec (`Complete`, `Completed ✅`, `Closed — Abandoned`, `Closed — Cancelled`) regardless of knowledge-evidence citations; the ledger records `"no knowledge evidence yet"` instead of skipping the spec ([Story 2 amendment](.writ/specs/2026-08-04-spec-lifecycle-archival/user-stories/story-2-archive-sweep-mechanism.md)).

### Fixed

- Three eval checks (`autonomy-governance`, `recommended-spec-implementation`, `supersession-writeback`) hardcoded active paths for governance-critical specs and reported 14 false-positive findings once the wider re-sweep archived those specs. Added `resolve_spec_path()` to `scripts/eval.sh` so checks that assert content inside a specific spec look in both `.writ/specs/` and `.writ/specs/archive/`.

### Internal

- Re-ran the archive sweep under the amended rule: 36 additional complete-family specs moved to `.writ/specs/archive/<name>/` via `git mv`, `LEDGER.md` gained 36 entries ([Story 6 second run](.writ/specs/2026-08-04-spec-lifecycle-archival/user-stories/story-6-dogfood-sweep.md)).
- Documents `scripts/publish-writ-runtime.sh` in `commands/release.md` — swaps in a minimal `scripts/writ-runtime-readme.md` for `npm publish` only, since npm always bundles the root `README.md` regardless of the `files` array.
- Removed 13 stale issue files under `.writ/issues/` resolved by prior work.

## [0.26.0] - 2026-08-04

**Spec Lifecycle & Archival** — fixes a spec-status detection bug that silently misclassified 27 of 39 real specs (bold `**Status:**` headers never matched the old literal `grep -q "Status: Complete"`), then builds an evidence-gated archive lifecycle on top of the fix: specs that are both Complete and cited by `.writ/knowledge/` evidence move to `.writ/specs/archive/<name>/` via `git mv`, excluded from every existing command's scan by glob depth alone — no command-suite changes required. Dogfooded against this repo's own 40-spec corpus.

### Added

- **Format-tolerant spec-status detection** — `scripts/spec-status.py` recognizes bold and unbold `Status:` headers and all complete-family values (`Complete`, `Completed ✅`, `Closed — Abandoned`), with a conservative not-complete default for missing headers ([Story 1](.writ/specs/2026-08-04-spec-lifecycle-archival/user-stories/story-1-status-detection-fix.md)).
- **Evidence-gated archive sweep** — new `/status --archive` flag (`scripts/archive-sweep.py`) moves specs that are both Complete and cited by `.writ/knowledge/` `related_artifacts` to `.writ/specs/archive/<name>/`, with a committed `LEDGER.md` audit trail and idempotent re-runs ([Story 2](.writ/specs/2026-08-04-spec-lifecycle-archival/user-stories/story-2-archive-sweep-mechanism.md)).
- **Spec lifecycle documentation** — `.writ/docs/spec-lifecycle.md` records the status vocabulary, archive convention, and the single-level-glob-depth invariant that makes archival "free" for the rest of the command suite ([Story 3](.writ/specs/2026-08-04-spec-lifecycle-archival/user-stories/story-3-lifecycle-documentation.md)).
- **`.cursorindexingignore` scaffolding** — `install.sh` seeds `.writ/specs/archive/**` exclusion at the project root, install-once, across all platforms ([Story 4](.writ/specs/2026-08-04-spec-lifecycle-archival/user-stories/story-4-cursorindexingignore-scaffolding.md)).
- **Supersession banner convention** — `Amends:`/`Extends:` declarations now write back a `Superseded by:` reverse pointer via `scripts/supersession-writeback.py`, wired into `/create-spec` and `/edit-spec` ([Story 5](.writ/specs/2026-08-04-spec-lifecycle-archival/user-stories/story-5-supersession-banner-convention.md)).

### Fixed

- `implement-spec.md`'s spec-selection listing didn't require `spec.md` presence, which could have surfaced the newly-real `archive/` folder as a bogus selectable spec — caught during the real dogfood run against this repo's own corpus ([Story 6](.writ/specs/2026-08-04-spec-lifecycle-archival/user-stories/story-6-dogfood-sweep.md)).
- `spec.md`'s own status header was stuck at "Not Started" despite all 6 stories being complete — caught by a post-implementation `/verify-spec` pass.

### Internal

- Dogfooded the archive sweep against this repo's real 40-spec corpus: 3 specs archived (`2026-03-27-context-engine`, `2026-04-24-phase4-production-grade-substrate`, `2026-07-18-artifact-integrity-handshake`).
- README documents the context assembler, cuts posturing taglines.

## [0.25.0] - 2026-08-04

**Deterministic Story Substrate** — moves Writ's two highest-consequence agent-interpreted pipeline steps to program: the story-dependency graph is now validated by a blocking pre-execution gate before `/implement-spec` computes parallel worktree batches, and context-hint resolution collapses from three drifting implementations (docs prose, orchestrator prose, a measurement-only function) into one deterministic, budget-enforced assembler.

### Added

- **Story graph validator** — `scripts/story-deps.py` blocks `/implement-spec` before batch computation on any of five invalid-graph classes (cycle, self-reference, missing/duplicate reference, malformed header), naming the affected story and exact diagnostic; `recommend-state.py`'s duplicate DFS implementation retired in favor of the shared module ([Story 1](.writ/specs/2026-08-03-deterministic-story-substrate/user-stories/story-1-story-graph-validator.md)).
- **Deterministic context assembler** — `scripts/story-context.py` resolves `## Context for Agents` hints (bracketed and extended reference forms) into a structured JSON payload with per-category byte counts; every failure mode degrades toward `spec-lite.md` rather than raising ([Story 2](.writ/specs/2026-08-03-deterministic-story-substrate/user-stories/story-2-context-assembler.md)).
- **Empirically derived `fetched_context` budget** — 21,000 bytes, set at 2x the measured max across all 170 stories in the corpus (compensating for a known heading-mismatch undercount); over-budget content truncates by relevance, warns, never blocks ([Story 3](.writ/specs/2026-08-03-deterministic-story-substrate/user-stories/story-3-derived-context-budget.md)).
- **Command discoverability** — every command in `commands/` now carries `name`/`description` YAML frontmatter, matching the convention skills already use.

### Changed

- `/implement-story` Step 2's ~50-line prose context-hint parser is replaced by a single assembler invocation; `.writ/docs/context-hint-format.md` now points at the script as the executable contract instead of restating the algorithm ([Story 4](.writ/specs/2026-08-03-deterministic-story-substrate/user-stories/story-4-prose-consolidation.md)).
- `tdd-cycle` skill promoted `candidate` → `proven` (3 cited consumers, crossing ADR-014's threshold); lifecycle evidence refreshed on 4 other candidate skills.
- `CLAUDE.md` architecture section condensed; documents the `agents/` (docs) vs `claude-code/agents/` (loadable definitions) split.

### Fixed

- Path-traversal vulnerability in the context assembler's extended-reference file resolution — caught and fixed during Story 2's own review cycle before ever shipping.
- `claude-code/agents/writ-tester.md` model pinned to `sonnet` (was drifting on `inherit`).
- Two malformed `Dependencies:` headers (prose `none` instead of the required bracket `[]`) caught by this release's spec-validation gate — `2026-08-03-deterministic-story-substrate` and the previously-shipped `2026-07-26-leanness-instrumentation`.

### Internal

- `scripts/` surface grew ~3,176 lines, justified in `.writ/leanness-baseline.json` (Business Rule 8 — moving hint-budget logic from unmeasured prose into measured, tested code); `commands/`/`skills/` growth from the frontmatter/lifecycle batch justified and reseeded.
- Two comparative research analyses added (`writ-vs-code-captain`, `writ-vs-openspec`); one improvement issue filed (structured ceremony-skip marker) and deliberately scoped out of this release.

## [0.24.0] - 2026-07-26

**Full-Surface Leanness Measurement & Coverage Guard** — closes the blind spot that let `scripts/`, the largest surface in the framework, go entirely unmeasured by the Tier A leanness tripwire (32% actual product coverage behind an appearance of full coverage). Rewrites the measurement registry to cover the entire product surface, adds a hard-FAIL coverage guard against future blind spots, introduces a static `story_context_bytes` proxy metric, and replaces percentage growth tolerance with a per-surface reduction ratchet.

### Added

- **Full-surface measurement** — registry-driven `compute_metrics()` now measures `commands/`, `agents/`, `skills/`, `adapters/`, `scripts/`, and `system-instructions.md` (previously commands-only); new `per_surface`, `total_product_lines`/`total_product_chars`, and `writ_workspace_lines` metrics, with legacy keys retained for zero-break Tier B continuity ([Story 1](.writ/specs/2026-07-26-leanness-instrumentation/user-stories/story-1-full-surface-measurement.md)).
- **Coverage guard** — `check_coverage()` hard-FAILs on any top-level repo entry that is neither in the registry nor explicitly declared out of scope, closing the exact blind spot that let `scripts/` go unmeasured across two prior audit cycles ([Story 2](.writ/specs/2026-07-26-leanness-instrumentation/user-stories/story-2-coverage-guard.md)).
- **`story_context_bytes`** — a static, deterministic proxy metric for what `implement-story` declares it loads for a full-pipeline story, explicitly labeled as declared load, never consumed tokens ([Story 3](.writ/specs/2026-07-26-leanness-instrumentation/user-stories/story-3-story-context-bytes.md)).
- **Reduction ratchet** — replaces the old percentage growth tolerance: per-surface baseline comparison where decreases are silent, justified increases are silent (via a `justification` field), and unjustified increases warn ([Story 4](.writ/specs/2026-07-26-leanness-instrumentation/user-stories/story-4-reduction-ratchet.md), [ADR-019](.writ/decision-records/adr-019-full-surface-leanness-measurement.md)).

### Fixed

- Coverage guard no longer flags `eval.sh`'s own `--report=` output file as an unmeasured surface — caught by CI on the PR's first real run and fixed before merge.

### Internal

- `scripts/tests/test_eval_leanness.sh`: 5 → 32 assertions.
- `.writ/leanness-baseline.json` migrated to schema 2 (per-surface `lines`/`chars` + `justification`); trend line deliberately reset.
- `.writ/docs/leanness-audit-format.md` updated for the new metric set ([Story 5](.writ/specs/2026-07-26-leanness-instrumentation/user-stories/story-5-adr-and-tier-b.md)).

Zero user-facing surface: dogfooding-only, no `commands/*.md` changes.

## [0.23.0] - 2026-07-19

**Git-Native Provenance & Recovery (Phase 9)** — makes git Writ's durable audit and recovery substrate, and hardens command robustness: a `refs/notes/writ` audit channel, logical-unit `/revert`, and an Artifact Integrity handshake without a new `.writ/index.md`.

### Added

- **Git-notes audit channel** — `/ship` attaches a spec/phase audit digest to the landed base-branch commit under `refs/notes/writ`; `/release` attaches a version rollup; install/update configure fetch/push refspecs; default-on with clean `writ.auditNotes=false` opt-out; `/status` surfaces the latest note ([ADR-017](.writ/decision-records/adr-017-git-notes-audit-channel.md), [format](.writ/docs/git-notes-audit-format.md)).
- **`/revert`** — logical-unit revert (story|spec) via layered commit resolver (`scripts/revert-resolve.py`: recorded SHA → `/ship` `Ref:` footer → phase-state → confirmed ghost-commit match), safe `git revert` by default, and Writ artifact restoration (status, WWB, drift log, `context.md`).
- **Artifact Integrity handshake** — standing rule in `commands/_preamble.md` (required → HALT + bounded repair; optional → warn+degrade); `## Artifact Map` in regenerated `.writ/context.md`; Required Artifacts blocks on seven high-traffic commands; eval index-guard against `.writ/index.md`.

### Internal

- Eval Tier 1: `git-notes-audit` (26/26), `revert` (23/23), `artifact-integrity` (19/19); full suite green at land.
- Reserved [ADR-018](.writ/decision-records/adr-018-third-party-skill-trust-model.md) (third-party skill trust) — documented, not activated this release.

## [0.22.0] - 2026-07-18

**Model-Tier Delegation** — a portable `model_tier` convention where agents carry an enforceable tier (`orchestration` | `capability`), resolved per-platform via native relative primitives, while skills and commands carry advisory-only tier metadata. Corrects the originating issue's skill-carrier framing: the tier lives at the agent spawn boundary, the only place Writ passes a `model` parameter. Ships with zero behavioral regression — every agent resolves to the same concrete model it runs today.

### Added

- **`model_tier` convention** — two named tiers (`orchestration` → anchor/`inherit`, `capability` → floor/`fast`), documented in `system-instructions.md` and its byte-identical `cursor/writ.mdc` mirror: enforcement boundary (agents enforced; commands/skills advisory only), carrier-per-file-type, schema, graceful degradation, and a reserved ordinal-offset form for a future finer-grained resolver ([ADR-016](.writ/decision-records/adr-016-model-tier-delegation.md)).
- **Agent adoption** — all 7 agents (`agents/*.md` + `.writ/manifest.yaml`) declare an explicit `model_tier`, mapped from today's `model:` settings with no change to the resolved concrete model.
- **Adapter resolution tables** — `adapters/cursor.md`, `adapters/codex.md`, `adapters/openclaw.md`, and `adapters/claude-code.md` each document a tier → native-resolution table and a warn-and-fall-back graceful-degradation rule.
- **Authoring + lint integration** — `/new-skill` scaffolds an advisory `model_tier:` frontmatter field; `/new-command` documents an advisory `model_tier` prose note (commands have no frontmatter mechanism); `scripts/lint-skill.sh` validates tier values in both shapes.
- **`.writ/docs/model-tiers.md`** — canonical user-facing explainer, referenced from `README.md` and `AGENTS.md`.

## [0.21.1] - 2026-07-18

**Housekeeping** — README and `/status` reconciled with shipped reality; the workspace ledger swept clean.

### Fixed

- **`/status` command allowlist reconciled** — added `/new-skill`, `/create-uat-plan`, and `/knowledge` to both allowlist locations, so `/status` can suggest every command that actually exists in `commands/*.md`.

### Changed

- **README brought current with v0.21.0 state** — all six live skills cataloged with descriptions, the two-command `--recommend` policy summarized with per-command annotations ([ADR-013](.writ/decision-records/adr-013-recommended-autonomous-delivery.md)), native-memory interop noted, the OpenClaw adapter added to Platform Support, the command count corrected to 30, and `uat-plan.md` / `recommendation-log.md` shown in the spec-package tree.

### Internal

- Workspace ledger reconciled: 9 stale spec headers set to terminal states with commit-level evidence (`infrastructure-command-refinement` closed as Abandoned — its targets left the suite), all 7 stale issues triaged (5 closed with evidence and deleted, 1 parked to the roadmap parking lot, 1 kept open), completed execution state purged from `.writ/state/`, and `.writ/context.md` regenerated.

## [0.21.0] - 2026-07-17

**Recommend Redistribution** — `--recommend` moves to the right seams. Experience showed a single command carrying one spec all the way through a production-approval boundary was the wrong first cut; per [ADR-013 (revised 2026-07-17)](.writ/decision-records/adr-013-recommended-autonomous-delivery.md), evidence-backed autonomy now lives on exactly two commands, and neither merges, opens PRs, nor releases — production stays a human decision.

### Added

- **`/implement-phase --recommend`** — the sole end-to-end autonomous loop: auto-authors missing specs (via `/create-spec --recommend`), auto-accepts its decomposition and execution-plan confirmations, and runs `/implement-spec` per spec through the existing isolated-lane flow. Terminal scope unchanged: honest completion report with manual UAT handoff.

### Changed

- **`/create-spec --recommend` authors and stops.** It autonomously runs contract-first discovery, auto-adopts the evidence-backed contract lock, story decomposition, sub-spec set, and visual-reference default — recording each material decision in `recommendation-log.md` — then delivers the locked, validated package without implementing.
- **`/implement-spec` is a plain execute command** — no confirmation gate, no flag. Invoking it runs the plan.
- **ADR-013 rewritten as a single coherent decision** — the current two-command policy stated directly, with the original single-spec shape recorded under Rejected Alternatives and Revision History. Policy (`system-instructions.md`, `cursor/writ.mdc`, `commands/_preamble.md`), product (mission, mission-lite, roadmap), and adapter surfaces reconciled to match.

### Removed

- **`--recommend` from `/implement-spec`, `/ship`, and `/create-uat-plan`.** The autonomous staging → production-approval flow is deferred ("bigger loops later"); its machinery (`scripts/recommend-state.py`, `.writ/docs/recommended-delivery-state-format.md`) is kept dormant as the preserved design — still eval-guarded, not deleted.

### Internal

- **Eval falsifiability gate reconciled in the same change:** `autonomy-governance` repointed to the revised policy literals with regression forbids; `recommended-spec-implementation` static assertions reconciled to the two-command model (162/162 scenarios, 16/16 static); `recommended-staging` redirected to guard only the dormant machinery plus an adapter merge-forbid (60/60 scenarios). Full suite green — 0 findings.
- `commands/_preamble.md` trimmed to 79 lines (within the 80-line eval limit).

## [0.20.1] - 2026-07-11

Internal eval robustness patch. Hardens the `recommended-spec-implementation` check against a pathological subprocess-spawn cost that read as a hang under x86_64 Python via Rosetta, and clears a Python 3.13+ deprecation warning. No user-facing feature or command changes.

### Fixed

- **Eval Python 3.13+ compatibility.** `scripts/eval-refresh-evidence.py` passes `maxsplit` to `re.split` by keyword, clearing a `DeprecationWarning` surfaced under native arm64 Python 3.14.

### Internal

- **Eval fixture-template reuse.** The `recommended-spec-implementation` check builds its git fixture repo once and `copytree`s it per fixture across both Python phases (`scripts/eval.sh`, `scripts/eval-recommend-state-adversarial.py`), cutting fixture-setup subprocess spawns (`git init` 40→3, `git config` 80→6) with all 36/36 static assertions still passing. Root cause traced to aggregate cross-arch spawn cost, not git or the helper — see [the improvement issue](.writ/issues/improvements/2026-07-11-eval-recommended-spec-spawn-heaviness.md).
- **Eval progress heartbeats.** The check emits stderr progress markers (fixture-template build, sandbox source build, per-platform install/update/unlink, adversarial suite) so a slow run is visibly progressing rather than looking hung.

## [0.20.0] - 2026-07-11

**Phase 8 (Memory Interop)** completes the 2026 harness-audit roadmap — Writ's markdown stays canonical while external memory layers become documented, optional indexes. Ships alongside two self-governance features: **Leanness Guardian** (the framework audits its own weight) and **Product Reconciliation** (verify/revise the product layer, closing the gap that only specs previously had).

### Added

- **Memory Interop — GBrain compatibility.** A new `gbrain-interop` skill plus `.writ/docs/gbrain-recipe.md` let a GBrain-equipped project register `.writ/` as a source (markdown-canonical routing, artifact→page mapping, graceful absence when no brain is installed) — grounded in GBrain's real interface, zero new Writ infrastructure.
- **Native-memory guidance per adapter.** All four adapters (Cursor, Claude Code, Codex, OpenClaw) document what belongs in native memory (session prefs, trivia) vs. the reviewable ledger (negotiated decisions, conventions, lessons), backed by a `memory-interop` eval check.
- **Leanness Guardian.** A Tier A eval tripwire (aggregate-weight + registry-parity) and a Tier B audit ritual let Writ govern its own growth, per [ADR-015](.writ/decision-records/adr-015-leanness-self-governance.md).
- **Product Reconciliation.** `/verify-spec --product` (a P1–P4 consistency lint over `.writ/product/`), `/plan-product --reconcile` (a targeted revision posture), and a read-only `/retro` product-drift nudge — the product-layer equivalent of spec verify/revise.

### Changed

- **Product docs reconciled with reality.** Mission, roadmap, and context realigned; Phase 8 marked implemented across all product docs (first dogfood output of `/plan-product --reconcile`).

### Internal

- **Two Tier 1 eval checks added** — `memory-interop` and `leanness` — both green on CI.

## [0.19.0] - 2026-07-11

Two phases ship together: **Phase 6 (Autonomy Ceiling)** — supervised multi-spec execution replacing the Ralph loop — and **Phase 7 (Compounding Layer)** — making Writ's self-improvement falsifiable and its skills primitive adopted.

### Added

- **Skill lifecycle.** Every skill carries a lifecycle state — `candidate` → `proven` → `promoted` — with supporting evidence in frontmatter. The boundary lint and `eval.sh` enforce that a skill's claimed maturity matches its recorded evidence, and the generated catalog renders lifecycle at a glance. See [ADR-014](.writ/decision-records/adr-014-skill-lifecycle.md).
- **Four skills extracted from commands.** `tdd-cycle` (from `/implement-story`'s coding phase), `error-rescue-mapping` (from `/create-spec`), `safe-refactor-loop`, and `code-explanation` are now first-class reusable capabilities instead of logic locked inside a single command — all lint-clean per `scripts/lint-skill.sh`.
- **`/knowledge --consolidate`.** A new mode that merges duplicate knowledge entries, surfaces contradictions for human resolution, and prunes stale ones — non-destructively, with a reviewable diff. Backed by a consolidation reducer, a registered eval check, and a `/retro` nudge to run it.

### Changed

- **Supervised multi-spec execution replaces the loop.** Use `/implement-phase` for multi-spec work: it sequences specs by authoritative cross-spec `Dependencies`, runs each spec in a fresh isolated execution lane (branch + worktree), quarantines terminal failures while independent specs continue, reconciles state read-only on resume, and reports categorical production health. Bounded single-spec autonomy remains separately supported via `/implement-spec --recommend <one-spec>`; multi-spec `/implement-phase --recommend` stays excluded per [ADR-013](.writ/decision-records/adr-013-recommended-autonomous-delivery.md).
- **`/implement-phase` gains a decomposition pre-pass.** When a roadmap phase has unspecced features, the command can propose a spec breakdown — dependency graph, single-writer file ownership, and named seams — for one planning confirmation, then seed `/create-spec` per spec. The phase→specs boundary becomes an explicit, contract-first artifact bound to the current codebase instead of tacit judgment made once at the first `/create-spec`.
- **`/refresh-command` is evidence-bound.** Command refinements now require a cited transcript signal (source transcript, observable signal, affected section). A fixture-driven `refresh-evidence` eval check and a pre-merge acceptance gate keep the refresh log honest; entries dated before `LEARNING_CONTRACT_SINCE = 2026-07-11` are grandfathered.

### Removed

- **Ralph, the autonomous CLI loop, is retired.** The `/ralph` command, `ralph.sh` loop, `PROMPT_build.md` prompt template, and CLI-pipeline/state-format docs are archived under `archive/ralph/` (preserved, not deleted) and removed from command discovery, the generated `SKILL.md` catalog, `.writ/manifest.yaml`, `.writ/docs/config-format.md`, all platform adapters, the README, and `/status` suggestions. See [ADR-012](.writ/decision-records/adr-012-ralph-deprecation.md).
- **`/explain-code` is retired into the `code-explanation` skill.** The capability is preserved as a reusable skill; the standalone command is removed from discovery and the catalog.

### Migration

- **This release does not migrate Ralph state.** There is no compatibility reader for `ralph-*.json`. **Finish or abandon any in-flight `ralph-*.json` run before upgrading**, then drive remaining multi-spec work with `/implement-phase`. The deliberate trade-off is the loss of opaque unbounded execution in exchange for isolation, resumability, and honest evidence.

## [0.18.1] - 2026-05-08

### Fixed

- **Startup update check false positives.** Writ now only recommends `/update-writ` after a copied installation proves upstream is strictly newer than the installed identity, preventing successful upstream reachability checks from triggering unnecessary update prompts.

### Internal

- **Issue backlog captured.** Added tracked issue records for the update-check false positive, spec branch preflight, and Writ business-process pipeline follow-ups.

## [0.18.0] - 2026-05-06

### Added

- **Codex CLI adapter support.** Writ now installs natively for Codex CLI with `adapters/codex.md`, Codex TOML agent translations, `AGENTS.md` Writ-block integration, `.codex/config.toml` seeding, and self-dogfooding `.codex/agents` support.

- **Codex lifecycle script parity.** `install.sh`, `update.sh`, `unlink.sh`, and `uninstall.sh` now understand `--platform codex`, including AGENTS.md merge/removal safeguards, install-once config behavior, and Codex-specific agent parity tooling.

### Changed

- **Lifecycle commands and README now document Codex.** `/update-writ`, `/reinstall-writ`, `/uninstall-writ`, `/refresh-command`, and README platform guidance cover Codex paths, TOML agents, restart expectations, and `.agents/skills/` behavior.

### Internal

- **Codex adapter spec package completed.** Added the completed `.writ/specs/2026-05-06-codex-cli-adapter/` audit trail with smoke evidence, story completion records, and source issue writeback.

## [0.17.0] - 2026-05-04

### Added

- **Skills — the third Writ primitive.** Reusable capability files (`skills/<name>/SKILL.md`) sit alongside commands and agents; commands and agents `Read` skills at the moment they need a tool. Foundation includes manifest schema, root catalog auto-render via `scripts/gen-skill.sh`, install/update fanout with three-way overlay, and boundary lint (`scripts/lint-skill.sh`) enforcing the verb/noun/tool roles per [ADR-009](.writ/decision-records/adr-009-command-agent-skill-boundary.md). All Writ-authored skills set `disable-model-invocation: true` so platforms don't ambient-load them. (Stories 1–3, 7)

- **`/new-skill` command** — three-phase scaffolder (capture → lint → write). Coaches verb-phrase descriptions before writing, runs the boundary lint pre-write, appends manifest entry alphabetically. (Story 6)

- **`/refresh-command --lint-skills`** — lints all `skills/*/SKILL.md` against the ADR-009 boundary; never auto-rewrites skill bodies. New Phase 5 in the standard `/refresh-command` flow. (Story 6)

- **`required_skills:` frontmatter convention** — schema documented across `system-instructions.md`, `cursor/writ.mdc`, and all three platform adapters (`cursor.md`, `claude-code.md`, `openclaw.md`). Reserve-only this release; no agent or command declares it yet. Review trigger: 2026-08-03. (Stories 4, 5)

- **`conventional-commits` skill — first pilot extraction.** Authors Conventional Commits messages (type, scope, summary, body, footers) from a diff; matches the project's existing convention when one exists; covers common anti-patterns. Lint-clean per `scripts/lint-skill.sh`.

- **Documentation surface for skills** — new `.writ/docs/skills.md` (canonical user-facing explainer), README "Three Primitives" + "Skills" sections, AGENTS.md updates, `.writ/docs/self-dogfooding.md` Skills section. (Story 7)

### Changed

- **`/ship`, `/release`, and the coding agent defer commit-format guidance to the `conventional-commits` skill** instead of inlining duplicate format spec. Single source of truth for message grammar; the commands retain orchestration concerns (splitting heuristic, source-mapping table, parsing-direction notes). Coding-agent commits now match `/ship`'s downstream format.

- **Root catalog `SKILL.md`** auto-renders the new "Available Skills" section when the manifest's `skills:` list is non-empty.

- **README refreshed for the new primitive** — "Three Primitives" section reflects the shipped pilot, "Skills" table added (parallel to the Agents table), `/new-skill` row added to "Setup & Lifecycle", command count corrected (30 → 31).

### Internal

- **Self-dogfooding parity for skills** — `.cursor/skills` and `.claude/skills` symlink to repo-root `skills/`, matching the existing pattern for `commands/` and `agents/`. Edits to any skill propagate to all three platforms via symlink.

- **Spec workspace** — `.writ/specs/2026-05-03-skills-foundation/` ships as the audit trail (spec, spec-lite, technical spec, 7 user stories, verification report).

## [0.16.0] - 2026-04-28

### Added

- **Daily Writ update awareness** — startup instructions now define a quiet first-in-session update check that runs before auto-orientation or command workflows, uses a once-per-day `.writ/state/` cache, and points copied installations to `/update-writ` only when an upstream update appears available. ([Daily Story 1], [Daily Story 2], [Daily Story 3])

### Internal

- **Daily update check spec package** — added the completed spec, technical spec, verification checklist, source issue linkage, and What Was Built records for the startup update awareness work.

## [0.15.0] - 2026-04-28

### Added

- **Writ runtime timestamp helper** — added the tiny `@sellke/writ` npm package surface for deterministic `date`, `timestamp`, and compact timestamp output, plus release guidance for public scoped publishing. This is a runtime helper for command metadata and filenames, not a general Writ CLI.

### Changed

- **Date helper references** — active Writ command docs now reference `npx @sellke/writ date` with local system date fallback where package availability should not block work.

## [0.14.0] - 2026-04-26

### Added

- **Knowledge ledger** — `.writ/knowledge/` directory for cross-cutting institutional
  knowledge (decisions, conventions, glossary, lessons), with the `/knowledge` command
  for capture and agent context-loading hooks at task start. Substrate is plain-text
  markdown over a database — see ADR-005. ([Story 1])

- **Spec `owner:` field** — recognized in `spec.md` frontmatter; `/verify-spec` Check 8
  flags missing owners (warning for legacy specs, required for new specs). Supports the
  team-readiness trajectory in ADR-007. ([Story 2])

- **SKILL.md auto-generation** — `.writ/manifest.yaml` is the single source of truth
  for command and agent listings; `scripts/gen-skill.sh` regenerates `SKILL.md` from it
  and CI fails if it drifts (`--check`). ([Story 3])

- **Preamble standing instructions** — `commands/_preamble.md` houses Prime Directive
  recap, knowledge-loading hook, and references convention; every command and agent
  gained a `## References` footer pointing to it. ([Story 4])

- **Eval Tier 1 static checks** — `scripts/eval.sh` runs required-section validation,
  broken-reference detection, length sanity, and anti-sycophancy phrase scanning across
  `.writ/` artifacts. GitHub Actions workflow (`.github/workflows/eval.yml`) enforces
  the gate on every PR and push. ([Story 5])

### Changed

- **Mission reframed** — `mission.md`, `mission-lite.md`, and `roadmap.md` name "code
  and methodology that doesn't degrade as projects, teams, and AI platforms churn
  around them" as Writ's destination, with audience sequencing solo-now → team-forward.
  See ADR-006, ADR-007, ADR-008.

- **Adapter docs** — Cursor, Claude Code, and OpenClaw guides each gained sections
  covering knowledge loading and the preamble convention.

- **`/implement-story` and core agents** — `coding-agent`, `documentation-agent`, and
  `user-story-generator` integrate the knowledge-loading hook directly; all other
  agents and commands carry the `## References` footer.

- **README** — `/knowledge` added to the Planning & Specification table;
  `.writ/knowledge/` and `.writ/eval/` added to the directory tree.

### Internal

- **Decision records** — ADR-005 (knowledge substrate: markdown over database), ADR-006
  (non-degrading destination), ADR-007 (team audience sequencing), ADR-008
  (spec-as-team-contract moat).
- **Spec format doc** — `.writ/docs/spec-format.md` formalizes spec frontmatter
  including the new `owner:` field.
- **Research** — `2026-04-24-writ-vs-gstack-rigor-comparison.md` informs the strategic
  refresh.
- **Phase 4 spec package** — full spec, sub-specs, 5 user stories with relocated
  verification checklists, two verification reports, and a CHANGELOG capturing the
  post-ship contract update.
- **Organic-validation issues** — two issues track Story 1 (knowledge loading on next
  Phase 5 feature) and Story 5 (remote CI gate). Story 5 confirmed in real-time on
  PR #15 (both eval CI runs PASS, ~6-8s).

[Daily Story 1]: .writ/specs/2026-04-28-daily-writ-update-check/user-stories/story-1-startup-protocol.md
[Daily Story 2]: .writ/specs/2026-04-28-daily-writ-update-check/user-stories/story-2-cache-and-detection-contract.md
[Daily Story 3]: .writ/specs/2026-04-28-daily-writ-update-check/user-stories/story-3-verification-and-issue-linkage.md

[Story 1]: .writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-1-knowledge-ledger.md
[Story 2]: .writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-2-spec-owner-field.md
[Story 3]: .writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-3-skill-md-generation.md
[Story 4]: .writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-4-preamble-enforcement.md
[Story 5]: .writ/specs/2026-04-24-phase4-production-grade-substrate/user-stories/story-5-eval-tier-1.md

## [0.13.1] - 2026-04-08

### Added

- **Plan Mode workflow integrity constraint** — Fourth Hard Constraint in Prime Directive: "Never let Plan Mode absorb a command's workflow." Prevents AI platforms from treating planning conversations as deliverables instead of producing documented artifacts. Applied to both `system-instructions.md` and `cursor/writ.mdc`.

- **Per-command Completion sections** — All 9 planning commands (`/create-spec`, `/plan-product`, `/new-command`, `/create-issue`, `/create-adr`, `/create-uat-plan`, `/research`, `/design`, `/edit-spec`) now have `## Completion` sections with concrete artifact requirements, suggested next steps, and terminal constraints prohibiting implementation offers.

- **Adapter Command Workflow Integrity** — Each adapter (Cursor, Claude Code, OpenClaw) has a `## Command Workflow Integrity` section naming its platform-specific tendency and countermeasure. `/prototype` signposted as escape valve for users who want fast implementation.

## [0.13.0] - 2026-04-02

### Added

- **Writ lifecycle management commands** — `/update-writ` (interactive update with per-file customization control), `/reinstall-writ` (full removal + fresh install), `/uninstall-writ` (remove platform files, preserve `.writ/`). Supports Cursor and Claude Code platforms. Codex and OpenClaw deferred to future work.
- **`scripts/uninstall.sh`** — Non-interactive terminal counterpart to `/uninstall-writ` with `--dry-run`, `--no-commit`, `--platform`, and `--include-writ` flags.

### Changed

- **README platform support** — Removed OpenClaw (deferred to future work alongside Codex). Command count updated 27→29. "Setup & Utilities" section renamed to "Setup & Lifecycle" with new lifecycle commands.
- **`/status` command allowlist** — Added `update-writ`, `reinstall-writ`, `uninstall-writ`.

## [0.12.0] - 2026-04-01

### Added

- **Ralph review sub-agent (Phase 2.5)** — Read-only review sub-agent in the Ralph CLI pipeline between validate and commit. Verifies acceptance criteria (per-criterion VERIFIED/UNVERIFIED), code quality, security, and spec drift before marking a story complete. PASS/FAIL/PAUSE contract matching Cursor's Gate 3 review agent. Closes the primary quality parity gap between CLI autonomous execution and supervised `/implement-story`.

- **Review back pressure** — Max 2 fix-and-re-review iterations per story (3 total reviews). Separate from the test/lint fix loop cap (3). Large drift triggers quarantine branching (`ralph/quarantine/{storyKey}`) and escalation to developer via `/ralph status`.

- **Ralph state schema extensions** — `reviewResult` (unknown/passed/failed/paused), `acVerified` ("N/M" format), `quarantineBranch` fields. Iteration log enriched with review data. New escalation types: `drift`, `review`.

### Changed

- **`/ralph status` display** — Completed stories show AC verification count and drift level. Failed stories surface review-specific errors (`review-failed`, `large-drift`) with quarantine branch guidance.
- **Ralph pipeline diagram** — Updated from 4 phases to 5 phases across `commands/ralph.md`, `PROMPT_build.md`, `ralph-cli-pipeline.md`, and `README.md`.
- **Claude Code adapter** — Key differences section updated for review sub-agent, architecture check omission, and sub-agent spawning clarification.
- **Changelog trimmed** — Entries for 0.7.0–0.11.0 archived in GitHub releases.

## [0.6.1] - 2026-03-20

### Fixed

- **`/implement-story` context schema title** — `context.md` schema heading corrected from `# Writ Context` to `# Writ Project Context`, matching the authoritative definition in the technical spec. Eliminates title inconsistency that could cause schema validation or parsing failures.
- **`/implement-story` context regeneration note** — Step 3 preamble now accurately states that `.writ/context.md` is regenerated once at Story Completion (Step 4), not after each gate. The prior wording implied per-gate regeneration that no gate implementation actually performed.

## [0.6.0] - 2026-03-20

### Added

- **Config persistence layer** (`/initialize`, `/ship`, `/release`, `/status`) — `.writ/config.md` as a shared convention store; commands load from it first, fall back to detection, and offer to persist detected values. Eliminates repeated convention re-detection across sessions.
- **Agent iteration caps** (`coding-agent`, `testing-agent`, `/implement-story`) — `MAX_SELF_FIX_ITERATIONS = 3` hard limit; agents emit `STATUS: BLOCKED` after 3 attempts; orchestrator surfaces a repair decision (retry / skip / abort) instead of silently continuing.
- **Spec-lite integrity check** (`/verify-spec`) — Check 9 detects material divergence between `spec-lite.md` and `spec.md`; `--fix` flag (and default auto-fix mode) fully regenerates spec-lite from the authoritative spec.
- **`/status` North Star rewrite** — Reads `.writ/config.md` for instant orientation; surfaces in-flight batch jobs from execution state files; surfaces `/refresh-command --batch` opportunities when 3+ transcripts accumulate; removes all legacy phantom command references.
- **Prototype → spec escalation** (`/prototype`, `/create-spec`) — On scope escalation, `/prototype` actively offers `/create-spec --from-prototype`; the new `--from-prototype` mode reads the current git diff, pre-populates the discovery contract, and marks Story 1 complete.
- **ADR unification** (`/plan-product`, `/create-adr`) — `/plan-product` now outputs foundational decisions as numbered ADR files (ADR-000-series) in `.writ/decision-records/` instead of `decisions.md`; `/create-adr` documents both ADR families and when to use each.
- **`.writ/context.md` auto-loading** (`/implement-story`, `/implement-spec`, `/status`, coding/review/arch-check agents) — Auto-maintained context snapshot (product mission, active spec, recent drift, open issue count); fully regenerated at each gate transition and story completion; loaded as the first context item by all three implementation agents.
- **Issue → spec promotion pipeline** (`/create-issue`, `/create-spec`, `/status`) — `spec_ref` field in issue template; `/create-spec --from-issue [path]` pre-populates the discovery contract from issue fields and writes `spec_ref` back on completion; `/status` surfaces stale untriaged issues (7+ days, no spec_ref).
- **`/refresh-command --batch` mode** — Ingests last N transcripts (default 5, overridable via `--n`); detects friction patterns recurring across 2+ sessions; recurrence-weighted proposals include frequency strings ("Observed in N/M sessions"); `/status` auto-triggers the suggestion when 3+ new transcripts accumulate since the last logged refresh.

## [0.5.0] - 2026-03-19

### Changed

- **Pipeline streamlining** (`/verify-spec`, `/ship`, `/release`) — each command owns one job. `/verify-spec` is a metadata-only diagnostic (checks 1–5 and 8) with default auto-fix; `/ship` skips tests unless `/ship --test`; `/release` runs an inline gate (spec validation, build probes when configured, conditional full test suite via `gh` merge-commit vs `HEAD`) before changelog work. Added `/release --skip-gate`. README command summaries aligned.
- **Migration docs** — `SKILL.md` and `commands/migrate.md` updated for the new flow (no `--pre-deploy` / Trello).

## [0.4.4] - 2026-03-19

### Fixed

- `unlink.sh` crashing with `unbound variable` on bash 3.2 (macOS default) when `DIR_SYMLINKS` array is empty — `set -u` treats `"${arr[@]}"` on an empty array as unbound. Fixed all four array iterations to use the `${arr[@]+"${arr[@]}"}` safe expansion pattern.

## [0.4.3] - 2026-03-19

### Removed

- **Symlink install mode** — `install.sh --link` is no longer offered. Copy mode is the only installation method for external users. Linked installations posed risks around shared mutable state and non-portable `.cursor/` directories.
- Link mode update handler in `update.sh` — now errors with guidance to convert via `unlink.sh`
- README "Link mode (power users)" section and "Copy vs Link" callout

### Added

- `scripts/unlink.sh` — converts existing symlinked Writ installations to independent file copies with manifest rewrite, supporting both per-file and directory-level symlinks
- `/migrate` entry in README command table (was documented in migration section but missing from the table)

### Changed

- `install.sh` retains defensive symlink-removal when it detects an existing linked installation, ensuring a clean conversion to copy mode
- `update.sh` rejects linked installations with a clear error pointing to `unlink.sh`

## [0.4.2] - 2026-03-19

### Fixed

- `install.sh` and `update.sh` `overlay_scan` silently exiting on `set -e` when the last file alphabetically needed an update — `[ "$mode" = "apply" ] && cp ...` returns exit code 1 in preview mode, which became the function's return value and killed the script. Replaced all `[ ... ] && ...` conditionals with `if/fi` blocks. Affected copy-mode install and update on all platforms.

## [0.4.1] - 2026-03-18

### Added

- **README freshness check in `/release`** — new Step 1.3 cross-references `README.md` against the repo before each release, catching silent staleness in command tables, agent tables, pipeline diagrams, and install URLs. Structural drift detection only; semantic accuracy remains a human judgment call.

## [0.4.0] - 2026-03-18

### Changed

- **A-Grade Command Refinement** — 12 commands refined across 4 spec batches, applying the litmus test: every line must teach something non-obvious, set a quality bar, or prevent a specific mistake — or it gets cut. Templates become principles. Net reduction of ~2,700 lines, zero capability lost.
  - `assess-spec` and `edit-spec` — continued core refinement; compressed assessment tables, replaced edit-spec templates with principles (-633 lines)
  - `initialize`, `research`, `create-adr` — utility commands refined ~57%; cut duplicate next-steps blocks, replaced 86-line document template and 155-line ADR template with principles, converted auto-execute research to prerequisite gate
  - `create-issue`, `design`, `prototype` — secondary commands refined ~47%; cut Excalidraw JSON schema and component primitives, rewrote 80-line agent prompt to 25 lines of principles
  - `new-command`, `refactor`, `review`, `retro` — remaining commands refined ~47%; collapsed 5 mode-specific refactor workflows into one principle, cut JSON/markdown templates and bash pseudocode

### Removed

- Verbose templates in all 12 commands — replaced with concise principles the AI can generalize from
- Redundant "AI Implementation Prompt," "Best Practices," "Common Pitfalls," "Future Enhancements," and "Integration Notes" sections across all refined commands
- Hardcoded line-number references in `new-command` template selection logic (broke on any edit)
- Excalidraw JSON schema and component primitive definitions in `design` (the AI knows SVG primitives)
- Dialog mockups and bash pseudocode that restated CLI behavior the AI already knows

### Added

- Refinement specs for 4 command groups: utility, secondary, remaining, infrastructure (Specs: `2026-03-18-*-command-refinement`)
- Infrastructure command refinement spec for the next batch (migrate, prisma-migration, test-database) — planning documentation, not yet implemented

## [0.3.0] - 2026-03-18

### Changed

- **Core A-Grade Refinement** — all 9 core command and agent files refined from mixed B-/B/B+/A- grades to A-grade quality (Spec: `2026-03-18-core-agrade-refinement`)
  - Templates replaced with principles — the AI knows how to format; tell it what matters
  - `/plan-product` reduced 56% (623 → 272 lines) — Phase 1 discovery preserved intact, Phase 2 templates replaced with principles
  - `/create-spec` reduced 43% (805 → 458 lines) — discovery phase untouched, file-creation templates condensed to principled guidance
  - `/implement-story` reduced 39% (469 → 285 lines) — drift response rewritten from 117 procedural lines to ~40 lines of principles
  - `/implement-spec` reduced 17% (294 → 244 lines) — already near A-grade, minor tightening
  - Review agent: 31-item checklist → 5 categorized review dimensions; examples condensed 50%
  - Documentation agent: framework-specific sections (VitePress, Docusaurus, Nextra, MkDocs, Storybook) replaced with single "follow detected conventions" principle
  - Coding agent: verbose scope detection heuristic → single-paragraph principle
  - Architecture-check and testing agents: condensed examples and removed redundant sections
- Clean testing boundaries between `/implement-spec` and `/verify-spec` — clarified which command owns test execution vs. verification

### Removed

- Redundant "Key Improvements," "Best Practices," "Tool Integration," and "Integration with Writ Ecosystem" sections from all commands
- `SwitchMode` API calls replaced with natural language guidance (Cursor doesn't support programmatic mode switching)
- Verbose output format examples in review and documentation agents — one example demonstrates judgment, not three

## [0.2.0] - 2026-03-16

### Added

- `/assess-spec` command — pre-implementation health check that flags oversized stories, deep dependency chains, context accumulation risks, and file-overlap conflicts with specific decomposition recommendations
- Pre-flight assessment hook in `/implement-spec` (Step 2.3b) — runs lightweight sizing checks automatically before showing the execution plan, with option to hand off to full `/assess-spec`
- AI workflow best practices research (`.writ/research/2026-03-16-ai-workflow-best-practices-research.md`) with self-challenge appendix validating Writ's thin-rule architecture

### Changed

- `install.sh` link mode now creates per-file symlinks instead of directory symlinks, enabling per-project command customization alongside linked Writ commands
- `install.sh` link mode auto-cleans stale symlinks when source files are removed upstream
- `install.sh` link mode now commits linked command and agent files to git (previously only committed manifest)
- README updated with `/assess-spec` in pipeline diagram, commands table, and key features

## [0.1.0] - 2026-03-15

First public release. Three completed specs deliver the full Writ pipeline — from product planning through retrospective.

### Added

**Phase 1 — Foundation** (Spec: `2026-02-27-phase1-foundation`)

- `/prototype` command — lightweight executor for quick changes without a full spec, with auto-escalation to `/create-spec` when complexity warrants it
- Tiered spec-healing review agent with drift detection and auto-amendment
- Drift report format (`drift-log.md`) for tracking spec amendments across story implementation
- `/refresh-command` — learning loop that scans agent transcripts and proposes concrete command diffs
- `/refresh-command` promotion pipeline for staged rollout of command updates
- Command overlay system enabling per-project customization of Writ commands
- `/plan-product` gstack enhancement with opinionated posture and strategic framing (DEC-006)

**Pipeline Quality Improvements** (Spec: `2026-03-13-pipeline-quality-improvements`)

- Coding agent self-check to reduce pipeline round-trips
- Weighted review with change surface classification for proportional review depth
- "What Was Built" record auto-generated on story completion
- Living spec auto-amendment when drift is detected during implementation
- Cross-spec consistency check in `/create-spec` to catch planning-level conflicts
- Documentation agent framework agnosticism — adapts to VitePress, Docusaurus, README, etc.

**Phase 2a — Shipping & Review** (Spec: `2026-03-15-phase2a-shipping-review`)

- `/ship` command — unified shipping workflow: merge default branch, run tests, split commits by concern, create PR with structured body and auto-labels
- `/review` command — standalone pre-landing code review with error & rescue maps, shadow path tracing, interaction edge cases, and failure modes registry
- `/retro` command — git-based retrospective with session detection, streak tracking, Ship of the Week, persistent JSON snapshots, and rolling trend analysis
- Error mapping in `/create-spec` for systematic error handling and rescue paths

**Infrastructure & Platform**

- Install script (`install.sh`) with manifest tracking, three-way merge, and `--link` mode for multi-project sync
- Update script (`update.sh`) with file-level preservation of user customizations
- Migration script (`migrate.sh`) for Code Captain → Writ transition with full artifact preservation
- Platform adapters: Cursor (native), Claude Code (subagent system), OpenClaw
- `/implement-spec` orchestrator with parallel batch execution and dependency graph resolution
- `/implement-story` 6-gate SDLC pipeline: arch-check → code → lint → review → test → docs
- Proportional verification strategy for `/implement-spec` — scales validation to change scope
- Plan Mode for open-ended discovery, AskQuestion for bounded decisions (ADR-001)
- Visual design system — `/design` command, visual QA agent, mockup management
- `.writ/` workspace directory structure for specs, research, retros, decision records, and documentation

### Fixed

- Cross-platform migration script compatibility (macOS + Linux)
- Documentation bugs across commands and agents
- Retro data contract: `test_ratio` uses numeric `0` instead of `null` for zero-test periods
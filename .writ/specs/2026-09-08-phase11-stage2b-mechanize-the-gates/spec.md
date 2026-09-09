# Phase 11 Stage 2b: Mechanize the Gates

> **Status:** Complete
> **Created:** 2026-09-08
> **Owner:** @unknown
> **Dependencies:** [2026-09-07-phase11-stage2-prune-the-base, 2026-09-05-phase11-repair-and-baseline]
> **Extends:** [2026-09-07-phase11-stage2-prune-the-base](../2026-09-07-phase11-stage2-prune-the-base/spec.md)
> **Origin:** Promoted from Goal Card [`2026-09-05-writ-contract-and-verifier-layer.md`](../../issues/goals/2026-09-05-writ-contract-and-verifier-layer.md) — Stage 2b (mechanize). Stage 2a pruned the shared base and marked every `implement-story` gate's verdict source; this spec puts a script behind eight of the ten. Evidence: [`2026-09-05-goldilocks-assessment.md`](../../product/2026-09-05-goldilocks-assessment.md) §2.3, §3 Mechanism 2, §5 Step 3; [`2026-09-05-goldilocks-harness-research.md`](../../research/2026-09-05-goldilocks-harness-research.md) F5–F6; archived [`2026-08-14-script-backed-quality-gates`](../archive/2026-08-14-script-backed-quality-gates/spec.md) (the Gate 4 override pattern).
> **Loop:** unit `story` · `max_iterations: 8` · `on_exhaustion: halt_reported` · stalled 3 turns: stop and report (carried from the Goal Card's STOP-CAPS)
> **Superseded by:** [2026-09-09-phase11-stage4b-pipeline-demote](../2026-09-09-phase11-stage4b-pipeline-demote/spec.md)

## Specification Contract

**Deliverable:** Eight of ten `/implement-story` gates re-derive their verdict from a script the way Gate 4 already does; Gate 1 (coding) and Gate 4.5 (visual QA) stay `prose-only`; `verdict-provenance.py --prose-only-blocking` becomes a finding the moment a third honor-system gate appears.

**Must Include:** The Gate 4 override rule generalized — agent still runs, script wins on disagreement, `unverifiable` continues the pipeline and does not mark the story `DEGRADED` — plus a read-only re-derivation of the new verdicts against the committed Stage 1 and Stage 2a baseline JSON, so we know what those eight runs *would* have scored without spending another $180.

**Hardest Constraint:** Each new script must tell a real defect from an environment that cannot answer. A FAIL that means “could not tell” gets muted within a week and takes the true findings with it. That is the same constraint the August quality-gates spec named, and Stage 2a’s `test_integrity: unverifiable` on all eight runs is the live proof it still bites.

**Stories:**

1. **Gate 3 review override** — `scripts/review-override.py` re-derives PASS/FAIL from `ac-trace.py` + `test-integrity.py`. Residual (architecture, security, taste) stays `review-agent`. Fresh-context evaluator waits for Stage 4.
2. **Gate 0 architecture re-derivation** — script re-derives PROCEED/CAUTION from `story-deps.py` + boundary map + changed-file count. ABORT stays LLM-judged; the script reports `unverifiable` on ABORT-class cases rather than inventing them.
3. **Gate 5 docs check** — script diffs documented symbols against changed exports. Missing docs framework or no public exports → `unverifiable`, not FAIL.
4. **Gate 0.5 + 2.5 classifiers** — scripts produce `boundary_map` and `change_surface` from git + path heuristics (and assess-spec overlap when present). Advisory maps become checkable artifacts; they do not hard-lock files.
5. **Gate 3.5 format + flip + watch** — drift-log / PAUSE-emission format check (the accept/reject/modify-spec choice stays human); `gates:` frontmatter updated; `--prose-only-blocking` on; `pipeline-baseline.py` grows a `background_tasks_outstanding` field so Stage 4 can count the print-mode drop; fixture + baseline-JSON replay recorded in What Was Built. No eight-run keep-or-revert.

**Success Criteria** (Goal Card DONE WHEN line 4, plus the QUALITY rule adapted — this is not a cut):

- `commands/implement-story.md` `gates:` block: exactly two `verification: prose-only` (Gate 1, Gate 4.5); every other gate names a `scripts/*.py` path that exists.
- `python3 scripts/verdict-provenance.py check --command commands/implement-story.md --prose-only-blocking` exits 0.
- `bash scripts/eval.sh` exits 0 at the end of every story.
- Each new script has pytest fixtures for `pass`, `fail`, and `unverifiable`.
- Replay table in Story 5 What Was Built: per-run, per-new-gate, agent verdict vs re-derived verdict for all sixteen committed baseline records.

**Scope Boundaries:**

- **Included:** scripts and `implement-story.md` wiring for gates 0, 0.5, 2.5, 3, 3.5, 5; frontmatter update; `--prose-only-blocking`; eval checks; runner watch field; fixture + baseline-JSON replay; drop 85/70 from `agents/visual-qa-agent.md`.
- **Excluded:** eight-run Fable 5.1 re-run; fresh-context evaluator / counterfactual patches (Stage 4); `spec-analyze.py` (Stage 3); demoting the five-agent default (Stage 4); Goal Card → `/goal` emit (Stage 4); fixing the orchestrator’s background-subagent drop; new gate numbers; pixel/DOM visual QA.

---

## 🎯 Experience Design

**Entry point.** A maintainer runs `/implement-spec` on this spec. Installed projects meet the result after a human `/release`: new `scripts/*.py` (already copied by `install.sh`) and an `implement-story` whose honor-system gates are two, named.

**Happy path.** (1) Gate 3 script lands and overrides a PASS that `ac-trace` would fail. (2) Gate 0 script lands; ABORT still goes to the human. (3) Gate 5 script lands. (4) 0.5 and 2.5 emit maps the later gates already consume. (5) 3.5 format-checks; frontmatter reads 8 `script` / 2 `prose-only`; `eval.sh --check=verdict-provenance` Findings 0 with `--prose-only-blocking`; replay table shows per-gate claim vs re-derived verdict on the sixteen committed runs.

**Moment of truth.** `verdict-provenance.py check --prose-only-blocking` prints `prose_only_count: 2 (cap 2)` and exits 0. Adding a third `prose-only` is a finding.

**Feedback model.** Each script prints one verdict line (`pass` / `fail` / `unverifiable`) plus a reason. The story report shows the agent’s claim and the measurement, the way Gate 4 already does.

**Error experience.** Script FAIL → existing BLOCKED escalation (no new control flow). `unverifiable` → continue, reason verbatim, no `DEGRADED`. Replay disagreement with a Stage 1/2a self-report is a note in What Was Built, not a revert.

**State catalog.** Scripts landing (frontmatter still 8 prose-only, provenance note) / all six new scripts exist / frontmatter flipped / blocking on / replay recorded.

## 📋 Business Rules

1. **Checker wins.** Where the agent’s string and the script disagree, the script is the verdict. Same wiring as Gate 4.
2. **`unverifiable` is not a failed gate.** Pipeline continues; reason is surfaced; story is not `DEGRADED` on that basis alone.
3. **No new gate numbers.** Existing headings keep their ids so `pipeline-baseline.py` can join.
4. **ABORT and Large-drift stay human.** Gate 0 ABORT and Gate 3.5 accept/reject/modify-spec are not scripted decisions.
5. **The two remaining `prose-only` gates are Gate 1 and Gate 4.5.** No other pair. Visual percentages stay gone; `agents/visual-qa-agent.md`’s 85/70 lines are in scope to drop (Stage 2a DEV-102).
6. **No eight-run re-run, no keep-or-revert.** Proof is fixtures plus read-only re-derivation against `.writ/eval/baselines/2026-09-06-claude-fable-5-1.json` and `2026-09-07-claude-fable-5-1.json`.
7. **Background-subagent drop is a watch item.** Record `background_tasks_outstanding` on new baseline records. Do not change how `/implement-story` spawns agents. Stage 4 owns any orchestrator fix.
8. **Python 3.9 stdlib.** Same shape as `build-smoke.py` / `test-integrity.py` / `verdict-provenance.py` (subcommands, exit 0/1/2, `--repo`).
9. **ADR-013 holds.** Nothing merges, opens a PR, or releases.
10. **Decision log.** Each story’s closing commit appends `{date} stage-2b: {what changed and why}`.

## Detailed Requirements

### Story 1 — Gate 3 review override

- `scripts/review-override.py`: `check --spec <folder> --repo . [--story <path>] [--new-files …] [--tests …]`. Stdlib, Python 3.9. Calls `ac-trace.py check` and `test-integrity.py` (coverage + authenticity when paths are given) as read-only helpers; does not reimplement them.
- Verdicts: `fail` when ac-trace reports a blocking finding on the story (`untested_criterion` after the story would be complete, `untasked_criterion`, `dangling_reference`, `duplicate_id`) or test-integrity reports `coverage_below_threshold` / `coverage_regression` / `test_imports_no_source`; `unverifiable` when either helper is `unverifiable` or the spec folder / story file is missing; `pass` otherwise.
- Does **not** judge architecture, security, or taste. Those stay `review-agent`. A script `pass` does not force the agent’s FAIL to PASS — checker wins only in the FAIL direction for Gate 3 (a mechanical fail blocks; a mechanical pass leaves the agent’s FAIL/PAUSE standing). Record this asymmetry in the story’s What Was Built; it is the residual the research left to the agent.
- `commands/implement-story.md` Gate 3 body gains a “Verify the claim, don't trust it.” block mirroring Gate 4, invoking the script after the review agent returns. FAIL → existing review-loop recode path. `unverifiable` → continue, reason verbatim.
- Frontmatter `gate3_review` stays `prose-only` until Story 5 flips it (truthful: the script exists but is not yet the declared source). Or Story 1 may set `script:` immediately — either is fine as long as Story 5’s final block is truthful. Prefer setting `script:` in this story so provenance never lies mid-spec.
- Tests: pytest fixtures for pass / fail-from-ac-trace / fail-from-integrity / unverifiable-helper / missing spec. `eval.sh` check `review-override` registered, not count-blocking.

### Story 2 — Gate 0 architecture re-derivation

- `scripts/arch-check.py`: `check --story <path> --repo . [--planned <file>…] [--changed <file>…] [--boundary <path>]`. Two input modes: `--planned` (Gate 0’s actual moment, pre-implementation) and `--changed` (post-hoc / replay). Passing neither is `unverifiable`, not an invented empty-tree PROCEED.
- Re-derives `proceed` when story-deps for the spec validate and the planned/changed set is non-empty and inside the boundary map’s owned+readable (or no boundary was supplied). Re-derives `caution` when the set is empty, crosses into out-of-scope, or story-deps reports a warning-class result the helper already emits. Never re-derives `abort` — that stays LLM-judged; the script prints `unverifiable` with reason `abort_is_llm_residual` when the caller asks it to classify an ABORT-shaped case, and otherwise does not mention ABORT.
- `commands/implement-story.md` Gate 0: after the architecture-check agent returns PROCEED or CAUTION, run the script; on `caution` inject the script’s reason into the coding-agent warnings the way the agent’s CAUTION already does; on `fail` (deps graph invalid) apply BLOCKED. ABORT path unchanged, including the ADR-024 floor→anchor re-run.
- Tests: planned-inside-boundary → proceed; planned-empty → caution; out-of-scope path → caution; invalid story-deps → fail; no mode flag → unverifiable. eval check `arch-check`.

### Story 3 — Gate 5 docs check

- `scripts/docs-check.py`: `check --repo . [--changed <file>…]`. Diffs public exports in `--changed` (or `git diff --name-only` against the story’s parent when `--changed` is omitted and git can answer) against documented symbols in README / changelog / detected docs framework / adjacent docstrings.
- `pass` when every new or newly-public export in the changed set is named in a doc the check can read. `fail` when a changed export has no matching documented symbol. `unverifiable` when no docs framework is detected **and** there are no public exports in the changed set (Writ itself, markdown-only stories), or when the changed set cannot be resolved.
- Fixtures must use a tiny app tree, not this repo. Writ-the-product is the `unverifiable` case, not the `pass` case.
- Gate 5 body: run after the documentation agent returns; `fail` → BLOCKED escalation with agent `documentation-agent`. `unverifiable` → continue.
- Tests: export-documented → pass; export-undocumented → fail; empty/markdown tree → unverifiable. eval check `docs-check`.

### Story 4 — Gate 0.5 + 2.5 classifiers

- `scripts/boundary-map.py`: `compute --story <path> --repo . [--overlap <path>]`. Writes nothing; prints a JSON `boundary_map` (`owned` / `readable` / `out_of_scope`) derived from the story’s files-in-scope / tasks plus optional assess-spec Check 5 overlap. Degrades to owned=changed-paths, readable=[], out_of_scope=[] when overlap is absent (the skill already degrades this way). Exit 0 on a well-formed map; exit 1 on a malformed story file; exit 2 on usage.
- `scripts/change-surface.py`: `classify --changed <file>…`. Prints one of `style-only` / `single-component` / `cross-component` / `full-stack` using the same four-class rule `skills/change-surface-classification/SKILL.md` names, implemented as path heuristics (not an LLM). Exit 0 with the class; exit 2 on usage (no files).
- One script with two subcommands is acceptable if both CLIs above remain as the public surface (a wrapper is fine). Prefer two small files matching the two gate ids.
- Gate 0.5 and Gate 2.5 bodies: run the script, pass its stdout to Gates 1 and 3 as today. The maps stay advisory — no hard file locking.
- Tests: overlap-present vs overlap-absent maps; each of the four surface classes; empty changed list → exit 2. eval checks `boundary-map` and `change-surface`.

### Story 5 — Gate 3.5 format + flip + watch

- `scripts/drift-format.py`: `check --story <path> [--drift-log <path>]`. `pass` when every `DEV-NNN` entry in the drift log (when present) matches `.writ/docs/drift-report-format.md`’s required fields and, if the review output contains a Large-drift heading, a PAUSE was emitted (the story file or a `--review-output` blob carries the verdict token). `fail` on a malformed entry or a Large-drift without PAUSE. `unverifiable` when there is no drift log and no Large-drift heading (the common case). Does **not** decide accept / reject / modify-spec.
- Flip `commands/implement-story.md` `gates:` so the eight scripted gates name their scripts and only `gate1_coding` and `gate4_5_visual` remain `prose-only`. `eval.sh` `check_verdict_provenance()` gains `--prose-only-blocking`.
- Drop the 85/70 percentage lines from `agents/visual-qa-agent.md` (Stage 2a DEV-102). Verdict vocabulary stays PASS / SOFT PASS / FAIL.
- `pipeline-baseline.py`: add `background_tasks_outstanding` (int, default 0) on each run record; extend `GATE_NAMES` / `REDERIVATION_KEYS` so future runs can record the new scripts. Do **not** rewrite the two committed baseline JSON files’ schema. Parse Claude Code print-mode stderr for the existing “Background tasks still running after 600s” line when ingesting a transcript.
- Replay: a `replay` subcommand or a small `scripts/tests/test_gate_replay.py` that loads both committed baseline JSONs (16 records), invokes each new script in `--changed` / post-hoc mode from whatever paths the record already carries, and writes a table of agent-verdict vs re-derived verdict. Disagreement is a note. `unverifiable` on historical `test_integrity: nothing_inspected` is the expected majority, not a defect.
- Decision-log line names the flip and the replay totals. No keep-or-revert. No `/revert`.

## Implementation Approach

Python 3.9 stdlib scripts under `scripts/` with pytest under `scripts/tests/`, mirroring `build-smoke.py` / `test-integrity.py` / `verdict-provenance.py` (subcommands, exit 0/1/2, `--repo` / `--project`). New scripts call existing helpers (`ac-trace.py`, `test-integrity.py`, `story-deps.py`) rather than copying their parsers. Verdict vocabulary is the existing `GATE_SCRIPT_VERDICTS` triple: `pass` / `fail` / `unverifiable`. `install.sh` already copies `scripts/*.py` — no install story.

Gate 3’s FAIL-only override is the one deliberate departure from Gate 4’s bidirectional override: a mechanical pass must not wash out a review-agent FAIL on architecture or security. Story 1 records that in What Was Built so Stage 4’s evaluator does not have to rediscover it.

## ⚠️ Technical Concerns

- Stage 2a’s eight runs already show `test_integrity: unverifiable` and original-story-test suites that failed to run. Gate 3’s override will inherit that: many historical PASSes will re-derive `unverifiable`, not FAIL. The replay table must not treat that as a script defect.
- Gate 0 changed-file count before coding is a planned-file count; after coding it is a git diff. The script needs `--planned` / `--changed` or it will lie at the only moment Gate 0 actually runs (pre-implementation).
- Gate 5 on a markdown-only repo (Writ itself) is structurally `unverifiable`. Fixtures must use a tiny app tree, not this repo.
- `pipeline-baseline.py` today only re-derives `build_smoke` and `test_integrity`. Story 5 extends `REDERIVATION_KEYS` so the watch field and new scripts can be recorded on *future* runs; it does not rewrite the two committed JSON files’ schema.

## 💡 Recommendations

- One script per gate (or one script with a `--gate` subcommand for 0.5 + 2.5, which share a git-diff input). Do not bundle Gate 3 into a mega-verifier.
- Ship via the existing `install.sh` `scripts/*.py` glob. No install-story.
- Leave `review-agent.md` almost alone — the override lives in the command, like Gate 4.

## Approved Scope Additions

_None yet. Additions agreed after lock are recorded here with date, approver, and the story they land in; the contract above is unchanged._

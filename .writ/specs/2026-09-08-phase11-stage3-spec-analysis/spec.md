# Phase 11 Stage 3: Spec Analysis

> **Status:** Not Started
> **Created:** 2026-09-08
> **Owner:** @unknown
> **Dependencies:** [2026-09-05-phase11-repair-and-baseline, 2026-09-08-phase11-stage2b-mechanize-the-gates]
> **Origin:** Promoted from Goal Card [`2026-09-05-writ-contract-and-verifier-layer.md`](../../issues/goals/2026-09-05-writ-contract-and-verifier-layer.md) — Stage 3 (spec analysis). Stage 2b put scripts behind eight `implement-story` gates; this spec is the one new capability the evidence supports: contradiction / gap / ambiguity detection on acceptance criteria before code exists. Evidence: [`2026-09-05-goldilocks-assessment.md`](../../product/2026-09-05-goldilocks-assessment.md) §5 Step 4; [`2026-09-05-goldilocks-harness-research.md`](../../research/2026-09-05-goldilocks-harness-research.md) F5 (Kiro ~60% first-draft AC defects; Writ has `exit-criteria.py` + `ac-trace.py` but nothing checks AC consistency).
> **Loop:** unit `story` · `max_iterations: 8` · `on_exhaustion: halt_reported` · stalled 3 turns: stop and report (carried from the Goal Card's STOP-CAPS)

## Specification Contract

**Deliverable:** `scripts/spec-analyze.py` detects contradictory, missing, and ambiguous acceptance criteria after story files exist; findings stay advisory for one release; precision is recorded on committed labeled fixtures.

**Must Include:** Hybrid judge — the script emits deterministic structural findings; `create-spec` / `verify-spec` run one LLM pass for contradiction / gap / ambiguity and pass that JSON to the script; the script schema-checks the JSON. Invoked from a new `create-spec` step after 2.6a (stories exist; treat “lock” as end-of-package, not Step 1.4b) and from `verify-spec`. `eval.sh` check. Precision numbers in the closing story’s What Was Built and `{date} stage-3:` decision-log line. No yuss checkout.

**Hardest Constraint:** A finding that means “could not tell” must be `unverifiable`, not `fail`. Advisory must not fail `create-spec` or `verify-spec`. A FAIL that means “could not tell” gets muted and takes the true findings with it.

**Stories:**

1. **CLI + schema** — `scripts/spec-analyze.py` `check --spec PATH [--findings FILE]`: structural findings, schema-check of the LLM JSON, `pass` / `fail` / `unverifiable`, pytest fixtures.
2. **Hooks** — new `create-spec` step after 2.6a; `verify-spec` advisory check; orchestrator LLM-pass contract (what the JSON must contain, not a new model API in the script).
3. **Eval + precision** — `eval.sh` check `spec-analyze` (helper health + fixture relay, not count-blocking); labeled fixtures named after the four Stage 1 yuss story slugs where we have names, otherwise synthetic; precision recorded; no eight-run.

**Success Criteria** (Goal Card DONE WHEN line 5):

- `scripts/spec-analyze.py` exists and is Python 3.9 stdlib.
- `/create-spec` invokes it after stories exist (new step after 2.6a); `/verify-spec` invokes it. Findings are notes; neither command fails the package on analysis findings.
- `bash scripts/eval.sh` has a `spec-analyze` check and exits 0 at the end of every story.
- Precision (true-positive / false-positive counts per class: contradiction, gap, ambiguity, clean) is written in Story 3 What Was Built and the decision-log line, scored on committed labeled fixtures. Nothing in this spec promotes the check to blocking.

**Scope Boundaries:**

- **Included:** CLI + finding schema; structural findings; LLM-pass ingest; `create-spec` + `verify-spec` wiring; `eval.sh` check; labeled fixtures + precision record.
- **Excluded:** Phase B (EARS-shaped criteria, property-test generation); promoting findings to blocking; Stage 4 (fresh-context evaluator, five-agent demotion, Goal Card → `/goal` emit); eight-run Fable re-run; yuss checkout; SMT solver; replacing `ac-trace.py`; new `implement-story` gate numbers.

---

## 🎯 Experience Design

**Entry point.** A maintainer runs `/create-spec` (or `/verify-spec` on an existing package). Installed projects meet the script after a human `/release` (`install.sh` already copies `scripts/*.py`).

**Happy path.** (1) Stories land; Step 2.6a `ac-trace` validates IDs. (2) Orchestrator runs one LLM pass against the story AC, writes a findings JSON. (3) `spec-analyze.py check --spec <folder> --findings <json>` prints structural + schema-checked semantic findings. (4) Step 2.9 / verify-spec report lists them as notes. (5) Package completes. (6) Story 3 records precision on the fixture set.

**Moment of truth.** A first-draft spec with a real contradiction shows a named `contradiction` note and still locks. A missing findings file with no structural hit prints `unverifiable`, not `fail`.

**Feedback model.** One verdict line (`pass` / `fail` / `unverifiable`), optional `reason:` lines, summary last — same family as Stage 2b scripts. Commands relay via `add_note` (analysis) or `add_finding` only when the helper is missing or exits 2.

**Error experience.** Helper usage/crash → existing command error path. `unverifiable` → continue, reason verbatim, package is not `DEGRADED`. Malformed LLM JSON → `fail` `malformed_findings` from the script; the command still treats it as a note and continues (advisory). No AskQuestion gate on analysis notes.

**State catalog.** Script exists / hooks wired / eval check registered / precision recorded / still advisory.

## 📋 Business Rules

1. **Advisory for one release.** Analysis findings never fail `create-spec` or `verify-spec`. Promotion to blocking is a later spec, and only after precision is recorded.
2. **`unverifiable` is not a failed analysis.** Missing `--spec`, unreadable stories, or semantic classes requested without `--findings` → `unverifiable`. Not `DEGRADED`.
3. **Do not replace `ac-trace.py`.** Step 2.6a and verify-spec 3e/3f stay the ID-coverage checker. This script judges meaning and structure `ac-trace` does not.
4. **Hybrid judge.** Script owns deterministic structural codes. Orchestrator owns one LLM pass. Script schema-checks that JSON; it does not call an LLM API.
5. **No Phase B.** EARS notation and property-test generation are out. Precision on Phase A is the gate for any later spec.
6. **No yuss checkout, no eight-run.** Precision is fixture-scored in this repo. Fixture names may reuse Stage 1 yuss story slugs; AC text is authored here.
7. **Python 3.9 stdlib.** Subcommands, exit 0/1/2, `--repo` / `--project` alias. `install.sh` already copies `scripts/*.py`.
8. **ADR-013 holds.** Nothing merges, opens a PR, or releases.
9. **Decision log.** Each story’s closing commit appends `{date} stage-3: {what changed and why}`. Story 3’s line names the precision totals.
10. **Shared `eval.sh`.** Additive `CHECKS` entry. Stage 2b also edits that file (header still `Not Started`); do not revert its checks.

## Detailed Requirements

### Story 1 — CLI + schema

- `scripts/spec-analyze.py`: `check --spec PATH [--findings FILE] [--repo .]`. Stdlib, Python 3.9.
- **Structural codes** (no LLM): `empty_criterion` (checked Given/When/Then line with empty body); `unmeasurable_criterion` (no observable outcome in the Then — e.g. “works correctly” / “as expected” with no named artifact or verdict); `under_min_criteria` (story with fewer than 3 `- [ ] Given` lines). These are `fail` reasons.
- **Semantic codes** (only from `--findings`): `contradiction`, `gap`, `ambiguity`. Each finding object requires `code`, `story` (story filename or `spec`), `summary` (non-empty), optional `ac_ids` (list of `AC-N.M`). Unknown codes or missing required fields → `malformed_findings` (`fail`).
- Verdicts: `fail` when any structural code fires or findings JSON is malformed; `unverifiable` when `--spec` is missing/unreadable, or when `--findings` is omitted and no structural code fired (semantic pass not possible); `pass` when stories are readable, findings JSON (if given) is well-formed, and no structural code fired.
- `--findings` absent is not a fail. Orchestrators that skip the LLM pass still get structural analysis.
- Does not import `ac-trace.py` parsers. May read story files the same way other scripts do (path + markdown).
- Tests: pytest fixtures for pass (clean + well-formed empty-or-clean findings), fail-structural, fail-malformed-json, unverifiable-missing-spec, unverifiable-no-findings-no-structural. Exit 0/1/2. Accept / reject / modify-spec is never a printed verdict.

### Story 2 — create-spec + verify-spec hooks

- `commands/create-spec.md`: new step **after 2.6a** (recommended label `Step 2.6c`, placed after 2.6b so 2.6b is not renumbered) that (1) instructs the orchestrator to run one LLM pass over the generated stories’ acceptance criteria looking for contradiction, gap, and ambiguity, grounded in exit-criteria grammar (observable, named outcomes), writing a JSON file under `.writ/state/` (gitignored) or a temp path; (2) runs `python3 scripts/spec-analyze.py check --spec <folder> [--findings <json>]`; (3) surfaces the verdict and reasons in Step 2.9 as notes. Package creation continues regardless of `fail` / `unverifiable`.
- `commands/verify-spec.md`: a new advisory check (do not reuse 3e/3f) that invokes the same CLI. Relay via notes. Do not fail the verify report on analysis `fail`.
- LLM-pass contract (in the command, not a new agent file): input is the spec folder’s story AC text; output is a JSON array of finding objects matching Story 1’s schema; if the model cannot judge, it writes `[]` and the script may still be `unverifiable` or `pass` on structure alone. Do not add an API key dependency. Do not change how `/implement-story` spawns agents.
- Tests: command-body grep / eval-wiring that the new step names the script and that verify-spec does too; a bash fixture that a `fail` script exit does not force `eval.sh --check=spec-analyze` to fail the *command* contract (notes only). Exact pin shape matches `test_eval_verdict_provenance.sh` / Stage 2b eval-wiring tests.

### Story 3 — eval check + precision record

- `scripts/eval.sh`: `spec-analyze` in `CHECKS`; `check_spec_analyze()` — missing helper → `add_finding`; usage exit 2 → `add_finding`; analysis `fail` / `unverifiable` / `pass` on the live repo → `add_note` only (not count-blocking). Live Writ specs may be `unverifiable` without a findings file.
- `scripts/tests/test_eval_spec_analyze.sh` in the Stage 2b eval-wiring shape.
- Labeled fixtures under `scripts/tests/fixtures/spec-analyze/` (or equivalent): at least one each of contradiction, gap, ambiguity, and clean. Names may reuse Stage 1 slugs (`story-2-event-creation-payment-flow`, `story-3-settlement-view-share-link`, `story-3-fee-sharing-pro-exemption`, `story-4-messaging-migration-quick-split-guard`) when a fixture is a stand-in for that story; otherwise `synthetic-*`. Gold labels live next to the fixtures.
- Precision: run the structural checker plus schema-check against gold labels (the semantic gold is the labeled JSON, not a live LLM). Record `{TP}/{FP}` per class and overall precision in Story 3 What Was Built. Decision-log: `{date} stage-3: spec-analyze.py advisory; hooks after 2.6a + verify-spec; precision {…}`. No keep-or-revert. No `/revert`.

## Implementation Approach

Python 3.9 stdlib script under `scripts/`, pytest under `scripts/tests/`, same CLI family as `ac-trace.py` / `verdict-provenance.py` / Stage 2b helpers (subcommands, exit 0 = ran without blocking helper defect, 1 = `fail` verdict, 2 = usage). Commands treat analysis `fail` as a note. `install.sh` already copies `scripts/*.py`.

Step 2.6a remains `ac-trace`. The new step is additive. Do not invent a Step 2.6 overlap that rewrites story generation.

## ⚠️ Technical Concerns

- Stage 2b’s `eval.sh` is a shared file whose spec header is still `Not Started`. This spec only appends a check.
- A live LLM pass is not reproducible. Precision must be scored on committed labels, not on one model’s mood.
- `unmeasurable_criterion` is a heuristic. Over-firing is a false-positive against the hardest constraint — prefer under-firing; record misses as gaps in the precision table, not as script `fail` on clean fixtures.
- Goal Card text says “Step 2.6”; this contract relocates the invoke to after stories exist. The decision-log must say so.

## 💡 Recommendations

- Keep the LLM prompt in the command body short: three codes, exit-criteria grammar, JSON schema only. No second review agent.
- Place findings JSON under `.writ/state/` so it is gitignored.
- Do not fold this into `ac-trace.py`. Different question, different schema.

## Approved Scope Additions

_None yet. Additions agreed after lock are recorded here with date, approver, and the story they land in; the contract above is unchanged._

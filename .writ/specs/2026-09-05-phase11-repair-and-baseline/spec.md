# Phase 11 Stage 1: Repair and Baseline

> **Status:** Not Started
> **Created:** 2026-09-05
> **Owner:** @unknown
> **Dependencies:** []
> **Origin:** Promoted from Goal Card [`2026-09-05-writ-contract-and-verifier-layer.md`](../../issues/goals/2026-09-05-writ-contract-and-verifier-layer.md) — Stage 1 of 4. Evidence: [`2026-09-05-goldilocks-harness-research.md`](../../research/2026-09-05-goldilocks-harness-research.md) and [`2026-09-05-goldilocks-assessment.md`](../../product/2026-09-05-goldilocks-assessment.md).
> **Loop:** unit `story` · `max_iterations: 8` · `on_exhaustion: halt_reported` · stalled 3 turns: stop and report (carried from the Goal Card's STOP-CAPS)

## Specification Contract

**Deliverable:** A repaired Writ corpus and a reproducible Claude Fable 5.1 pipeline baseline over four yuss.app stories, so every later Phase 11 cut is measured against a number rather than an opinion.

**Must Include:** A baseline JSON that a later run can be diffed against without a human interpreting either side.

**Hardest Constraint:** Replaying a completed story without the model seeing the answer. A git worktree at the parent commit still exposes the future via `git log --all` and reflogs. Each replay therefore runs in an isolated checkout where later commits are unreachable — a fresh clone truncated at the parent SHA (`git clone --no-checkout` + `git fetch --depth 1 origin <sha>` + `git checkout FETCH_HEAD`, or `git archive <sha>` into a new `git init`), never a worktree of `~/Projects/yuss`.

**Stories:**

1. **Repair dead ends** — the 19 verified items in assessment §2.4, plus three new `eval.sh` checks so they stay closed.
2. **Validated token measurement** — `measure-invocation.py` measures with the Anthropic `count_tokens` API when a key is present and says so in its output.
3. **Story selection** — `scripts/pipeline-baseline.py select` applies fixed criteria to yuss.app's archived specs and records the four chosen stories with parent SHAs.
4. **Replay runner** — `pipeline-baseline.py run` builds the isolated checkout, invokes Claude Code headless with `/implement-story`, and parses metrics.
5. **Baseline capture and gate** — 4 stories × 2 runs at Fable 5.1, one committed JSON, and `check_pipeline_baseline` in `eval.sh`.

**Success Criteria (Goal Card DONE WHEN 1–2, verbatim):**
- Every `.md` path referenced in `commands/*.md` resolves on disk or to a creating command; `comm` of `skills/` vs `.writ/manifest.yaml` is empty; zero `.writ/knowledge/` entries contain single-character bullets.
- `.writ/eval/baselines/` holds at least one JSON for Fable 5.1 over the 4-story yuss.app set, and `scripts/measure-invocation.py` reports `token_method_validated: true`.

**Scope Boundaries:**
- Included: dead-end repair with regression checks; validated token counting; story selection; isolated replay; one committed Fable 5.1 baseline; the eval gate that validates it.
- Excluded: any edit to `system-instructions.md` or `commands/_preamble.md` beyond fixing a dead end; any gate mechanization; `spec-analyze.py`; pipeline demotion; GPT-6 Astra runs; any change pushed to yuss.app.

**⚠️ Technical Concerns:**
- Headless invocation of a Writ slash command (`claude -p '/implement-story …'`) inside an isolated yuss checkout is unverified. Story 4 opens with a one-story smoke run; if it fails, the runner falls back to manual-with-ingest and the story's What Was Built records the deviation.
- Eight full pipeline runs at Fable 5.1 default-high effort dominate the cost of this spec. Story 5 records tokens per run so Stage 2 knows the price before repeating it.
- yuss's original tests may need a database or Stripe keys. Selection criteria exclude stories whose tests require live services.

**💡 Recommendations:**
- Land Story 1 and commit before any measurement; a baseline over a corpus with a required-but-nonexistent `objective.md` measures the wrong thing.
- Put the selection criteria in the JSON, not only in the script, so a reader can tell why those four stories without reading code.

## 🎯 Experience Design (developer-facing)

**Entry point.** A Writ maintainer preparing to cut instruction from the shared base opens `.writ/eval/baselines/` and finds one JSON per model. `python3 scripts/pipeline-baseline.py compare <a> <b>` prints a per-story, per-metric delta.

**Happy path.** (1) `pipeline-baseline.py select --yuss ~/Projects/yuss` writes the four stories and their parent SHAs. (2) `pipeline-baseline.py run --model claude-fable-5-1 --runs 2` builds eight isolated checkouts, runs the pipeline in each, and appends eight run records. (3) `bash scripts/eval.sh --check=pipeline-baseline` validates the file. (4) The maintainer commits the JSON.

**Moment of truth.** The first `compare` after a Stage 2 cut shows exit-criteria pass rate, tokens, and interrupts side by side — and the maintainer keeps or reverts the cut on that line, not on a feeling.

**Feedback model.** Each `run` prints one line per story per run: story id, exit-criteria verdict, tests passed/total, tokens in/out/cache, wall-clock, interrupts. The JSON is the durable record; stdout is the progress view.

**Error experience.** No `ANTHROPIC_API_KEY`: `measure-invocation.py` prints its existing estimate with `token_method_validated: false` and a one-line note naming the env var. `pipeline-baseline.py run` never requires a vendor key — it inherits the operator environment. Missing headless driver (or `pnpm`): `run` stops before creating any checkout and names the install path. A model with no headless driver (Grok, local weights, a Cursor session): `run` refuses and names `ingest` after an IDE `/implement-story`. A replay whose tests need a live service: excluded at `select` time with the reason in the JSON's `excluded` list, never discovered mid-run. Story 1's regression checks failing after a later edit: `eval.sh` names the file and line.

**State catalog.** `select` written / `run` in progress (partial records flushed after each run so a crash loses one run, not eight) / `run` complete / `compare` with mismatched selections (refused — different story sets are not comparable).

## 📋 Business Rules

1. **Isolation.** A replay checkout contains no commit later than the story's parent SHA. `pipeline-baseline.py run` asserts `git rev-list --all | wc -l` equals the truncated depth before invoking the model, and records the assertion in the run record.
2. **yuss is read-only.** The runner reads `~/Projects/yuss` and writes only under a temp directory it creates and removes. No command in this spec pushes, commits, or writes inside `~/Projects/yuss`.
3. **Secrets stay in the environment.** Writ never stores a provider key and does not pick a vendor. The runner inherits the operator environment and forwards it to the selected driver. Auth is the CLI or IDE login — Anthropic, OpenAI, xAI/Grok, a local runtime, or anything else the host already has. The baseline JSON carries story IDs, SHAs, metrics, and the selection criteria — never source text, transcript text, or keys.
4. **One model per file.** A baseline file is named `<date>-<model-id>.json` and carries `model` in its header. Astra lands as a sibling file under the same schema; the schema does not change for it.
5. **Verdict beside re-derivation.** For every gate that has a script today (Gate 2 `build-smoke.py`, Gate 4 `test-integrity.py`, completion `exit-criteria.py`), a run record stores the agent's reported verdict and the script's re-derived verdict as two fields. Gates with no script store the reported verdict and `rederived: null`.
6. **Dead ends stay closed.** Story 1 adds three `eval.sh` checks (referenced-path resolution, skills↔manifest parity, knowledge-entry integrity). They block, not note.
7. **ADR-013 boundary.** Nothing in this spec merges, opens a PR, or releases. Installed projects see these scripts only after a human `/release`.
8. **Decision log.** Each story's closing commit appends one line to `.writ/decision-log.md` in the form `{date} stage-1: {what changed and why}`; Story 1 creates the file.
9. **Fable 5.1 only.** The card's constraint stands; `run --model` accepts any model ID but this spec commits only a `claude-fable-5-1` file. Sibling files (Grok, Codex, local weights) use the same schema.

## Detailed Requirements

### Story 1 — Repair dead ends

The nineteen items in `.writ/product/2026-09-05-goldilocks-assessment.md` §2.4, grouped by resolution:

- **Create or drop the reference.** `create-spec.md:297` `objective.md` — drop from the list (no command creates it; `initialize` writes `tech-stack.md` and `code-style.md` under `.writ/docs/`; write those two with their full paths).
- **Define or remove the flag.** `implement-spec.md:72` `--force` — add to the Invocation table with behavior (re-run Completed stories) or remove the clause. Removal is the default unless `implement-spec.md` already implements re-run semantics.
- **Remove the phantom bound.** `create-spec.md:772` cites `loop.max_iterations` in a file with no `loop:` block — reword to "count as one attempt" without naming a bound this command does not declare, or add the block. Adding requires `calibrated_against` evidence; rewording is the default.
- **Retire the no-op emit or point it at a stub.** `implement-story.md:150`, `create-spec.md:770` `(no-op until ADR-025 Story 1) escalated(...)` — leave the literal (pinned by `check_model_escalation`) but add one sentence naming the missing sink so the next reader does not search for `signal.py`.
- **Register the skills.** Add `subagent-result-completeness` and `subagent-worktree-integration` to `.writ/manifest.yaml`; run `gen-skill.sh`.
- **Wire or mark `gbrain-interop`.** Either add one `Read skills/gbrain-interop/SKILL.md` at the adapter memory sections' point of need, or set its `status:` to a value the lifecycle lint accepts for "no consumer" and say so in the SKILL.md.
- **Restore the knowledge ledger.** For each of the ten shredded `.writ/knowledge/lessons/*.md` entries (each also has an empty `## TL;DR`, so reconstruction recovers the statement, not only the bullets), either reconstruct from the source phase-close record (`.writ/specs/archive/*/` What Was Built or the refresh log) or delete the entry and note the deletion in `knowledge/README.md`. Fix the writeback bug in `scripts/phase-state.py knowledge_writeback` (the phase-close path) that iterated a string as a list and produced single-character bullets.
- **Resolve the contradictions.** `verify-spec.md:765` ↔ `release.md:107` (checks 1–8 vs 1–6): make `release.md` authoritative and fix `verify-spec.md`. `status.md:266` ↔ `:482`: body is authoritative; fix the Integration table. `implement-story.md:70/219/231`: Gate 3 emits PAUSE, Gate 3.5 owns the pause and its three options; say so once and cross-reference. `create-spec.md:579` ↔ `implement-spec.md:269`: `implement-spec` writes the bold unadorned `Complete` form.
- **Discoverability.** Add `/create-spec --from-issue <path>` to `create-spec.md`'s Invocation list.
- **Toolchain.** `implement-spec.md:210–216`: replace hard-coded `npx tsc` / `npm test` with the runner-detection language `ship.md` already uses.
- **Cul-de-sacs.** `implement-spec.md:218`: name the next action (re-run the suspected story with `--force` if Story 1 defines it, else quarantine per `implement-phase`'s vocabulary). `ship.md:434–437`: state that Step 6 runs on the next `/ship` or `/release` invocation that finds the landed commit.
- **Adapters.** `claude-code.md:519`: replace the `haiku → sonnet` gotcha with ADR-024's anchor-as-ceiling rule. `cursor.md:50–55`: regenerate the install tree from `manifest.yaml`. `openclaw.md:60–64`, `codex.md:32,117`: mark unverified rows as unverified in one consistent form; delete "after this platform ships" copy.

Regression checks (new in `eval.sh`, blocking): `check_referenced_paths` (every backticked `*.md` path in `commands/*.md` exists, is created by a named command, or is in an allowlist with a reason), `check_skill_manifest_parity` (`comm -3` of skill dirs vs manifest names is empty), `check_knowledge_integrity` (no `.writ/knowledge/**/*.md` has a bullet whose content is a single character).

### Story 2 — Validated token measurement

`scripts/measure-invocation.py` gains a `--tokenizer anthropic` mode (default when `ANTHROPIC_API_KEY` is set) that calls the Messages `count_tokens` endpoint for each measured text with `model=claude-fable-5-1` (overridable by `--model`), caches results by content hash under `.writ/state/token-cache.json`, and reports `token_method: "anthropic-count-tokens"`, `token_method_validated: true`, and the model ID. Without a key it keeps today's output byte-for-byte except that `token_note` names the env var. Network failure mid-run degrades to the estimate for the failed items and sets `token_method_validated: false` with the failure count. Unit tests cover both branches with the HTTP call mocked; `scripts/tests/` already has the pattern.

### Story 3 — Story selection

`scripts/pipeline-baseline.py select --yuss <path> --out .writ/eval/baselines/<date>-claude-fable-5-1.json` scans `<yuss>/.writ/specs/archive/*/user-stories/story-*.md` and selects exactly four stories meeting all of: `Status: Completed`; a `Commit:` line or a story-referencing commit found via `git log --grep`; at least one test file touched by that commit; test command runnable without a live service (heuristic: the commit's test files import no module matching a configurable deny-list — `prisma`, `stripe`, `@neondatabase`, `next-auth` server — and the story's Notes do not mention a database migration as a prerequisite); and one story from each of four surface classes derived from the commit's changed paths — API route (`app/api/**`), UI (`components/**` or `app/**/page.tsx`), data model (`prisma/**` or `lib/db/**` — with the live-service rule relaxed only if a schema file is the sole touch and tests mock the client), refactor (no new files, net negative lines). Ties break toward the most recent story. The JSON's `selection` block records each story's path, spec folder, parent SHA (`<commit>^`), surface class, test files, and the criteria values that admitted it; an `excluded` list records the last ten candidates rejected and why.

### Story 4 — Replay runner

`pipeline-baseline.py run --model <id> --runs N` iterates the selection. For each story and run: create `$TMPDIR/writ-baseline-<story>-<n>/`, build the isolated checkout at the parent SHA (Business Rule 1, assertion recorded), copy the story file and its spec folder's `spec.md`, `spec-lite.md`, and sub-specs into the checkout's `.writ/specs/<folder>/` (these are the inputs a real run would have had), ensure the Writ installation the checkout expects is present (yuss carries its own `.claude/`; if the checkout at that SHA predates a needed script, copy the current `scripts/` in and record `writ_scripts: current`), then invoke `claude -p "/implement-story <story-id>" --model <id> --output-format stream-json` with a wall-clock cap, capturing the transcript to the temp dir. After exit: run the story's original tests from the parent's `package.json` test command against the produced tree; run `exit-criteria.py`, `test-integrity.py`, and `build-smoke.py`; parse the transcript for usage (`input_tokens`, `output_tokens`, `cache_read_input_tokens`), AskQuestion or `STATUS: BLOCKED` occurrences, and gate verdict strings; append one run record; delete the temp dir unless `--keep`. The first task is a single-story smoke run that proves headless invocation works or triggers the fallback (manual session + `ingest` subcommand that computes the same record from a given checkout and transcript path).

### Story 5 — Baseline capture and gate

Run `run --model claude-fable-5-1 --runs 2` to completion, commit `.writ/eval/baselines/2026-MM-DD-claude-fable-5-1.json`, and add `check_pipeline_baseline` to `eval.sh`: when no file exists, emit a note; when one exists, block on schema violations (`schema: pipeline-baseline-v1`, `model`, `selection` with exactly four stories, `runs` with `runs_per_story × 4` records each carrying every metric field, `criteria` block present, no field containing more than 200 characters of free text). Add `compare <a> <b>` printing per-story deltas and refusing mismatched selections. Record total tokens and dollar estimate for the eight runs in the story's What Was Built.

## Implementation Approach

Python 3.9-compatible scripts in `scripts/`, tested under `scripts/tests/` with the existing pytest + bash pattern; `eval.sh` checks added next to their nearest neighbor and registered in `CHECKS`. The Anthropic call uses `urllib` from the stdlib (no new dependency) with the `anthropic-version` header the API requires. The runner shells out to `git` and `claude`; it never imports yuss code. Every story ends with `bash scripts/eval.sh` at `Findings: 0` (run outside the sandbox — it does `git init` in a temp dir). Stories 2, 3 are independent of each other and of Story 1's content but should land after Story 1's commit so the baseline measures the repaired corpus; Story 4 depends on 3; Story 5 depends on 2 and 4.

## Approved Scope Additions

**2026-09-07 — no resident key; driver ≠ model (user-approved, Stories 4–5).** Writ does not hold a vendor API key and does not treat Anthropic as the only host. `run` talks to a **driver** (a headless agent CLI that can execute `/implement-story`). `--driver auto` infers from the model id: `claude-*` → the implemented `claude` driver; `gpt-*` / `o1` / `o3` / `o4` → registered `codex` (ingest until a headless argv exists); `grok-*`, `llama*`, `qwen*`, and other local/open-weight prefixes → ingest after an IDE session. Auth is the operator's CLI or IDE. Preflight requires `pnpm` plus a driver binary only when the model has an implemented driver. `invocation.driver` is recorded. `measure-invocation.py` still uses `ANTHROPIC_API_KEY` *when present* for optional `count_tokens`; baseline run tokens come from the driver's result event. AC-4.1 and AC-5.1 amended. This spec still *commits* only the Fable 5.1 file (Business Rule 9).

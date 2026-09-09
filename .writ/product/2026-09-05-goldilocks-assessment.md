# Goldilocks Assessment: Is Writ Tuned for Fable 5.1 and GPT-6 Astra?

> **Date:** 2026-09-05
> **Status:** Analysis and proposed plan — not yet a roadmap phase. Promote via `/plan-product` or `/create-spec`.
> **Evidence base:** [`2026-09-05-goldilocks-harness-research.md`](../research/2026-09-05-goldilocks-harness-research.md) (external), two full-corpus audits of `commands/`, `agents/`, `skills/`, `adapters/`, `scripts/` run this session (internal), `scripts/measure-invocation.py`, `git` history, and [`2026-08-14-writ-dogfooding-quality-assessment-research.md`](../research/2026-08-14-writ-dogfooding-quality-assessment-research.md).
> **Writ version assessed:** 0.35.0

## 1. Verdict

The user asked four questions. Here are the answers, then the evidence.

**Is Writ too prescriptive or not prescriptive enough?** Both, in different places, and the split is clean. Writ is **over-prescriptive about behavior** — how to think, verify, order reads, phrase questions, and format tool calls — and **under-prescriptive about verification** — seven of ten pipeline gate verdicts are model self-report with no script that re-derives them. The frontier models it targets now do the first natively and still cannot be trusted on the second. Writ has the ratio backwards.

**Does it lead models down dead-end paths?** Yes, in a bounded and fixable set of places: a required context file no command creates, a flag referenced but never defined, a loop cap cited in a command with no loop, an ADR-mandated signal emit whose sink does not exist, two consumed skills missing from the manifest, and a knowledge writeback that shredded half its own ledger. None of these is a design flaw; all are drift from a corpus that grew 79% by bytes in five months with no mechanical governor (the roadmap says so itself).

**Does it over-correct or under-correct?** It over-corrects at the *prompt* layer (28 KB of shared base loaded on every invocation, ~60 imperative rules before a command starts, five agents and eleven skill loads per story) and under-corrects at the *verifier* layer (the eval harness has 47 checks and 44 of them police Writ's own markdown; zero assert that a user's feature works). The dogfooding study said this in August: prompt-level guarantees silently failed, mechanical ones held. The external literature says the same thing louder.

**What is the Goldilocks framework?** One that owns three things and delegates everything else: **the contract** (spec, exit criteria, stakes), **the verifier** (scripts and executable checks that re-derive every gate verdict), and **the boundary** (what the agent may never do without a human). Everything that describes how a capable model should reason, plan, or check itself is depreciating scaffolding and should be deleted until measurement says otherwise. Writ already has the durable core. It is buried under the depreciating layer.

## 2. What we measured

### 2.1 Load and growth

| Measure | Value | Source |
|---|---|---|
| Shared base every invocation loads | 28,157 bytes (`system-instructions.md` 22.5 KB + `_preamble.md` 5.7 KB) | `measure-invocation.py` |
| Base share of a typical command's floor | 44–83% (median command floor 41.6 KB) | same |
| `create-spec` floor / `implement-story` ceiling | 77.8 KB / 106.8 KB (~19K / ~27K tokens, unvalidated chars/4) | same |
| Product bytes (`commands/ agents/ skills/ system-instructions.md`) | 426 KB (v0.10.0, Mar 27) → 764 KB (v0.35.0, Sep 4): **+79% in 5 months** | `git ls-tree -l` per tag |
| Imperative-rule proxy (must/never/always/only/do not…) | `system-instructions.md` 45, `_preamble.md` 16, `create-spec` 48, `implement-phase` 49, `implement-story` 43 | `rg -c` |
| Known instruction-following ceiling | all-rules compliance falls sharply by ~40 rules, near zero at ~80 | research F2 |

The base alone is at or past the first threshold before any command loads. This is a structural reason to expect silent non-compliance, independent of any single rule's merit.

### 2.2 Behavior requests vs constraints in agent prompts

| Agent | Default-capability coaching | Genuine constraints | Notes |
|---|---|---|---|
| `architecture-check-agent` | ~55% | ~45% | Restates judgment heuristics; only `readonly` and the verdict vocabulary bind |
| `documentation-agent` | ~55% | ~45% | Mermaid templates, JSDoc examples |
| `visual-qa-agent` | ~50% | ~50% | Comparison checklist a vision model does unprompted |
| `testing-agent` | ~45% | ~55% | One rare "verified, not trusted" line pointing at `test-integrity.py` |
| `coding-agent` | ~35% | ~65% | Scope law, no-supplementary-files, do-not-mark-complete, `MAX_SELF_FIX_ITERATIONS` |
| `review-agent` | ~30% | ~70% | Parse contract, severity floor, PAUSE semantics |
| `user-story-generator` | ~25% | ~75% | AC-ID grammar checked later by `ac-trace.py` |

The constraint-heavy agents are the ones the dogfooding study found load-bearing. The coaching-heavy ones are the ones the research says degrade output on Fable 5 / Opus 5.

### 2.3 Who checks each gate verdict

| Gate | Verdict source | Mechanically re-derived? |
|---|---|---|
| 0 Architecture `PROCEED/CAUTION/ABORT` | agent self-report | No |
| 0.5 Boundary map | inline LLM + skill | No ("advisory, no hard file locking") |
| 1 Implementation self-check | agent self-report | No |
| 2 Lint / typecheck / build | shell | **Yes** (`build-smoke.py`, project tools) |
| 2.5 Change surface | inline LLM + skill | No |
| 3 Review `PASS/FAIL/PAUSE` | agent self-report | No |
| 3.5 Drift severity | orchestrator + skill | No |
| 4 Tests + coverage | agent claims, script overrides | **Yes** (`test-integrity.py`) |
| 4.5 Visual QA % match | agent self-report | No |
| 5 Docs updated | agent self-report | No |
| Spec / phase completion | run claims | **Yes** (`exit-criteria.py`) |

Three of eleven. The two mechanical gates in the pipeline (2 and 4) plus exit criteria are exactly the ones the dogfooding study credits with catching severe bugs. Review — the most expensive gate — is honor-system.

### 2.4 Dead ends found (all verified on disk this session)

| Location | Problem |
|---|---|
| `commands/create-spec.md:297` | Requires `objective.md`; no command creates it; zero files by that name in the repo |
| `commands/implement-spec.md:72` | Behavior gated on `--force`; flag absent from the invocation table |
| `commands/create-spec.md:772` | Cites `loop.max_iterations`; file has no `loop:` frontmatter |
| `commands/implement-story.md:150`, `create-spec.md:770` | Mandated `escalated(...)` emit "no-op until ADR-025 Story 1"; `scripts/signal.py` and `/retro --friction` do not exist |
| `.writ/manifest.yaml` | `subagent-result-completeness`, `subagent-worktree-integration` on disk and consumed, absent from registry |
| `skills/gbrain-interop` | Zero `Read skills/…` consumers in commands or agents |
| `.writ/knowledge/` | 10 of 21 entries have single-character bullets and `related_artifacts: [".", "/", "."]` — the phase-close writeback shredded its payload |
| `verify-spec.md:765` vs `release.md:107` | "release runs checks 1–8" vs "release runs checks 1–6" |
| `status.md:266` vs `status.md:482` | Archive eligibility: "complete-family alone" vs "Complete + knowledge-evidenced" |
| `implement-story.md:70/219/231` | Gate 3 PAUSE, Gate 3.5 PAUSE, and the control-flow summary disagree on who owns the Large-drift pause and which options to present |
| `create-spec.md:26–30` vs `:174–176` | `--from-issue` mode is fully documented but absent from the Invocation table — the Goal Card promotion path is undiscoverable from the top of the file |
| `create-spec.md:579` vs `implement-spec.md:269–270` | Writers disagree on the Complete status spelling (`Complete` vs `Complete (<date>)`); detection tolerates both, the forward contract does not |
| `implement-spec.md:210–216` | Hard-codes `npx tsc --noEmit` / `npm test` in a multi-stack framework; `ship` and `release` detect runners, this step does not |
| `implement-spec.md:218` | Integration failure → "identify which story likely broke it, report to user" — no next action (retry, quarantine, abort) |
| `ship.md:434–437` vs `:635` | Step 6 attaches the audit note "once the landed commit exists" but `/ship` exits at open PR; the step cannot complete in-session and has no re-entry |
| `adapters/claude-code.md:519` | Gotcha says "change `model: haiku` to `model: sonnet`" — contradicts ADR-024's anchor-as-ceiling rule at `:138` |
| `adapters/cursor.md:50–55` | Install directory tree omits `visual-qa-agent.md` and most current commands |
| `adapters/openclaw.md:60–64`, `adapters/codex.md:32,117` | Floor row marked "unverified"; Codex copy still reads "after this platform ships" and "future specs may wire" hooks that exist as TOMLs today |

### 2.5 Decision-point load on the happy path

`create-spec`: 11 forks, 2 user gates (3 if UI). `implement-story`: 14 forks, 0 user gates. `implement-spec`: 0 user gates. `ship`: 2. The user-gate count is right — Writ is not interrupting humans needlessly. The fork count is what ADR-023's postscript already flagged: progressive disclosure "cut the floor 35.9% while adding eight decision points, five of which fire unconditionally and buy nothing."

### 2.6 Where the eval harness points

47 checks in `scripts/eval.sh`. About 44 assert facts about Writ's own markdown, scripts, and ADR literals. Three (`build-smoke`, `test-integrity`, `quality-config-audit`) exercise tools meant for user projects — but against Writ fixtures. Zero assert that a user's software does what its spec says. The harness is an excellent self-governor and not yet an outcome gate.

## 3. Diagnosis

Three mechanisms explain almost every finding.

**Mechanism 1 — behavior-request debt.** Every release of Writ since March added instruction about how the model should work, calibrated to the model of that month. Vendor guidance now says explicitly that this class of instruction "can degrade output quality" on current models and should be removed when default performance is better. Writ has no process for removing it; `/refresh-command` adds amendments (13 of 16 proposed were applied in five refreshes) and the leanness check only *notes* weight growth. The result is a base that plausibly exceeds the instruction-following ceiling and agents that spend half their prompt coaching defaults.

**Mechanism 2 — self-report gates.** Writ's design discovered the right principle once — Gate 4's "verify the claim, don't trust it" backed by `test-integrity.py` — and did not generalize it. Eight gates trust a string the agent returns. The external evidence on reviewer reliability (45% vs 68% merge rates, 56% rejection, richer prompts increasing false rejections, 80 agents endorsing a nonexistent bug) says this is the single largest quality risk in the pipeline, and the dogfooding study confirms it is where defects live.

**Mechanism 3 — growth without a governor.** The roadmap records, in its own words, "no mechanically enforced efficiency constraint as of this date." The byte goal was correctly withdrawn because bytes measure the wrong thing. But nothing replaced it, so the corpus grew 79% and drift accumulated (Section 2.4). The knowledge-ledger shredding is the sharpest instance: infrastructure fired, nobody checked the output, and half the "lessons" are noise.

## 4. What is durable and must stay

Apply the test from the research — *does this line name a fact about the environment or the human boundary, or a fact about the model?* — and Writ's core passes:

- **Contract-first discovery with pushback** (`create-spec` Plan Mode, the Prime Directive's hard constraints). No platform primitive does this. It is Writ's differentiator.
- **`exit_criteria` grammar and `exit-criteria.py`.** This is the same artifact Claude Code `/goal` and Codex goal mode consume. Writ got here first.
- **Stakes-proportional diligence** (ADR-023) and **autonomy gate classes** (ADR-022). Both are facts about the world, not the model.
- **The human production boundary** (ADR-013: never merge, never open PRs, never release under `--recommend`). Constraint, not request.
- **Worktree isolation, commit provenance, git notes, spec lifecycle and archival.** Environment facts.
- **The scripts.** `test-integrity.py`, `build-smoke.py`, `exit-criteria.py`, `ac-trace.py`, `story-deps.py`, `phase-state.py` — the part of Writ that works when the prose does not.
- **Anti-sycophancy as a mechanical check** (`check_anti_sycophancy`). The right pattern: a prose rule with a script behind it.

## 5. The plan

Framed as a roadmap candidate — **Phase 11: Contract-and-Verifier Layer** — sequenced so nothing is cut without a measurement and nothing is added without evidence. Each step names its exit criterion in Writ's grammar.

### Step 0 — Fix the dead ends (S, this week, no spec required)

Nineteen items in Section 2.4. Each is a one-commit fix or a one-line deletion. Do this before any measurement so the baseline is not contaminated by drift.

*Exit:* every path referenced in `commands/*.md` resolves or is created by a named command; `comm` between `skills/` and `.writ/manifest.yaml` is empty; zero knowledge entries with single-character bullets; the three file-pair contradictions each resolve to one statement.

### Step 1 — Baseline before any cut (M, one spec)

A fixed task set — four real stories from an installed project (yuss.app is the candidate; it has the August study as a prior) — run through the current pipeline at Fable 5.1 and GPT-6 Astra. Record per run: exit-criteria pass/fail, tokens (with a real tokenizer; `measure-invocation.py` still uses unvalidated chars/4), wall-clock, human interrupts, and gate verdict vs mechanical re-derivation where a script exists. Add it as `check_pipeline_baseline` in `eval.sh` with results committed to `.writ/eval/baselines/`.

*Exit:* a `.writ/eval/baselines/<date>-<model>.json` exists for each of two models; `measure-invocation.py` reports `token_method_validated: true`.

### Step 2 — Prune the shared base by the constraint test (M, one spec)

Line by line through `system-instructions.md` and `_preamble.md`. Each line is classified *environment fact*, *human boundary*, or *behavior request*. The first two stay. Behavior requests move to `.writ/decision-records/pruned-instructions-ledger.md` with the date and the reason, so re-adding is one commit. Re-run Step 1's baseline. Keep the cut only if exit-criteria pass rate does not fall.

Candidates, from the audit: the Judgment Principles prose, the Prose section, the Recommendation Semantics detail (keep the rule, drop the tutorial), the Skills and Model Tiers explainers (these are docs, not instructions — link them), the Startup Update Awareness procedure (move to a script or an adapter). Also the Fable 5.1 batching line goes into `adapters/`, not core.

*Exit:* `system-instructions.md` + `_preamble.md` total under 10 KB; every removed line appears in the ledger with a reason; baseline exit-criteria pass rate at or above Step 1.

### Step 3 — Mechanize the remaining gate verdicts (L, one or two specs)

Generalize Gate 4's pattern. For each self-report gate in Section 2.3, either write the script or mark the gate `verification: prose-only` in the command frontmatter so the gap is visible.

Priority order by evidence weight: **Gate 3 review** — replace general-purpose same-family review with a fresh-context evaluator whose rubric *is* the story's acceptance criteria and test results (`ac-trace.py` already maps AC to tests), with the reviewer's proposed fix executed as a counterfactual before it can block; **Gate 0 architecture** — re-derive PROCEED/CAUTION from `story-deps.py` + boundary map + changed-file count, keep ABORT as the only LLM-judged verdict; **Gate 5 docs** — a diff check that documented symbols match changed exports; **Gate 4.5 visual** — an actual pixel or DOM diff or drop the percentage. Ship the scripts to installed projects via `install.sh`; today they live only in Writ's repo.

*Exit:* at most two gates in `implement-story.md` carry `verification: prose-only`; `eval.sh` has a check per new script; installed projects receive the scripts on `update.sh`.

### Step 4 — Spec analysis before implementation (M, one spec)

The one new capability the evidence supports. At `create-spec` lock and in `verify-spec`: detect contradictory, missing, and ambiguous acceptance criteria before code exists. Phase A: an LLM-judged pass grounded in exit-criteria grammar, output as advisory findings. Phase B (only if Phase A precision is measured acceptable): structured criteria (EARS-shaped) and property-test generation for projects that have a test framework.

*Exit:* `scripts/spec-analyze.py` exists and runs at Step 2.6 of `create-spec`; findings are advisory for one release; precision on the Step 1 task set is recorded before any promotion to blocking.

### Step 5 — Make the pipeline an escalation, not the default (L, one spec, after Steps 2–3)

Default `implement-story`: one frontier agent in a worktree with spec, exit criteria, tests, and the boundary; a fresh-context rubric evaluator; stall and iteration caps. The five-agent pipeline with structured-disagreement review becomes the path for stories ADR-023 triage rates high-stakes, or when the evaluator fails twice. Retire self-critique stages (Gate 1 self-check as a gate; keep it as the agent's own habit). Agent prompts are rewritten to constraints only (target: the `user-story-generator` ratio, ~75% constraint).

*Exit:* `implement-story --default` spawns at most two subagents; `--full-pipeline` is explicit; baseline pass rate on the Step 1 set does not fall; per-story token cost falls.

### Step 6 — Emit contracts the platforms can run (S–M, one spec)

`create-goal` and `implement-phase` emit `GOAL.md` / `VERIFY.md`-shaped files that Claude Code `/goal` and Codex goal mode consume directly. Adapters own the invocation. ADR-013's boundary stays a hard constraint in the emitted contract. `implement-phase --recommend` keeps working but is no longer the only loop runner.

*Exit:* a Goal Card round-trips into a `/goal` invocation on Claude Code with no manual editing; the emitted contract contains the ADR-013 boundary verbatim.

### Governor (cross-cutting)

Replace the withdrawn byte goal with two mechanical checks that measure what the postscript said matters: **decisions per happy-path run** (count forks in each pipeline command; fail on growth without a `## Decision Budget` justification) and **verdict provenance** (fail if a gate verdict is added without either a script or a `verification: prose-only` marker). Both are `eval.sh` checks; neither is a byte count.

## 6. What this plan does not do

- It does not delete the Prime Directive. The hard constraints pass the test. Only the surrounding tutorial goes.
- It does not remove the multi-agent pipeline. It demotes it from default to escalation, on measurement.
- It does not chase per-model prompt tuning. One batching line for Fable 5.1 in the adapters is the whole model-specific surface.
- It does not rewrite Writ around `/goal`. Platforms diverge; Writ emits the contract and keeps the discovery flow no platform offers.
- It does not set a byte target. ADR-023 was right; the governor counts decisions and verdict provenance instead.

## 7. Open questions for the user

1. **Baseline project.** yuss.app has the August study as prior data. Is it available for a four-story task set, or should the baseline use Writ's own repo (weaker, since Writ's stories are markdown)?
2. **Appetite for Step 5.** Demoting the five-agent pipeline is the most visible change to how Writ *feels*. Steps 0–4 stand on their own if Step 5 is deferred.
3. **Astra access.** Step 1 assumes both models are runnable from this workspace. If only one is, the baseline is single-model and says so.

## 8. Next commands

- `/create-goal` — a Goal Card for the mission (this session, next).
- Step 0 fixes: direct edits, no spec.
- `/create-spec "pipeline baseline harness"` for Step 1; `/create-adr` to record the constraint-test pruning policy before Step 2 begins.
- `/plan-product` to promote Phase 11 into `roadmap.md` once the user confirms Section 7.

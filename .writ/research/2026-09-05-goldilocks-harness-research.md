# The Goldilocks Harness: What Frontier Models (Sep 2026) Still Need From a Workflow Framework

> **Date:** 2026-09-05
> **Prepared for:** Writ product direction — the "is Writ tuned for Fable 5.1 / GPT-6 Astra" review
> **Decision this informs:** Which parts of Writ to cut, keep, harden, or add for the next roadmap phase
> **Depth:** Full 4-phase (architecture-level, hard to reverse once shipped to installed projects)

## Research Questions

1. What do the September 2026 frontier models (Claude Fable 5.1, GPT-6 Astra) do natively that Writ currently instructs them to do — and where does that instruction now cost quality?
2. Which classes of harness scaffolding survive model improvement, and which classes depreciate? Is there a test that tells them apart?
3. What is the empirical evidence on prompt-level guarantees versus mechanical guarantees (scripts, tests, executable specs) for correctness in agentic pipelines?
4. What do the leading spec-driven frameworks (Kiro, Spec Kit, OpenSpec, BMAD, Tessl) and the native platform primitives (`/goal`, `/loop`, GOAL.md/VERIFY.md) do that Writ does not, and vice versa?
5. Do AI review agents earn their place in a pipeline, and under what conditions?
6. Given all of the above: where is Writ over-prescriptive, where is it under-specified, and what would a "Goldilocks" framework look like?

## Executive Summary

**Frontier models in September 2026 have crossed the line where most behavioral instruction is net-negative.** Anthropic's own Fable 5 prompting guide says prompts and skills developed for prior models "are often too prescriptive for Claude Fable 5 and can degrade output quality." Claude Code removed roughly 80% of its system prompt for Opus 5 with no measurable loss. Anthropic's long-running-agent harness lost its sprint construct and context-reset machinery between Opus 4.5 and 4.6 because the model no longer needed them. Every one of these findings points the same direction: **constraints keep working as models improve; behavior requests compound and go harmful.** Instruction-following research puts the ceiling for all-rules compliance around 40 simultaneous rules, falling to zero near 80. Writ's shared base (`system-instructions.md` + `_preamble.md`) is 28 KB and by a rough modal-verb count carries ~60 imperative rules before any command loads; `create-spec` adds ~48 more.

**At the same time, the case for mechanical verification has gotten stronger, not weaker.** Writ's own August dogfooding study found prompt-level guarantees silently failed while script-level ones held. The wider literature confirms it: AI review without an executable reference is structurally circular (same training distribution reviewing itself); reviewer-only PRs merge at 45% versus 68% for human-reviewed; 56% of CodeRabbit comments are rejected; richer reviewer prompts *increase* false rejections; 80+ agents unanimously endorsed a nonexistent OpenSSL vulnerability that one empirical test killed. Kiro's requirements analysis found ~60% of first-draft specs contain contradictions, gaps, or ambiguities detectable by an SMT solver before any code exists. The winning architecture across sources is the same: **specification first, deterministic verification second, AI judgment scoped to the residual.**

**Recommendation: Writ should become a contract-and-verifier layer, not a behavior layer.** Concretely: (1) cut the shared behavioral base to the constraints that still bind (safety, scope, the human production boundary), and remove every instruction that tells a frontier model *how to think or verify*; (2) move every remaining quality guarantee from prose to a script or an executable check, and treat any prose-only guarantee as a known gap; (3) add pre-implementation spec analysis (contradiction/gap/ambiguity detection) as the one new capability the evidence supports; (4) reposition `implement-story`'s five-agent pipeline as an *opt-in escalation for high-stakes stories*, defaulting to a single frontier agent running against exit criteria with a fresh-context verifier — the configuration both Anthropic's and OpenAI's guidance now favors. The alternative of continuing to add per-model tuning is rejected: the evidence says the tuning surface shrinks every release, and a framework that grows 79% in five months while models grow more capable is aimed at the wrong target.

## Key Findings

### F1. The models: what changed between "prior models" and Fable 5.1 / GPT-6 Astra

**Verified facts (primary sources):**

- Claude Fable 5.1 released 2026-09-01. Anthropic: "sets a new standard on coding, knowledge work, and long-running problem-solving tasks." Cursor: "especially skilled at verifying its own work, allowing it to take on difficult coding tasks from start to finish." A customer quote reports a 38-hour unattended orchestration run. AWS: "if it gets stuck it says so, and it is less likely to disable a failing test to pass." Cache reads are 75% cheaper ($0.25/MTok), which cuts the cost of long agentic sessions by 25–45%. 1M context, 128K output, adaptive thinking always on, per-message effort switching without cache invalidation. ([Anthropic announcement](https://www.anthropic.com/claude-fable-and-mythos-5-1), [What's new](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1), [Overview](https://platform.claude.com/docs/en/models/fable-5-1/overview), [AWS](https://aws.amazon.com/blogs/machine-learning/introducing-claude-fable-5-1-on-aws/))
- GPT-6 Astra released 2026-09-03/05. OpenAI: "best model for software engineering to date"; Terminal-Bench 4.0 57.9% vs Fable 5.1's 55.8%; ~65% fewer output tokens than Opus 5 on Agents' Last Exam. Codex gains cross-context-window notes and searchable earlier windows instead of lossy compaction. GitHub Copilot: "plans and validates as it goes, batches diagnosis with verification, and independently confirms its results before declaring a task done." First OpenAI model to hit its "critical cybersecurity capability threshold." ([OpenAI](https://openai.com/index/gpt-6-astra/), [GitHub Changelog](https://github.blog/changelog/2026-09-04-gpt-6-astra-is-generally-available-in-github-copilot/), [The Verge](https://www.theverge.com/ai-artificial-intelligence/989601/openai-gpt-6-astra-release))
- Both vendors describe the same three native behaviors: **plan-then-act, self-verify before declaring done, and persist state across long sessions.** These are the three behaviors Writ's `implement-story` pipeline was built to *impose*.

**One counter-signal worth keeping:** Fable 5.1's parallel tool calling is *more variable* than Fable 5 — it may serialize independent reads unless told to batch. Anthropic recommends a one-line batching instruction. This is a legitimate, small, model-specific instruction — the kind that belongs in an adapter, not in the framework core. ([What's new](https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1))

**Implication for Writ:** Any instruction that tells the model to plan, verify, or checkpoint is now redundant at best. Redundant is not free: see F2.

### F2. Instruction compounding: redundant behavior requests are actively harmful

- **Anthropic, Fable 5 prompting guide:** "Skills developed for prior models are often too prescriptive for Claude Fable 5 and can degrade output quality. Review and consider removing older instructions if default performance is better." Same guide: fresh-context verifier subagents "tend to outperform self-critique," and a single "audit each claim against a tool result" instruction nearly eliminated fabricated status reports. ([Prompting Claude Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5))
- **Anthropic, Opus 5 prompting guide (summarized):** "If your prompt contains explicit verification instructions... remove them. The same applies to legacy harness scaffolding that adds separate verification steps." Stay-in-scope constraints keep working; behavior requests compound. ([XiaoHu summary](https://best.xiaohu.ai/en/article/opus5-prompting-guide/))
- **Claude Code shrank its system prompt ~80%** for Opus 5 with no measurable regression. Boris Cherny's guidance: "delete your CLAUDE.md every 6 months"; a stripped `SIMPLE=1` variant "is slightly more intelligent without prompts." What remains in the harness is "safety and permissions and static analysis and UI." ([Howardism, Harness Shrinkage](https://www.howardism.dev/articles/harness-shrinkage-as-models-improve))
- **The mechanism:** an instruction that tells a model to do something it already does natively is *additive* — it pushes the behavior past its useful point. Documented for self-verification (over-verification loops, "Unproductive Self-Verification") and generalized as "Instruction Compounding." ([Howardism](https://www.howardism.dev/articles/unproductive-self-verification), [Howardism](https://www.howardism.dev/articles/instruction-compounding))
- **Instruction-count ceiling:** an ablation across frontier models found all-rules compliance falls steeply by ~40 simultaneous rules and reaches zero near 80 (cited in Harness Shrinkage). Writ's base load alone plausibly exceeds the first threshold.
- **Diagnostic test for what survives ([Howardism, What Scaffolding Survives](https://www.howardism.dev/articles/what-scaffolding-survives-model-improvement)):** *Constraints* (don't touch X, stay in scope, never push to main) survive because they encode facts about the environment the model cannot infer. *Behavior requests* (think step by step, verify your work, be thorough) depreciate because they encode facts about the model's weaknesses, and those change every release. **A line that names a fact about the world is durable; a line that names a fact about the model is not.**

**Implication for Writ:** Apply the constraint/behavior-request test line by line to `system-instructions.md`, `_preamble.md`, and every agent prompt. The Prime Directive's *hard constraints* ("never confirm without verifying," "never reverse a position without new evidence") pass as constraints. Much of the surrounding text — verification stage instructions, prose-style rules, "match confidence to evidence" — is behavior request and should be measured against default performance before it is kept.

### F3. Harness components encode assumptions about model weakness — and Anthropic already pruned theirs

Anthropic's harness-design post (March 2026) is the closest thing to a controlled study of harness shrinkage:

- With Opus 4.5 the long-running harness needed a **sprint construct** (bounded task chunks) and **context resets**. With Opus 4.6 both were removed: the model managed its own context and "removing the context reset... made it 'more coherent, not less.'"
- What survived: the **planner** (because it decomposes the *problem*, a fact about the world) and the **evaluator** (a fresh-context judge with a rubric). The post's central sentence: "every component encodes an assumption about what the model can't do" — and the evaluator's value "depends on where the task sits relative to the model's capability boundary."
- Their evaluator did not tell the generator *how* to fix; it reported *what* was wrong against a rubric, and a fresh generator context did the fix. ([Anthropic, Harness design for long-running apps](https://www.anthropic.com/engineering/harness-design-long-running-apps); earlier [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents))

The "Harness Anchor" paper formalizes the failure side: under a given agent regime, one dominant mechanism repeatedly pushes the loop toward the same failure class; the fix is to identify and remove *that* anchor rather than add compensating instructions. ([arXiv 2609.00006](https://arxiv.org/abs/2609.00006))

**Implication for Writ:** `implement-story`'s twelve stages, five subagents, and eleven skill loads each encode an assumption. Some (worktree isolation, commit provenance, exit-criteria checking) are facts about the world. Others (context slicing per agent, structured "What Was Built" hand-offs designed for models that lost the plot, three-iteration review loops) were built for a capability boundary that has moved. The roadmap already recorded one such case: progressive-disclosure extraction cut `implement-story`'s byte floor by 35.9% "while adding eight decision points, of which five fire unconditionally on every run and buy nothing."

### F4. Context files help efficiency marginally and correctness not at all

Two independent studies of AGENTS.md / CLAUDE.md-style context files:

- **ETH SRI, ICLR 2026 (Gloaguen et al.):** repository-level context files do not improve task correctness; LLM-generated ones can *reduce* it; modest gains are in exploration cost only. ([arXiv 2602.11988](https://arxiv.org/html/2602.11988v1), [SRI Lab](https://www.sri.inf.ethz.ch/publications/gloaguen2026agentsmd))
- **288-run two-agent ablation on real repositories (July 2026):** same conclusion — efficiency gains, no correctness gains; the value is in *environment facts* the agent cannot discover cheaply (build commands, test entrypoints, where things live). ([arXiv 2607.27250](https://arxiv.org/abs/2607.27250), [summary](https://codex.danielvaughan.com/2026/08/06/do-context-files-help-coding-agents-agents-md-ablation-study-codex-cli-correctness-vs-efficiency/))

**Implication for Writ:** The correctness lever is not in the instruction files. It is in specs, tests, and checks. Writ's `CLAUDE.md`/`AGENTS.md` and the `writ.mdc` rule should be environment facts (paths, commands, boundaries), not personality or process.

### F5. Prompt-level guarantees fail silently; mechanical ones hold

- **Writ's own evidence (2026-08-14 dogfooding study of yuss.app):** "Prompt-level guarantees silently failed, mechanical ones held. Where Writ has no gate, defects exist; where it has one, they don't." Degradation appeared everywhere no command routinely touched. (`.writ/research/2026-08-14-writ-dogfooding-quality-assessment-research.md`)
- **SWE-Gate (Sep 2026):** of 644 agent repairs that passed functional tests, 221 (34%) violated review-derived acceptance constraints. Functional tests alone overstate completion; *constraints* must be checkable too. ([arXiv 2609.04167](https://arxiv.org/abs/2609.04167))
- **Refute-or-Promote (31-day defect-discovery campaign):** 80+ agents, including dedicated adversarial reviewers, unanimously endorsed a Bleichenbacher padding oracle in OpenSSL CMS that did not exist. "It was killed only by a single empirical test, motivating the mandatory empirical gate." ([arXiv 2604.19049](https://arxiv.org/pdf/2604.19049))
- **Kiro Requirements Analysis (Aug 2026):** across 35 projects and ~1,400 acceptance criteria, ~60% of first-draft requirement sets contained a contradiction, gap, or ambiguity detectable by SMT-solver analysis before code was written. EARS-notation structure plus property-based tests close the loop from requirement to executable check. ([Kiro blog](https://kiro.dev/blog/deep-spec-analysis/), [Keith Hodo](https://keithhodo.dev/posts/requirements-analysis-agentic-clis/), [GeekWire](https://www.geekwire.com/2026/aws-targets-ai-slop-with-new-spec-check-in-kiro-coding-tool-amid-scrutiny-of-agent-reliability/), [byteiota](https://byteiota.com/aws-kiro-requirements-analysis-formal-verification-for-ai-coding-agents/))

**Implication for Writ:** Writ has 48 `eval.sh` checks and 24 scripts — this is its real moat, and the dogfooding study says it is the part that works. But the checks guard *Writ's own repo*; installed projects get the prose gates. Writ's `check_anti_sycophancy` is a mechanical check of a prose rule, which is the right pattern and should be the template for everything else. The missing piece the evidence supports is **spec analysis before implementation** — Writ has `exit-criteria.py` for grammar and `ac-trace.py` for coverage, but nothing checks that a spec's acceptance criteria are mutually consistent and complete.

### F6. AI review is circular without an external reference — and expensive when it isn't scoped

- **Structural argument (Zietsman, Mar 2026):** generator and reviewer from the same family share training distribution and blind spots; "the review checks code against itself, not against intent." Correlated estimators do not cancel error, they consolidate it (popularity trap; homogenisation trap in LLM-generated tests). Proposed architecture: "specifications first, deterministic verification pipeline second, AI review only for the structural and architectural residual." ([arXiv 2603.25773](https://arxiv.org/pdf/2603.25773))
- **Outcome data:** CRA-only PRs merge at 45.2% vs 68.4% human-only; 60% of abandoned CRA-only PRs had 0–30% signal ratio; 12 of 13 review agents average below 60% signal. Recommendation: narrow, specific checks over general-purpose review. ([arXiv 2604.03196](https://www.arxiv.org/pdf/2604.03196)) CodeRabbit: 56.3% of 31,073 review comments rejected, 43% of rejections were false positives. ([arXiv 2607.03316](https://www.emergentmind.com/papers/2607.03316))
- **Over-correction is prompt-induced:** richer reviewer prompts (explain, propose fix) cut false acceptances but *more than doubled* false rejections of correct code; rationales were "not consistently trustworthy." Fix: treat the reviewer's proposed patch as an executable counterfactual and test it. ([arXiv 2603.00539](https://arxiv.org/pdf/2603.00539))
- **What does work:** minimal, *structured disagreement* — a reviewer and a critic forced to classify disagreement as evidence-backed or concern-only, with code citations required. Naive cooperation produced "false consensus." Three agents beat five. Even so, "for easy tasks, the review loop may be wasted computation." ([arXiv 2608.18167](https://arxiv.org/html/2608.18167))
- **Fresh-context evaluator with a rubric** is the configuration Anthropic kept (F3) and the Fable 5 guide recommends (F2).

**Implication for Writ:** The `review-agent` (PASS/FAIL, max 3 iterations) is a general-purpose same-family reviewer reading the same artifact — the configuration the evidence rates worst. It is also load-bearing in the dogfooding study ("gates caught real, severe bugs"), so the answer is not removal but repositioning: rubric-driven fresh-context evaluation against the *spec's exit criteria and tests*, with structured disagreement, scoped to the residual mechanical checks cannot reach, and gated on stakes (ADR-023 already has the triage vocabulary).

### F7. Native loop primitives now exist; the platform owns the loop, the framework owns the contract

- **Claude Code `/goal`:** sets a completion condition; the agent works until met, impossible, or errored; a *separate evaluator model* judges completion. ([Claude Code docs](https://code.claude.com/docs/en/goal), [Jeremy Watt](https://neonwatty.com/posts/agent-loops-in-claude-code/))
- **Codex goal mode:** same shape with explicit cross-session state and a GOAL.md / VERIFY.md / PROGRESS.md convention — the verification is a file the agent cannot rewrite while running. ([Daniel Vaughan](https://codex.danielvaughan.com/2026/07/06/codex-cli-goal-mode-long-running-autonomous-agents-verification-trust-architecture/), [follow-up on token budgets](https://codex.danielvaughan.com/2026/07/23/codex-cli-goal-mode-long-horizon-autonomous-workflows-ralph-loop-token-budgets/))
- **Loop engineering** (Osmani): design the *system that prompts the agent* — trigger, topology, verifier, stop rule — rather than the prompt. "Models depreciate, scaffolding compounds" only when the scaffolding is a verifier or a boundary, not a behavior request. ([Loop Engineering](https://addyosmani.com/blog/loop-engineering/), [Practical Loop Engineering](https://addyosmani.com/blog/practical-loop-engineering/), [Agent Harness Engineering](https://addyosmani.com/blog/agent-harness-engineering/), [fryga](https://fryga.io/blog/the-harness-is-the-product))
- **METR:** 50%-time-horizons for frontier models are now in the multi-hour range; measurements above ~16 hours are unreliable with current suites. The bottleneck is no longer "can the model sustain the task" but "can anyone check the result." ([METR](https://metr.org/time-horizons/))

**Implication for Writ:** Writ's `create-goal` (Goal Card with DONE WHEN in exit-criteria grammar) and `exit_criteria` frontmatter are exactly the artifacts these primitives consume. Writ should *emit* GOAL.md/VERIFY.md-shaped contracts and let `/goal` run them, rather than maintaining its own loop runners (`implement-phase --recommend` re-implements what the platforms now ship). The roadmap's ADR-013 boundary — never merge, never release — stays; it is a constraint, not a behavior request.

### F8. Spec-driven frameworks converge on the same shape; the differentiator is analysis and verification, not ceremony

- Spec Kit, OpenSpec, BMAD, Kiro, Tessl all do intent → spec → plan → tasks → implement. Critiques converge: heavy ceremony that "reads like a waterfall process wearing an agentic costume," specs that drift from code, and enterprises rejecting tools that cannot integrate with existing requirements systems. ([Jia Wei Ng](https://jiaweing.com/blog/the-state-of-spec-driven-development), [Martinelli](https://martinelli.ch/why-spec-driven-development-tools-fail-in-the-enterprise/), [braingrid](https://www.braingrid.ai/blog/stop-shopping-for-spec-driven-development-tools), [Levelop](https://levelop.dev/blog/spec-driven-development-tools-compared), [DEV](https://dev.to/willtorber/spec-kit-vs-bmad-vs-openspec-choosing-an-sdd-framework-in-2026-d3j))
- **Kiro is the outlier** because it added a *verifier* to the spec stage (F5) and property-based tests from requirements. That is the only feature in the field with a published quantitative effect.
- Writ's differentiators relative to this field, per its mission doc: contract-first with pushback (Prime Directive), stakes-proportional diligence (ADR-023), observable autonomy with a hard production boundary (ADR-013), spec lifecycle and archival, git-native provenance. None of these are ceremony; all survive the F2 test. Writ's *disadvantage* is that it delivers them as ~760 KB of prose across 33 commands, 7 agents, 17 skills.

## Options Analysis

### Option A — Behavioral pruning + mechanical hardening + spec analysis (recommended)

Cut the shared base to constraints; move guarantees to scripts; add a spec-analysis check; make the multi-agent pipeline an escalation path rather than the default.

- **Pros:** Directly addresses every finding. Aligns Writ with vendor guidance for the models it targets. Reuses Writ's real asset (48 checks, 24 scripts, exit-criteria grammar). Lower per-invocation cost.
- **Cons:** Requires measurement discipline — pruning without a baseline is guesswork. Some pruned instructions will turn out to have been load-bearing; a reversible, per-line audit trail is required. Reduces the surface that makes Writ *look* thorough.
- **Effort:** M–L across two or three specs. **Risk:** Medium; mitigated by baseline-before-cut and by keeping every removed line in a dated ledger.

### Option B — Per-model tuning (adapters carry model-specific prompt variants)

Keep the framework as is; add Fable 5.1 and Astra sections to adapters with tuned instructions.

- **Pros:** Small, incremental, no architectural change.
- **Cons:** The evidence says the tuning surface shrinks every release and that the harmful direction is *too much* instruction, not the wrong instruction. Tuning multiplies the maintenance surface across model × platform. It treats the symptom.
- **Effort:** S. **Risk:** Low short-term, high long-term (harness debt compounds).

### Option C — Full rewrite around native `/goal` primitives

Reduce Writ to Goal Cards + exit criteria + scripts; delete the pipeline commands; let the platforms run loops.

- **Pros:** Maximal alignment with F7. Smallest possible framework.
- **Cons:** Abandons working, evidence-backed gates (dogfooding study). Breaks every installed project. Assumes platform primitives are stable and portable across Cursor/Claude Code/Codex/OpenClaw; today they are not. Throws away the contract-first discovery flow, which is Writ's actual differentiator and which no platform primitive provides.
- **Effort:** L. **Risk:** High.

### Option D — Status quo, monitor

- **Pros:** Zero cost now.
- **Cons:** Product grew 79% by bytes in five months while the target models got more capable and more instruction-sensitive. The roadmap itself records "no mechanically enforced efficiency constraint as of this date." Drift will continue.

## Recommendation

**Primary: Option A.** Sequence it so each step has a mechanical measurement before and after:

1. **Baseline first.** Run a small fixed task set (three or four real stories from an installed project) through the current pipeline at Fable 5.1 and Astra, recording pass/fail on exit criteria, wall-clock, tokens, and human-interrupt count. Without this, every subsequent cut is opinion. The eval harness already exists; this is a new check, not a new system.
2. **Prune the shared base by the constraint/behavior-request test.** Target: every line in `system-instructions.md` and `_preamble.md` either names a fact about the environment or the human boundary, or it is removed into a dated ledger. Success is measured against step 1, not by byte count (the roadmap's byte-goal postscript is right that bytes measure the wrong thing; the right thing is decisions-per-run and exit-criteria pass rate).
3. **Mechanize the remaining prose guarantees.** Each guarantee in a command that is checked only by the model reading a sentence gets a script or is marked `unverified` in frontmatter. Ship the checks to installed projects, not just to Writ's repo.
4. **Add spec analysis.** One script, run at `create-spec` lock and `verify-spec`: acceptance-criteria contradiction, gap, and ambiguity detection. Start with an LLM-judged pass grounded in exit-criteria grammar; graduate to structured (EARS-like) criteria and property tests where the project has them. This is the single new capability the evidence supports.
5. **Make the multi-agent pipeline an escalation, not the default.** Default `implement-story`: one frontier agent, worktree, spec + exit criteria + tests, fresh-context rubric evaluator, stall/iteration caps. Escalate to structured-disagreement review (reviewer + critic with required code citations) only when ADR-023 stakes triage says the story is high-stakes or the evaluator fails twice. Retire self-critique stages.
6. **Emit, don't run, loops.** Have `create-goal` and `implement-phase` produce GOAL.md/VERIFY.md-shaped contracts consumable by Claude Code `/goal` and Codex goal mode, keeping ADR-013's production boundary as a hard constraint.

**Alternatives if A is infeasible:** B as a stopgap only if a release deadline forces it, with an explicit sunset. C is the right long-term shape only if platform loop primitives converge on a portable contract, which should be re-checked in six months.

## Risks & Mitigation

| Risk | Mitigation |
|---|---|
| Pruning removes a line that was silently load-bearing | Baseline task set before any cut; every removed line goes to a dated ledger with the reason; re-add is one commit |
| Fresh-context evaluator inherits reviewer over-correction bias (F6) | Rubric is the spec's exit criteria and test results, not "find problems"; the evaluator's proposed fix is executed as a counterfactual before it can block |
| Spec analysis produces its own false positives and becomes a new gate users route around | Ship as advisory for one release; promote to blocking only on measured precision |
| Native `/goal` primitives diverge across platforms | Writ emits the contract file; adapters own the invocation; the contract stays platform-neutral |
| The team reads "prune" as "delete the Prime Directive" | The hard constraints pass the F2 test and stay; only behavior requests are candidates |
| Fable 5.1 serializes tool calls (F1 counter-signal) | One-line batching instruction in `adapters/cursor.md` and `adapters/claude-code.md` — a model-specific fact, kept out of core |

## Further Research

- **Measured, not estimated, tokens.** `measure-invocation.py` still uses an unvalidated chars/4 ratio. A real tokenizer pass is a prerequisite for the baseline in Recommendation step 1.
- **Does structured disagreement hold at Fable 5.1 / Astra?** The Adversarial Review results predate both models; the false-consensus failure may be weaker or stronger.
- **Where is the capability boundary for the evaluator?** Anthropic says evaluator value depends on task position relative to the boundary. A per-stakes evaluator on/off experiment on the baseline set would answer this for Writ's task class.
- **Property-based tests from acceptance criteria** — Kiro's approach depends on EARS-shaped requirements. Whether Writ's exit-criteria grammar is close enough to generate property tests without a second notation is untested.

## Sources

**Models**
- Anthropic, Introducing Claude Fable 5.1 and Claude Mythos 5.1 — https://www.anthropic.com/claude-fable-and-mythos-5-1
- Anthropic, What's new in Claude Fable 5.1 — https://platform.claude.com/docs/en/models/fable-5-1/whats-new-fable-5-1
- Anthropic, Claude Fable 5.1 overview — https://platform.claude.com/docs/en/models/fable-5-1/overview
- AWS, Introducing Claude Fable 5.1 on AWS — https://aws.amazon.com/blogs/machine-learning/introducing-claude-fable-5-1-on-aws/
- OpenAI, GPT-6 Astra: A new generation of intelligence — https://openai.com/index/gpt-6-astra/
- OpenAI, GPT-6 Astra model docs — https://developers.openai.com/api/docs/models/gpt-6-astra
- GitHub Changelog, GPT-6 Astra GA in Copilot — https://github.blog/changelog/2026-09-04-gpt-6-astra-is-generally-available-in-github-copilot/
- The Verge, OpenAI's next big AI model — https://www.theverge.com/ai-artificial-intelligence/989601/openai-gpt-6-astra-release
- METR, Task-Completion Time Horizons — https://metr.org/time-horizons/

**Prompting and harness shrinkage**
- Anthropic, Prompting Claude Fable 5 — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5
- Anthropic Opus 5 prompting guide (summary) — https://best.xiaohu.ai/en/article/opus5-prompting-guide/
- Anthropic, Harness design for long-running apps — https://www.anthropic.com/engineering/harness-design-long-running-apps
- Anthropic, Effective harnesses for long-running agents — https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- Howardism, Harness Shrinkage as Models Improve — https://www.howardism.dev/articles/harness-shrinkage-as-models-improve
- Howardism, What Scaffolding Survives Model Improvement — https://www.howardism.dev/articles/what-scaffolding-survives-model-improvement
- Howardism, Instruction Compounding — https://www.howardism.dev/articles/instruction-compounding
- Howardism, Unproductive Self-Verification — https://www.howardism.dev/articles/unproductive-self-verification
- Finding the Harness Anchor for AI Agents — https://arxiv.org/abs/2609.00006
- Claude Code issue #60744, verification lane boundary — https://github.com/anthropics/claude-code/issues/60744

**Context files**
- Gloaguen et al., Evaluating AGENTS.md (ICLR 2026) — https://arxiv.org/html/2602.11988v1 ; https://www.sri.inf.ethz.ch/publications/gloaguen2026agentsmd
- Do Context Files Help Coding Agents? 288-run ablation — https://arxiv.org/abs/2607.27250 ; https://codex.danielvaughan.com/2026/08/06/do-context-files-help-coding-agents-agents-md-ablation-study-codex-cli-correctness-vs-efficiency/

**Verification and review**
- Writ dogfooding quality assessment (internal) — `.writ/research/2026-08-14-writ-dogfooding-quality-assessment-research.md`
- SWE-Gate — https://arxiv.org/abs/2609.04167
- Refute-or-Promote — https://arxiv.org/pdf/2604.19049
- Zietsman, executable specs vs circular AI review — https://arxiv.org/pdf/2603.25773
- Adversarial Review: structured disagreement — https://arxiv.org/html/2608.18167
- Jin & Chen, over-correction in LLM code judgment — https://arxiv.org/pdf/2603.00539
- Code review agents and PR outcomes (AIDev) — https://www.arxiv.org/pdf/2604.03196
- Is Agentic Review Helpful? CodeRabbit study — https://www.emergentmind.com/papers/2607.03316

**Spec-driven development and formal analysis**
- Kiro, Deep spec analysis — https://kiro.dev/blog/deep-spec-analysis/
- Keith Hodo, Red to Green Proves Nothing — https://keithhodo.dev/posts/requirements-analysis-agentic-clis/
- GeekWire, AWS targets AI slop — https://www.geekwire.com/2026/aws-targets-ai-slop-with-new-spec-check-in-kiro-coding-tool-amid-scrutiny-of-agent-reliability/
- byteiota, Kiro Requirements Analysis — https://byteiota.com/aws-kiro-requirements-analysis-formal-verification-for-ai-coding-agents/
- Jia Wei Ng, The state of spec-driven development — https://jiaweing.com/blog/the-state-of-spec-driven-development
- Martinelli, Why SDD tools fail in the enterprise — https://martinelli.ch/why-spec-driven-development-tools-fail-in-the-enterprise/
- braingrid, Stop shopping for SDD tools — https://www.braingrid.ai/blog/stop-shopping-for-spec-driven-development-tools
- Levelop, Spec Kit vs Kiro vs OpenSpec — https://levelop.dev/blog/spec-driven-development-tools-compared
- DEV, Spec Kit vs BMAD vs OpenSpec — https://dev.to/willtorber/spec-kit-vs-bmad-vs-openspec-choosing-an-sdd-framework-in-2026-d3j

**Loop engineering and native primitives**
- Claude Code, /goal — https://code.claude.com/docs/en/goal
- Jeremy Watt, Claude Code agent loops — https://neonwatty.com/posts/agent-loops-in-claude-code/
- Daniel Vaughan, Codex goal mode and the verification problem — https://codex.danielvaughan.com/2026/07/06/codex-cli-goal-mode-long-running-autonomous-agents-verification-trust-architecture/
- Daniel Vaughan, Codex goal mode: long-horizon workflows — https://codex.danielvaughan.com/2026/07/23/codex-cli-goal-mode-long-horizon-autonomous-workflows-ralph-loop-token-budgets/
- Addy Osmani, Loop Engineering — https://addyosmani.com/blog/loop-engineering/
- Addy Osmani, Practical Loop Engineering — https://addyosmani.com/blog/practical-loop-engineering/
- Addy Osmani, Agent Harness Engineering — https://addyosmani.com/blog/agent-harness-engineering/
- fryga, The harness is the product — https://fryga.io/blog/the-harness-is-the-product

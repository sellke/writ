# Spec: Progressive Disclosure — `implement-phase`

> **Status:** Closed — Not Implemented (measured evidence, 2026-08-12)
> **Owner:** @AdamSellke
> **Created:** 2026-08-12
> **Dependencies:** [2026-08-12-disclosure-implement-story]
> **Origin:** ADR-021's progressive-disclosure programme, sixth and last of the six one-file-per-spec extractions. Sequenced last deliberately: this spec is executed **by the command it rewrites**. The file was re-measured on 2026-08-12 with `scripts/measure-invocation.py` — 29,136 bytes / 321 lines, **90.77 bytes per line, the densest command in the repo** and 2.63× the lightest (`migrate.md`, 34.48 B/line). It ranks **4th of 31 by floor load** (54,096 bytes) while sitting **79 lines under ADR-021's proposed 400-line cap**, which is the concrete evidence behind the 2026-08-12 maintainer decision to make the byte budget binding and demote the line cap to a secondary tripwire. Governed by [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md) and [ADR-020](../../decision-records/adr-020-component-contract.md).

> **Not implemented — closed 2026-08-12 on measured evidence.** The pilot
> (`2026-08-12-disclosure-implement-story`) shipped and measured progressive
> disclosure's real cost: **~1,017 bytes of irreducible overhead per extracted
> skill** (27,872 B removed from the command, 36,005 B added as 8 skills). Its
> worst path regressed **+9.7%** against a projected +4.1% — the projection
> underestimated overhead by 2.3x, and every spec in this set was projected the
> same way. Per this spec set's own Business Rule 1, a pilot regression is *"a
> signal about the approach rather than a per-file exemption."*
>
> The saving tracks how genuinely branchy a command is, not how large its file
> is. Selecting by file size was the error. This spec's own measured common-path
> payoff did not justify ~5 more skills of overhead on a command that is either a
> sequential pipeline or already near break-even.
>
> The contract, extraction plan, pinned-literal inventory and measurement method
> here are **kept intact and unexecuted** — they are the design record if the
> economics change (a materially smaller skill preamble, or a harness that loads
> lazily by default). Nothing here was wrong; the premise underneath it was.

## Contract (Locked)

**Deliverable:** `commands/implement-phase.md` — 29,136 bytes / 321 lines — reduced to a thin contract with its per-phase procedural detail extracted to `skills/<name>/SKILL.md`, loaded on demand via `required_skills:`.

**Must include:** The thin contract retains only what [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md) permits — frontmatter contract (ADR-020), `## Overview`, `## Invocation` table, the phase list with gate names, `## Completion`, `## References`. Skills authored through `/new-skill` (born `status: candidate`, lint-clean). **Follow the extraction pattern and skill-naming convention established by the dependency spec `2026-08-12-disclosure-implement-story`.**

**Hardest constraint:** This spec is executed **by the command it rewrites**. `/implement-phase` spawns the lane subagent that edits `commands/implement-phase.md` while the orchestrator is running from that same file. It is deliberately sequenced last among the six disclosure specs for this reason. The rewritten file must remain a complete, self-sufficient instruction set at every commit — a half-extracted state that loses the lane/merge/quarantine contract would break the very run performing the extraction.

## Approved Scope Changes

### 2026-08-12 — the loading mechanism changes from `required_skills:` to inline `Read`

**The escalation this spec raised at contract time was verified and accepted by the maintainer.** The `## Contract (Locked)` block above is preserved **verbatim** and is not edited; this section is the dated record of the approved change, and it governs where the two differ.

**What was escalated.** § Technical Concerns recorded that `required_skills:` is an **eager pre-load with no conditional path**: `system-instructions.md` § *Harness contract* loads every named skill *"before any phase work begins"*, and `adapters/claude-code.md:396` says the same. Under that mechanism every invocation pays for every declared skill, so bytes moved out of the command reappear in the **floor** plus per-skill scaffold overhead — a naive extraction makes `/implement-phase` cost **more** than the monolith. The Contract's own phrase, *"loaded on demand via `required_skills:`"*, joined two clauses that could not both be true.

**Verified.** Both sources confirm the eager contract. The escalation was correct and it changed the phase's mechanism — this spec raising it before writing a byte is the reason the whole six-spec programme is not now certifying against a number nobody pays.

**Ruling.** All six disclosure specs switch to inline **`Read skills/<name>/SKILL.md` at the point of need**. `required_skills:` frontmatter is **not used by this spec**. The inline form is the mechanism `system-instructions.md` itself documents as the standing alternative, it is genuinely conditional — the agent issues the call only if execution reaches that step — and it is already the shipping pattern in **seven commands** (`implement-story.md:525` → `tdd-cycle`, plus `ship`, `release`, `research`, `refactor`, `create-spec`, `new-skill`).

The Contract's *"loaded on demand"* is therefore **satisfied** by this change rather than contradicted by it. Only the named mechanism moves.

**What is unchanged.** The three-skill extraction plan, the ≤ 24,960-byte budget, every pinned-literal constraint, Business Rule 3's no-redesign rule, and the ownership boundary. `scripts/lint-skill.sh:52` forbids `Read skills/` **inside a skill**, so inline reads live in commands only — skills still never chain.

**Tooling.** `scripts/measure-invocation.py` was fixed in `e8f2a09` (*"required_skills: is eager, not conditional"*). It had wrongly excluded declared skills from the floor and ignored inline reads entirely. It now reports:

```
floor    = base + command + eagerly declared skills     always paid
ceiling  = floor + inline-read skills                   worst-case path
```

Every figure in this spec was **re-measured against the fixed tool on 2026-08-12**. `implement-phase` declares nothing and has no existing inline read, so its baseline `eager_bytes` and `conditional_bytes` are both 0 and its **baseline ceiling equals its floor at 54,096** — the pre-fix and post-fix baselines coincide for this file, which is why no number in § The Binding Budget moved.

**Consequences carried into the rules below:** Business Rule 1 is replaced (the hard skill-bytes cap was a workaround for the eager mechanism), Business Rule 2 is restated and strengthened, Business Rule 4 is reversed, and Business Rule 11 is closed — `MAX_SKILLS` now has an owner.

## The Binding Budget

**A command file may not cost more to load than the shared contract it runs inside.** Maintainer decision, 2026-08-12.

The shared base every invocation pays is `system-instructions.md` (20,153 B) + `commands/_preamble.md` (4,807 B) = **24,960 bytes**, and progressive disclosure cannot reduce it. `implement-phase.md` at 29,136 bytes currently costs *more than the whole contract it executes inside*. That is the budget: **≤ 24,960 bytes**, a 4,176-byte / **14.33%** cut.

Measured with `python3 scripts/measure-invocation.py --root . --command implement-phase`. Baseline, re-measured 2026-08-12 against this working tree **with the `e8f2a09` tooling fix in place**:

| Measure | Value |
|---|---|
| `base_bytes` (irreducible) | 24,960 |
| `command_bytes` | 29,136 |
| `command_lines` | 321 |
| `eager_bytes` (declared via `required_skills:`) | 0 |
| `floor_bytes` (base + command + eager) | 54,096 |
| `conditional_bytes` (inline-read skills) | 0 |
| `ceiling_bytes` (floor + conditional) | 54,096 |
| `base_share_of_floor` | 46.1% |
| bytes per line | 90.77 (corpus mean 49.12) |

The file declares no skills and contains no inline `Read skills/…` call, so **its baseline ceiling equals its floor**. The `e8f2a09` fix moved no baseline number for this file; it changes what the *after* figures mean, and that is the whole point of § Approved Scope Changes.

**Floor and every path are reported before and after.** [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md) caveat 2 warns that disclosure can *raise* total load. Under the retired eager mechanism the ceiling was not a worst case at all — it was what every run paid, and caveat 2 was close to unavoidable. Under conditional loading the floor is what every run pays and the ceiling is a genuine worst path that most runs never reach. Reporting one number cannot tell you whether disclosure worked; Business Rule 1 now specifies which numbers must be reported and which one binds.

### Why the line cap would never have caught this file

ADR-021's decision 5 takes `check_length`'s command limit from 2000 → 400 lines. `implement-phase.md` is **321 lines**. It would have passed a 400-line cap untouched while being the 4th-heaviest command by actual load and the densest per line in the repo by a factor of 2.63. The line cap measures the wrong quantity — a file of long unwrapped prose lines, which is exactly this file's house style, is invisible to it. This spec is the evidence entry for demoting the line cap to a secondary tripwire and making the byte budget binding.

## Why This Exists

`/implement-phase` is the outermost autonomous loop in Writ. Every byte of it is paid on every phase run, and it is paid *again* by every fresh lane subagent that reads the phase contract. It is also the command that carries Writ's safety machinery: lane isolation, `phase-spec-result-v1` validation, merge-only-on-verified-success, quarantine, and the guarantee that the phase branch is never touched by failed work.

That combination — heaviest safety surface, densest prose, invisible to the line cap — is why this file is the interesting one and why it goes last. The extraction has to reduce the file without moving a single safety invariant behind a conditional load.

### The constraint that shapes the whole extraction

`scripts/eval.sh` carries **19 `require_literal` assertions against `commands/implement-phase.md`**, plus a 20th requiring a `## Required Artifacts` block (`check_artifact_integrity`, and independently `scripts/eval-artifact-integrity.py`). Every one of them is a *blocking* finding, and Business Rule 8 forbids this spec from editing `scripts/eval.sh`.

Verified 2026-08-12 by `grep -n 'require_literal "$implement_phase"' scripts/eval.sh`:

| Check | Literal | Currently at |
|---|---|---|
| `check_spec_dependencies` | `` Valid explicit `Dependencies` graph `` | Step 2.1 |
| `check_spec_dependencies` | `topological` | Step 2.1 |
| `check_spec_dependencies` | `roadmap order` | Step 2.1 |
| `check_spec_dependencies` | `inference remains advisory` | Step 2.1 |
| `check_spec_dependencies` | `stop before the confirmation gate` | Step 2.1 |
| `check_phase_lanes` | `fresh subagent` | Step 3.2 |
| `check_phase_lanes` | `writ/phase/{phase-id}/{spec-id}` | Step 3.2 |
| `check_phase_lanes` | `phase-spec-result-v1` | Steps 3.2 / 3.2b / 3.3 |
| `check_phase_lanes` | `only a verified` | Step 3.2 |
| `check_phase_lanes` | `scripts/phase-state.py` | Steps 3.1–3.3, 4.1b, 4.1c |
| `check_phase_challenges` | `User Challenge` | Step 3.2b |
| `check_phase_challenges` | `ordinary failures use their normal` | Step 3.2b |
| `check_phase_quarantine` | `writ/quarantine/{spec-id}` | Step 3.3 |
| `check_phase_quarantine` | `one transient retry` | Step 3.3 |
| `check_phase_quarantine` | `skipped_blocked` | Steps 3.2 / 3.3 |
| `check_phase_quarantine` | `does not guess or mutate git` | Step 3.3 |
| `check_phase_knowledge` | `evidence-bound` | Step 4.1b |
| `check_phase_knowledge` | `no qualifying candidate` | Step 4.1b |
| `check_phase_health` | `production health` | Steps 4.1c / 4.2 |
| `check_artifact_integrity` | `## Required Artifacts` | line 33 |

This is not an obstacle to route around. It is the same boundary Hard Constraint 2 draws by hand: the strings the eval suite pins are, almost exactly, the safety invariants that must not move behind a conditionally-loaded file. The extraction is designed so that **every one of the 20 anchors stays in `commands/implement-phase.md`**, and only the surrounding narrative moves.

**That coincidence is now load-bearing.** Since the 2026-08-12 ruling made the loading genuinely conditional — meaning a skill's content is *routinely* absent, by design — the question of which sentences may live in a skill stopped being a judgment call and became the spec's central safety question. The answer already existed, written by somebody else for another reason: the eval suite pins the phrases whose loss would be dangerous, and Business Rule 2 was derived independently from asking which statements must survive a failed load. **Two processes, no coordination, the same set of sentences.** Business Rule 2 states the argument in full; this table is its evidence.

Note the second-order effect: `## Required Artifacts` is *not* in ADR-021's permitted retained-section list, but two eval checks require it. The permitted list is therefore incomplete as written. Recorded in § Technical Concerns; not corrected here.

## 📋 Business Rules

1. **Floor must fall, and every path is reported.** Replaces the pre-ruling "ceiling must not rise" rule and its hard skill-bytes cap — see § Approved Scope Changes. That cap existed to stop a ceiling rise under a mechanism where the ceiling was paid on every invocation; it required ~27% compression of already-dense prose to reach break-even, and under conditional loading it is **no longer needed as a hard cap**. It is replaced by a path-dependent rule:

   - **Floor binds.** `command_bytes` ≤ **24,960** and `floor_bytes` < **49,136**. With no skill declared eagerly, `floor_bytes` is exactly `base + command` — the bytes **every** invocation pays, with no path through the command that avoids them. This is the number the budget is about and the only one that is capped.
   - **The always-taken path binds too.** `phase-lane-execution` is reached by every run that executes a single spec, so floor + that skill is the honest cost of a real invocation. It must be **< 54,096** — strictly below the monolith. Without this clause the floor could fall while every real run got more expensive, which is caveat 2 wearing a disguise.
   - **The remaining paths are reported, not capped.** Report `floor_bytes`, the always-taken path, each common partial path, and the worst path (all three skills). The worst path may exceed 54,096 only if reaching it requires **at least two independently rare conditions**, and only with the measured number stated. It is a worst case, not a bill.
   - **The clearest win in the phase is a measurement, not a claim.** A `/implement-phase` run whose features all resolve to existing spec folders never enters the decomposition pre-pass, so it must **genuinely never pay `phase-decomposition`'s bytes** — where the eager mechanism would have charged them on every invocation forever. Story 5 measures that path and states it explicitly.

   The failure this rule prevents is unchanged: reporting `floor_bytes` alone and calling it a success. What changed is that a ceiling rise is no longer automatically a regression — under a conditional mechanism it is a question about *which path*, and the rule now asks that question instead of banning the answer.

2. **The safety-critical contract stays in the command, never behind a conditional load — and the case is now stronger, not weaker.** Four invariants are stated in `commands/implement-phase.md` itself, in normative language:
   - **Lane before work** — the lane branch and worktree are created *before* any spec work begins; a dirty base or branch collision stops before launch.
   - **Merge only on verified success** — only a verified `phase-spec-result-v1` with `status: succeeded`, a real commit, and non-empty verification evidence merges into the phase branch.
   - **Quarantine on terminal failure** — a terminal failure preserves its lane as `writ/quarantine/{spec-id}` with recorded evidence and a recovery command.
   - **The phase branch is never touched by failed work.**

   The test is a thought experiment with a `grep` behind it: **if every skill failed to load, could the command still be read as forbidding an unverified merge?** It must be yes. Verification: all 20 eval anchors return hits from `commands/implement-phase.md` itself, and the four invariants are quotable from the command with no skill loaded.

   **Under inline `Read` the non-load state is not merely reachable — it is the design.** The pre-ruling version of this rule rested on `required_skills:` degrading gracefully (unknown names warn, never hard-fail), which made a missing skill a reachable accident. The inline mechanism widens the set of ways a skill's content is absent, and removes the one warning that existed:

   - **The step is never reached.** That is the mechanism working as intended and it is why the floor falls. It also means a rule placed in `phase-decomposition` simply does not exist on the majority path.
   - **The `Read` fails.** A renamed, moved, or unwritten file returns an error at a step the agent is already mid-way through. There is no pre-flight resolution and no harness warning, because there is no declaration to resolve.
   - **Nothing governs it.** `scripts/eval-leanness.py`'s `check_required_skills()` resolves **frontmatter declarations only** (verified 2026-08-12, `scripts/eval-leanness.py:712`). An inline `Read skills/<name>/SKILL.md` naming a file that does not exist produces **zero** findings from the governor. `scripts/measure-invocation.py` does catch it — `unresolved_skills` plus a warning that the figures are a lower bound — but that is a read-only measurement that always exits 0, not a gate. Recorded in § Technical Concerns and escalated to `2026-08-12-governor-enforcement`.

   So the rule strengthens: **an invariant that depends on a `Read` succeeding is not an invariant.** Lane-before-work, merge-only-on-verified-success, quarantine-on-terminal-failure, and the phase branch never being touched by failed work are stated in the command body in normative language, and a skill may describe their mechanics but may never be the only place they are stated.

   **The eval suite drew this exact boundary independently, and that is the load-bearing argument.** § Why This Exists records 20 blocking `eval.sh` anchors against this file. They are *almost exactly* the safety machinery: `fresh subagent`, `writ/phase/{phase-id}/{spec-id}`, `phase-spec-result-v1`, `only a verified`, `writ/quarantine/{spec-id}`, `one transient retry`, `skipped_blocked`, `does not guess or mutate git`, `scripts/phase-state.py`, `ordinary failures use their normal`. Nobody coordinated that. The eval suite was written to pin the phrases whose loss would be dangerous; this rule was derived from asking which statements must survive a failed load. **Two independent processes drew the same line around the same set of sentences** — which is the strongest available evidence that the line is in the right place, and it is why the extraction is designed so all 20 anchors stay in the command and only the surrounding narrative moves. Had the two disagreed, one of them would be wrong; they agree, so the boundary is not an artifact of either.

3. **Relocate and contract; do not redesign.** Every clause of the decomposition pre-pass, lane isolation, `phase-spec-result-v1` validation, merge-only-verified-success, quarantine, User Challenge presentation, and the Question Policy's four conditions survives **byte-faithful in meaning**. The verification method is a **relocation ledger** (Story 5, § Detailed Requirements): a table with one row per removed line range of the pre-spec file, naming its destination — *retained*, *`skills/<name>/SKILL.md` § heading*, or *compressed, with the compressed text quoted*. Every row of the pre-spec file's 321 lines is accounted for exactly once. **No row may read "dropped"** without a named maintainer approval. Prose compression is permitted and expected (ADR-021 names it a tactic within extraction); deletion of a rule is not.

4. **Precise placement, not blanket declaration — this rule is reversed by the 2026-08-12 ruling.** The pre-ruling form read *"declare all three in `required_skills:`, do not curate"*, which was correct under an eager mechanism: curating a static array that is loaded in full changes nothing, so declaring everything at least kept the reader honest. **Under conditional loading, precise placement is the entire mechanism.** Each skill is loaded by exactly one inline `Read skills/<name>/SKILL.md` sitting at the **narrowest step that needs it**:

   - `phase-decomposition` — inside the decomposition pre-pass, *after* the branch that establishes there are unspecced features and the user approved decomposing them. Not in Step 1.2's classification, which runs on every phase.
   - `phase-lane-execution` — at the start of the per-spec iteration, where lane creation begins.
   - `user-challenge-presentation` — inside the `challenge_required` branch, after validation, not at the top of the failure-handling section.

   **No skill is hoisted to the preamble, the frontmatter, the `## Overview`, or any always-executed step.** A `Read` placed above the branch it serves is an eager load wearing an inline syntax: it costs the same bytes on every run and reports as `conditional_bytes`, which flatters the measurement while paying the full price. That is now the specific failure mode this rule exists to catch, and Story 5 checks placement against the phase list, not merely presence.

   Reachability is therefore **three ways, not four**: the inline `Read` at its point of use (which is simultaneously the load mechanism and the reader's pointer — under the retired mechanism these were two separate obligations); registration in `.writ/manifest.yaml` under `skills:`; and rendering into the root `SKILL.md` catalog (`bash scripts/gen-skill.sh --check` reports no delta). **`required_skills:` is not used and must not appear in this command's frontmatter** — a stray declaration silently converts a conditional load into an eager one and invalidates every path figure this spec certifies. A skill that is written and never inline-read is dead weight in the repo and a silent hole in the command.

5. **Both loop bounds are preserved exactly, including `halt_reported`.** The `loop:` block keeps its top-level `spec` bound (`max_iterations: 12`, `on_exhaustion: halt_reported`) and its nested `spec_attempt` bound (`max_iterations: 2`, `on_exhaustion: quarantine`), with both `calibrated_against:` strings intact. `scripts/eval-loop-bounds.py` `scenario_transcription_drift` cross-reads `scripts/phase-state.py:414`'s `attempts < 2` guard and fires `drift-spec-attempt` if the declaration diverges — verified 2026-08-12. **`halt_reported` on the outer loop is a deliberate maintainer decision and is not to be "corrected" to `quarantine`:** quarantining at outer-loop exhaustion would fabricate a failure record for work that never failed, and would cascade `skipped_blocked` onto its dependents. The prose that explains this (currently the *Iteration bound* paragraph in Step 3.2) is part of the contract and stays in the command with the invariants.

6. **The file is a complete, self-sufficient instruction set at every commit.** The rewrite lands as **one atomic commit** (Story 4). There is no intermediate state in which the command has lost a section to a skill that is not yet written, or declares a skill that does not yet exist. Stories 1–3 author skills and touch **zero bytes** of `commands/implement-phase.md`; Story 4 is the only writer of that file. This is not tidiness — the command executing this spec reads that file, and a half-extracted commit is a broken orchestrator.

7. **`commands/_preamble.md` is not edited.** It stands at **93 of 95 lines** (verified 2026-08-12) and its cap is owned end-to-end by `2026-08-11-autonomy-gate-classes`, whose Business Rule 3 restricts that spec to a single constant in `check_length` and whose Business Rule 1 forbids raising the cap a second time. Shared procedure that would otherwise belong in the preamble becomes a **shared skill** instead. Raising the cap from this spec would re-open a decision another spec locked.

8. **This spec owns exactly one command file plus the skills it creates.** `commands/implement-phase.md`, `skills/<new>/SKILL.md`, `.writ/manifest.yaml` (append-only, `skills:` section), and the regenerated root `SKILL.md`. **No edit to `scripts/phase-state.py`, `scripts/eval-loop-bounds.py`, `scripts/eval.sh`, `scripts/eval-leanness.py`, any other `scripts/*`, or any other file under `commands/`.** A diff touching `scripts/` fails review outright.

9. **Skills are born through `/new-skill`.** `status: candidate`, `disable-model-invocation: true`, verb-phrase description, lint-clean under `bash scripts/lint-skill.sh` *before* the file is written. `lint-skill.sh` rejects workflow shape ("Run the full", "Execute the entire") and body-level command/skill/subagent invocation — which means the extracted procedure must be rewritten as a *capability* ("how to run a unit of work in an isolated lane and dispose of its result"), never as a transcript of `/implement-phase`'s steps. That rewrite is the real work of Stories 1–3, not a formatting pass.

10. **Skill names are reconciled with the dependency spec before any skill is created.** `skills/` is a shared namespace across six sibling disclosure specs. Existing: `code-explanation`, `conventional-commits`, `error-rescue-mapping`, `gbrain-interop`, `safe-refactor-loop`, `tdd-cycle`. `2026-08-12-disclosure-implement-story` establishes the naming convention and lands first; the names proposed in § Detailed Requirements are **provisional** and are checked against that spec's landed skills, and against `.writ/manifest.yaml`'s uniqueness rule across `commands:`/`agents:`/`skills:`, as the first task of Story 1.

11. **`MAX_SKILLS` is recorded, not raised — and the escalation now has a receiver.** `scripts/eval-leanness.py:71` sets `MAX_SKILLS = 12`; the repo holds 6. This spec adds 3, and five sibling specs are adding their own. ADR-021 already flags that the cap will be exceeded and states it must be raised **deliberately with justification, not silently**. The cap lives in a script this spec does not own (Business Rule 8), so nothing changes here. What changed on 2026-08-12 is the disposition of the escalation: **`2026-08-12-governor-enforcement` now owns `MAX_SKILLS`**, by maintainer assignment recorded in that spec's own § Approved Scope Changes. Five sibling specs flagged the cap independently and none could take it; it is no longer unowned. Story 5 still reports the crossing as evidence — the report is the input that spec's derivation is answerable to.

## Detailed Requirements

### What the thin contract retains

Sections that stay in `commands/implement-phase.md`, with their pre-spec byte sizes:

| Section | Bytes | Why it stays |
|---|---:|---|
| Frontmatter (ADR-020 contract + `loop:` block) | 2,272 | ADR-021 §1; Business Rule 5 |
| `# Implement Phase Command` + `## Overview` | 940 | ADR-021 §1 |
| `## Required Artifacts` | 289 | Two eval checks require it (§ Why This Exists) |
| `## Invocation` table | 699 | ADR-021 §1 |
| Phase list with gate names | new | ADR-021 §1 — the *shape* stays visible even when the detail does not |
| Lane & failure invariants (new, condensed) | new | Business Rule 2; carries 16 of the 20 eval anchors |
| `## Question Policy (Core Rules)` | 1,252 | Hard Constraint 1 — the four conditions survive; the Overview names it "the defining constraint" |
| `## Completion` | 786 | ADR-021 §1 |
| `## References` | 164 | ADR-021 §1; `check_preamble` requires the `_preamble.md` entry |

The `## Integration with Writ` table (943 B), `## Recommended Mode` (1,655 B), and the two presentation templates (`Phase Execution Plan` 995 B, `Phase Report` 918 B) are **not** extracted by this spec. They are legitimate future targets, but the budget is met without them and Business Rule 3 rewards a smaller, fully-accounted diff over a larger, riskier one. Recorded so a later reviewer does not read the omission as an oversight.

### What extracts, and where

Three skills — **the extraction plan is unchanged by the 2026-08-12 ruling; only the loading mechanism moved.** Names provisional pending Business Rule 10.

Each is loaded by one inline `Read skills/<name>/SKILL.md` at the narrowest step that needs it (Business Rule 4). Their conditionality is not equal, and the difference decides how each is measured:

| Skill | Load site | Fires when | Frequency |
|---|---|---|---|
| `phase-decomposition` | inside the decomposition pre-pass, after approval | the phase has unspecced features **and** the user approved decomposing them | **rare** — never on a phase whose features all resolve to existing spec folders |
| `phase-lane-execution` | at the start of the per-spec iteration | any run that executes at least one spec | **always** — treat as floor-equivalent (Business Rule 1) |
| `user-challenge-presentation` | inside the `challenge_required` branch | a lane returns `challenge_required` | **rare** — most phases raise none |

**Two of the three are genuinely rare, and that is exactly what the escalation predicted.** The Technical Concern that raised this said inline loading *"would give real conditionality for the two genuinely rare skills"*. It does, and the ruling took it. `phase-lane-execution` is the honest exception and is treated as such rather than counted as a conditional win.

**1. `skills/phase-decomposition/SKILL.md`** — *Decompose a set of unspecced roadmap features into independently shippable specs with declared dependencies, single-writer file ownership, and named seams.*

Source: Step 1.2b in full (lines 93–128, 3,919 B) plus the "Decompose now" guidance paragraph inside Step 1.2 (~400 B). Carries the five-step analysis, the proposal presentation format, the seams concept, the single-writer-per-file rule, and the `--all` / `--recommend` boundary note. Retains in the command: the classification of features as Specced/Unspecced, the three-option `AskQuestion`, and a one-line pointer naming the skill.

**Zero eval anchors in this range** — verified by grepping each of the 20 literals against lines 93–128. This is the cleanest extraction of the three and is why it is Story 1.

**2. `skills/phase-lane-execution/SKILL.md`** — *Run a unit of work in a fresh isolated git lane and dispose of its result — merge on verified success, preserve or quarantine on failure, reconcile before resume.*

Source: Step 3.1 (577 B), Step 3.2 (3,058 B), Step 3.3 (1,590 B) = 5,225 B. Carries the mechanics *narrative*: how `create-lane` verifies the base, how the fresh subagent is seeded from artifact paths only, the `--quick` pass-through, the inherited-answer rule, the classify → retry → quarantine sequence, dependent blocking, and `reconcile` on `--resume`.

Retained in the command as a condensed **Lane & Failure Invariants** block carrying 9 of the anchors verbatim (`fresh subagent`, `writ/phase/{phase-id}/{spec-id}`, `phase-spec-result-v1`, `only a verified`, `scripts/phase-state.py`, `writ/quarantine/{spec-id}`, `one transient retry`, `skipped_blocked`, `does not guess or mutate git`) plus the *Iteration bound* paragraph in full (Business Rule 5). Step 2.1's five anchors are untouched — Step 2.1 is not extracted.

**3. `skills/user-challenge-presentation/SKILL.md`** — *Present a four-part User Challenge and persist its resolution so a resumed run never re-asks a decided question.*

Source: Step 3.2b (1,267 B). Carries the validate → present → persist mechanics, the four-part rendering format, and the audited-low-risk auto-proceed rule.

Retained in the command: a two-to-three line statement that `/implement-phase` is the **sole presenter** of `User Challenge`s, that a malformed challenge is a contract error routed to normal failure handling, and the literal `ordinary failures use their normal` failure path. Both `check_phase_challenges` anchors stay.

### Projected arithmetic

| | Bytes out | Retained/pointer back | Net |
|---|---:|---:|---:|
| Decomposition pre-pass | 4,319 | 400 | −3,919 |
| Lane / merge / quarantine | 5,225 | 1,950 | −3,275 |
| User Challenge | 1,267 | 380 | −887 |
| Inline `Read` literals + section glue | — | +240 | +240 |
| **Total** | **10,811** | **2,970** | **−7,841** |

**Projected `command_bytes` ≈ 21,295** — a 26.9% cut, landing **14.7% under the 24,960 budget**. Projected `floor_bytes` ≈ 46,255, down 14.5% from 54,096. Projected lines ≈ 251.

The glue figure survives the mechanism change within noise: the retired `required_skills:` block was ≈ 95 B of frontmatter, and the three inline `Read skills/<name>/SKILL.md` literals add ≈ 60 B over the skill names Business Rule 4 already required at each point of use. Net ≈ −35 B, inside the ±50 B precision of every other row. **The floor projection does not move because of the ruling.**

#### The path table — this is what replaces the hard skill-bytes cap

With no eager declaration, `floor_bytes` is `base + command` and is paid by every invocation with no exceptions. Everything above it is per-path. Projected skill sizes, authored to the source ranges without the pre-ruling 27% forced compression:

| Skill | Source prose | Projected skill |
|---|---:|---:|
| `phase-decomposition` | 4,319 | ≈ 3,600 |
| `phase-lane-execution` | 5,225 | ≈ 4,400 |
| `user-challenge-presentation` | 1,267 | ≈ 1,500 |
| **Total** | **10,811** | **≈ 9,500** |

| Path | Skills read | Projected bytes | vs. 54,096 monolith |
|---|---|---:|---:|
| **Floor** — every invocation, no exceptions | none | **46,255** | **−7,841 (−14.5%)** |
| **A. Always-taken** — specs all resolve, no challenge | lane | 50,655 | **−3,441 (−6.4%)** |
| B. A + a challenge fires | lane + challenge | 52,155 | −1,941 (−3.6%) |
| C. Unspecced features decomposed, no challenge | lane + decomposition | 54,255 | +159 (+0.3%) |
| **D. Worst path** — all three in one run | all three | **55,755** | **+1,659 (+3.1%)** |

Read the table in the order the rules bind. **Floor** and **path A** are the two capped figures (Business Rule 1) and both clear comfortably. **Path D** exceeds the monolith by 3.1% and is permitted: reaching it requires unspecced features, a user approval to decompose them, *and* a lane returning `challenge_required` — two independently rare conditions plus the always-taken one, which is exactly the bar Business Rule 1 sets.

**The headline result is path A against the old mechanism.** Had this landed under `required_skills:`, all three skills would have sat in the floor: 46,255 + 9,500 = **55,755 on every invocation**, 1,659 bytes *worse than the monolith* — the outcome the escalation predicted, arrived at by doing everything else right. The same extraction, loaded conditionally, costs 50,655 on the common path. **The mechanism is worth 5,100 bytes per run; the extraction itself is worth 7,841.**

**And the sharpest single number: `phase-decomposition`'s ≈ 3,600 bytes.** A `/implement-phase` run whose features all resolve to existing spec folders never enters the pre-pass and therefore **never pays them** — not amortised, not reduced, *never*. Under the eager mechanism that same run would have paid them on every invocation for the life of the file. That is the clearest win in the entire phase, and Business Rule 1 requires Story 5 to measure and state it rather than leave it as an argument.

These projections are authored from measured section sizes and are **estimates**. Story 5 reports the measured actuals for the floor and every path and is the pass condition; the projection is not. Skill sizes are no longer capped at bytes-removed — but Business Rule 3 still forbids dropping a rule, and a skill that lands far over its projection moves path D, which Story 5 must then state rather than absorb.

### The self-modification hazard

`/implement-phase` will spawn the lane subagent that edits `commands/implement-phase.md`. Concretely, on the sequencing this phase uses:

- The lane subagent works inside `writ/phase/10/2026-08-12-disclosure-implement-phase` in a **separate worktree**. The orchestrator's own checkout of `commands/implement-phase.md` on the phase branch is unchanged until the `--no-ff` merge lands, so the running instruction set is not mutated mid-iteration. This is a property of the lane isolation the spec is rewriting — which is precisely why Business Rule 2 exists.
- This spec is **last** in the phase, so no subsequent iteration reads the rewritten file within the same run.
- If the spec is instead run directly (`/implement-spec` on the phase branch, no lane), the file being edited **is** the file being executed. Business Rule 6's one-atomic-commit rule is what makes that survivable.
- Story 4 records the pre-edit blob SHA in its evidence, so an orchestrator that loses its footing can be re-seeded with `git show <sha>:commands/implement-phase.md`.

## Out of Scope

- **Any edit to `scripts/`.** Business Rule 8. Including the `MAX_SKILLS` cap (Business Rule 11), `check_length`'s command limit (owned by the governor-enforcement work), and every `require_literal` in `scripts/eval.sh`.
- **`commands/_preamble.md`.** Business Rule 7 — owned by `2026-08-11-autonomy-gate-classes`.
- **Any other file under `commands/`.** The five sibling disclosure specs own theirs.
- **Changing either loop bound, or `halt_reported`.** Business Rule 5.
- **Extracting `## Recommended Mode`, `## Integration with Writ`, or the two presentation templates.** Named and deliberately deferred — see § Detailed Requirements.
- **Redesigning the phase pipeline.** Business Rule 3. No new failure mode, no changed gate, no altered `phase-spec-result-v1` contract, no change to what `scripts/phase-state.py` is asked to do.
- **Amending ADR-021's permitted retained-section list** to include `## Required Artifacts`, even though two eval checks require it. Recorded in § Technical Concerns; an ADR amendment is its own decision.
- **Correcting `system-instructions.md`'s `required_skills:` status claim.** The eager-load contradiction is **resolved** for this spec by the 2026-08-12 ruling (§ Approved Scope Changes) — this spec uses inline `Read` and does not touch the harness contract. But `system-instructions.md:252` still reads *"**Status: adopted** … The first consumer is Phase 10 progressive disclosure"*, which the ruling makes false: the phase does not use the field. Correcting it is assigned to `2026-08-12-governor-enforcement`, the only spec that owns that file. Not taken here.
- **Adding a governor check for inline-read resolution.** `check_required_skills()` resolves frontmatter declarations only, so this spec's three inline reads get no enforcement. Recorded in § Technical Concerns and escalated; `scripts/` is out of reach under Business Rule 8 in either direction.
- **Declaring anything in `required_skills:`.** Business Rule 4. The field must not appear in this command's frontmatter at all.
- **Promoting any extracted skill past `status: candidate`.** ADR-014: promotion accrues from real use. ADR-021 states plainly that this phase does not close the lifecycle loop.
- **`claude-code/`, `cursor/`, `codex/` mirrors and `adapters/`.** `check_phase_lanes` and `check_phase_quarantine` assert literals in `adapters/*.md`, but those are adapter-side and unaffected by a command-side extraction. Verify, do not edit.

## Implementation Approach

1. **Stories 1–3 author the three skills** and touch zero bytes of `commands/implement-phase.md`. Each is `/new-skill` → lint → write → manifest → `gen-skill.sh --check`. They are mutually independent apart from a serialized append to `.writ/manifest.yaml`, so they run in sequence rather than in parallel worktrees — the manifest is a hand-edited YAML file and three concurrent appends is a merge conflict for no gain at this size.
2. **Story 4 is the single atomic rewrite** of `commands/implement-phase.md`: the thin contract, the invariants block, the three inline `Read skills/<name>/SKILL.md` calls at their narrowest steps, and the relocation ledger. **No frontmatter edit** — see § Approved Scope Changes. It depends on all three skills existing, because Business Rule 4 requires every inline `Read` to resolve to a real file and Business Rule 6 forbids an intermediate state.
3. **Story 5 measures and verifies** — floor and ceiling before/after, the full eval suite, the 20 anchors, the loop-bound drift check, and the no-drift review against the relocation ledger.

Stories 1–3 before 4 is not a preference. It is the only order in which the file is never in a half-extracted state.

## Success Criteria

1. `python3 scripts/measure-invocation.py --root . --command implement-phase` reports `command_bytes` **≤ 24,960** (from 29,136) and `floor_bytes` **< 49,136** (from 54,096). `eager_bytes` is **0** and `eager_skills` is **empty** — no eager declaration exists.
2. The path table is measured and reported: floor, the always-taken path (floor + `phase-lane-execution`), each common partial path, and the worst path. The **always-taken path is < 54,096**. A worst path above 54,096 is permitted, stated with its number, and justified by naming the two independently rare conditions required to reach it (Business Rule 1). `conditional_skills` lists all three; `unresolved_skills` is empty.
2b. The saving on the majority path is stated as a number: a run resolving all specs from existing folders does not load `phase-decomposition`, and the bytes it therefore never pays are reported.
3. All 20 eval anchors are present in `commands/implement-phase.md` itself: 19 `require_literal` strings plus a `## Required Artifacts` block. Verified by grepping the command file directly, not the skills.
4. `bash scripts/eval.sh` produces **no new findings** relative to the pre-spec baseline (baseline captured 2026-08-12: `--check=length` exits 0, full run's report path recorded in Story 5).
5. `python3 scripts/eval-loop-bounds.py` reports `drift-spec-attempt` PASS, and `commands/implement-phase.md`'s `loop:` block is byte-for-byte identical to its pre-spec form — `git diff` shows zero changes inside it.
6. The four safety invariants of Business Rule 2 are quotable from `commands/implement-phase.md` with no skill loaded, in normative language.
7. Three skills exist under `skills/`, each `status: candidate`, each passing `bash scripts/lint-skill.sh`, each listed in `.writ/manifest.yaml`, and `bash scripts/gen-skill.sh --check` reports no delta.
8. `commands/implement-phase.md` contains **exactly three** inline `Read skills/<name>/SKILL.md` calls, one per skill, each at the narrowest step that needs it and **none in the frontmatter, `## Overview`, or any always-executed step** (Business Rule 4). `grep -c 'required_skills' commands/implement-phase.md` returns **0**.
9. The relocation ledger accounts for all 321 lines of the pre-spec file exactly once, with no row reading "dropped".
10. `git diff --name-only` for the whole spec lists **no path under `scripts/`**, no `commands/*.md` other than `implement-phase.md`, and does not include `commands/_preamble.md`.
11. `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` returns `status: ok`. Verified 2026-08-12 at authoring time: it does, and the resolved order places `2026-08-12-disclosure-implement-story` before this spec and `2026-08-12-governor-enforcement` after it.

## Technical Concerns (surfaced at contract time)

- **RESOLVED 2026-08-12 — `required_skills:` is an eager pre-load, and the mechanism was changed.** This concern was escalated at contract time, verified by the maintainer against `system-instructions.md` § *Harness contract* (*"before any phase work begins"*) and `adapters/claude-code.md:396`, and **accepted**. The six disclosure specs switch to inline `Read skills/<name>/SKILL.md`; `required_skills:` is not used. See § Approved Scope Changes for the full ruling and § Detailed Requirements → *The path table* for what it is worth (≈5,100 bytes per run on the common path; the whole difference between a 14.5% floor cut and a command that cost 1,659 bytes *more* than the monolith on every invocation). The escalation is left on the record rather than deleted: not deciding it in-flight is what made the ruling possible, and the concern that changed a phase's mechanism is worth more as history than as a tidy file.
- **ADR-021's permitted retained-section list omits `## Required Artifacts`, which two eval checks require.** `check_artifact_integrity` in `scripts/eval.sh` and `scripts/eval-artifact-integrity.py` both blocking-require it in seven high-traffic commands including this one. A thin contract authored strictly to ADR-021 §1 would fail the eval suite. This spec keeps the section and records the gap; ADR-021 needs an amendment, owned by whoever holds the ADR.
- **19 blocking eval literals pin prose inside a file this spec is rewriting, and the spec cannot edit the eval.** This is a genuine coupling defect in the repo — the eval suite asserts on *phrasing* rather than on structure — but it is load-bearing here in a useful direction, since the pinned phrases are mostly the safety invariants. The risk is the inverse case: a phrase pinned for a *narrative* reason (`topological`, `roadmap order`) forces narrative to stay that could otherwise compress. Both are in Step 2.1, which this spec does not extract, so it does not bite now. It will bite whoever extracts Step 2.1 later.
- **The forced-compression risk is retired, and this is the second-order value of the ruling.** The pre-ruling plan required 10,811 B of source prose to fit 7,841 B of skills — a ~27% compression on prose already at 90.77 B/line, with scaffold overhead on top — purely to stop an eager ceiling from rising. That pressure was a workaround for the mechanism, not a property of the extraction, and it pushed directly against Business Rule 3: the cheapest way to hit a byte target on dense normative prose is to soften a rule into advice. **Under conditional loading the cap is gone and the skills are authored to the source, not to a number.** What remains is Business Rule 3's no-drift requirement and Business Rule 1's path reporting — a skill that lands far over projection moves path D and must be stated, not absorbed.

- **`phase-lane-execution` is on the always-taken path, so one of the three skills is only nominally conditional.** Every `/implement-phase` run that executes a single spec reaches it. Moving it inline converts an eager cost into a cost that is conditional in form and unconditional in practice, plus the read. `scripts/measure-invocation.py` will report its bytes under `conditional_bytes` regardless, which **flatters the floor**. Business Rule 1 refuses that flattery by binding the always-taken path (floor + this skill) as a second capped figure. Recorded rather than resolved: the alternative — leaving 5,225 B of lane narrative in the command — breaks the 24,960 budget, so the skill is correct and the *accounting* is what needed the guard.

- **No governor check resolves an inline `Read`, so this spec's three loads have no standing enforcement.** `scripts/eval-leanness.py`'s `check_required_skills()` (verified 2026-08-12, `scripts/eval-leanness.py:682-724`) iterates `fields.get("required_skills", "")` and nothing else. A typo'd or unwritten inline path produces **zero** findings from the gate that `2026-08-12-governor-enforcement` is about to make blocking. `scripts/measure-invocation.py` does catch it — `_inline_read_skills()` at `:140` feeds `unresolved_skills` and a lower-bound warning — but it always exits 0 by design. The practical consequence for this spec: Business Rule 4's reachability is self-verified in Story 5 and re-verified by nothing afterwards. Escalated to `2026-08-12-governor-enforcement`, which owns `eval-leanness.py`; **not fixed here** (Business Rule 8).

- **`required_skills_declarations` is now permanently 0, which changes what that metric means.** `2026-08-12-governor-enforcement` Story 1 exists to surface `required_skills_declarations` into the eval report as instrumentation Business Rule 8's vacuous-pass guard, on the stated expectation that *"progressive disclosure's extraction work lands the first real declarations"* (`system-instructions.md:252`). After the ruling, no disclosure spec declares the field, so the metric reports 0 forever and the check behind it has nothing to resolve permanently rather than transiently. Story 1's *mechanism* is still right — that is precisely the case the guard exists to make visible — but its *framing* is now false. Flagged for that spec.
- **`MAX_SKILLS = 12` will be crossed by the six-spec programme, and now has an owner.** Counted from the six authored rosters on 2026-08-12 — `implement-story` +8, `create-spec` +5, `verify-spec` +4, `release` +5, `ship` +4, this spec +3 = **29 new against 6 existing, a post-phase total of 35**. Business Rule 11 still reports rather than raises. If the cap fires during this spec's eval run it will read as a new finding against Success Criterion 4 — Story 5 must distinguish "new finding caused by this spec's content" from "new finding caused by the cap the phase always intended to cross," and report both rather than suppressing either. **`2026-08-12-governor-enforcement` now owns the constant** (maintainer assignment, 2026-08-12), so this is a handoff with a receiver rather than an open escalation. Note for that spec: `2026-08-12-disclosure-ship` § Technical Concerns states *"at least 29 skills"* as a **total**; it is a total of 29 only because it counted `create-spec` and `release` at +4 each instead of +5 and omitted `verify-spec` entirely. The measured total is **35**.
- **This spec is executed by the command it rewrites.** Mitigated by lane isolation, last-in-phase sequencing, and Business Rule 6's atomic commit — see § Detailed Requirements → *The self-modification hazard*. The residual risk is a direct (non-lane) run, where the editing agent and the executing agent read the same file. Story 4 records the pre-edit blob SHA for recovery.
- **The dependency and the four other siblings were authored concurrently with this spec.** `2026-08-12-disclosure-implement-story` fixes the extraction pattern and the skill-naming convention (Business Rule 10) and now exists; `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` returns `status: ok`. Skill-name collisions were checked at authoring time across all six disclosure specs plus `2026-08-12-governor-enforcement`: the three names proposed here (`phase-decomposition`, `phase-lane-execution`, `user-challenge-presentation`) collide with nothing claimed elsewhere. That check was a **snapshot** — the sibling specs are not yet implemented and their names can still move, which is why Business Rule 10 makes reconciliation the first task of each authoring story rather than a settled fact. The dependency edge **must not be deleted to make the validator quiet** if it ever reports `missing_reference` — deleting it would silently release this spec to run before the pattern it is required to follow exists.
- **The programme's six files are the top six by floor load, and `implement-spec` is not among them.** The six disclosure specs cover `implement-story`, `create-spec`, `verify-spec`, `implement-phase`, `release`, and `ship`. So no sibling spec extracts `/implement-spec`'s lane-side procedure, and the ADR-021 §4 question — whether lane mechanics should be **one shared skill** rather than two copies — has no live counterparty. It becomes live the day `implement-spec` is extracted. `skills/phase-lane-execution/SKILL.md` should therefore be authored as a general capability rather than as this command's Step 3.2 in disguise, so that day is a reuse rather than a rewrite.

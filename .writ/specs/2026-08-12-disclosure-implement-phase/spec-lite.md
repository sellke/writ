# Progressive Disclosure — `implement-phase` (Lite)

> Source: .writ/specs/2026-08-12-disclosure-implement-phase/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `commands/implement-phase.md` (29,136 B / 321 lines) → thin contract + 3 skills loaded by inline **`Read skills/<name>/SKILL.md` at the point of need**.

**MECHANISM RULING (maintainer, 2026-08-12) — read this first.** This spec's escalation was **verified and accepted**: `required_skills:` is an **eager** pre-load with no conditional path (`system-instructions.md` § Harness contract *"before any phase work begins"*; `adapters/claude-code.md:396`), so extraction under it makes the command cost **more** than the monolith. **All six disclosure specs switch to inline `Read`. `required_skills:` is NOT used — it must not appear in this command's frontmatter at all.** The inline form is genuinely conditional and already ships in seven commands (`implement-story.md:525` → `tdd-cycle`). The extraction plan, the budget, the pinned literals, and the no-redesign rule are all unchanged. `scripts/lint-skill.sh:52` forbids `Read skills/` *inside a skill*, so inline reads live in commands only. Full record: spec.md → § Approved Scope Changes. **Tooling:** `scripts/measure-invocation.py` was fixed in `e8f2a09` — it wrongly excluded `required_skills:` from the floor and ignored inline reads; now `floor = base + command + eagerly-declared skills`, `ceiling = floor + inline-read skills`. **Re-measure; do not inherit pre-fix figures.**

**Budget (binding, maintainer decision 2026-08-12):** `command_bytes` **≤ 24,960** — the irreducible shared base (`system-instructions.md` 20,153 + `commands/_preamble.md` 4,807). A command may not cost more to load than the contract it runs inside. That is a 14.33% cut. Measure with `python3 scripts/measure-invocation.py --root . --command implement-phase`. Baseline (re-measured post-fix): `eager_bytes` 0 · floor 54,096 · `conditional_bytes` 0 · **ceiling 54,096 (equals floor — no declaration, no inline read)** · 90.77 B/line (densest in repo, 2.63× the lightest; 4th of 31 by floor; **321 lines, so a 400-line cap would never have caught it**).

**Files in scope — this spec owns exactly these:**
- `commands/implement-phase.md` — the only command file. **No other `commands/*.md`, not `_preamble.md`.**
- `skills/phase-decomposition/SKILL.md`, `skills/phase-lane-execution/SKILL.md`, `skills/user-challenge-presentation/SKILL.md` — names **provisional**, reconcile with `2026-08-12-disclosure-implement-story` first (BR10).
- `.writ/manifest.yaml` (append `skills:` entries only) + regenerated root `SKILL.md`.
- **Zero edits under `scripts/`.** Not `phase-state.py`, not `eval-loop-bounds.py`, not `eval.sh`, not `eval-leanness.py` (BR8).

**The 20 blocking anchors.** `scripts/eval.sh` carries 19 `require_literal` assertions against `commands/implement-phase.md`, plus `## Required Artifacts` (`check_artifact_integrity` + `scripts/eval-artifact-integrity.py`). **All 20 must stay in the command file, not in a skill** — the spec cannot edit `eval.sh`. The literals: `` Valid explicit `Dependencies` graph ``, `topological`, `roadmap order`, `inference remains advisory`, `stop before the confirmation gate` (Step 2.1, **not extracted**); `fresh subagent`, `writ/phase/{phase-id}/{spec-id}`, `phase-spec-result-v1`, `only a verified`, `scripts/phase-state.py`; `User Challenge`, `ordinary failures use their normal`; `writ/quarantine/{spec-id}`, `one transient retry`, `skipped_blocked`, `does not guess or mutate git`; `evidence-bound`, `no qualifying candidate`; `production health`.

**Extraction plan (unchanged by the ruling — projected −7,841 B → ≈ 21,295 B).** Glue is +240 B either way (retired `required_skills:` block ≈95 B out, three inline `Read` literals ≈60 B in), so **the floor projection did not move because of the ruling**:

| Skill | Source | Out | Retained | Net | Load site | Fires |
|---|---|---:|---:|---:|---|---|
| `phase-decomposition` | Step 1.2b + proposal block + "Decompose now" para | 4,319 | 400 | −3,919 | inside the pre-pass, **after** approval | **rare** |
| `phase-lane-execution` | Steps 3.1 + 3.2 + 3.3 | 5,225 | 1,950 | −3,275 | start of per-spec iteration | **always** |
| `user-challenge-presentation` | Step 3.2b | 1,267 | 380 | −887 | inside the `challenge_required` branch | **rare** |

Retained: frontmatter (+ `loop:`), Overview, `## Required Artifacts`, Invocation table, phase list with gate names, a new **Lane & Failure Invariants** block, Question Policy, Completion, References. **Not extracted this spec:** `## Recommended Mode`, `## Integration with Writ`, the two presentation templates — deferred deliberately, budget is met without them.

**The hard skill-bytes cap is RETIRED.** It required ~27% compression of dense normative prose purely to stop an eager ceiling rising, and that pressure pushed straight against BR3 (the cheapest way to hit a byte target is to soften a rule into advice). Skills are now authored to the source: `phase-decomposition` ≈3,600 · `phase-lane-execution` ≈4,400 · `user-challenge-presentation` ≈1,500 ≈ **9,500 B total**. BR3's no-drift rule and BR1's path reporting are what remain.

**Projected path table — this is what BR1 now measures:**

| Path | Skills read | Bytes | vs. 54,096 |
|---|---|---:|---:|
| **Floor** — every invocation | none | **46,255** | **−7,841 (−14.5%)** |
| **A. Always-taken** — specs resolve, no challenge | lane | 50,655 | **−3,441** |
| B. + challenge fires | lane + challenge | 52,155 | −1,941 |
| C. unspecced + decomposed, no challenge | lane + decomp | 54,255 | +159 |
| **D. Worst path** — all three | all three | **55,755** | **+1,659 (+3.1%)** |

Floor and path A are the capped figures. Path D is permitted: it needs two independently rare conditions. **Under the old eager mechanism all three sat in the floor: 55,755 on *every* run — 1,659 B worse than the monolith. The mechanism is worth ~5,100 B per run.** And the sharpest number: a run whose features all resolve to existing spec folders **never pays `phase-decomposition`'s ≈3,600 B at all** — never amortised, never reduced. Under `required_skills:` that same run paid them every time. **Measure and state it (BR1, SC 2b).**

---

## For Review Agents

**Acceptance Criteria:**
1. `command_bytes` ≤ 24,960; `floor_bytes` < 49,136; `eager_bytes` = 0 and `eager_skills` empty.
2. Path table measured and reported (floor · always-taken · partials · worst). **Always-taken path < 54,096.** A worst path above it is stated with its number and the two rare conditions needed to reach it. `conditional_skills` lists all three; `unresolved_skills` empty.
2b. The bytes a spec-resolving run never pays for `phase-decomposition` are stated as a number.
3. All 20 anchors grep-present in `commands/implement-phase.md` itself.
4. `bash scripts/eval.sh` → no new findings vs. the 2026-08-12 baseline (`--check=length` exits 0).
5. `loop:` block byte-for-byte unchanged; `python3 scripts/eval-loop-bounds.py` → `drift-spec-attempt` PASS.
6. 3 skills, `status: candidate`, lint-clean, in manifest, `gen-skill.sh --check` no delta, each loaded by exactly one inline `Read` at its narrowest step.
7. Relocation ledger accounts for all 321 pre-spec lines exactly once; no row reads "dropped".
8. `git diff --name-only` → no `scripts/` path, no other `commands/*.md`. `grep -c required_skills commands/implement-phase.md` → **0**.

**Business Rules (the ones that decide PASS/FAIL):**
- **BR1 path-dependent ceiling (REPLACED 2026-08-12):** floor binds (≤24,960 command / <49,136 floor) **and** the always-taken path (floor + `phase-lane-execution`) must be **<54,096**. Other paths are **reported, not capped**; a worst path above 54,096 is allowed if it needs ≥2 independently rare conditions and the number is stated. **The hard skill-bytes cap is gone** — it was a workaround for the eager mechanism. Still banned: reporting the floor alone and calling it a win.
- **BR2 safety invariants stay in the command — STRENGTHENED:** lane-before-work · merge-only-on-verified-success · quarantine-on-terminal-failure · the phase branch is never touched by failed work. Test: **if every skill failed to load, could the command still be read as forbidding an unverified merge?** Must be yes. Under inline `Read`, non-load is **the design**, not an accident: the step may never be reached, the `Read` may fail mid-step, and **nothing governs it** — `check_required_skills()` resolves frontmatter only (`eval-leanness.py:712`), so a bad inline path yields zero findings. **An invariant that depends on a `Read` succeeding is not an invariant.**
  - **Why this boundary is right:** the 20 blocking `eval.sh` anchors are *almost exactly* the safety machinery. The eval suite pinned the dangerous-to-lose phrases; BR2 was derived from asking what must survive a failed load. **Two independent processes, same set of sentences.** That convergence is the argument.
- **BR3 relocate, do not redesign:** verified by the **relocation ledger** — one row per removed line range, destination = retained / `skills/<n>` § heading / compressed-with-text-quoted. Every line accounted once. Compression yes; deleting a rule no.
- **BR4 precise placement, REVERSED 2026-08-12:** was *"declare all, don't curate"* (correct when a static array loads in full). Now **placement is the mechanism**: one inline `Read` per skill at the **narrowest step that needs it**, **none hoisted** to frontmatter, `## Overview`, or any always-executed step. A `Read` above its branch is an eager load in inline syntax — it costs full price and reports as `conditional_bytes`, flattering the number. Reachability is **three ways**: inline `Read` at point of use · manifest · root `SKILL.md`.
- **BR5 both loop bounds preserved exactly:** `spec` (12, `halt_reported`) and nested `spec_attempt` (2, `quarantine`), `calibrated_against:` strings intact. `eval-loop-bounds.py` cross-reads `scripts/phase-state.py:414`'s `attempts < 2`. **`halt_reported` is deliberate — quarantining at outer-loop exhaustion would fabricate a failure record and cascade `skipped_blocked`. Do not "correct" it.**
- **BR6 self-sufficient at every commit:** Stories 1–3 touch **zero bytes** of the command; Story 4 flips it in **one atomic commit**. The command executing this spec reads that file.
- **BR7:** `_preamble.md` is 93/95 lines and owned by `2026-08-11-autonomy-gate-classes`. Do not edit, do not raise the cap. Shared procedure → shared skill.
- **BR9:** skills born via `/new-skill`, lint-clean *before* writing. `lint-skill.sh` rejects workflow shape — rewrite the procedure as a **capability**, not a transcript of the command's steps.
- **BR11:** `MAX_SKILLS = 12` (`eval-leanness.py:71`), repo has 6. Report if crossed; do not raise it here. **`2026-08-12-governor-enforcement` now owns the constant** (maintainer assignment 2026-08-12) — this is a handoff with a receiver. Measured phase roster: implement-story +8, create-spec +5, verify-spec +4, release +5, ship +4, here +3 = **29 new, 35 total**.

---

## For Testing Agents

There is no application code and no test suite. Verification is structural.

**Success Criteria:**
1. `python3 scripts/measure-invocation.py --root . --command implement-phase` → `command_bytes` ≤ 24,960, `floor_bytes` < 49,136, `eager_bytes: 0`, `eager_skills: []`, `conditional_skills` = the three, `unresolved_skills: []`. Report the **whole path table** before and after — floor, always-taken, partials, worst — not floor and ceiling alone.
2. `for s in <the 19 literals>; do grep -Fq "$s" commands/implement-phase.md || echo MISSING; done` → no output. `grep -c '^## Required Artifacts' commands/implement-phase.md` → 1.
3. `bash scripts/eval.sh` → no new findings vs. baseline; `bash scripts/eval.sh --check=length` → exit 0.
4. `python3 scripts/eval-loop-bounds.py` → `drift-spec-attempt` PASS; `git diff commands/implement-phase.md` shows no change inside `loop:`.
5. `bash scripts/lint-skill.sh skills/*/SKILL.md` → exit 0. `bash scripts/gen-skill.sh --check` → no delta.
6. `git diff --name-only` → no `scripts/` path; `commands/` shows only `implement-phase.md`.
7. `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` → `status: ok` (blocked on the dependency existing).

**Edge Cases:**
- **`required_skills:` is EAGER — RESOLVED, mechanism changed.** The escalation was verified and accepted on 2026-08-12; this spec uses inline `Read` and the field is banned from its frontmatter. Do not re-litigate; do not "restore" the declaration. See spec.md → § Approved Scope Changes.
- **`phase-lane-execution` is only nominally conditional.** Every run that executes a spec reaches it, so `measure-invocation.py` books it under `conditional_bytes` while it is paid in practice — which **flatters the floor**. BR1 answers by binding floor + this skill as a second capped figure. Recorded, not resolved: leaving 5,225 B of lane narrative in the command breaks the 24,960 budget, so the skill is right and the *accounting* needed the guard.
- **Nothing enforces an inline read.** `check_required_skills()` reads frontmatter only, so a typo'd inline path is invisible to the governor that `governor-enforcement` is about to make blocking. `measure-invocation.py` catches it (`unresolved_skills` + lower-bound warning) but always exits 0. Escalated to `governor-enforcement`; `scripts/` is out of reach here (BR8).
- **`required_skills_declarations` is now permanently 0.** `governor-enforcement` Story 1 surfaces it as the vacuous-pass guard on the stated expectation that this phase would land the first declarations (`system-instructions.md:252`). It will not. The mechanism is still right; the framing is false. Flagged for that spec.
- **ADR-021's permitted retained-section list omits `## Required Artifacts`**, which two eval checks blocking-require. Keep the section; the ADR needs an amendment nobody here owns.
- **Dependency resolves.** All six disclosure specs plus `2026-08-12-governor-enforcement` were authored concurrently; `spec-deps.py` returns `status: ok`. Skill-name collisions checked across all of them at authoring time — the three names here are clear. That was a snapshot; BR10 still requires re-checking at each authoring story. **Never delete the dependency edge to quiet the validator.**
- **`implement-spec` is not one of the six extracted files** (the six are the top six by floor: implement-story, create-spec, verify-spec, implement-phase, release, ship). So ADR-021 §4's "one shared skill, not two copies" question about lane mechanics has no live counterparty yet. Author `phase-lane-execution` as a general capability so it is reusable when it does.
- Step 2.1's five anchors pin *narrative* phrasing, not safety. Step 2.1 is not extracted here, so it doesn't bite — it will bite whoever extracts it later.

**Anti-goal to watch for:** a smaller file that lost a rule. The failure mode is not an over-budget command — it is a command that passes every byte check while the lane/merge/quarantine contract now lives only in a file that warns-and-continues when it fails to load.

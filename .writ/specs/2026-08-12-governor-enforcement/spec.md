# Spec: Governor Enforcement

> **Status:** Not Started
> **Owner:** @AdamSellke
> **Created:** 2026-08-12
> **Dependencies:** [2026-08-12-disclosure-implement-story, 2026-08-12-disclosure-create-spec, 2026-08-12-disclosure-verify-spec, 2026-08-12-disclosure-release, 2026-08-12-disclosure-ship, 2026-08-12-disclosure-implement-phase]
> **Origin:** Phase 10, the closing spec. `2026-08-11-governor-instrumentation` built the instrument and deliberately shipped it warn-only; the six progressive-disclosure specs bring the surface into compliance. This spec is the one that makes the measurement cost something. ADR-021 named three reasons the old governor never caught 516KB of command prose — reason 1 (*"the limit cannot bind"*), reason 2 (*"growth warns, it does not fail"*), reason 3 (*"a ratchet is not a budget"*). Instrumentation answered reason 2's mechanism. This spec answers 1 and 3, and throws the switch on 2.

## Contract (Locked)

**Deliverable:** Make the governor bite. Flip the four component-contract checks from `warnings` to `structural`, land the absolute per-invocation byte budget as a **blocking** cap, and retire the `check_length` command limit that never could bind.

**Must include:** The flip is the **single named constant** `CONTRACT_CHECK_SEVERITY` in `scripts/eval-leanness.py` — `2026-08-11-governor-instrumentation` Story 7 built and tested that seam precisely so this spec changes one string, not four checks. Verify the seam still holds before using it.

**Hardest constraint:** This spec turns a green suite red the moment any file regresses, and a permanently-red gate becomes invisible — the exact failure mode ADR-021 diagnosed and the reason instrumentation shipped warn-only in the first place. It may flip **only** once the surface actually complies; a flip that lands with known violations recreates the problem it exists to solve.

## Approved Scope Changes

### 2026-08-12 — three obligations transferred here by the mechanism ruling

The `## Contract (Locked)` block above is preserved **verbatim** and is not edited. This section is the dated record of what the maintainer added on top of it, and it governs where the two differ. Its § Out of Scope entry recording `MAX_SKILLS` as *"assigned here by another spec, both outside this spec's file set … Disposition: recorded, not silently absorbed and not silently dropped"* is now **resolved in the affirmative**: the maintainer widened the file set, which is the disposition that entry named as one of its two exits.

**The ruling.** `2026-08-12-disclosure-implement-phase` escalated that `required_skills:` is an **eager** pre-load with no conditional path — `system-instructions.md` § *Harness contract* (*"before any phase work begins"*) and `adapters/claude-code.md:396` both confirm it — so extraction under it makes a command cost **more** than the monolith. The escalation was verified and accepted. **All six disclosure specs switch to inline `Read skills/<name>/SKILL.md` at the point of need; `required_skills:` is retired for this phase.** `scripts/measure-invocation.py` was fixed in `e8f2a09` to model it correctly (`floor = base + command + eager`, `ceiling = floor + inline`).

Three consequences land here, because this spec owns the files they live in and no other spec does:

1. **The compliance gate gains a second condition** (Business Rule 2, Story 4): *no command declares `required_skills:`*. A stray declaration silently converts a conditional load into an eager one and invalidates every ceiling figure the six disclosure specs certified against. Story 4 already asserts every command is ≤ 24,960 bytes; this is the other half of the same precondition, and it is cheap to assert and expensive to discover late.

2. **`MAX_SKILLS` is now owned here.** Five sibling specs flagged `MAX_SKILLS = 12` (`scripts/eval-leanness.py:71`) independently and **none could take it** — every disclosure spec bars itself from `scripts/`. It was the one obligation in the phase with no owner. It is now this spec's, with Business Rule 8 governing the derivation. New Story 7.

3. **`system-instructions.md`'s `required_skills:` status claim is now false and is corrected here.** Line 252 reads *"**Status: adopted** … The first consumer is Phase 10 progressive disclosure ([ADR-021](…)) … Progressive disclosure's extraction work lands the first real declarations."* The phase does not use the field, so the adoption's stated justification never materialised. No other spec owns that file. Also Story 7.

**Everything else in the spec is unchanged**: the METRIC bridge lands first, the absolute cap appends to `structural` directly and never routes through `CONTRACT_CHECK_SEVERITY`, the budget stays pinned rather than derived live, `eval-leanness.py` gains no exemption reader, and Story 6's mutation proof closes the chain. The two-tests-pass-for-the-wrong-reason finding stands exactly as recorded.

### 2026-08-12 (c) — Two orphaned obligations assigned here

Both surfaced during the mechanism ruling. Neither has another owner: every
disclosure spec is barred from `scripts/`, and no Phase 10 spec's file set
includes `adapters/`.

**(i) Inline reads have no resolution check.** `check_required_skills()`
(`scripts/eval-leanness.py:712`) resolves `required_skills:` frontmatter only.
The phase moves its entire skill-loading surface — **35 skills** — from a
mechanism *with* a resolution check to one *without*. A mistyped
`Read skills/tdd-cyle/SKILL.md` is a silent no-op: the gate passes, the skill
never loads, and the command quietly loses a capability with nothing failing.
`scripts/measure-invocation.py` reports it under `unresolved_skills` but always
exits 0 by design, so it cannot gate.

Extend `check_required_skills()` to resolve **both** mechanisms — declared
names and inline `Read skills/<name>/SKILL.md` occurrences — and report the
inline count in `metrics` alongside `required_skills_declarations`, which is
now permanently 0. Without this, the enforcement flip lands a governor that
cannot see the mechanism the phase actually uses.

**(ii) The false first-consumer claim is in four files, not one.**
`system-instructions.md` (Story 7 already owns it) plus
`adapters/cursor.md:217`, `adapters/claude-code.md:396`, and
`adapters/openclaw.md:277` each state that Phase 10 progressive disclosure is
`required_skills:`'s first consumer. The phase rejected that mechanism, so all
four are false. Story 7 extends to the three adapters, correcting the claim
without touching the schema — the convention remains documented and available,
it simply has no consumer and carries a restored 2026-11-11 review trigger.

### 2026-08-12 (d) — Scope corrected: enforce what complies, warn on what does not

The five sibling disclosure specs were **closed unimplemented** after the pilot
measured ~1,017 bytes of overhead per extracted skill and a **+9.7%** worst-path
regression. Five of the six target commands are therefore unconverted and remain
above 24,960 bytes. That splits this spec's deliverable in two, and the split is
the whole point of a governor that is worth reading:

**Flips to blocking `structural` — the surface complies, measured:**
`contract_compliance` reads **31/31** commands with `problem`/`outcome`/
`exit_criteria`, **31/31** with `## Completion`, **5/5** loop-bearing commands
bounded, **7/7** agents. These are Phase 10's determinism half, they shipped in
the foundation, and nothing has regressed them. `CONTRACT_CHECK_SEVERITY` flips.

**Stays non-blocking `warnings` — the surface does NOT comply:**
the absolute per-invocation byte cap. Landing it blocking today makes `eval.sh`
red on five commands nobody is converting, and a permanently-red gate becomes
invisible — the exact failure ADR-021 reason 2 diagnosed and this spec exists to
avoid. It ships **measured and reported**, with the budget recorded and the
per-command overage named, so the number is visible without being a wall.

**This is not a softened deliverable, it is the deliverable applied honestly.**
Business Rule "no exemption to make the flip possible" is upheld precisely by
*not* flipping the half the surface fails. Story 4's compliance gate therefore
gates each half against its own evidence rather than blocking both on the weaker.

The byte cap becomes blocking when a future decision converts the remaining
commands or lowers the base. Recorded against ADR-021's 2026-11-11 review.

## The Binding Budget (maintainer decision, 2026-08-12)

**A command file may not cost more to load than the shared contract it runs inside.**

Budget = the irreducible shared base = **24,960 bytes**. Verified 2026-08-12 against the working tree:

| Component | Bytes |
|---|---|
| `system-instructions.md` | 20,153 |
| `commands/_preamble.md` | 4,807 |
| **Base (`base.bytes` from `scripts/measure-invocation.py`)** | **24,960** |

Every invocation pays that base before it reads a single line of the command it was asked to run. `scripts/measure-invocation.py` already computes it under exactly this name, and the cap reuses that accounting rather than inventing a second one.

### Why bytes, and why this number

The budget is **derived from a measured property, not fitted to a wish**: it is the size of the contract every command already loads. Its selectivity is the evidence that it is the right instrument. Measured 2026-08-12 across the 31 non-infra commands:

| Instrument | Selects | Verdict |
|---|---|---|
| **24,960-byte budget** | exactly **6** files: `implement-story` (52,709), `create-spec` (46,423), `verify-spec` (32,110), `implement-phase` (29,136), `release` (28,589), `ship` (28,371) | **exactly ADR-021's top-6 disclosure targets**, in descending order |
| 400-line cap | **10** files, and **misses `implement-phase` entirely** (321 lines / 29,136 bytes) | selects five files that are already under budget and exempts the fourth-largest command in the product |

Bytes-per-line varies **2.63x** across the command surface — from 34.5 (`commands/migrate.md`) to 90.8 (`commands/implement-phase.md`). A line is not a unit of load. That spread is why `implement-phase.md` is simultaneously the 12th-longest command and the 4th-heaviest, and why a line cap cannot express the budget ADR-021 asked for.

The 2000-line command limit is retired because it has never been within reach of binding: the largest command in the tree is **989 lines**, and the limit is 2.02x that. ADR-021 reason 1, re-measured and still true.

### The line limit's new role belongs to an amendment this spec does not own

`2026-08-12-disclosure-implement-story` owns the ADR-021 amendment recording the bytes-over-lines decision, and specifies it in its Story 1. Read as authored on 2026-08-12, its terms are:

> ADR-021 Decision point 5 (`check_length`'s command limit 2000 → 400 lines) is **superseded as the *binding* instrument** by an absolute byte budget of 24,960 — the measured shared base — **with the 400-line cap retained as a secondary, non-binding tripwire.** The Decision is not reopened; only the unit changes.

**This spec enforces that; it does not re-decide it.** Story 3's first task is to read the landed amendment — the spec that authors it is a dependency, so it precedes this one. If the amendment is absent when Story 3 runs, Story 3 halts and reports. An enforcement spec that invents the rule it enforces is not enforcement.

One measured consequence that spec's Story 1 does not carry, recorded here because this spec is the one that will discover it: **a 400-line tripwire fires on a fully byte-compliant surface.** After the six disclosure specs shrink the top 6, five commands remain over 400 lines while comfortably under budget — `security-audit` (527 lines / 18,230 bytes), `refresh-command` (506 / 20,493), `status` (478 / 22,874), `plan-product` (443 / 24,753), `create-uat-plan` (417 / 16,239). "Non-binding" is what makes that survivable — five *notes* rather than five *findings* — but five standing notes is still a standing channel, and standing channels are precisely what instrumentation Business Rule 1 was written to prevent. Business Rule 6 below is the disposition: land the amendment's value, record the firing, escalate.

## Why This Exists

`2026-08-11-governor-instrumentation` shipped a working instrument and, by design, no teeth. Verified 2026-08-12 against the working tree:

- `python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json` returns `structural: []` and `warnings: []`.
- `contract_compliance` reads `commands_checked: 31 / commands_with_contract: 31 / commands_with_completion: 31 / loop_commands_checked: 5 / loop_commands_bounded: 5 / agents_checked: 7 / agents_with_contract: 7`. Full saturation.
- `required_skills_declarations: 0`.

Everything the four checks assert is already true. The checks are therefore **currently free** — they cost nothing to satisfy and nothing to violate. That is the definition of an instrument that has finished its job and is waiting to become a gate.

What is *not* yet true is the budget. Six commands exceed 24,960 bytes today, totalling 217,338 bytes against a compliant allowance of 149,760 — **67,578 bytes over**, which is the work the six disclosure specs exist to do. This spec is sequenced behind all six for that reason, and it declares all six as dependencies so `spec-deps.py` computes the order rather than a human remembering it.

### The seam, re-verified

Business Rule 3 of the instrumentation spec promised a one-string flip. Verified 2026-08-12 by loading `scripts/eval-leanness.py` in-process, setting `CONTRACT_CHECK_SEVERITY` to each value, and running `main()` against this repo:

```
shipped default: 'warnings'
  warnings:   rc=0 structural=0 warnings=0
  structural: rc=0 structural=0 warnings=0
```

The seam holds and the constant sits at `scripts/eval-leanness.py:278`, reading `CONTRACT_CHECK_SEVERITY = "warnings"   # -> "structural"`. Both runs report zero because the surface complies — which is the *precondition* being confirmed, not a demonstration that the seam moves findings. That demonstration exists in the committed fixture tests, and Story 6 re-establishes it by mutation.

### Five committed tests break on the flip, and none of them is a bug

Verified by mutation on 2026-08-12: a scratch copy of the repo with the constant flipped to `"structural"` runs `scripts/tests/test_eval_leanness_contract.py` at **81 tests, 5 failures**. Every one of the five asserts the *pre-flip* posture and must be inverted, not deleted:

| Test | Why it fails | Disposition |
|---|---|---|
| `FlipSeamTests.test_shipped_default_is_warnings` | asserts the committed constant is `"warnings"` | invert to assert `"structural"`, with the same "the committed constant must not drift" intent |
| `FlipSeamTests.test_default_routes_everything_non_blocking` | asserts the default sends fixture findings to `warnings` | becomes the blocking-by-default assertion |
| `FlipSeamTests.test_flip_moves_the_identical_dicts_to_structural` | in-process flip is now a no-op | invert the direction: pin `"warnings"` in-process and assert the identical dicts move back |
| `FlipSeamTests.test_main_exits_zero_and_stays_non_blocking_on_a_noncompliant_root` | a non-compliant root is now blocking | becomes "a non-compliant root produces `structural` findings"; the script still exits 0 (`eval.sh` decides FAIL) |
| `EvalShBoundaryTests.test_shipped_severity_passes_the_gate_on_the_same_tree` | the shipped severity now FAILs the non-compliant fixture tree | swap with `test_flipped_severity_fails_the_gate`; the shipped value is the FAIL case |

**Two tests pass after the flip for the wrong reason, and are the more dangerous finding.** `test_the_constant_carries_its_handoff_comment` partitions the source on the literal `CONTRACT_CHECK_SEVERITY = "warnings"` — after the flip that literal survives only inside the handoff comment's diff preview at `scripts/eval-leanness.py:276`, so the test keeps matching the *documentation* instead of the *statement*. `EvalShBoundaryTests._run_leanness_check` has the same anchor: its `helper_source.replace('\nCONTRACT_CHECK_SEVERITY = "warnings"', ...)` becomes a no-op and its `assertIn` passes trivially because the file already holds the requested value. Story 7 of the instrumentation spec recorded this exact trap ("a naive `replace(...)` rewrites the diff preview inside the handoff comment rather than the statement"). It caught the trap in one direction and left it live in the other. Story 5 fixes both anchors; a green test that no longer tests anything is worse than a red one.

## 📋 Business Rules

1. **No exemption is granted to make the flip possible.** `file_has_exemption()` exists (`scripts/eval.sh:185`, a grep for `eval-exempt:` in the file body) and using it to get a command under budget would convert enforcement into decoration. No command, agent, or script file gains an `eval-exempt:` marker in this spec's diff, and `scripts/eval-leanness.py` gains **no exemption reader at all** — the absolute cap has no silencing path by construction, not by policy. A story that finds itself wanting an exemption has found a file the disclosure specs did not finish, and the correct output is a report, not a marker.

2. **The flip is gated on measured compliance, and the gate is a committed assertion.** Before `CONTRACT_CHECK_SEVERITY` changes, a test in the committed suite must assert against the **real repo** — not a fixture — **all three** of: every non-infra command is ≤ 24,960 bytes; `eval-leanness.py` reports zero contract findings with `contract_compliance` fully saturated; and **no command declares `required_skills:`**. "We checked before flipping" is a hope; a committed assertion is a gate, and it keeps guarding after the flip lands. If any assertion is red, the flip does not land and the spec reports what failed and by how much.

   **The third condition is new, added by the 2026-08-12 mechanism ruling** (§ Approved Scope Changes). `required_skills:` is an eager pre-load: the harness loads every declared skill *"before any phase work begins"*, so a declaration moves those bytes into the **floor**, where every invocation pays them. The phase retired the mechanism precisely for that reason, and all six disclosure specs certified their ceilings on the assumption that nothing is declared. **A single stray declaration silently converts a conditional load into an eager one and invalidates every one of those figures** — without changing a byte of any command's own size, so the byte assertion cannot catch it and neither can `check_length`. It is a one-line assertion (`required_skills_declarations == 0`, already computed by `check_required_skills()` and reported in `metrics`) against a failure that is otherwise discovered by someone re-measuring months later and finding the phase's headline numbers were never true.

   Note the asymmetry that makes this cheap: the metric is already there. Story 1 is separately making it *visible* in the report; this rule makes it *binding* in the gate. The two are the same number serving two channels.

3. **An absolute cap is not silenceable by a justification.** `2026-08-11-governor-instrumentation` Story 1 fixed a real defect — `justification` silenced a whole surface at any magnitude forever — and bound it per-metric to a recorded ceiling under schema 3. That fix is not weakened here, and the absolute cap does not participate in it. A justification explains growth against a **baseline**; it has no meaning against an **absolute budget**. The cap therefore reads `.writ/leanness-baseline.json` for nothing, consults no `justifications` map, and is asserted by a test that plants a justification naming the over-budget file and proves the finding survives it.

4. **Every new blocking finding names the exact file and the exact field.** `subject` is `commands/implement-story.md`, `what` gives the measured bytes, the budget, and the overage, and `fix` names the disclosure action. A red gate that says "commands are too big" is a wall; a red gate that says "`commands/implement-story.md` is 52,709 bytes, 27,749 over the 24,960-byte budget" is a work queue. This extends Business Rule 2 of the instrumentation spec into the blocking channel, where the cost of an unactionable finding is a blocked commit rather than an ignored note.

5. **The budget is a pinned absolute whose derivation is itself checked.** Deriving the cap live from `base.bytes` at each run would mean that growing `system-instructions.md` silently raises every command's allowance — a self-raising budget, which is ADR-021 reason 3 rebuilt in a new place. The budget is therefore a **pinned constant of 24,960** carrying its derivation and its measurement date, and a separate non-blocking check asserts that the live base still equals it. Base drift becomes a visible finding demanding a deliberate re-derivation, never a silent allowance increase.

6. **A tripwire that fires on a compliant surface is not a tripwire.** Whatever value the ADR-021 amendment sets for the `check_length` command limit, it must emit **zero** findings and **zero** notes against a byte-compliant tree. Five commands sit between 400 lines and the byte budget today, so a 400-line tripwire is a standing five-note channel from the moment it lands — the same invisibility that ADR-021 reason 2 documents. If the amendment's value fires on a compliant surface, Story 3 does not soften it and does not silently pick a different number: it lands the amendment's value, records the measured firing, and escalates the conflict to the maintainer as a Tier B finding.

7. **The `_preamble` and `spec-lite` limits are untouched.** `check_length()` holds three limits within twenty lines of each other: `spec-lite` at `-gt 100` (`scripts/eval.sh:404`), `_preamble` at `-gt 95` (`scripts/eval.sh:412`), and the command limit at `-gt 2000` (`scripts/eval.sh:423`). Only line 423 is this spec's. `2026-08-11-autonomy-gate-classes` owns the `_preamble` constant and a diff touching it fails review. The proximity is the hazard: a careless regex or a sloppy sed rewrites the wrong one, and both wrong edits look plausible in a diff. Story 3's verification includes asserting lines 404 and 412 are byte-identical to their pre-story state.

8. **`MAX_SKILLS` is re-derived from a rule, never fitted to a count.** Added 2026-08-12 with the ownership transfer (§ Approved Scope Changes). The prohibited move is the one `2026-08-11-autonomy-gate-classes` Business Rule 1 names: *"a cap chosen after the fact to accommodate whatever was written is not a cap."* Raising `MAX_SKILLS` to whatever the phase's roster happens to reach — 35, or 35-plus-headroom — is exactly that, and would be the same defect the `_preamble` cap was protected from. The derivation must therefore satisfy three tests, each of which the fitted number fails:

   - **It is computed from constants that exist for other reasons**, not from the roster it is about to admit.
   - **It can still fire.** A cap that clears the current content by construction has no state in which it speaks, which is ADR-021 reason 1 (*"the limit cannot bind"*) rebuilt in the skills surface.
   - **It moves only when its inputs move**, and each input moves by a deliberate act.

   The derivation and the warn-only decision are in § Detailed Requirements → *`MAX_SKILLS`*. The measured roster is an **input the derivation is answerable to**, not the source of the number: if the phase's 35 had landed above the derived cap, the correct outcome would be a firing cap and a Tier B escalation, not a larger constant.

## Detailed Requirements

### The METRIC bridge defect (Story 1, and it lands first)

`scripts/eval-leanness.py` reports `contract_compliance` and `required_skills_declarations` in its JSON `metrics`. **Neither reaches the eval report.** Verified 2026-08-12 — `scripts/eval.sh`'s `check_leanness()` TSV bridge (`scripts/eval.sh:2828-2847`) prints a fixed METRIC set with a branch for `per_surface` and a branch for `story_context_bytes` and no branch for either contract key. A real run confirms it: the leanness section of the report carries four `Metrics:` lines, and `grep -c "contract_compliance\|required_skills_declarations"` over the report returns **0**.

Two consequences, and the second is why this is Story 1 rather than a footnote:

1. Business Rule 8 of the instrumentation spec — *"a check with nothing to assert reports nothing, and says so in the metrics"* — exists so a vacuous pass is distinguishable from a verified pass. `required_skills_declarations: 0` is that guard, and it is invisible in the only channel a maintainer reads. The guard has been decorative since the day it shipped.
2. This spec is about to make the contract checks blocking. The moment they bind, `contract_compliance` stops being a progress trend and becomes **the denominator of the gate** — the number that says how much of the surface the red or green actually covers. Flipping to blocking while that number is unreadable ships a gate whose coverage nobody can see.

`eval.sh` is in this spec's ownership set, so this is in reach and is taken rather than scoped out. The bridge gains a branch for each key, rendering counts in the same `METRIC` shape the existing lines use, and the legacy first `METRIC` line is left byte-identical for the Tier B consumers its own comment protects.

### The absolute per-invocation byte cap (Story 2)

A new check in `scripts/eval-leanness.py`, blocking unconditionally.

```python
# ADR-021 reason 3: "a ratchet is not a budget." The per-surface delta ratchet
# in check_baseline() stays exactly as it is; this is an absolute ceiling
# alongside it, and the two answer different questions.
#
# The budget is the irreducible shared base a command runs inside — measured
# 2026-08-12 as system-instructions.md (20,153) + commands/_preamble.md (4,807).
# Pinned, not derived live: a live derivation lets base growth raise every
# command's allowance silently, which is reason 3 rebuilt (Business Rule 5).
COMMAND_BYTE_BUDGET = 24960
COMMAND_BYTE_BUDGET_DERIVED = "2026-08-12: system-instructions.md + commands/_preamble.md"
```

**Accounting is reused, never re-invented.** `scripts/measure-invocation.py` already reports `base.bytes`, and per command `command_bytes`, `floor_bytes`, `conditional_bytes`, and `ceiling_bytes`. It loads `eval-leanness.py` by path to reuse *its* parsers (`all_command_files`, `is_infra`, `read_frontmatter`, `parse_skill_names`), so the dependency runs measure→leanness and cannot be reversed without a cycle. The cap therefore lives in `eval-leanness.py` and computes `command_bytes` with the same definition `measure-invocation.py` uses — raw byte length of the command file — and a test asserts the two agree per command against the real repo. One accounting, two readers.

**The cap binds on `command_bytes`, not `floor_bytes` or `ceiling_bytes`.** The maintainer decision is about the command file. `floor_bytes` includes the base, which no command can shrink, so capping it would charge every command for a cost it cannot control. `ceiling_bytes` includes declared skills, and ADR-021 caveat 2 warns that disclosure can *raise* total load — a command that pulls every skill costs more than the monolith did. That risk is real and is made **visible as a metric, not a second gate**: `per_command_invocation` in `metrics` reports `command_bytes` / `floor_bytes` / `ceiling_bytes` for each command, so caveat 2 is observable in the channel Story 1 just repaired. Adding a second budget for it is a decision this spec does not have and does not take.

**Severity is unconditional.** The cap does **not** route through `emit_contract_findings()` and does **not** consult `CONTRACT_CHECK_SEVERITY`. It appends to `structural` directly. Routing it through the seam would make one string control both the contract checks and the budget, so a future un-flip would silently disable the budget too — and ADR-021 reason 3 asked for a cap that fails, full stop. The seam governs the four contract checks it was built for; the cap is its own decision.

**Infra is excluded by the existing rule.** `commands/_preamble.md` is base, not a command, and is excluded via `is_infra()` / `INFRA_PREFIXES` — the same reuse Business Rule 7 of the instrumentation spec established. Hardcoding the filename anywhere is a defect.

### The `check_length` command limit (Story 3)

Ownership is one line: `scripts/eval.sh:423`, `if [ "$count" -gt 2000 ]`, and the `add_finding` beneath it. Lines 404 and 412 are out of bounds (Business Rule 7).

The disposition is the ADR-021 amendment's to state and this story's to enforce. The two things the story must do regardless of the value the amendment sets:

- **Retire the 2000.** It has never been within 2x of the largest file in the tree and cannot bind. Leaving it in place beside a real budget teaches a reader that the line count is a governed quantity when it is not.
- **Point the reader at the binding gate.** Whatever remains at line 423 carries a comment naming `COMMAND_BYTE_BUDGET` as the limit that actually binds and citing the amendment, so a maintainer who trips the tripwire is not left thinking lines are the budget.

If the amendment's value fires against a compliant surface, Business Rule 6 governs: land it, record the firing, escalate.

### The compliance pre-check gate (Story 4)

A test in the committed suite, running against the real repo, asserting **all** of:

1. Every non-infra command is ≤ `COMMAND_BYTE_BUDGET`, listing every violator with its measured bytes and overage on failure.
2. `eval-leanness.py --root <repo>` returns `structural: []` under the shipped severity **and** `[]` under an in-process `"structural"` pin — the second is what proves the flip is safe *before* it is thrown.
3. `contract_compliance` is saturated: `commands_with_contract == commands_checked`, `commands_with_completion == commands_checked`, `loop_commands_bounded == loop_commands_checked`, `agents_with_contract == agents_checked`.

This runs green only if the six disclosure specs finished the job. If it is red, **the spec halts here** and its output is the report constraint 3 demands: which files, how many bytes over, which disclosure spec owned each. Story 5 never starts. Granting an exemption to turn it green is Business Rule 1's prohibition, and reaching for one is the failure this rule exists to catch.

The test stays in the suite after the flip. It is the regression guard for the state the flip depends on, and it fails loudly if a later commit pushes a command back over budget — before that commit reaches the gate and turns the whole run red for a reason nobody can locate.

### The flip (Story 5)

One string at `scripts/eval-leanness.py:278`:

```
-CONTRACT_CHECK_SEVERITY = "warnings"   # -> "structural"
+CONTRACT_CHECK_SEVERITY = "structural"
```

Plus, and this is the larger part of the story: the five inverted tests, the two broken anchors, and the handoff comment. The comment at `scripts/eval-leanness.py:262-277` documents a flip that has now happened; it is rewritten to record **when** it was thrown, **what precondition Story 4 verified**, and **what un-flipping would mean** — so the next reader finds the history at the constant rather than in a spec folder, exactly as instrumentation Story 7 intended.

The `# -> "structural"` trailing marker is removed. Leaving it reads as a pending action and is the sort of stale instruction `2026-08-11-retire-dead-prescription` exists to delete.

### The mutation proof (Story 6)

A green suite proves nothing about a gate. Story 6 proves the gate would go red on a **real** regression, by causing one and reverting it:

- Append bytes to a real command file until it crosses 24,960; assert `bash scripts/eval.sh --check=leanness` exits non-zero and the report names that file with its overage; revert; assert green.
- Delete a `problem:` field from a real command; assert FAIL naming that file and field; revert; assert green.
- Remove a `## Completion` section; same; revert; same.
- Delete a `loop.max_iterations`; same; revert; same.
- Plant a bound justification in `.writ/leanness-baseline.json` naming the over-budget file at its inflated value; assert the cap **still** fails (Business Rule 3); revert.

Mutations happen on a scratch copy or through a fixture root — never on the committed tree, per the discipline instrumentation Story 7 established for its `eval.sh` boundary test. The story's exit condition is a clean `git status` and a green `bash scripts/eval.sh`.

`scripts/eval-loop-bounds.py`'s `governor-boundary-intact` scenario (`scripts/eval-loop-bounds.py:539-555`) cross-reads `eval-leanness.py` for the literal `check_loop_bounds` and emits pass/skip on its presence. Nothing in this spec renames or removes that function, so the scenario stays passing — and Story 6 asserts it, because "we did not touch it" is not evidence.

### `MAX_SKILLS` (Story 7)

`scripts/eval-leanness.py:71`, `MAX_SKILLS = 12`, inside the block commented *"Count ceilings — headroom over today's 31/7/6 so the tripwire stays silent until genuine growth, then speaks once (warn-only, never blocking)."* Consumed by `check_ceilings()` at `:1132`.

**The measured pressure.** Counted from the six disclosure specs' authored rosters on 2026-08-12:

| Spec | New skills |
|---|---:|
| `2026-08-12-disclosure-implement-story` | 8 |
| `2026-08-12-disclosure-create-spec` | 5 |
| `2026-08-12-disclosure-release` | 5 |
| `2026-08-12-disclosure-verify-spec` | 4 |
| `2026-08-12-disclosure-ship` | 4 |
| `2026-08-12-disclosure-implement-phase` | 3 |
| **New** | **29** |
| Existing | 6 |
| **Post-phase total** | **35** |

All 29 names are distinct across the six rosters; there is no double-count. **Correction to the record while raising it:** `2026-08-12-disclosure-ship` § Technical Concerns states *"at least 29 skills"* as a **total**. It reaches 29 only by counting `create-spec` and `release` at +4 each instead of +5 and omitting `verify-spec` entirely. The measured total is **35**, and this spec is the one that will be held to it.

#### The derivation

**`MAX_SKILLS = MAX_COMMANDS + MAX_AGENTS = 35 + 10 = 45.`**

Under [ADR-021](../../decision-records/adr-021-progressive-disclosure-token-budget.md) a skill is not an independent artifact. It exists only because a **consumer** — a command or an agent — extracted a capability out of itself, and ADR-021 §4 requires shared capability rather than per-consumer copies. So the skill population is structurally bounded by the consumer population, and that population already carries two deliberate ceilings **in the same block of the same file, set for their own reasons**: `MAX_COMMANDS = 35` and `MAX_AGENTS = 10`.

**One skill per potential consumer is the boundary where extraction has stopped producing shared capability and become a 1:1 shadow of the consumer surface.** Above that line, `skills/` is not disclosure; it is duplication with an extra layer of indirection — precisely the *"two copies instead of one shared skill"* failure ADR-021 §4 names, expressed as a count. That is what the number means, and it is the only thing a count *can* meaningfully mean here.

Against Business Rule 8's three tests:

| Test | Result |
|---|---|
| Computed from constants that exist for other reasons | **Yes** — `MAX_COMMANDS` and `MAX_AGENTS` were set by the leanness-instrumentation work and are not touched here. The derivation never reads the roster. |
| Can still fire | **Yes** — post-phase 35 against 45 leaves 10 of headroom. A second disclosure programme of this size (the next-heaviest commands, `implement-spec` among them — ADR-021 §4 explicitly anticipates it) crosses it. |
| Moves only when its inputs move | **Yes** — and each input moves only by a deliberate edit to a named constant. |

The counterfactual is the test that matters: **had the phase's roster come in at 50 skills, this derivation would still yield 45 and the cap would fire.** A number derived from the roster could not do that, which is the whole difference between a cap and an accommodation.

Recorded alongside the constant: the derivation, the date, the measured post-phase count of 35, and the 10 remaining headroom — so the next reader sees why 45 and not what 45 was made to fit.

#### It stays warn-only, and the reason is the phase's own central finding

**Decision: `MAX_SKILLS` remains a warning, in `check_ceilings()`, non-blocking. It is not promoted alongside the byte cap.** Stated explicitly because the surrounding spec makes four other things blocking, and silence would read as an oversight.

**A count is not a unit of load.** That is ADR-021's finding and this phase's evidence: `commands/implement-phase.md` is 321 lines — comfortably inside any plausible line cap — while being the 4th-heaviest command in the product and 4,176 bytes over budget. Story 3 of this spec retires a 2000-line limit for exactly that reason. Making a *skill count* blocking would re-commit the same error one surface over: a gate on a quantity that does not measure what anyone cares about.

Three further reasons, each independently sufficient:

- **It would block the fix.** Under the 2026-08-12 mechanism ruling, skills load conditionally — a skill on a path a run does not take costs that run **nothing**. Extraction is the action that *lowers* per-invocation load. A blocking count cap would make the remedy the offence.
- **Bytes are already governed, correctly.** The `skills` surface is in `SURFACE_REGISTRY` and under ADR-019's per-surface ratchet with the schema-3 bound-justification mechanism. Every disclosure spec is already required to file a bound justification for its skill-surface growth. **The blocking instrument for skill bloat exists and is measured in bytes.** The count is a tripwire against proliferation, which is a different question and correctly a softer one.
- **The load ceiling that would supersede it is out of scope here.** A budget on `ceiling_bytes` is explicitly deferred by this spec pending post-disclosure data. If one is ever adopted, the count cap becomes **redundant, not stricter** — and that is the condition under which to revisit it, recorded now so the revisit has terms.

### The `required_skills:` status correction (Story 7)

`system-instructions.md:252` currently reads:

> **Status: adopted.** The convention's review trigger fired on **2026-08-03** … the recorded outcome is **revisit → adopt**. The first consumer is Phase 10 progressive disclosure ([ADR-021](…)), which needs a declarative, harness-resolved, per-invocation load mechanism … Progressive disclosure's extraction work lands the first real declarations; no agent or command declares the field yet.

**Three of those claims are now false.** Phase 10 is not the first consumer, it does not need the mechanism, and its extraction work lands **zero** declarations. The 2026-08-03 trigger resolved *revisit → adopt* on a justification that consisted almost entirely of a named future consumer, and that consumer evaluated the mechanism and rejected it — for a measured reason the record should carry: **the field is an eager pre-load, so extraction under it moves bytes into the floor and makes a command cost more per invocation than the monolith it replaced.**

**The correction has two parts, and the second is the one that matters.**

1. **The status claim.** Deprecating the convention outright is not this spec's decision — the schema is referenced by `commands/new-skill.md`, implemented in all three adapters, and validated by `check_required_skills()`; removing it is ADR-scale. The schema stays documented **unchanged**. What changes is the status paragraph: it records that Phase 10 evaluated the mechanism and did not adopt it, states the eager-pre-load reason with its two sources (`system-instructions.md` § Harness contract; `adapters/claude-code.md:396`), and records that **the convention still has no consumer**.

2. **The review trigger is restored, and this is the substantive half.** The original trigger's resolution was justified by a consumer that never arrived. **A resolution whose premise turned out to be false should not survive as a settled adoption** — that is how a convention accretes permanence it never earned, and `2026-08-11-retire-dead-prescription` exists because this repo has that failure mode. Restoring the trigger is the honest disposition; recording *why not* would require an argument that the adoption stands on something other than the consumer it named, and there is none.

   **Recommended trigger date: 2026-11-11**, aligned to ADR-021's own review trigger rather than a fresh 90-day clock. The reasoning: that review already asks whether measured per-invocation load dropped for at least 4 of the 6 targeted commands. **The same review is in the best position to answer whether an eager mechanism ever acquired a consumer**, because it is reading exactly the data that would justify one. Two triggers, one reading, no second calendar entry to forget. Terms: if no command or agent declares `required_skills:` by that date, deprecate; if one does, record it and reset.

**Sizing note, and it interacts with Business Rule 5.** `system-instructions.md` is 20,153 of the 24,960-byte `COMMAND_BYTE_BUDGET` derivation. Editing it changes `base.bytes`, so **this spec becomes the cause of its own `check_budget_derivation()` finding**. That is handled, not avoided — see § Technical Concerns.

## Out of Scope

- **Shrinking any command, agent, or skill file.** The six disclosure specs own the migration. If this spec finds a file over budget, it reports it; it does not fix it. An enforcement spec that edits the surface it measures cannot tell you whether the surface complied.
- **`scripts/eval.sh`'s `spec-lite` limit (line 404) and `_preamble` limit (line 412).** Business Rule 7. `2026-08-11-autonomy-gate-classes` owns the `_preamble` constant.
- **Weakening the schema-3 bound-justification mechanism.** `2026-08-11-governor-instrumentation` Story 1 fixed a live defect. The per-metric binding, the recorded ceiling, the "down is free" precedence, and the `--update-baseline` reset all stay exactly as they are. This spec adds a check that ignores justifications; it changes none of their semantics.
- **The per-surface delta ratchet.** `check_baseline()` is untouched. ADR-021 is explicit that the absolute cap lands *alongside* the ratchet, not in place of it — they detect different things, and a spec that replaced one with the other would lose drift detection to gain a ceiling.
- **A second budget for `ceiling_bytes` or `floor_bytes`.** ADR-021 caveat 2 is real, and this spec makes it visible as a metric. Gating on it is a decision that needs the post-disclosure data this spec is the first to produce.
- **Amending ADR-021.** `2026-08-12-disclosure-implement-story` owns the amendment. This spec reads it and enforces it. If it is absent, Story 3 halts.
- **`.writ/product/roadmap.md`'s Phase 10 Success Criteria — still not this spec's.** `2026-08-12-disclosure-implement-story` hands `governor-enforcement` four obligations: the byte cap, the severity flip, *"the `MAX_SKILLS` raise,"* and the stale roadmap criterion (*"No command file exceeds **400 lines** without a tracked exemption"* — which names both the demoted unit and an exemption path Business Rule 1 forbids for the budget), reasoning that *"that spec has to edit the criterion when it changes the code."*

  The reasoning is sound and the assignment conflicted with this spec's locked contract, which names its owned files exhaustively. **That conflict is now half resolved.** This entry originally offered two exits — *"either the maintainer widens this spec's file set to cover them, or a later spec picks them up"* — and on 2026-08-12 the maintainer took the first, for two of the three items: **`MAX_SKILLS` and `system-instructions.md` are now in scope** (§ Approved Scope Changes, Story 7). `MAX_SKILLS` had been flagged by five sibling specs and could be taken by none of them, because every disclosure spec bars itself from `scripts/`; it was the one obligation in the phase with no possible owner.

  **`.writ/product/roadmap.md` was not widened and remains out of scope.** Its stale 400-line criterion still needs an owner before Phase 10 closes. Taking it unilaterally would still put a diff outside the locked contract in front of a reviewer who was told the file set was exhaustive — and the fact that two adjacent items were granted is a reason for more care here, not less: a granted scope change is evidence the maintainer draws these lines deliberately.

- **Deprecating or redesigning the `required_skills:` convention.** Story 7 corrects a false status claim and restores a review trigger. It does **not** remove the schema, change it, alter `check_required_skills()`, or touch the three adapters' descriptions of the harness mechanism (which are accurate — the mechanism *is* eager). Deprecation is ADR-scale and belongs to the restored trigger's review, not to an enforcement spec.

- **Adding a governor check that resolves inline `Read skills/<name>/SKILL.md` calls.** `check_required_skills()` resolves frontmatter declarations only (`scripts/eval-leanness.py:712`), so the phase's 29 inline reads have **no** standing enforcement. Recorded in § Technical Concerns and escalated. It is new checker behavior, not enforcement of an existing decision, and this spec is already flipping four checks to blocking in the same file — the correct instinct is one gate change per spec.
- **`status:` / `evidence:` (ADR-014 vocabulary) on commands and agents.** Listed under the roadmap's "Make the governor bite" feature and deferred by the instrumentation spec for the same reason: it is contract *content* with no consumer until `/refresh-command`'s Evidence Gate is wired for it.

## Technical Concerns (surfaced at contract time)

- **All six dependencies now exist, and none has been implemented.** They were authored on 2026-08-12 alongside this spec. `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` returns `status: ok` and places `2026-08-12-governor-enforcement` **immediately after all six disclosure specs** in the topological order — the sequencing this spec's safety rests on, computed rather than remembered. They are `Status: Not Started`, so every byte-budget figure here is a pre-disclosure measurement: **six commands over budget by 67,578 bytes**. Story 4 is where "the disclosure specs finished" stops being an assumption. The dependencies are not to be removed to quiet anything — the ordering they encode is the entire reason this spec can flip a gate safely.

- **A sibling spec asserts a figure this spec measured differently.** `2026-08-12-disclosure-implement-story`'s spec.md states a 400-line cap *"would also fire on `migrate` (396 lines, 13,656 bytes)."* Measured here on the same tree, `commands/migrate.md` is **396 lines — under 400**, so it would not fire; it is the low end of the bytes-per-line spread (34.5), which is the point that sentence is making, but "fires on" is the wrong verb. That spec's own Story 1 uses the correct example (`create-uat-plan`, 417 lines / 16,239 bytes). Nothing in this spec depends on it, and the ADR amendment's **Measured:** line is the place it matters — flagged so the amendment does not inherit it.

- **ADR-021's own figures are stale, and the drift is upward.** The ADR records `implement-story.md` at 49,360 chars / 961 lines and the surface at 516,589 chars. Measured 2026-08-12: 52,709 bytes / 989 lines, and `per_surface.commands.chars` is **560,772**. The ADR also states `_preamble.md` is held to 80 lines; `scripts/eval.sh:412` holds it to 95. None of this changes any decision here — the budget is computed from today's base, not from the ADR's numbers — but a story quoting ADR-021's figures as current will quote them wrong. Re-measure.

- **The pinned budget will drift out of its own derivation — and after 2026-08-12, this spec is one of the causes.** `system-instructions.md` and `commands/_preamble.md` are live files under active Phase 10 work; `_preamble.md` in particular is `2026-08-11-autonomy-gate-classes`'s target. The instant either changes, `COMMAND_BYTE_BUDGET` stops equalling `base.bytes`. Business Rule 5 makes that a visible non-blocking finding rather than a silent divergence, but somebody still has to decide what to do about it, and the honest answer is that the budget should be re-derived deliberately and re-recorded with a date — not auto-tracked.

  **What changed is who trips it.** Story 7 edits `system-instructions.md`, which is 20,153 of the 24,960-byte derivation. So this spec now **causes its own base-drift finding**, in a check it wrote two stories earlier, in the same run. The disposition, decided in advance rather than in the moment:

  1. **`COMMAND_BYTE_BUDGET` is not re-derived by Story 7.** Re-deriving mid-spec would move the number Story 4's gate certified against and Story 6 proved bites, retroactively invalidating both. Business Rule 5's *"re-deriving is a deliberate, dated act"* means a deliberate act **by somebody looking at the whole picture**, not an automatic adjustment by the story that happened to nudge the base.
  2. **Story 7 is therefore sequenced last**, after Story 6. The gate chain 1 → 6 completes against a stable base; the drift lands after the proof, not during it.
  3. **Story 7 records the new `base.bytes`, the delta, and the fact that the budget is unchanged** — which is exactly the output `check_budget_derivation()` was built to produce. The check firing on its own author's edit, in the same run it shipped, is the strongest available demonstration that it works.

- **`required_skills_declarations` is now permanently 0, which changes what Story 1's metric means.** Story 1 surfaces it into the report as instrumentation Business Rule 8's vacuous-pass guard, on the stated expectation — `system-instructions.md:252`, the line Story 7 corrects — that *"progressive disclosure's extraction work lands the first real declarations."* After the ruling, no disclosure spec declares the field, so the count is 0 **by design and indefinitely**, not transiently pre-migration. Story 1's mechanism is unaffected and still right: distinguishing *"0 findings"* from *"0 things checked"* is precisely what that guard exists for, and a permanent 0 is the strongest case for surfacing it. Only the framing was wrong, and Story 7 fixes the sentence it came from. Worth stating plainly so nobody reads the 0 as a Story 1 defect: **`check_required_skills()` will assert nothing for the foreseeable future, and the report will say so.**

- **No check resolves an inline `Read`, so the phase's 29 skill loads are ungoverned.** `check_required_skills()` iterates `fields.get("required_skills", "")` and nothing else (`scripts/eval-leanness.py:682-724`). Under the mechanism ruling every disclosure spec loads its skills inline instead, so a typo'd, renamed, or never-written skill path produces **zero** findings from the gate this spec is about to make blocking. `scripts/measure-invocation.py` does catch it — `_inline_read_skills()` at `:140` feeds `unresolved_skills` plus a lower-bound warning — but it is a read-only measurement that always exits 0 by design. **Net effect: the phase moved its entire skill-loading surface from a mechanism with a resolution check to one without, and the resolution check that remains is not a gate.** Each disclosure spec self-verifies once, in its own verification story, and nothing re-verifies afterwards. Out of scope here (new checker behavior, and one gate change per spec), but it is the most consequential gap the ruling opened and it should not wait long for an owner.

- **The false `required_skills:` consumer claim exists in four files, and the ruling named one.** `system-instructions.md:252` is Story 7's. The identical claim — *"Phase 10 progressive disclosure (ADR-021) is its first consumer"* — also appears verbatim in `adapters/cursor.md:217`, `adapters/claude-code.md:396`, and `adapters/openclaw.md:277`. Those files' *description of the mechanism* is accurate and needs no change: the harness genuinely does pre-load declared skills before the consumer's first phase, which is the fact the escalation rested on. It is only the trailing consumer sentence that is now false, in three places. **Not taken here** — `adapters/` is in no Phase 10 spec's file set, and `2026-08-12-disclosure-implement-phase` explicitly scopes it *"verify, do not edit."* Recorded so the correction is not left half-done by accident: a reader who finds the corrected `system-instructions.md` and then reads an adapter will get the retired claim back, with more confidence for having seen it twice.

- **`plan-product.md` sits 207 bytes under the budget** (24,753 of 24,960). It is the file most likely to convert a routine edit into a blocked commit, and it is not a disclosure target. This is the budget working as intended — a real ceiling produces near misses — but the first maintainer to hit it will experience it as the gate being arbitrary. The finding text is the only defense: it must name the byte count, the budget, and the overage so the response is "trim 300 bytes" rather than "why is this failing."

- **A blocking gate has a failure mode a warning does not: it blocks the fix.** If a command regresses past budget, every subsequent commit fails `eval.sh` until it is trimmed — including a commit that is trimming it, if the trim is staged across two commits. The instrumentation spec never had to think about this because nothing it added could stop work. `file_has_exemption()` is the escape hatch that exists, and Business Rule 1 forbids it here. The disposition is deliberate: the escape hatch for a real emergency is `git revert` of the commit that broke the budget, which is reversible and reviewable, rather than a marker in a file that outlives the emergency by months. Story 6's mutation run is where this gets exercised for real.

- **Two currently-green tests are green for the wrong reason after the flip, and a story that only fixes the five red ones will not notice.** `test_the_constant_carries_its_handoff_comment` and `EvalShBoundaryTests._run_leanness_check` both anchor on the literal `CONTRACT_CHECK_SEVERITY = "warnings"`, which survives the flip inside the handoff comment's diff preview at `scripts/eval-leanness.py:276`. Instrumentation Story 7 documented this trap and defended against it in one direction only. A red test announces itself; a test that silently stops asserting does not. Story 5 owns both anchors, and the verification is that each still fails when the property it claims to check is broken.

- **Story 6's mutation proof is the most likely task to be quietly skipped.** It is slow, it edits real files, and every one of its assertions is about a state the implementer has to deliberately create and then undo. The temptation is to assert the gate's behavior on fixtures and call it done — which is exactly what the existing suite already does, and exactly what cannot tell you whether the *real* gate on the *real* tree bites. If the mutation run genuinely cannot be automated in the harness, record the reduced coverage in the drift log honestly rather than claiming a proof that was not run.

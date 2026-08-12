# Technical Spec: Governor Enforcement

> Source: `.writ/specs/2026-08-12-governor-enforcement/spec.md`

## Verified pre-state (2026-08-12)

Every figure below was measured against the working tree on branch `phase/10-progressive-disclosure`. Re-measure before relying on any of it — the disclosure specs run between this spec's authoring and its implementation, and the whole point is that they change these numbers.

### The governor is green and toothless

```
$ python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json
structural: 0
warnings:   0
contract_compliance: {commands_checked: 31, commands_with_contract: 31,
                      commands_with_completion: 31, loop_commands_checked: 5,
                      loop_commands_bounded: 5, agents_checked: 7,
                      agents_with_contract: 7}
required_skills_declarations: 0
```

Full saturation. The four contract checks assert only things that are already true, which is precisely the state ADR-020's "Enforcement sequencing (load-bearing)" section names as the precondition for flipping.

### The seam holds

```
shipped default: 'warnings'   (scripts/eval-leanness.py:278)
  CONTRACT_CHECK_SEVERITY="warnings"   → rc=0 structural=0 warnings=0
  CONTRACT_CHECK_SEVERITY="structural" → rc=0 structural=0 warnings=0
```

Loaded in-process by `importlib.util.spec_from_file_location`, constant set, `main()` run against this repo. Both runs are zero because the surface complies — this confirms the *precondition*, not that the seam moves findings. The fixture proof of movement lives in `scripts/tests/test_eval_leanness_contract.py`; Story 6 re-establishes it against real files.

### The budget and what it selects

```
system-instructions.md    20,153
commands/_preamble.md      4,807
                        --------
base.bytes                24,960   ← COMMAND_BYTE_BUDGET
```

`scripts/measure-invocation.py --format json` reports this as `base.bytes` with the component split, and per command: `command_bytes`, `command_lines`, `base_bytes`, `floor_bytes`, `conditional_bytes`, `ceiling_bytes`, `resolved_skills`, `unresolved_skills`, `base_share_of_floor`.

Over budget today — 6 files, 217,338 bytes against a compliant allowance of 149,760, **67,578 over**:

| Command | Bytes | Lines | Over by | Bytes/line |
|---|---|---|---|---|
| `implement-story.md` | 52,709 | 989 | 27,749 | 53.3 |
| `create-spec.md` | 46,423 | 871 | 21,463 | 53.3 |
| `verify-spec.md` | 32,110 | 732 | 7,150 | 43.9 |
| `implement-phase.md` | 29,136 | 321 | 4,176 | **90.8** |
| `release.md` | 28,589 | 640 | 3,629 | 44.7 |
| `ship.md` | 28,371 | 627 | 3,411 | 45.2 |

Exactly ADR-021's top-6 disclosure targets, in descending order, and exactly this spec's six declared dependencies.

### Why lines cannot express this budget

Over 400 lines but **under** budget — five files a line cap would gate and a byte budget correctly ignores:

| Command | Lines | Bytes | Headroom |
|---|---|---|---|
| `security-audit.md` | 527 | 18,230 | 6,730 |
| `refresh-command.md` | 506 | 20,493 | 4,467 |
| `status.md` | 478 | 22,874 | 2,086 |
| `plan-product.md` | 443 | 24,753 | **207** |
| `create-uat-plan.md` | 417 | 16,239 | 8,721 |

And `implement-phase.md` is over budget at **321 lines** — a 400-line cap exempts the fourth-heaviest command in the product. Bytes-per-line across the 31 non-infra commands ranges 34.5 (`migrate.md`) to 90.8 (`implement-phase.md`), a 2.63x spread. A line is not a unit of load.

The retiring limit: `-gt 2000` at `scripts/eval.sh:423`, against a maximum observed 989 lines. 2.02x out of reach — ADR-021 reason 1, re-measured.

### `check_length()`'s three limits and their exact addresses

| Line | Limit | Surface | Owner |
|---|---|---|---|
| `scripts/eval.sh:404` | `-gt 100` | `spec-lite.md` files | **not this spec** |
| `scripts/eval.sh:412` | `-gt 95` | `commands/_preamble.md` | **`2026-08-11-autonomy-gate-classes`** |
| `scripts/eval.sh:423` | `-gt 2000` | `commands/*.md` | this spec |

Eight and eleven lines apart. Any `sed`, regex, or replace-all that is not anchored on the loop it belongs to will hit the wrong one, and all three edits produce a plausible-looking diff. ADR-021 states `_preamble.md` is capped at 80; the code says 95 — do not "correct" the code to match the ADR.

## Component 1 — the METRIC bridge (Story 1)

### The defect, reproduced

`scripts/eval.sh:2828-2847` is a heredoc'd Python one-shot that flattens `eval-leanness.py`'s JSON into TSV for the bash reader. It prints:

- one legacy aggregate `METRIC` line (explicitly protected by its own comment for Tier B consumers that read only the first),
- a `per_surface` line, guarded by `if "per_surface" in m`,
- a product-rollup line inside the same guard,
- a `story_context_bytes` line with its proxy disclaimer, guarded by `if "story_context_bytes" in m`.

There is **no branch for `contract_compliance` and none for `required_skills_declarations`.** A real run confirms the consequence: the leanness section of the report carries four `Metrics:` lines and `grep -c "contract_compliance\|required_skills_declarations"` over it returns **0**.

### Why it matters more after the flip than before

Business Rule 8 of `2026-08-11-governor-instrumentation` exists so a vacuous pass is distinguishable from a verified pass — `required_skills_declarations: 0` is that guard, and it has been invisible in the maintainer's channel since it shipped. And once the contract checks bind, `contract_compliance` is no longer a progress trend: it is the **denominator of the gate**, the number that says how much surface the red or green covers. A gate whose coverage is unreadable is a gate you cannot reason about.

### The change

Two guarded branches in the same shape as the existing ones, e.g.:

```python
if "contract_compliance" in m:
    cc = m["contract_compliance"]
    print("METRIC\tcontract_compliance: %s" % ", ".join(
        "%s=%s" % (k, v) for k, v in cc.items()))
if "required_skills_declarations" in m:
    print("METRIC\trequired_skills_declarations=%s" % m["required_skills_declarations"])
```

Constraints:
- The legacy first `METRIC` line stays **byte-identical**. Its comment names the consumers it protects.
- `clean()` handles tabs and newlines already; the bash `while IFS=$'\t' read -r kind a b c` loop splits on tabs, so a value containing a tab would shift fields. Keys and integer counts cannot, but the rendering must not introduce one.
- Absent keys emit nothing rather than `None` — an older `eval-leanness.py` (a mismatched install) must not print `contract_compliance: None` into a report.

## Component 2 — the absolute cap (Story 2)

### Placement and severity

New pure function in `scripts/eval-leanness.py`, wired in `main()` **outside** the `emit_contract_findings()` block:

```python
structural += check_command_budget(root, metrics)
```

Not `emit_contract_findings(check_command_budget(root), structural, warnings)`. The distinction is load-bearing: routing the cap through the seam would put the budget and the four contract checks behind one string, so any future un-flip — or the typo-fallback that sends an unrecognised value to `warnings` — would silently disable the budget as collateral. ADR-021 reason 3 asked for a ceiling that fails. It fails unconditionally.

The `emit_contract_findings()` router keeps its current signature and its `severity or CONTRACT_CHECK_SEVERITY` behavior (`scripts/eval-leanness.py:303-315`) untouched, including the `"warnings"` pin used by `check_required_skills`.

### The constants

```python
# ADR-021 reason 3: "a ratchet is not a budget." check_baseline()'s per-surface
# delta ratchet stays exactly as it is; this is an absolute ceiling alongside
# it. They answer different questions: the ratchet detects drift from a
# recorded floor, the budget refuses a size regardless of history.
#
# The budget is the irreducible shared base every invocation pays before it
# reads the command it was asked to run:
#     system-instructions.md   20,153
#     commands/_preamble.md     4,807
#                              ------
#                              24,960   (measure-invocation.py -> base.bytes)
#
# PINNED, not derived live. A live derivation means growing
# system-instructions.md silently raises every command's allowance — reason 3
# rebuilt in a new place. Base drift is reported by check_budget_derivation()
# as a non-blocking finding so re-deriving is a deliberate, dated act.
COMMAND_BYTE_BUDGET = 24960
COMMAND_BYTE_BUDGET_DERIVED = "2026-08-12: system-instructions.md + commands/_preamble.md"
```

### Accounting reuse, and the dependency direction

`scripts/measure-invocation.py` loads `eval-leanness.py` by path (`_load_leanness()`) to reuse its parsers — `all_command_files`, `is_infra`, `read_frontmatter`, `parse_skill_names`. The dependency runs **measure → leanness** and cannot be reversed without a cycle. The cap therefore lives in `eval-leanness.py` and uses the identical definition of `command_bytes` (raw byte length of the file, `len(open(path,'rb').read())`).

A test asserts the two agree per command against the real repo. Two implementations of "how big is this command" that can disagree is a defect waiting for the first file that reads differently in one than the other.

### What is capped

`command_bytes` only.

- `floor_bytes` = base + command. Includes a cost no command can influence; capping it charges every command for `system-instructions.md`.
- `ceiling_bytes` = floor + every declared skill. ADR-021 caveat 2 warns disclosure can *raise* total load — a command that ends up pulling every skill costs more than the monolith did. That risk is **made visible, not gated**: `metrics` gains `per_command_invocation` reporting `command_bytes` / `floor_bytes` / `ceiling_bytes` per command, so caveat 2 is observable in the channel Story 1 just repaired. Gating on it needs post-disclosure data this spec is the first to produce, and is not a decision this spec has.

`is_infra()` excludes `commands/_preamble.md` — it is base, not a command. No filename is hardcoded (Business Rule 7 of the instrumentation spec).

### Finding shape

```python
{
  "subject": "commands/implement-story.md",
  "what": "52709 bytes, over the 24960-byte per-invocation budget by 27749 "
          "(211% of budget). A command may not cost more to load than the "
          "shared contract it runs inside.",
  "fix": "Extract procedural detail to skills/<name>/SKILL.md and declare it "
         "in required_skills: (ADR-021). Budget derivation: "
         "system-instructions.md + commands/_preamble.md, measured 2026-08-12.",
}
```

Business Rule 4: the exact file, the measured value, the budget, and the overage. A maintainer whose commit is blocked must be able to act from the finding alone. The `fix` names the remedy ADR-021 prescribes — never "add an exemption", which Business Rule 1 forbids and which the code cannot do anyway.

### Non-silenceability, by construction

- `check_command_budget()` does not receive the baseline and does not read `.writ/leanness-baseline.json`.
- It does not consult `justifications`, `justification`, or any schema-3 field.
- `eval-leanness.py` gains **no** `file_has_exemption` equivalent and no `eval-exempt:` reader. `file_has_exemption()` lives in `scripts/eval.sh:185` and is a grep for `eval-exempt:` in the file body; it governs `check_length`, `check_manifest`, and their peers. It has never applied to `eval-leanness.py`, and this spec does not introduce it.

The test that proves it: plant `surfaces.commands.justifications.chars = {value: <inflated>, date, text}` in a fixture baseline, run against a fixture root holding an over-budget command, assert the `structural` finding is present and unchanged. A justification explains growth against a **baseline**. It has no meaning against an **absolute budget**, and the code must make that structural rather than documentary.

### Budget derivation drift

A separate non-blocking check:

```python
def check_budget_derivation(root) -> list[dict]:   # -> warnings
    """COMMAND_BYTE_BUDGET is pinned; the base it was derived from is live."""
```

Compares live `system-instructions.md` + `commands/_preamble.md` bytes to `COMMAND_BYTE_BUDGET`. On mismatch, a warning naming the recorded derivation, the recorded value, the live value, and the delta — and stating explicitly that the budget is **unchanged** until somebody re-derives it deliberately.

Expect this to fire during Phase 10: `_preamble.md` is `2026-08-11-autonomy-gate-classes`'s target, and `system-instructions.md` is under active edit. That is the check working. It must never auto-adjust `COMMAND_BYTE_BUDGET`.

## Component 3 — the `check_length` command limit (Story 3)

Ownership: `scripts/eval.sh:423` and the `add_finding` beneath it. Nothing else in `check_length()`.

The disposition is stated by the ADR-021 amendment owned by `2026-08-12-disclosure-implement-story` Story 1. **Read it; enforce it; do not re-decide it.** If the amendment is absent, Story 3 halts and reports — an enforcement spec that invents its own rule is not enforcement.

As that spec specifies the amendment on 2026-08-12: Decision point 5's 2000 → 400 line change is *superseded as the binding instrument* by the 24,960-byte budget, *"with the 400-line cap retained as a secondary, non-binding tripwire."* Expected shape of the edit: `-gt 2000` → `-gt 400`, and `add_finding` → `add_note`. **Verify against the landed amendment text**, not against this paraphrase — a sibling spec's description of a record is not the record.

Two things the story does regardless of the value:

1. **The 2000 goes.** It is 2.02x the largest file in the tree and has never been within reach of binding. Leaving it beside a real budget teaches a reader that line count is a governed quantity when it is not.
2. **Line 423 points at the binding gate.** Whatever remains carries a comment naming `COMMAND_BYTE_BUDGET` as the limit that actually binds, citing the amendment, so a maintainer who trips a line tripwire is not left believing lines are the budget.

**The measured conflict, recorded for whoever writes the amendment.** A 400-line tripwire fires **five times on a fully byte-compliant surface** (`security-audit`, `refresh-command`, `status`, `plan-product`, `create-uat-plan` — all over 400 lines, all under budget, headroom 207 to 8,721 bytes). Five standing findings, or five standing notes, is the ignored-channel failure ADR-021 reason 2 documents and the instrumentation spec's Business Rule 1 was written to prevent. Business Rule 6 governs the response: land the amendment's value, record the measured firing, escalate as a Tier B finding. Do not soften it and do not quietly substitute a different number.

**Verification, mandatory:** after the edit, assert `scripts/eval.sh` lines 404 and 412 are byte-identical to their pre-story state. A diff touching the `_preamble` constant fails review.

## Component 4 — the pre-flip gate (Story 4)

A committed test running against the **real repo**, not a fixture. **Four** assertions, all of which must hold:

| # | Assertion | Failure output |
|---|---|---|
| 1 | every non-infra command ≤ `COMMAND_BYTE_BUDGET` | every violator, its bytes, its overage, and which disclosure spec owned it |
| 2 | `structural == []` under the shipped severity **and** under an in-process `"structural"` pin | the findings that would become blocking |
| 3 | `contract_compliance` saturated on all four pairs | the unsaturated pair and its counts |
| 4 | **`required_skills_declarations == 0`**, cross-checked by a direct frontmatter grep over `commands/*.md` | the declaring file and the skill names it declares |

Assertion 2 is the one that makes this a gate rather than a report: it runs the post-flip world *before* the flip and proves it green. Assertion 1 covers the budget, which the contract checks do not measure. **Assertion 4, added by the 2026-08-12 mechanism ruling, covers the loading mechanism, which neither of the others can see.** Together they are the complete precondition.

**Why assertion 4 needs its own row.** `required_skills:` is an eager pre-load: the harness loads every declared skill *"before any phase work begins"*, so a declaration moves those bytes into the **floor**, where every invocation pays them. The six disclosure specs each certified a ceiling on the assumption that nothing is declared. A stray declaration — a copy-paste from `commands/new-skill.md`'s worked example, or a well-meant "make the skills discoverable" edit — invalidates every one of those figures **without changing a single command's own byte count**. Assertion 1 measures file size and cannot see it. `check_length` measures lines and cannot see it. The only symptom is a number in a report nobody re-derives.

The metric already exists: `check_required_skills()` computes `required_skills_declarations` and `main()` reports it at `scripts/eval-leanness.py:1243`. Story 1 makes it *visible* in the report; this assertion makes it *binding* in the gate — the same number serving two channels. **Cross-check it against a direct grep** so that a future change to `parse_skill_names()` cannot turn a green assertion into a vacuous one. That is task 4.3's empty-tree lesson applied to a different parser.

**Green only if the six disclosure specs finished.** Red → **the spec halts at Story 4**. Its output is the report constraint 3 demands: which files, how many bytes over, which spec owned each. Story 5 never starts. There is no exemption path and reaching for one is the failure Business Rule 1 exists to catch.

The test stays in the suite permanently. Post-flip it is the regression guard for the state the flip depends on, and it fails with a precise, file-naming message *before* a regression reaches the gate and turns the whole run red for a reason nobody can locate.

## Component 5 — the flip (Story 5)

```
scripts/eval-leanness.py:278
-CONTRACT_CHECK_SEVERITY = "warnings"   # -> "structural"
+CONTRACT_CHECK_SEVERITY = "structural"
```

The trailing `# -> "structural"` marker is removed. Leaving it reads as a pending action — exactly the stale-instruction class `2026-08-11-retire-dead-prescription` exists to delete.

### The five tests that break

Verified by mutation on 2026-08-12: a scratch copy with the constant flipped runs `scripts/tests/test_eval_leanness_contract.py` at **81 tests, 5 failures**. Each asserts the pre-flip posture and is **inverted, not deleted** — deleting them removes the guard against an accidental un-flip.

| Test | Post-flip form |
|---|---|
| `FlipSeamTests.test_shipped_default_is_warnings` | rename and assert `"structural"`; same "must not drift" intent |
| `FlipSeamTests.test_default_routes_everything_non_blocking` | the default now routes everything **blocking** |
| `FlipSeamTests.test_flip_moves_the_identical_dicts_to_structural` | reverse direction: pin `"warnings"` in-process, assert the identical dicts move back |
| `FlipSeamTests.test_main_exits_zero_and_stays_non_blocking_on_a_noncompliant_root` | a non-compliant root now yields `structural` findings; the script **still exits 0** — `eval.sh` decides FAIL |
| `EvalShBoundaryTests.test_shipped_severity_passes_the_gate_on_the_same_tree` | the shipped severity now FAILs the non-compliant tree; swap roles with `test_flipped_severity_fails_the_gate` |

`test_pinned_required_skills_findings_survive_the_flip` and `test_unrecognised_severity_falls_back_to_warnings` pass unchanged and must keep passing — Business Rule 6 of the instrumentation spec (graceful degradation, `system-instructions.md`) survives this spec intact.

### The two tests that pass for the wrong reason

More dangerous than the five, because a red test announces itself and a silently-inert test does not. Both anchor on the literal `CONTRACT_CHECK_SEVERITY = "warnings"`, which survives the flip inside the handoff comment's diff preview at `scripts/eval-leanness.py:276`:

- `test_the_constant_carries_its_handoff_comment` partitions the source on that literal and inspects the preceding 1,400 characters for `governor-enforcement`, `ADR-020`, `Enforcement sequencing`. After the flip it partitions on the **comment** and keeps passing while asserting nothing about the statement.
- `EvalShBoundaryTests._run_leanness_check` does `helper_source.replace('\nCONTRACT_CHECK_SEVERITY = "warnings"', f'\nCONTRACT_CHECK_SEVERITY = "{severity}"', 1)` then `assertIn`. Post-flip the `replace` finds nothing and the `assertIn` passes trivially because the file already holds the requested value — so `test_flipped_severity_fails_the_gate` "passes" without ever having flipped anything.

Instrumentation Story 7 documented this exact trap ("a naive `replace(...)` rewrites the diff preview inside the handoff comment rather than the statement") and defended one direction only. Re-anchor both — on the statement's own trailing context, or by matching the assignment with a regex anchored to start-of-line and end-of-statement — and verify each still **fails** when the property it claims to check is broken.

### The handoff comment

`scripts/eval-leanness.py:262-277` documents a flip that has now happened. Rewrite it to record: the date thrown, the precondition Story 4 verified (all commands within budget, `contract_compliance` saturated), the governing decisions (ADR-020 "Enforcement sequencing", ADR-021 reason 2), and what un-flipping would mean. Instrumentation Story 7's stated intent was *"the whole handoff is at the constant, not scattered across a spec folder"* — that stays true after the handoff completes.

## Error & Rescue Map

| Failure | Where | Behavior | Rescue |
|---|---|---|---|
| Command file unreadable | `check_command_budget` | one `structural` finding naming the file; no traceback | fix permissions/encoding; the script still exits 0 |
| `commands/` absent | `all_command_files` | zero findings, existing behavior | none needed |
| Zero-byte command | `check_command_budget` | under budget, no finding, no division | none |
| Exactly 24,960 bytes | `check_command_budget` | compliant — `>` not `>=` | asserted explicitly by a test |
| Base drift | `check_budget_derivation` | non-blocking finding; budget unchanged | re-derive deliberately and re-record with a date |
| Justification planted against an over-budget surface | `check_command_budget` | finding unchanged | none — this is the designed behavior (Business Rule 3) |
| `CONTRACT_CHECK_SEVERITY` typo | `emit_contract_findings` | falls back to `warnings`; **the cap stays blocking** | fix the string; the pre-flip gate test catches it |
| Amendment absent when Story 3 runs | Story 3 task 1 | **halt and report** | author the amendment in `2026-08-12-disclosure-implement-story` |
| A command over budget when Story 4 runs | Story 4 | **halt and report** | the owning disclosure spec finishes; never an exemption |
| Mutation left in the tree after Story 6 | Story 6 exit | non-clean `git status` fails the story | `git checkout` the mutated path |
| A command declares `required_skills:` when Story 4 runs | Story 4 assertion 4 | **halt and report**, naming the file and the declared skills | remove the declaration and load the skill inline at its point of need; every ceiling the disclosure specs certified assumed no eager declaration |
| `parse_skill_names()` changes and assertion 4 goes vacuous | Story 4 | the cross-check grep disagrees with the metric | the grep is the tiebreaker — a green assertion that stopped asserting is the same defect as the two tests Story 5 re-anchors |
| Base drift caused by Story 7's own `system-instructions.md` edit | `check_budget_derivation` | non-blocking finding, **expected and by design** | record the new `base.bytes` and the delta; **do not** re-derive `COMMAND_BYTE_BUDGET` — re-deriving mid-spec invalidates what Story 4 certified and Story 6 proved |
| `MAX_SKILLS` derivation questioned in review | Story 7 | — | answer with the counterfactual: name the roster size at which the cap fires. 45 fires at 46. A number that can never fire is an accommodation, not a cap |

## Shadow paths and edge cases

| Case | Expected |
|---|---|
| Compliant tree | `structural: []`, `warnings: []`, `eval.sh` exit 0 |
| `plan-product.md` at 24,753 (207 headroom) | no finding — the likeliest false positive, asserted by name |
| `_preamble.md` | never checked; `is_infra()`, no hardcoded filename |
| An older `eval-leanness.py` without the contract metrics | the METRIC bridge prints nothing for them, never `None` |
| `governor-boundary-intact` (`scripts/eval-loop-bounds.py:539-555`) | still passes — it greps `eval-leanness.py` for the literal `check_loop_bounds`; nothing here renames it, and Story 6 asserts rather than assumes |
| `check_baseline`, `check_parity`, `check_coverage`, `check_ceilings` | untouched |
| `required_skills:` findings | still `warnings` post-flip; the pin outlives the flip |
| `required_skills_declarations` post-phase | **0, permanently** — the mechanism was retired, so the check has nothing to resolve indefinitely rather than transiently. Story 1's guard reports it; Story 4 asserts it; Story 7 corrects the sentence that predicted otherwise |
| An inline `Read skills/<n>/SKILL.md` naming a missing skill | **no finding** — `check_required_skills()` resolves frontmatter only (`:712`). `measure-invocation.py` catches it via `unresolved_skills` but always exits 0. Out of scope, recorded in spec.md → Technical Concerns |
| `MAX_SKILLS` crossed | **warning, never blocking** — by decision, not omission (Component 6). Bytes are the blocking instrument for the skills surface, via ADR-019's ratchet |

## Test strategy

- **Extend** `scripts/tests/test_eval_leanness_contract.py` — the five inverted seam tests and both re-anchored source assertions.
- **New file** for the cap: budget boundary (24,959 / 24,960 / 24,961), infra exclusion, unreadable file, absent directory, the justification-immunity test, the base-drift check, and `command_bytes` agreement with `measure-invocation.py` against the real repo.
- **Story 7's assertions:** the committed `MAX_SKILLS` value (a drift guard in the same spirit as `test_shipped_default_is_warnings`), the skills count being below it, and `MAX_COMMANDS` / `MAX_AGENTS` / `check_ceilings()`'s body byte-identical to `HEAD`. Plus a re-run of Story 4's gate on the moved base.
- **The pre-flip gate** is its own test against the real repo, with failure output that lists violators rather than asserting a bare boolean.
- **Story 6's mutations** run on a scratch copy or fixture root — never the committed tree, per the discipline instrumentation Story 7 established for `EvalShBoundaryTests`. Exit condition: clean `git status` and a green `bash scripts/eval.sh`.
- Coverage: new code ≥80%; the cap's severity path and the pre-flip gate 100%; error paths 100%.

## Growth this spec causes

Every story edits `scripts/eval-leanness.py`, `scripts/eval.sh`, or the test suite, so the `scripts` surface passes the ceiling recorded in `.writ/leanness-baseline.json` (`surfaces.scripts.justifications.lines.value: 30554`, `.chars.value: 1304568`). Per Business Rule 9 of `2026-08-11-governor-instrumentation`, each story raises **its own** ceiling in a dated entry naming that story — never a batched raise at the end, never a wider silence. The mechanism working under this spec's own pressure is the point.

**Story 7 adds a second surface to that list.** It edits `system-instructions.md`, which is its own gated surface in `SURFACE_REGISTRY` *and* a component of `COMMAND_BYTE_BUDGET`'s derivation. So Story 7 may need a bound justification against `surfaces.system_instructions.*` as well, and it will separately produce a non-blocking `check_budget_derivation()` finding. Neither is a defect: the same spec that built both mechanisms is the first thing to trip them, which is the strongest evidence available that they work. The rule that does **not** bend: `COMMAND_BYTE_BUDGET` stays 24,960 (Business Rule 5).

## Component 6 — `MAX_SKILLS` and the `required_skills:` record (Story 7)

Added 2026-08-12 by the mechanism ruling (spec.md → § Approved Scope Changes). Two edits, both non-blocking, both consequences of the same decision, sequenced **last** for a reason given below.

### `MAX_SKILLS`

Address: `scripts/eval-leanness.py:71`, inside the block commented *"Count ceilings — headroom over today's 31/7/6 so the tripwire stays silent until genuine growth, then speaks once (warn-only, never blocking)."* Consumed by `check_ceilings()` at `:1132`.

```python
MAX_COMMANDS = 35      # not this story's
MAX_AGENTS = 10        # not this story's
MAX_SKILLS = 12        # -> 45
```

Measured corpus, 2026-08-12: `metrics.skills` is **6**. Post-phase roster from the six disclosure specs — implement-story +8, create-spec +5, release +5, verify-spec +4, ship +4, implement-phase +3 = **29 new**, all names distinct, **total 35**.

**Derivation: `MAX_SKILLS = MAX_COMMANDS + MAX_AGENTS = 35 + 10 = 45`.**

Under ADR-021 a skill exists only because a **consumer** — a command or an agent — extracted a capability out of itself, and §4 requires shared capability rather than per-consumer copies. So the skill population is structurally bounded by the consumer population, whose two ceilings already sit in this same block, set for their own reasons. One skill per potential consumer is the line where extraction has stopped producing shared capability and become a 1:1 shadow of the consumer surface — ADR-021 §4's *"two copies instead of one shared skill"* expressed as a count, which is the only thing a count can meaningfully express here.

| Business Rule 8 test | Evidence |
|---|---|
| Computed from constants that exist for other reasons | `MAX_COMMANDS` / `MAX_AGENTS` were set by the leanness-instrumentation work and are untouched. The derivation never reads the roster |
| **Can still fire** | 35 against 45 leaves 10 of headroom; **it fires at 46**. A second disclosure programme of this size — ADR-021 §4 explicitly anticipates `implement-spec` — crosses it |
| Moves only when its inputs move | and each input moves only by a deliberate edit to a named constant |

**The counterfactual is the whole argument.** Had the phase's roster come in at 50, this derivation would still yield 45, the cap would fire, and the correct output would be a Tier B escalation rather than a bigger number. A cap derived from the roster cannot do that, which is exactly the *"a cap chosen after the fact to accommodate whatever was written is not a cap"* failure `2026-08-11-autonomy-gate-classes` Business Rule 1 bans — the same rule that protected the `_preamble` cap, which was derived as 79 + 14 + 2 = 95 rather than fitted to the file.

Recorded at the constant: the derivation, its date, the measured 35, the headroom of 10, and the warn-only decision with its revisit condition.

**It stays warn-only.** Stated explicitly because four other things in this spec become blocking and silence would read as an oversight:

- **A count is not a unit of load.** ADR-021's finding, with this phase's own evidence: `commands/implement-phase.md` is 321 lines — inside any plausible line cap — and 4,176 bytes over budget. Story 3 retires a 2000-line limit for that reason. Gating a *skill count* repeats the error one surface over.
- **It would block the fix.** Under conditional loading a skill on an untaken path costs that run nothing, so extraction is the action that *lowers* per-invocation load. A blocking count cap makes the remedy the offence.
- **Bytes are already governed.** The `skills` surface is in `SURFACE_REGISTRY` under ADR-019's per-surface ratchet with schema-3 bound justifications, and every disclosure spec is already required to file one for its skill-surface growth. The blocking instrument for skill bloat exists and measures bytes.
- **Revisit condition, recorded now:** if a `ceiling_bytes` budget is ever adopted — deferred by this spec pending post-disclosure data — the count cap becomes **redundant, not stricter**.

### The `required_skills:` status correction

`system-instructions.md:252` currently asserts **Status: adopted**, that the 2026-08-03 review trigger resolved *revisit → adopt*, that *"the first consumer is Phase 10 progressive disclosure (ADR-021)"*, and that *"progressive disclosure's extraction work lands the first real declarations."*

Three of those are now false. The phase is not the consumer, does not need the mechanism, and lands **zero** declarations. The trigger resolved to adopt on a justification consisting almost entirely of a named future consumer, and that consumer measured the mechanism and rejected it.

| What | Disposition |
|---|---|
| The schema (optional array · order preserved · duplicates deduplicated · unknown names warn) | **unchanged** — referenced by `commands/new-skill.md:273`, implemented in three adapters, validated by `check_required_skills()`. Removing it is ADR-scale |
| The harness contract paragraph | **unchanged** — it is accurate, and its accuracy is what the escalation rested on |
| The status paragraph | **rewritten**: Phase 10 evaluated and did not adopt; the eager-pre-load reason with both sources; the convention still has no consumer |
| The review trigger | **restored** — recommended **2026-11-11**, aligned to ADR-021's own review, terms: no consumer by then → deprecate; a consumer appears → record and reset |
| `adapters/{cursor,claude-code,openclaw}.md` — the identical false consumer sentence | **not edited.** `adapters/` is in no Phase 10 spec's file set; `2026-08-12-disclosure-implement-phase` scopes it *"verify, do not edit."* Recorded as an open correction needing an owner |

**Why restore rather than record why not.** A resolution whose premise turned out false should not survive as a settled adoption; that is how a convention accretes permanence it never earned, and `2026-08-11-retire-dead-prescription` exists because this repo has that failure mode. Recording *why not* would require an argument that the adoption stands on something other than the consumer it named, and there is none.

**Why 2026-11-11.** ADR-021's review trigger falls that day and already asks whether measured per-invocation load dropped for at least 4 of the 6 targeted commands. The same reading is best placed to answer whether an eager mechanism ever acquired a consumer. Two triggers, one review, no second calendar entry to forget.

### Why Story 7 runs last

`system-instructions.md` is **20,153 of the 24,960-byte `COMMAND_BYTE_BUDGET` derivation**. Editing it changes `base.bytes`, so **this spec causes its own `check_budget_derivation()` finding** — in a check it wrote in Story 2, in the same run.

1. **`COMMAND_BYTE_BUDGET` is not re-derived.** Business Rule 5's *"deliberate, dated act"* means a decision taken looking at the whole picture, not an automatic adjustment by the story that happened to nudge the base. Re-deriving mid-spec would move the number Story 4 certified against and Story 6 proved bites, retroactively invalidating both.
2. **Sequenced after Story 6**, so the gate chain completes against a stable base.
3. **Story 7 records the new `base.bytes`, the delta, and that the budget is unchanged**, and re-runs Story 4's gate to confirm nothing certified moved. The check firing on its own author's edit, in the run it shipped, is the strongest demonstration available that it works.

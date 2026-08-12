# Story 2: Absolute Per-Invocation Byte Cap, Blocking

> **Status:** Complete — rescoped to non-blocking (spec.md → Approved Scope Changes, 2026-08-12 (d))
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer whose leanness governor has a ratchet but no ceiling
**I want to** a command file that costs more to load than the shared contract it runs inside to **fail** the eval, not warn
**So that** ADR-021 reason 3 — *"a ratchet is not a budget"* — stops being a diagnosis and becomes a gate a bloated file cannot ratchet happily past forever

## Acceptance Criteria

- [x] Given `COMMAND_BYTE_BUDGET = 24960` and a command file of 24,961 bytes, when `eval-leanness.py` runs, then it emits a `structural` finding for that file and `eval.sh` reports FAIL.
- [x] Given a command file of exactly 24,960 bytes, when the check runs, then it emits **no** finding — the comparison is `>`, not `>=`, and this is asserted explicitly rather than left to a reading of the code.
- [x] Given `commands/plan-product.md` at 24,753 bytes (207 under budget, the tightest near-miss on the surface), when the check runs, then it emits no finding — asserted **by name**, because a false positive against a compliant file is the fastest way to teach a maintainer that the gate is arbitrary.
- [x] Given an over-budget command, when the finding is read, then `subject` is the exact repo-relative path, `what` names the measured bytes, the budget, and the overage, and `fix` names the ADR-021 extraction remedy — never an exemption (Business Rule 1 and Business Rule 4).
- [x] Given `.writ/leanness-baseline.json` carrying a bound justification for `commands.chars` at a value above the current measurement, when the check runs against an over-budget command, then the `structural` finding is **present and unchanged**. A justification explains growth against a baseline; it has no meaning against an absolute budget (Business Rule 3).
- [x] Given `scripts/eval-leanness.py` after this story, when it is searched, then it contains **no** `eval-exempt` reader, no `file_has_exemption` equivalent, and the budget check reads no path under `.writ/`. Non-silenceability is structural, not documentary.
- [x] Given `CONTRACT_CHECK_SEVERITY` set to `"warnings"`, `"structural"`, or an unrecognised value in-process, when the budget check runs against an over-budget command, then the finding is in `structural` in **all three** cases — the cap does not route through `emit_contract_findings()` and does not read the constant.
- [x] Given `commands/_preamble.md`, when the check runs, then it is never checked — excluded via the existing `is_infra()` / `INFRA_PREFIXES` rule, with no hardcoded filename anywhere in the new code.
- [x] Given the real repo, when `check_command_budget`'s `command_bytes` for each command is compared to `scripts/measure-invocation.py`'s `command_bytes` for the same command, then every pair is equal — one accounting, two readers.
- [x] Given `system-instructions.md` or `commands/_preamble.md` whose combined size no longer equals 24,960, when the checker runs, then `check_budget_derivation()` emits a **non-blocking** finding naming the recorded derivation, the recorded value, the live value, and the delta — and `COMMAND_BYTE_BUDGET` is **unchanged**.
- [x] Given an unreadable or zero-byte command file, when the check runs, then it emits a naming finding (unreadable) or no finding (zero-byte), and the script still exits 0 — no traceback, no division.
- [x] Given `metrics` after this story, when it is read, then `per_command_invocation` reports `command_bytes`, `floor_bytes`, and `ceiling_bytes` per command, so ADR-021 caveat 2 (disclosure can *raise* total load) is observable rather than assumed away.

## Implementation Tasks

- [x] 2.1 Re-measure the base before writing anything: `python3 scripts/measure-invocation.py --root . --format json` and confirm `base.bytes`. If it is no longer 24,960, record the new measurement and the delta — the budget is the maintainer's pinned number and this story does not silently re-derive it
- [x] 2.2 Write the tests first: budget boundary (24,959 / 24,960 / 24,961), `plan-product.md` by name, infra exclusion, unreadable file, zero-byte file, absent `commands/`, and the severity-independence matrix across all three `CONTRACT_CHECK_SEVERITY` values
- [x] 2.3 Write the justification-immunity test — a fixture baseline with an inflated bound justification over a fixture root with an over-budget command; assert the finding is present and dict-identical to the no-justification run
- [x] 2.4 Add `COMMAND_BYTE_BUDGET` and `COMMAND_BYTE_BUDGET_DERIVED` with the derivation comment (components, sum, measurement date, and why it is pinned rather than derived live)
- [x] 2.5 Add `check_command_budget(root)` — pure function returning `list[dict]`, reusing `all_command_files()` / `is_infra()` and the same byte accounting `measure-invocation.py` uses
- [x] 2.6 Add `check_budget_derivation(root)` — non-blocking base-drift finding; never mutates the budget
- [x] 2.7 Wire both into `main()`: the budget appends to `structural` **directly** (not through `emit_contract_findings()`), the derivation check into `warnings`
- [x] 2.8 Add `per_command_invocation` to `metrics` and render it through Story 1's bridge shape
- [x] 2.9 Add the cross-script agreement test against the real repo (`check_command_budget` vs `measure-invocation.py` per command)
- [x] 2.10 Raise `surfaces.scripts.justifications.{lines,chars}` for this story, dated, naming this story
- [x] 2.11 Verify acceptance criteria and that `bash scripts/eval.sh` is green on a compliant tree — and, if any command is still over budget, **stop and report** rather than proceeding to Story 3

## Notes

**Technical considerations:**

- **The cap does not route through the seam, and that is the point.** `emit_contract_findings()` decides severity from `CONTRACT_CHECK_SEVERITY`, including a fallback to `warnings` on an unrecognised value. Putting the budget behind that string means a future un-flip — or a typo in one — silently disables the budget as collateral damage. ADR-021 reason 3 asked for a ceiling that fails. It appends to `structural` directly, unconditionally.
- **Pinned, not derived live.** Computing the budget from live `base.bytes` at each run means growing `system-instructions.md` raises every command's allowance without anyone deciding to — reason 3 rebuilt in a new place. The constant is pinned with its derivation and date; `check_budget_derivation()` makes drift visible so re-deriving is a deliberate, dated act.
- **`command_bytes` only.** `floor_bytes` includes the base, which no command can influence — capping it charges every command for `system-instructions.md`. `ceiling_bytes` includes declared skills, and ADR-021 caveat 2 warns disclosure can raise total load. That risk is made **visible as a metric**, not gated: gating it needs post-disclosure data this spec is the first to produce, and it is a decision this spec does not have.
- **One accounting.** `measure-invocation.py` already loads `eval-leanness.py` by path to reuse its parsers, so the dependency runs measure→leanness and cannot be reversed. The cap lives in `eval-leanness.py` and uses the identical byte definition. Two implementations of "how big is this command" that can disagree is a defect waiting for its first file.
- **The finding text is the gate's whole usability.** A blocked commit with "commands are too big" is a wall. "52,709 bytes, over the 24,960-byte budget by 27,749" is a work queue.

**Risks / challenges:**

- **This story lands a blocking check.** If any command is still over budget when it runs, `eval.sh` goes red and stays red. The spec's dependency ordering exists to prevent that — all six disclosure specs precede it — but the story must verify rather than assume, and task 2.11 is the stop condition. Do **not** ship the cap non-blocking "for now": a cap that warns is the exact instrument ADR-021 reason 3 rejected.
- **The temptation to reach for `file_has_exemption`.** It exists at `scripts/eval.sh:185` and would make a red tree green in one line. Business Rule 1 forbids it, and the structural defense is that `eval-leanness.py` never gains the reader at all. If this story finds itself wanting one, it has found a file a disclosure spec did not finish, and the output is a report.
- **`plan-product.md` at 207 bytes of headroom** is the file most likely to convert a routine edit into a blocked commit. It is not a disclosure target. That is a real ceiling behaving like one — but the near-miss test exists so the *check* is never the thing that broke.
- **Base drift will fire during Phase 10.** `_preamble.md` is `2026-08-11-autonomy-gate-classes`'s target and `system-instructions.md` is under active edit. The derivation check firing is correct behavior, not a defect to suppress — and it must never auto-adjust the budget.

**Integration points:**

- Depends on Story 1 for the metric channel `per_command_invocation` renders through.
- Story 4's pre-flip gate asserts this cap is green against the real repo.
- Story 6 mutates a real command past budget and asserts `eval.sh` FAILs naming it.
- `scripts/measure-invocation.py` — read it before writing the accounting; do not fork it.
- `check_baseline`, `check_parity`, `check_coverage`, `check_ceilings`, and `emit_contract_findings` are all untouched.

## Implementation Notes (2026-08-12)

### The rescope this story lands under

The story as authored says *"blocking unconditionally"* and task 2.11 says
*"Do **not** ship the cap non-blocking 'for now'."* **Approved Scope Change
2026-08-12 (d) overrides both**, and the reason is the same reason the
prohibition was written:

> Landing it blocking today makes `eval.sh` red on five commands nobody is
> converting, and a permanently-red gate becomes invisible — the exact failure
> ADR-021 reason 2 diagnosed and this spec exists to avoid.

The five sibling disclosure specs were closed **unimplemented** after the pilot
measured ~1,017 bytes of per-skill overhead and a **+9.7%** worst-path ceiling
regression. Only `implement-story` converted. So the prohibition's premise —
that the six disclosure specs would land first — is false, and the cap ships
**measured and reported** instead. Business Rule 1's *"no exemption to make the
flip possible"* is upheld by **not flipping the half the surface fails**, not
by granting an exemption: no `eval-exempt:` marker was added and
`eval-leanness.py` gained no exemption reader (asserted by
`test_eval_leanness_has_no_exemption_reader_at_all`).

`COMMAND_BUDGET_SEVERITY = "warnings"` is the cap's **own** constant, carrying
that reasoning in-file. It is deliberately **not** `CONTRACT_CHECK_SEVERITY`:
the two are independent decisions and one string must never govern both.

### Task 2.1 — the base, re-measured before anything was written

```
$ python3 scripts/measure-invocation.py --root . --format json
base.bytes = 24960
  system-instructions.md   20153
  commands/_preamble.md     4807
```

Unchanged from the spec's figure. `COMMAND_BYTE_BUDGET = 24960` stands as
pinned, and `check_budget_derivation()` is silent at story close.

### Measured surface (task 2.11)

| Command | Bytes | Over by |
|---|---:|---:|
| `create-spec.md` | 46,423 | 21,463 |
| `verify-spec.md` | 32,110 | 7,150 |
| `implement-phase.md` | 29,136 | 4,176 |
| `release.md` | 28,589 | 3,629 |
| `ship.md` | 28,371 | 3,411 |
| **Total** | | **39,829** |

`implement-story.md` is **24,837** — converted by the pilot and now 123 bytes
inside budget, which is the one place the phase's disclosure work shows up in
this table. `plan-product.md` at 24,753 is the tightest near-miss (207 bytes)
and is asserted compliant **by name**.

Observed report output:

```
- WARNING [commands/create-spec.md]: 46423 bytes, over the 24960-byte per-invocation
  budget by 21463 (186% of budget). A command may not cost more to load than the
  shared contract it runs inside. Remediation: Extract procedural detail to
  skills/<name>/SKILL.md and load it inline at its point of need (ADR-021, amended
  2026-08-12). ...
- Metrics: command_budget: budget=24960 checked=31 over_budget=5 total_overage=39829
  — commands/create-spec.md +21463; commands/verify-spec.md +7150;
  commands/implement-phase.md +4176; commands/release.md +3629; commands/ship.md +3411
- Metrics: per_command_invocation: 31 commands measured (…); heaviest ceiling:
  implement-story at 91903 bytes
```

`bash scripts/eval.sh --check=leanness` → **exit 0, Findings: 0**. The number is
visible without being a wall.

### ADR-021 caveat 2, now observable

`per_command_invocation` reports `command_bytes` / `floor_bytes` /
`ceiling_bytes` per command. The heaviest ceiling is `implement-story` at
**91,903 bytes** against a 49,797-byte floor — the pilot's extraction bought a
smaller floor and a larger envelope, which is caveat 2 measured rather than
assumed away. It stays a **metric**, not a second gate: gating `ceiling_bytes`
needs post-disclosure data and is a decision this spec does not have.

### Acceptance criteria that changed meaning

- AC 1 (*"emits a `structural` finding … and `eval.sh` reports FAIL"*) is met as
  **a finding in `warnings` and a named entry in `metrics.command_budget`**, per
  the rescope. Everything else about it — the file, the measured bytes, the
  budget, the overage — holds exactly.
- AC 7 (severity matrix) is met **more strongly** than written: the cap produces
  dict-identical findings under `"warnings"`, `"structural"` and a typo, and
  `check_command_budget`'s executable source contains no reference to
  `CONTRACT_CHECK_SEVERITY`, `emit_contract_findings`, `justification`,
  `baseline`, or `.writ` at all.

### Tests

`scripts/tests/test_governor_enforcement.py` → `CommandBudgetTests`, 17 cases:
boundary (24,959 / 24,960 / 24,961), `plan-product.md` by name, infra exclusion
proven by source inspection rather than by fixture alone, absent `commands/`,
zero-byte, unreadable, finding shape, the severity matrix, the
no-exemption-reader source assertion, justification immunity, base-drift both
ways, `command_bytes` agreement with `measure-invocation.py` across all 31
commands, and the non-blocking end-to-end `main()` path.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 1 (no exemption; no exemption reader at all); Rule 3 (an absolute cap is not silenceable by a justification); Rule 4 (every blocking finding names the file, the measurement, and the overage); Rule 5 (the budget is pinned and its derivation is itself checked)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The absolute per-invocation byte cap — constants, accounting reuse, what is capped and what is only reported, unconditional severity, non-silenceability by construction] — from spec.md → ## Detailed Requirements → ### The absolute per-invocation byte cap
- **Error map rows:** [unreadable command file; zero-byte command; exactly 24,960 bytes; base drift; justification planted against an over-budget surface; `CONTRACT_CHECK_SEVERITY` typo leaves the cap blocking] — from sub-specs/technical-spec.md → ## Error & Rescue Map
- **Contract:** [Deliverable: "land the absolute per-invocation byte budget as a **blocking** cap"; hard constraint 4: "The absolute cap must fail, not warn — ADR-021 reason 3"; hard constraint 5: do not weaken the schema-3 justification fix and do not let the cap be silenceable by one] — from spec.md → ## Contract (Locked), ## The Binding Budget

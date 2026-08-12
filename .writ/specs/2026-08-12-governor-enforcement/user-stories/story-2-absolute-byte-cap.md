# Story 2: Absolute Per-Invocation Byte Cap, Blocking

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 1

## User Story

**As a** Writ maintainer whose leanness governor has a ratchet but no ceiling
**I want to** a command file that costs more to load than the shared contract it runs inside to **fail** the eval, not warn
**So that** ADR-021 reason 3 — *"a ratchet is not a budget"* — stops being a diagnosis and becomes a gate a bloated file cannot ratchet happily past forever

## Acceptance Criteria

- [ ] Given `COMMAND_BYTE_BUDGET = 24960` and a command file of 24,961 bytes, when `eval-leanness.py` runs, then it emits a `structural` finding for that file and `eval.sh` reports FAIL.
- [ ] Given a command file of exactly 24,960 bytes, when the check runs, then it emits **no** finding — the comparison is `>`, not `>=`, and this is asserted explicitly rather than left to a reading of the code.
- [ ] Given `commands/plan-product.md` at 24,753 bytes (207 under budget, the tightest near-miss on the surface), when the check runs, then it emits no finding — asserted **by name**, because a false positive against a compliant file is the fastest way to teach a maintainer that the gate is arbitrary.
- [ ] Given an over-budget command, when the finding is read, then `subject` is the exact repo-relative path, `what` names the measured bytes, the budget, and the overage, and `fix` names the ADR-021 extraction remedy — never an exemption (Business Rule 1 and Business Rule 4).
- [ ] Given `.writ/leanness-baseline.json` carrying a bound justification for `commands.chars` at a value above the current measurement, when the check runs against an over-budget command, then the `structural` finding is **present and unchanged**. A justification explains growth against a baseline; it has no meaning against an absolute budget (Business Rule 3).
- [ ] Given `scripts/eval-leanness.py` after this story, when it is searched, then it contains **no** `eval-exempt` reader, no `file_has_exemption` equivalent, and the budget check reads no path under `.writ/`. Non-silenceability is structural, not documentary.
- [ ] Given `CONTRACT_CHECK_SEVERITY` set to `"warnings"`, `"structural"`, or an unrecognised value in-process, when the budget check runs against an over-budget command, then the finding is in `structural` in **all three** cases — the cap does not route through `emit_contract_findings()` and does not read the constant.
- [ ] Given `commands/_preamble.md`, when the check runs, then it is never checked — excluded via the existing `is_infra()` / `INFRA_PREFIXES` rule, with no hardcoded filename anywhere in the new code.
- [ ] Given the real repo, when `check_command_budget`'s `command_bytes` for each command is compared to `scripts/measure-invocation.py`'s `command_bytes` for the same command, then every pair is equal — one accounting, two readers.
- [ ] Given `system-instructions.md` or `commands/_preamble.md` whose combined size no longer equals 24,960, when the checker runs, then `check_budget_derivation()` emits a **non-blocking** finding naming the recorded derivation, the recorded value, the live value, and the delta — and `COMMAND_BYTE_BUDGET` is **unchanged**.
- [ ] Given an unreadable or zero-byte command file, when the check runs, then it emits a naming finding (unreadable) or no finding (zero-byte), and the script still exits 0 — no traceback, no division.
- [ ] Given `metrics` after this story, when it is read, then `per_command_invocation` reports `command_bytes`, `floor_bytes`, and `ceiling_bytes` per command, so ADR-021 caveat 2 (disclosure can *raise* total load) is observable rather than assumed away.

## Implementation Tasks

- [ ] 2.1 Re-measure the base before writing anything: `python3 scripts/measure-invocation.py --root . --format json` and confirm `base.bytes`. If it is no longer 24,960, record the new measurement and the delta — the budget is the maintainer's pinned number and this story does not silently re-derive it
- [ ] 2.2 Write the tests first: budget boundary (24,959 / 24,960 / 24,961), `plan-product.md` by name, infra exclusion, unreadable file, zero-byte file, absent `commands/`, and the severity-independence matrix across all three `CONTRACT_CHECK_SEVERITY` values
- [ ] 2.3 Write the justification-immunity test — a fixture baseline with an inflated bound justification over a fixture root with an over-budget command; assert the finding is present and dict-identical to the no-justification run
- [ ] 2.4 Add `COMMAND_BYTE_BUDGET` and `COMMAND_BYTE_BUDGET_DERIVED` with the derivation comment (components, sum, measurement date, and why it is pinned rather than derived live)
- [ ] 2.5 Add `check_command_budget(root)` — pure function returning `list[dict]`, reusing `all_command_files()` / `is_infra()` and the same byte accounting `measure-invocation.py` uses
- [ ] 2.6 Add `check_budget_derivation(root)` — non-blocking base-drift finding; never mutates the budget
- [ ] 2.7 Wire both into `main()`: the budget appends to `structural` **directly** (not through `emit_contract_findings()`), the derivation check into `warnings`
- [ ] 2.8 Add `per_command_invocation` to `metrics` and render it through Story 1's bridge shape
- [ ] 2.9 Add the cross-script agreement test against the real repo (`check_command_budget` vs `measure-invocation.py` per command)
- [ ] 2.10 Raise `surfaces.scripts.justifications.{lines,chars}` for this story, dated, naming this story
- [ ] 2.11 Verify acceptance criteria and that `bash scripts/eval.sh` is green on a compliant tree — and, if any command is still over budget, **stop and report** rather than proceeding to Story 3

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

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Business rules:** [Rule 1 (no exemption; no exemption reader at all); Rule 3 (an absolute cap is not silenceable by a justification); Rule 4 (every blocking finding names the file, the measurement, and the overage); Rule 5 (the budget is pinned and its derivation is itself checked)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The absolute per-invocation byte cap — constants, accounting reuse, what is capped and what is only reported, unconditional severity, non-silenceability by construction] — from spec.md → ## Detailed Requirements → ### The absolute per-invocation byte cap
- **Error map rows:** [unreadable command file; zero-byte command; exactly 24,960 bytes; base drift; justification planted against an over-budget surface; `CONTRACT_CHECK_SEVERITY` typo leaves the cap blocking] — from sub-specs/technical-spec.md → ## Error & Rescue Map
- **Contract:** [Deliverable: "land the absolute per-invocation byte budget as a **blocking** cap"; hard constraint 4: "The absolute cap must fail, not warn — ADR-021 reason 3"; hard constraint 5: do not weaken the schema-3 justification fix and do not let the cap be silenceable by one] — from spec.md → ## Contract (Locked), ## The Binding Budget

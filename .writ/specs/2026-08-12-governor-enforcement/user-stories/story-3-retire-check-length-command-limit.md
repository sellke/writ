# Story 3: Retire the `check_length` Command Limit

> **Status:** Complete — Tier B escalation recorded (Business Rule 6)
> **Priority:** Medium
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer reading `scripts/eval.sh` to learn what governs command size
**I want to** the 2000-line command limit gone and whatever replaces it pointing at the budget that actually binds
**So that** the file stops teaching a false lesson — that line count is a governed quantity — now that a real byte budget exists eleven lines away in another script

## Acceptance Criteria

- [x] Given the ADR-021 amendment owned by `2026-08-12-disclosure-implement-story`, when this story starts, then that amendment has been **read** and its stated disposition for the `check_length` command limit is quoted in this story's Notes. If the amendment does not exist, the story **halts and reports** — it does not re-decide the rule it exists to enforce.
- [x] Given `scripts/eval.sh:423`, when this story completes, then the `-gt 2000` limit no longer exists in any form. It is 2.02x the largest command in the tree (989 lines) and has never been within reach of binding — ADR-021 reason 1, re-measured.
- [x] Given whatever remains in the command loop of `check_length()`, when a maintainer reads it, then a comment names `COMMAND_BYTE_BUDGET` in `scripts/eval-leanness.py` as the limit that actually binds and cites the ADR-021 amendment — so a maintainer who trips a line tripwire is not left believing lines are the budget.
- [x] Given `scripts/eval.sh` after this story, when line 404's `-gt 100` (spec-lite) and line 412's `-gt 95` (`_preamble`) are compared to their pre-story bytes, then both are **identical**. `2026-08-11-autonomy-gate-classes` owns the `_preamble` constant; a diff touching it fails review.
- [x] Given the amendment's value applied to a byte-compliant surface, when `bash scripts/eval.sh --check=length` runs, then the number of findings and notes it produces against `commands/*.md` is **measured and recorded** in this story's Notes — whether that number is zero or five.
- [x] Given that measurement is non-zero, when the story completes, then it has **landed the amendment's value unchanged**, recorded the firing, and escalated the conflict as a Tier B finding. It has not softened the value and has not quietly substituted a different number (Business Rule 6).
- [x] Given `bash scripts/eval.sh --check=length` after this story, when it runs against the current tree, then it exits 0 and the `spec-lite` and `_preamble` checks behave exactly as they did before.
- [x] Given this story's diff, when it is inspected, then no `eval-exempt:` marker was added to any file (Business Rule 1).

## Implementation Tasks

- [x] 3.1 Read the ADR-021 amendment in `.writ/decision-records/adr-021-progressive-disclosure-token-budget.md`. Quote its `check_length` disposition verbatim in the Notes. **If absent: halt, report, do not proceed**
- [x] 3.2 Record the pre-state exactly: `git show HEAD:scripts/eval.sh | sed -n '400,430p'`, and the current line numbers of all three limits — they will have moved if earlier stories edited `eval.sh`
- [x] 3.3 Measure what the amendment's value would produce against today's surface: for each non-infra `commands/*.md`, its line count and its byte count, and the set that would fire
- [x] 3.4 Apply the amendment's disposition to the command loop only — anchored on that loop, never a file-wide `sed` or replace-all
- [x] 3.5 Write the pointer comment naming `COMMAND_BYTE_BUDGET` and citing the amendment
- [x] 3.6 Assert the `_preamble` and `spec-lite` limits are byte-identical to `HEAD` — by diff, not by eye
- [x] 3.7 If task 3.3's measurement is non-zero, write the Tier B escalation into the Notes: the value, the files that fire, their byte headroom, and why a standing channel is the failure ADR-021 reason 2 documents
- [x] 3.8 Raise `surfaces.scripts.justifications.{lines,chars}` for this story, dated, naming this story
- [x] 3.9 Verify acceptance criteria: `bash scripts/eval.sh --check=length` and the full `bash scripts/eval.sh`

## Notes

**Technical considerations:**

- **This story enforces; it does not decide.** The bytes-over-lines decision belongs to the ADR-021 amendment owned by `2026-08-12-disclosure-implement-story` Story 1. An enforcement spec that invents the rule it enforces has no authority, and the halt condition in task 3.1 is what keeps that honest.
- **The amendment's terms as specified on 2026-08-12** (read the landed text, not this paraphrase): ADR-021 Decision point 5 — `check_length`'s command limit 2000 → 400 lines — is *superseded as the binding instrument* by the 24,960-byte budget, *"with the 400-line cap retained as a secondary, non-binding tripwire."* The Decision is not reopened; only the unit changes. So the expected shape of this story's edit is `-gt 2000` → `-gt 400`, and `add_finding` → `add_note`. **Verify that against the landed amendment before writing it** — a paraphrase in a sibling spec is not the record.
- **Non-binding is what makes the five-file firing survivable, not acceptable.** Five *notes* is a materially better outcome than five *findings*, but instrumentation Business Rule 1 is about a channel nobody reads, and notes are that channel. Business Rule 6 still applies.
- **The measured conflict, recorded at spec time so nobody rediscovers it late.** A 400-line tripwire fires **five times on a fully byte-compliant surface**: `security-audit` (527 lines / 18,230 bytes / 6,730 headroom), `refresh-command` (506 / 20,493 / 4,467), `status` (478 / 22,874 / 2,086), `plan-product` (443 / 24,753 / 207), `create-uat-plan` (417 / 16,239 / 8,721). Five standing findings or notes is exactly the ignored-channel failure ADR-021 reason 2 documents and instrumentation Business Rule 1 was written to prevent. Business Rule 6 governs: land it, record it, escalate.
- **The 2000 has never been near binding.** Largest command: 989 lines. The limit is 2.02x that. It is a runaway-content backstop wearing a budget's clothes, which is ADR-021 reason 1 in one sentence.
- **Bytes-per-line varies 2.63x** across the command surface — 34.5 (`migrate.md`) to 90.8 (`implement-phase.md`). That spread is why `implement-phase.md` is the 12th-longest command and the 4th-heaviest, and why a line cap cannot express this budget: at 321 lines it sits under any plausible line cap while being 4,176 bytes over the byte budget.

**Risks / challenges:**

- **The three limits sit within twenty lines of each other.** `spec-lite` `-gt 100` at line 404, `_preamble` `-gt 95` at line 412, command `-gt 2000` at line 423 — 8 and 11 lines apart, in three near-identical `while`/`if` blocks. Any unanchored `sed`, regex, or replace-all can hit the wrong one, and every wrong edit produces a plausible-looking diff. Anchor on the loop, and verify by diff against `HEAD`.
- **ADR-021 states `_preamble.md` is capped at 80 lines; `scripts/eval.sh:412` says 95.** Do **not** "correct" the code to match the ADR. That constant is `2026-08-11-autonomy-gate-classes`'s and is out of bounds here in either direction.
- **Line numbers will have moved.** Stories 1 and 2 edit `eval.sh`. Re-locate all three limits by content before touching anything; the numbers in this story are the 2026-08-12 measurement.
- **"Retire" can be read as "delete the whole loop."** The command loop also carries the `file_has_exemption` skip and the `relpath` handling that a replacement tripwire needs. Read the amendment's disposition before deciding how much of the loop survives.

**Integration points:**

- `scripts/eval.sh` `check_length()` only, and only its command loop.
- `.writ/decision-records/adr-021-progressive-disclosure-token-budget.md` — read-only here; the amendment is authored elsewhere.
- `scripts/eval-leanness.py`'s `COMMAND_BYTE_BUDGET` (Story 2) is what the pointer comment names, so Story 2 must land first.
- `.writ/product/roadmap.md`'s Phase 10 success criterion *"No command file exceeds 400 lines without a tracked exemption"* is stale under the amendment. `2026-08-12-disclosure-implement-story` assigns correcting it to **this spec**, reasoning that whoever changes the code should change the criterion in the same breath — but this spec's locked contract names its file set exhaustively and `.writ/product/roadmap.md` is not in it. Do **not** take it unilaterally here; the conflict and its disposition are recorded in spec.md → Out of Scope, and it needs a maintainer decision before Phase 10 closes.

## Implementation Notes (2026-08-12)

### Task 3.1 — the landed amendment, quoted verbatim

`.writ/decision-records/adr-021-progressive-disclosure-token-budget.md` →
`## Amendments` → *"2026-08-12 — The binding instrument is bytes, not lines"*:

> **Correction:** Decision point 5 makes `check_length`'s command limit (2000 →
> 400 lines) the binding instrument. It is superseded as the *binding*
> instrument by an **absolute byte budget of 24,960** — the measured shared
> base that every invocation pays before a command file is opened
> (`system-instructions.md` 20,153 + `commands/_preamble.md` 4,807). A command
> file may not cost more to load than the shared contract it runs inside. The
> 400-line cap is retained as a **secondary, non-binding tripwire**.

The amendment is present and landed, so the halt condition did not fire. Its
disposition is exactly the shape the story predicted: `-gt 2000` → `-gt 400`,
`add_finding` → `add_note`.

### Task 3.2 — pre-state

`scripts/eval.sh` `check_length()` held three limits, at lines 404 (`-gt 100`,
spec-lite), 412 (`-gt 95`, `_preamble`) and 423 (`-gt 2000`, commands). Line
numbers were unchanged from the spec's 2026-08-12 measurement; Stories 1 and 2
edited `check_leanness()` at ~2828, far below.

### Task 3.3 / 3.7 — the measurement, and the Tier B escalation

**A 400-line tripwire fires on NINE commands today, five of them fully
byte-compliant.** Measured on this tree:

| Command | Lines | Bytes | Byte verdict |
|---|---:|---:|---|
| `create-spec.md` | 871 | 46,423 | over budget by 21,463 |
| `verify-spec.md` | 732 | 32,110 | over budget by 7,150 |
| `release.md` | 640 | 28,589 | over budget by 3,629 |
| `ship.md` | 627 | 28,371 | over budget by 3,411 |
| `security-audit.md` | 527 | 18,230 | **compliant** — 6,730 headroom |
| `refresh-command.md` | 506 | 20,493 | **compliant** — 4,467 headroom |
| `status.md` | 478 | 22,874 | **compliant** — 2,086 headroom |
| `plan-product.md` | 443 | 24,753 | **compliant** — 207 headroom |
| `create-uat-plan.md` | 417 | 16,239 | **compliant** — 8,721 headroom |

And the instrument's own counter-example stands: `implement-phase.md` is **321
lines** — inside the tripwire — and **4,176 bytes over budget**. The 400-line
cap misses the 4th-heaviest command in the product and fires on five compliant
ones.

**Tier B escalation, per Business Rule 6.** The amendment's value was landed
**unchanged** and no substitute number was quietly chosen. The conflict:

- A tripwire that fires on a compliant surface is not a tripwire. Five of the
  nine notes describe files where the *binding* instrument says nothing is
  wrong, which is a standing channel — the ignored-channel failure ADR-021
  reason 2 documents and instrumentation Business Rule 1 was written to prevent.
- `add_note` makes it survivable, not correct. Nine standing notes is a better
  outcome than nine standing findings, but notes are exactly the channel
  Business Rule 1 is about.
- **Escalated for a maintainer decision:** either retire the line tripwire
  entirely now that a byte budget exists (the ADR itself says lines are a poor
  proxy and that 400 was "derived from the current distribution, not from a
  measured quality threshold"), or re-derive it from something it can be
  answerable to. This story has no authority to do either — it enforces the
  amendment, it does not re-decide it.

### Tasks 3.4–3.6 — the edit and its boundary

The edit is anchored on the `command_files()` loop and nothing else. Verified
by diff, not by eye:

```
$ git show HEAD:scripts/eval.sh | sed -n '400,415p' > /tmp/len-before.txt
$ sed -n '400,415p' scripts/eval.sh > /tmp/len-after.txt
$ diff /tmp/len-before.txt /tmp/len-after.txt && echo "NEIGHBOURS BYTE-IDENTICAL"
NEIGHBOURS BYTE-IDENTICAL
$ grep -n "gt 100\|gt 95\|gt 400\|gt 2000" scripts/eval.sh
404:    if [ "$count" -gt 100 ]; then
412:    if [ "$count" -gt 95 ]; then
446:    if [ "$count" -gt 400 ]; then
```

`spec-lite` at 100 and `_preamble` at 95 are byte-identical to `HEAD`. No
`eval-exempt:` marker was added to any file.

The pointer comment names `COMMAND_BYTE_BUDGET` in `scripts/eval-leanness.py`
as the limit that binds, cites the amendment, carries the 2.63x bytes-per-line
spread and the `implement-phase.md` counter-example, and records why the
retired 2000 could never bind. The note text itself repeats the pointer, so a
maintainer who reads only the report still lands on the right number.

### Task 3.9 — verification

`bash scripts/eval.sh --check=length` → **exit 0**, nine non-blocking notes,
zero findings. `bash scripts/tests/test_eval_length_caps.sh` → 9/9, including
three new scenarios: 401 lines produces a note and exit 0, 400 lines is silent
(the test is `-gt`), and no `gt 2000` survives anywhere in `scripts/eval.sh`.
The `_preamble` 95/96 boundary scenarios and the spec-lite 101 scenario are
unchanged and still pass.

### Out of scope, restated because it is adjacent

`.writ/product/roadmap.md`'s Phase 10 criterion — *"No command file exceeds 400
lines without a tracked exemption"* — is now doubly stale: it names the demoted
unit **and** an exemption path Business Rule 1 forbids for the budget. It is
**not** in this spec's file set and was **not** touched. It still needs an
owner before Phase 10 closes.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 6 (a tripwire that fires on a compliant surface is not a tripwire — land the amendment's value, record the firing, escalate); Rule 7 (the `_preamble` and `spec-lite` limits are untouched); Rule 1 (no exemption markers)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [The `check_length` command limit — the one line owned, the two things the story does regardless of the amendment's value, and the measured five-file conflict] — from spec.md → ## Detailed Requirements → ### The `check_length` command limit
- **Error map rows:** [Amendment absent when Story 3 runs → halt and report; rescue is authoring it in `2026-08-12-disclosure-implement-story`] — from sub-specs/technical-spec.md → ## Error & Rescue Map
- **Contract:** [Deliverable: "retire the `check_length` command limit that never could bind"; binding-budget section: the 400-line limit becomes a secondary, non-binding tripwire and **you enforce what that amendment says**] — from spec.md → ## Contract (Locked), ## The Binding Budget

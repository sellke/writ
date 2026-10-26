# Story 1: The `/why` Command File

> **Status:** Completed ✅
> **Commit:** 6625f742650f73dc1c0681fa0edc479050bf6064
> **Priority:** High
> **Dependencies:** None

## User Story

**As a** developer about to change code in a Writ project
**I want to** ask `/why` and get the reason from the ADRs, specs, drift logs, and audit notes, with a confidence tier on every claim
**So that** I keep the decisions their authors recorded, and I can tell a recorded reason from a guess

## Acceptance Criteria

> **AC IDs assigned through:** AC-1.5

- [x] Given `commands/why.md`, when its frontmatter is read, then it carries `name: why`, `description`, `problem`, `outcome`, `entry_level: high`, and exactly three `exit_criteria` entries, and the body has `## Overview`, `## Invocation`, `## Required Artifacts`, `## Confidence Tiers`, `## Command Process`, `## Integration with Writ`, `## Completion`, and `## References`, with `## Completion` immediately before `## References` `[AC-1.1]`
- [x] Given `## Confidence Tiers`, when its first table is read, then the first column lists `Recorded`, `Stated`, `Corroborated`, `Inferred`, `Unknown` in that order, and the section states that code is not evidence of its own intent and that conflicting sources give the lower tier `[AC-1.2]`
- [x] Given `## Command Process`, when its headings are read, then it has six `### Step N:` headings numbered 1 to 6; Step 2 names `refs/notes/writ`, `drift-log.md`, `What Was Built`, and `.writ/decision-records/`; Step 3 names `git log`; Step 4 reads MCP servers only when the strongest claim is below `Stated` and never prompts to connect or authorize one; and each step says what to do when its source is absent: a subject not found gets one natural-language question, and no `.writ/`, no git repository, or no connected MCP server is named in the answer and skipped `[AC-1.3]`
- [x] Given Step 6 and the output templates in `commands/why.md`, when read, then the saved-record path is `.writ/research/<YYYY-MM-DD>-why-<slug>.md`, the record ends with `## Preserve / Change / Avoid / Risk` followed by `### Preserve`, `### Change`, `### Avoid`, `### Risk` in that order, and Step 6 runs only when a change follows `[AC-1.4]`
- [x] Given dogfood fixture questions 1 to 3 in technical-spec.md → Dogfood Fixture, when `/why` answers each in this repository, then each answer's top tier is `Recorded` and cites the expected ledger source, and What Was Built records the three answer lines `[AC-1.5]`

## Implementation Tasks

- [x] 1.1 Write the failing tests first. Create `scripts/tests/test_why_command.py` with `test_command_file`, `test_tiers`, `test_source_order`, `test_handoff_shape`, `test_budgets`, and `test_step_headings` as technical-spec.md → Tests describes. Use the Python 3.9 standard library and the section helpers in `scripts/tests/test_front_door.py`. Run them and confirm each fails on the missing file, not on an import or syntax error `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
- [x] 1.2 Read `skills/plain-prose/SKILL.md`, then write `commands/why.md` frontmatter, `## Overview`, `## Invocation`, and `## Required Artifacts` from technical-spec.md → `commands/why.md` Skeleton. Copy the frontmatter strings exactly. Run `test_command_file` `[AC-1.1]`
- [x] 1.3 Write `## Confidence Tiers`: the five-row table and the three rules beneath it. Run `test_tiers` `[AC-1.2]`
- [x] 1.4 Write `## Command Process` Steps 1 to 5 from technical-spec.md → Step contents, with every degradation in technical-spec.md → Error & Rescue Map named in the step it belongs to. Run `test_source_order` and `test_step_headings` `[AC-1.3]`
- [x] 1.5 Write Step 6 and the two output templates from technical-spec.md → Output Templates, then `## Integration with Writ`, `## Completion` with its Terminal constraint line, and `## References` linking `commands/_preamble.md` and `system-instructions.md`. Run `test_handoff_shape` and `test_budgets` `[AC-1.1, AC-1.4]`
- [x] 1.6 Run dogfood fixture questions 1 to 3 against this repository by following `commands/why.md`. Record each answer line, top tier, and ledger source in What Was Built. If an answer misses its expected tier, fix the command file, not the fixture `[AC-1.5]`
- [x] 1.7 Verify. Run the plain-prose scan from `skills/plain-prose/SKILL.md` step 1 on `commands/why.md`. Run `uv run --python 3.9 pytest scripts/tests/test_why_command.py`, then the full `uv run --python 3.9 pytest` alone, then the bash test loop, then `bash scripts/eval.sh` outside any sandbox. Expect `check_manifest` to report `commands/why.md` unregistered and `gen-platform-trees.py --check` to report the plugin trees stale until Story 2; every other check passes `[AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5]`

## Notes

- **No helper script, no subagents.** The command is prose plus read-only git calls. See spec.md → 📋 Business Rules (No subagents, Read-only).
- **Platform-neutral names.** Name MCP servers in plain prose, the way `commands/prototype.md` does. A backticked vendor tool name fails the vendor scan in `scripts/gen-platform-trees.py`.
- **Referenced paths.** Backticked `*.md` tokens must resolve or carry a placeholder (`<...>`, `*`, `YYYY`). `drift-log.md` resolves as a basename. Do not link Writ's own ADRs or dated research documents from the command; `scripts/eval-shipped-refs.py` fails on them.
- **Mirroring.** `/writ` Step 4 collects `### Step N` headings when a command has no `### Phase N` headings. Keep the six steps at `###`.
- **Known window.** Between this story and Story 2, `check_manifest` and the generated-tree check fail. Story 2 clears both.
- **Risks.** The command growing past 200 lines; tiers drifting from the table into ad hoc labels in the templates. `test_budgets` and `test_tiers` catch both.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Error map rows:** [Locate the subject, Find anchor commits, Read git notes, Read ledger files, Read git history, Read MCP server, Save why record]
- **Shadow paths:** [Happy path, Nil input, Empty input, Upstream error, No ledger, Stale ledger, Conflicting sources, Change follows]
- **Business rules:** [Ledger first, The anchor locates, Five tiers, Code is not evidence of its own intent, Null results are reported, Conflicts take the lower tier, MCP only when needed, Read-only, No subagents, A change follows, Fixed handoff shape, Saved record, Budgets, Entry level]
- **Experience:** [Entry Point, Happy Path, Moment of Truth, Feedback Model, Error Experience, State Catalog, Output Shape]

---

## What Was Built

**Implementation Date:** 2026-10-26

### Files Created

1. **`commands/why.md`** (173 lines, 11,226 bytes)
   - Frontmatter copied from technical-spec.md → Skeleton; `entry_level: high`; three exit criteria.
   - `## Confidence Tiers` table (five tiers) and three rules; `## Command Process` Steps 1–6 with every Error & Rescue Map row in the step that reads the source; answer and saved-record templates; Integration, Completion with Terminal constraint, References.

2. **`scripts/tests/test_why_command.py`** (command section)
   - `test_command_file`, `test_tiers`, `test_step_headings`, `test_source_order`, `test_handoff_shape`, `test_budgets` (AC-1.1–AC-1.4). Python 3.9 stdlib + pytest; fence-aware `section()` and `first_table()` helpers in the style of `scripts/tests/test_front_door.py`.

3. **`.writ/specs/2026-10-25-why-command/drift-log.md`** — created with the Story 1 section (DEV-001, DEV-002).

### Files Modified

[None modified]

### Implementation Decisions

1. **Thin command** — 173 lines against the 200-line budget; no helper script, no subagents. MCP servers are named in plain prose, as `commands/prototype.md` does, so the vendor scan has nothing to flag.
2. **Absent-source literals in the step** — Steps 2–4 print the Error & Rescue Map's user-sees strings (`Ledger: none in this project`, `Git: not a git repository`, `MCP: none connected`) where each absence is detected. Gate 3 evaluator finding, fixed before completion.
3. **References link two shipped `.writ/docs/` formats** (`git-notes-audit-format.md`, `what-was-built-format.md`) and no ADR or dated research file, so `scripts/eval-shipped-refs.py` stays clean.
4. **Gate 4 authenticity `test_imports_no_source` carried as the known false positive** — the test reads markdown and imports no project module (`.writ/issues/improvements/2026-09-03-test-integrity-authenticity-flags-every-bash-test.md`). Evidence instead: red phase (6 failed, each on the missing file) and eight mutations, 8/8 caught (swap two tiers; drop "Never prompt to connect"; rename `### Avoid`; pad to 213 lines; un-number Step 6; drop the code-is-not-evidence rule; change the record path; `entry_level: medium`). Story 2's `subprocess` calls give the file a project-script reference.

### Dogfood Fixture (AC-1.5)

Each question was answered in this repository by following `commands/why.md`.

1. "Why is the visual design command named `/writ-design` and not `/design`?"
   - **Answer:** Claude Code shipped its own `/design` in August 2026, so a Writ `/design` collided with it; the maintainer chose the rename, with no alias, because an alias would bring the collision back. — Recorded
   - Ledger source: `.writ/specs/2026-10-20-platform-neutral-names/spec.md` → Specification Contract, Must Include 2 ("maintainer chose 'rename to /writ-design'") and Technical Concerns ("No alias is kept"); `.writ/issues/bugs/2026-10-19-design-command-name-collision.md` → TL;DR (Recorded). Git: `d36a283` `feat(design)!: rename /design to /writ-design`. No `refs/notes/writ` note on the anchor commits.
2. "Why were friction signals never built?"
   - **Answer:** ADR-030 retired them before they were built: `/retro` already reads transcripts on Claude Code, Cursor, and Codex and is Writ's learning channel, so `scripts/signal.py`, the signal file, the `/status` nudge, and the `Signal:` evidence type were dropped. — Recorded
   - Ledger source: `.writ/decision-records/adr-030-contract-verifier-boundary-front-door.md` § Decision ("Friction signals are retired") and its `Supersedes` banner over ADR-025 Decisions 1, 3, and 6. Git: `bede42e` (ADR-025), `5da628c` (roadmap refresh). MCP: not read; the ledger answered at Recorded.
3. "Why does `commands/status.md` list `/writ` first in both allowlists?"
   - **Answer:** The front-door spec put `/writ` first in the slash allowlist as the entry command, and DEV-003 extended it to the Maintainer Note's bare list because that note says every new command goes there and `test_status_allowlists` checks both lists together. — Recorded
   - Ledger source: `.writ/specs/2026-10-22-front-door/drift-log.md` → DEV-003; technical-spec.md → Registration Edits ("add `/writ` first"). Git: `06b78eb` (front-door Story 2). No later commit touched the allowlists, so no stale-ledger line.

### Test Results

**Verification:** Automated, test-first (`uv run --python 3.9 pytest scripts/tests/test_why_command.py` red: `6 failed`, each `commands/why.md does not exist`; green: `6 passed`), plus the mutation run above.
**Coverage:** Not measured by the script (no coverage report; markdown and test changes only).

- ✅ Targeted: `uv run --python 3.9 pytest scripts/tests/test_why_command.py` → 6 passed.
- ⚠️ `bash scripts/eval.sh`: 6 findings, all the window the story names: `check_manifest` (unregistered `commands/why.md`), the README orphan, and four gen-platform-trees `--check` lines (plugin copies missing or stale). Story 2 clears them.
- ✅ Gate 0 arch-check: pass (rederived proceed). Gate 2: no linter configured; arch-lint: none — see .writ/docs/architecture-lint.md; build-smoke unverifiable (unsupported_stack). Gate 2.5: cross-component, 0 crossings, route evaluator-agent. Gate 3 review-override: unverifiable (no_coverage_report). Gate 3.5 drift-format: pass. Gate 4 coverage: unverifiable (no_coverage_report); authenticity: `test_imports_no_source`, known false positive, carried on the evidence above, not DEGRADED. Gate 4.5 app-verify: unverifiable (no_recipe). Gate 5 docs-check: unverifiable (no_public_exports).

### Review Outcome

**Result:** PASS

- **Iteration count:** 1 iteration(s)
- **Drift:** Small (DEV-001, DEV-002)
- **Security:** None (markdown only; read-only git calls described, no data flow)
- **Boundary Compliance:** 0 crossings
- gate3-route: evaluator-agent

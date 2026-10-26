# Retro Fix Ladder (Lite)

> Source: .writ/specs/2026-10-25-retro-fix-ladder/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `/retro` fixes each mistake finding at the highest working rung (architecture, types, lint, test, docs), proves each new check fails on a real past mistake, and keeps `.writ/retros/rule-enforcers.md`, checked by a new shipped `scripts/retro-check.py`. `/refresh-command` logs covered signals as `execution failure` and edits a skill only when the cited transcript read it (`skill not used` otherwise).

**Implementation Approach:**
- Order: Story 1 (script), Story 2 (seed table), Story 3 (`/retro`); Story 4 (`/refresh-command`) is independent.
- `retro-check.py`: check shape (ADR-029); `--retro`, `--table`, `--repo`; reason codes in technical-spec.md → ## `retro-check.py`. Python 3.9 stdlib, read-only, argv-list subprocess only.
- Ladder signals: Silent patch, Stale guidance, Repeated mistake, User correction. Others `**Rung:** none`.
- Config-only rungs route `apply`; source or test edits route `issue`. Never an applied test rung.
- Edit by section heading. Regenerate trees with `python3 scripts/gen-platform-trees.py`; never hand-edit.
- No `scripts/eval.sh` edit. Command pins live in pytest.

**Files in Scope:**
- Story 1: `scripts/retro-check.py`, `scripts/tests/test_retro_check.py`, `.writ/docs/agent-cli-contract.md` (one row), generated `plugins/writ/scripts/`.
- Story 2: `.writ/retros/rule-enforcers.md`, a seed test in `scripts/tests/test_retro_fix_ladder.py`.
- Story 3: `commands/retro.md`, `scripts/tests/test_retro_fix_ladder.py`, generated command copies.
- Story 4: `commands/refresh-command.md`, `scripts/eval-refresh-evidence.py`, `.writ/docs/refresh-log-format.md`, `scripts/tests/test_refresh_command_criteria.py`, generated command copies.
- Never: `commands/{why,writ,prototype,implement-story,review}.md`, `skills/design-divergence/`, `skills/tdd-cycle/`, `agents/*`, `scripts/eval.sh`.

**Error Handling:**
- Retro file missing → `unverifiable retro_missing`; no git → `unverifiable no_git`; bad args → exit 2.
- Proof check passes on the mistake → restore the edited file, `result passes`, route `issue`.
- Proof cannot run → `result pending`, route `issue`, proof is the issue's done check.
- `retro-check.py` fails twice in Step 8 → report reason lines; edits stay.
- Fewer than two qualifying fix commits in Story 2 → stop and report; no synthetic proofs.

**Integration Points:**
- `/retro` hands Writ command defects to `/refresh-command`; its `execution failure` entries are ladder candidates for the next retro.
- `check_referenced_paths` needs the seeded table to exist before `commands/retro.md` cites it.
- Byte ceiling 24,960 per command (`COMMAND_BYTE_BUDGET`); refresh-command has about 3,370 bytes of room.

---

## For Review Agents

**Acceptance Criteria:**
1. `retro-check.py` passes a conforming retro file and table and fails each malformed fixture with its named reason. `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
2. The seeded table passes `retro-check.py --table`, with at least two enforced rows proven against real past commits and one `none` row. `[AC-2.2, AC-2.3, AC-2.4]`
3. `commands/retro.md` names the five rungs in order, the Ladder and Proof grammar, the table path, and `retro-check.py`, and contains no friction-signal remnant. `[AC-3.1, AC-3.2, AC-3.4]`
4. `commands/refresh-command.md` carries both criteria and four reason tokens; `eval-refresh-evidence.py` accepts the two new tokens and rejects an unknown one. `[AC-4.1, AC-4.2, AC-4.4]`
5. Full pytest (3.9), bash tests, `gen-platform-trees.py --check`, and `bash scripts/eval.sh` are clean.

**Business Rules:**
- Rung vocabulary and order are fixed: architecture, types, lint, test, docs; `none` outside the ladder.
- A proof's mistake is a resolvable commit SHA or a transcript listed in the retro file; never a fixture written for the occasion.
- `applied` requires `result fails`; a test-rung finding is never `applied`.
- The table lives in `.writ/retros/`, which does not ship; never in `.writ/docs/`.
- No signal file, emitter, `Signal:` evidence, or `--friction` flag (ADR-030).

**Experience Design:**
- Entry: `/retro --spec <path>`; `/refresh-command <name>`.
- Happy path: finding shows its ladder → approve Apply → proof fails on the past commit → table row added → `retro-check.py` prints `pass`.
- Moment of truth: "lint: yes" with "Proof: mistake <sha>; ... result fails".
- Feedback: the retro file, the table diff, and the `retro-check.py` verdict line.
- Error: a proof that does not fail turns the finding into an issue draft, with the file restored.

---

## For Testing Agents

**Success Criteria:**
1. Every reason code in technical-spec.md has one failing fixture and the conforming fixture passes.
2. `retro-check.py --help` exits 0; no arguments and a bad flag exit 2 with empty stdout.
3. Command-text pins in `test_retro_fix_ladder.py` and `test_refresh_command_criteria.py` pass; both commands under 24,960 bytes.

**Shadow Paths to Verify:**
- **Happy path:** conforming retro file plus table → `pass`.
- **Nil input:** no `--retro` and no `--table` → exit 2.
- **Empty input:** `## Findings` with no blocks → `pass`.
- **Upstream error:** no git work tree → `unverifiable no_git`.

**Edge Cases:**
- Ladder skips a rung (`architecture`, then `lint`) → `ladder_order`.
- Applied lint finding with `result passes` → `proof_not_failing`.

**Coverage Requirements:**
- Every reason code exercised; every new reason token in `eval-refresh-evidence.py` exercised.

**Test Strategy:**
- Fixtures in `tmp_path`, a `git init` repo for SHAs, subprocess calls to the real script; markdown read as text for command pins.

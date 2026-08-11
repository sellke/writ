# Technical Spec: Autonomy Gate Classes

> Source: `.writ/specs/2026-08-11-autonomy-gate-classes/spec.md`

## Current State (verified 2026-08-11)

`commands/_preamble.md` is **79 lines**. Its sections, in order: `Plan Mode Integrity` (with the `Narrow Recommended-Delivery Exception`), `User Challenge (Scope-Degradation Escalation)`, `File Organization`, `Artifact Integrity`, `Tool Selection`, `Knowledge Context`, `Adapter Neutrality`.

`scripts/eval.sh` `check_length()` spans roughly lines 396-430 and enforces three separate limits:

| Lines | Subject | Test | Owner |
|---|---|---|---|
| 403-404 | `spec-lite.md` files | `-gt 100` | Not this spec |
| **411-412** | **`commands/_preamble.md`** | **`-gt 80`** | **This spec** |
| 422-423 | `commands/*.md` | `-gt 2000` | Phase 10 `governor-enforcement` (→ 400) — also explicitly deferred there by the sibling `2026-08-11-governor-instrumentation` spec |

Current `_preamble` block, verbatim:

```bash
  file="$PROJECT_ROOT/commands/_preamble.md"
  if [ -f "$file" ] && ! file_has_exemption "$file" "length"; then
    count="$(line_count "$file")"
    if [ "$count" -gt 80 ]; then
      add_finding "commands/_preamble.md" "$count lines (limit 80)." "Move command-specific detail out of the shared preamble."
    fi
  fi
```

`add_finding` increments `TOTAL_FINDINGS`, which drives a non-zero exit — this is **blocking**, not a warning, and `length` runs in the default full-suite CI gate.

**One correction to the contract's own wording:** the contract says the command-file limit sits "twelve lines below" the `_preamble` limit. Measured test-to-test it is **eleven** (411 → 422). The substance is unchanged — it is close enough to make an accidental cross-edit easy, which is exactly why the ownership split in Business Rule 3 exists.

## Story 1 — Cap Raise and Its Proof

### The change

Two lines, in place:

```bash
    if [ "$count" -gt 95 ]; then
      add_finding "commands/_preamble.md" "$count lines (limit 95)." "Move command-specific detail out of the shared preamble."
```

The remediation hint is unchanged — it is still the correct advice, and rewriting it would widen the diff for no reason.

### Where 95 comes from

| Component | Lines |
|---|---|
| `commands/_preamble.md` today | 79 |
| `## Autonomy Gate Classes` section budget | 14 |
| Reserve | 2 |
| **New limit** | **95** |

The order matters and is auditable in the git history: the budget is fixed in this spec, before the content exists. If Story 2's authored section overruns 14 lines, the fix is to cut prose (in the new section or elsewhere in `_preamble.md`) — **not** to revisit 95. The reserve is two lines, not ten, because reserve is the part of a budget that decays into slack.

### Test harness

`scripts/eval.sh:13` computes `PROJECT_ROOT` from the script's own directory:

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
```

So the check can be exercised against a synthetic project without touching the real repo: copy `scripts/eval.sh` into `$TMP/scripts/`, write `$TMP/commands/_preamble.md` at a chosen length, `mkdir -p $TMP/.writ/state` (the report path), and run `bash scripts/eval.sh --check=length` from `$TMP`.

**Verified during spec authoring, against the pre-change script:**

| Fixture preamble | Exit | Finding |
|---|---|---|
| 96 lines | 1 | `` `commands/_preamble.md`: 96 lines (limit 80). `` |
| 80 lines | 0 | none |

Post-change, the same harness must produce:

| Fixture preamble | Expected exit | Expected finding |
|---|---|---|
| 95 lines | 0 | none |
| 96 lines | 1 | `96 lines (limit 95).` |

Shape the test after `scripts/tests/test_eval_leanness.sh`: `set -euo pipefail`, a `REPO` computed from `$0`, `ok`/`fail` helpers, a temp dir cleaned on exit. No new dependencies. Assert on **both** the exit code and the finding text — exit code alone cannot distinguish "the cap fired" from "some other check in `--check=length` fired".

### Regressions this test must also cover

The same harness cheaply proves the ownership boundary held. Add fixtures asserting the two neighbouring limits are untouched:

- a fixture `commands/example.md` of 2001 lines → finding `2001 lines (limit 2000).`
- a fixture `.writ/specs/x/spec-lite.md` of 101 lines → finding `101 lines (limit 100).`

If either message changes, this spec edited a line it does not own.

### The exemption trap

`file_has_exemption "$file" "length"` greps for `eval-exempt:.*(length|all)`. Any such marker in `commands/_preamble.md` skips the length check entirely — no finding, no note, exit 0. That is a plausible-looking "fix" for a preamble that grows again, and it is forbidden by Business Rule 4. The test asserts the real `commands/_preamble.md` contains no `eval-exempt:` string.

## Story 2 — The Gate-Class Section

### Placement

Immediately after the `User Challenge (Scope-Degradation Escalation)` section (currently ending at line 47), before `## File Organization`. That section already states ADR-013's select-or-pause boundary; the gate-class table is the classification that boundary applies to. Split across the file, the table reads as a freestanding policy rather than a refinement of the rule three lines above it.

### Candidate content (14 lines, illustrative but line-verified)

```markdown

## Autonomy Gate Classes

Extends ADR-013's select-or-pause boundary above; it does not replace it.

| Class | Behavior |
|---|---|
| Product & spec direction | **Human gate** — contract lock is an explicit human action |
| Production boundary (merge/PR/release/tag) | **Human gate** — Prime Directive |
| Design & UX judgment | **Human gate** — taste is not evidence-decidable |
| Destructive / irreversible | **Autonomous** only if the precondition below holds |
| Everything else | **Autonomous** within ADR-013's boundary, with audit rationale |

**Reversibility precondition.** A destructive-class operation runs unattended **only when both hold**: (1) its effect is provably git-revertable — confined to tracked files with a resolvable revert target; (2) the restore path is recorded **before** the mutation. If either fails, it **pauses** with a bounded `AskQuestion`.
```

Leading blank separator + 13 content lines = **14**. Final file: **93 lines**, two under the new cap and inside the declared reserve.

The precondition is one long unwrapped line. `_preamble.md`'s `Artifact Integrity` section (lines 58-62) already uses long unwrapped lines, so this matches existing house style rather than introducing one. Wrapping it to three lines would consume the entire reserve and leave zero headroom — a legitimate implementer choice, but then the reserve is spent and Business Rule 1 still forbids raising the cap again.

### Normative wording requirements

- "only when both hold" — not "generally", not "where practical".
- "pauses" — the consequence is stated as behavior, not as a recommendation.
- Both conditions numbered and separately checkable.
- "before the mutation" carries emphasis; the ordering *is* the rule. A restore path written after the mutation describes a loss, not a recovery.

### What must not appear

- A sixth class, or a renamed class.
- Any softening of the three human gates (they are gates, not defaults).
- ADR-022's reasoning, dissent, or review trigger. Those belong in the ADR; the preamble is loaded on all 31 command invocations and carries only the operative rule. The section may cite ADR-013 by name — it already appears in the file — but must not import the ADR's argument.

## Story 3 — Applicability Check (read-only)

For each destructive-class command ADR-022 names, answer both conditions and record the answer. Template:

| Command | (1) Provably git-revertable? | (2) Restore path recorded before mutation? | Evaluable by an agent reading `_preamble.md`? |
|---|---|---|---|
| `/revert` | | | |
| `/refactor` | | | |
| `/uninstall-writ` | | | |
| `/reinstall-writ` | | | |

Known starting observations (do not treat as the finished answer — verify each):

- **`/revert`** already HALTs on a dirty working tree before any git operation (`commands/revert.md:56-62`) and resolves target commits before mutating. That is condition (1) implemented under a different name. Its `git reset --hard` path sits behind a second destructive confirmation and is the branch most likely to fail the precondition outright.
- **`/refactor`** commits one verified change per concern with tests green either side — reversible by construction, provided the tree is clean at start.
- **`/uninstall-writ`** deletes platform files (`.cursor/`, `.claude/`, `.codex/`, the manifest) that in a *target* project may be untracked or gitignored. This is precisely the case condition (1) is meant to catch, and it is the likeliest genuine "precondition fails → pause" result.
- **`/reinstall-writ`** restores from upstream and the manifest records baselines, but it discards local modifications, which are only recoverable if they were committed.

The deliverable is the filled table plus one paragraph per "no" answer explaining what an agent would be unable to determine. **No command file is edited.** A "no" that warrants action is filed via `/create-issue` and referenced from the story.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Raise the `_preamble` constant | Message string left at `limit 80` while the test reads 95 | Both lines change together; test asserts the finding text contains `limit 95` | 96-line fixture asserts on message text, not just exit code |
| Raise the constant | Adjacent `-gt 2000` / `-gt 100` edited by accident | Business Rule 3; reviewed as a diff-scope check | Fixture assertions that both neighbouring limits still fire with their original numbers |
| Cap stops binding | Cap raised high enough that nothing can ever exceed it | Budget-derived number (79+14+2), reserve capped at 2 | 96-line fixture must fail; if it passes, the cap is decorative |
| Cap bypassed | `eval-exempt: length` added to `_preamble.md` now or later | Business Rule 4 | Test asserts no `eval-exempt:` string in the real `commands/_preamble.md` |
| Section overruns budget | Authored section needs 16-18 lines | Cut prose; compress the precondition to one line; **never** re-raise the cap | Post-Story-2 line count asserted ≤95 by the real eval run |
| Precondition read as advice | Hedged wording ("should", "where possible") | Business Rule 5, normative wording list above | Review-gate check against the wording requirements; no automated test — this is a human read |

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| `check_length` `_preamble` branch | 93-line preamble → exit 0 | `commands/_preamble.md` absent → `[ -f "$file" ]` guard skips silently, exit 0 | 0-line preamble → `0 -gt 95` false → passes (correct: length is an upper bound only) | `line_count` disagreeing with `wc -l` on a missing trailing newline would shift the boundary by one — assert 95/96 explicitly rather than trusting the helper |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| `governor-enforcement` lands its 2000 → 400 change concurrently | Different lines of the same function; both diffs are two lines wide and non-overlapping. Rebase, do not re-resolve semantically. |
| Progressive disclosure later restructures `_preamble.md` | Out of scope. The surviving artifact is the budget rule, not the number 95. |
| Someone adds an unrelated preamble section before this one lands | The 79-line baseline is invalidated and 95 must be re-derived from the new baseline, not stretched. Re-check `wc -l commands/_preamble.md` at implementation start. |
| A destructive-class command is added after this ships | It inherits the precondition automatically — the table classifies by behavior, not by a command list. This is the intended property; ADR-022 rejected a static name-based blocklist for exactly this reason. |

## Testing Strategy

- **Story 1:** shell test in `scripts/tests/` building a temp project root; four assertions minimum — 95→pass, 96→fail with `limit 95`, command-limit fixture still says `limit 2000`, spec-lite fixture still says `limit 100`. Plus a grep assertion that the real `commands/_preamble.md` carries no `eval-exempt:` marker.
- **Story 2:** the real `bash scripts/eval.sh --check=length` exits 0, `wc -l commands/_preamble.md` ≤ 95, and a content check that all five class names and both numbered conditions are present. Full `bash scripts/eval.sh` shows no new findings versus the pre-spec baseline.
- **Story 3:** not automatable. The evidence is the filled table plus per-`no` explanation in the story file.

## Non-Goals (restated from spec.md → Out of Scope)

No change to the command-file or `spec-lite.md` limits. No implementation of a mechanical git-revertability check. No edits to `/revert`, `/refactor`, `/uninstall-writ`, `/reinstall-writ`. No changes to `system-instructions.md`, the Prime Directive, or ADR-013. No progressive-disclosure restructuring of `_preamble.md`. No reopening of the destructive-class decision.

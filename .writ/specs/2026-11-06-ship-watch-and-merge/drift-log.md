# Drift Log

> Spec: .writ/specs/2026-11-06-ship-watch-and-merge/
> Created: 2026-11-06
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: The merge rule re-derives readiness — Drift Report

> Run: 2026-11-06
> Overall Drift: Small

### Deviations

#### [DEV-001] The merge rule validates a little more than the technical spec, and resolves `--repo` first
- **Severity:** Small
- **Spec said:** technical-spec § `jev-judge.py` Merge Rule: step 7 builds `"pr_ready_" + <first blocker class, else first unknown code, else verdict>`; `head_sha` must match `^[0-9a-fA-F]{40}$`; `snapshot` must be a non-empty string; step 3 resolves a relative snapshot against `repo` and step 4 runs the child with `cwd=repo`.
- **Implementation did:** `_merge_token` lowercases the class or code, maps other characters to `_`, and caps it at 40 characters. A `head_sha` with surrounding whitespace and a whitespace-only `snapshot` are usage errors. `merge_rule` resolves `repo` before building the child's paths.
- **Reason:** For every token the real `pr-ready.py` prints the output is the same. The regex's `$` matches before a trailing newline, so `"<40 hex>\n"` would otherwise pass. The Gate 3 review reproduced a relative `--repo sub` doubling the child's paths (the child runs in `repo`), which asked with `pr_ready_exit_2`; resolving first fixes it.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach names the normalized token, the strict field checks, and the resolved repo.

## Story 2: `/ship` opens the PR without asking and records the ledger — Drift Report

> Run: 2026-11-06
> Overall Drift: Small

### Deviations

#### [DEV-002] The PR-agent Overview paragraph cut moves to Story 4
- **Severity:** Small
- **Spec said:** technical-spec § `ship.md` Changes by Story → Story 2 and § Byte Budget list the "How `/ship` absorbs the PR agent concept" paragraph (−369 bytes) as a Story 2 cut.
- **Implementation did:** Kept the paragraph in Story 2. Story 4, which rewrites the Overview, cuts it.
- **Reason:** With every Story 2 cut, `commands/ship.md` measured 24,767 bytes, below the 24,960 floor that § Byte Budget forbids ("If a story's cuts would cross the floor, leave the remaining cuts to Story 4").
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Line Budget Constraints names the deferred cut.

#### [DEV-003] The Doubt Rule call is stated once, in a `### Decisions` subsection
- **Severity:** Small
- **Spec said:** AC-2.2: each decision names its record and `scripts/jev-judge.py doubt --record` and says an asked answer is labeled with `doubt-label`; technical-spec names the files `decision-<step>.json`.
- **Implementation did:** `### Decisions` (before Step 1) states the record fields, the `doubt --record` and `doubt-label` calls, and the temp-file write once. Each site names its file (`decision-tests.json`, `decision-plan.json`, `decision-branch.json`, `decision-commit.json`), site, options, and recommended option.
- **Reason:** One rule stated once and cited keeps the four sites short and identical in mechanics; the byte budget had no room for four copies.
- **Resolution:** Auto-amended spec-lite.md
- **Spec amendment:** spec-lite.md → For Coding Agents → Implementation Approach names the `### Decisions` subsection.

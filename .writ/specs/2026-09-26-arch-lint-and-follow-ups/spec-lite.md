# Architecture Lint and Drift-Guard Follow-ups (Lite)

> Source: .writ/specs/2026-09-26-arch-lint-and-follow-ups/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** Codex TOMLs that cannot drift silently, an issue-closure convention, and architecture rulesets detected and run in Gate 2 with a shipped guide and a `/create-adr` hook.

**Implementation Approach:**
- One new helper `scripts/arch-lint.py detect` (stdlib, 3.9, read-only, no subprocess, offline); extend `gen-codex-agent-tomls.py` with `--check`.
- Helper-family output: verdict line, `tool:`/`command:`/`reason:` lines, summary last.
- Command edits are prose inside existing steps and gates; no new gate numbers.

**Files in Scope:**
- `scripts/gen-codex-agent-tomls.py`, its test, `scripts/eval.sh`, `codex/agents/*.toml` — freshness
- `commands/status.md`, `skills/project-context-snapshot/SKILL.md`, `commands/create-issue.md` — closure
- `scripts/arch-lint.py`, `scripts/tests/test_arch_lint.py`, `commands/implement-story.md` — Gate 2
- `.writ/docs/architecture-lint.md`, `commands/create-adr.md` — guide and ADR hook
- `scripts/tests/test_governor_enforcement.py`, `test_lean_commands.py` — disclosed re-pins

**Error Handling:**
- Unmapped agent stem → write mode exits before any write; `--check` reports `unmapped`
- Tool configured but absent → `not-installed`, never fails Gate 2, never installs
- Unreadable config → `unverifiable`, `reason: config_unreadable <path>`

**Integration Points:**
- Detected `command:` lines run through Gate 2's existing lint failure path
- `spawn-cap.py` still passes; `implement-story.lean.md` untouched

---

## For Review Agents

**Acceptance Criteria:**
1. Generator maps every agent, validates before writing, and `--check` names stale/missing/orphan/unmapped stems `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
2. `eval.sh` fails on a stale TOML; all TOMLs regenerated `[AC-1.5]`
3. Issues with `## Resolution` are closed and excluded from `/status` and snapshot open counts `[AC-2.1, AC-2.2]`
4. `/create-issue` documents closing; `status.md` stays under budget `[AC-2.3, AC-2.4]`
5. `arch-lint.py detect` finds the four ruleset types with correct mode and command `[AC-3.1, AC-3.2, AC-3.3]`
6. Gate 2 runs detected commands via the lint path; story report prints `arch-lint:` `[AC-3.4, AC-3.5]`
7. Guide ships with valid examples for all four tools; `/create-adr` suggests an Enforcement note `[AC-4.1, AC-4.2, AC-4.3, AC-4.4]`

**Business Rules:**
- Missing ruleset never blocks; detected ruleset violations fail via the existing lint path
- Only dependency-cruiser and import-linter are run; the other two are reported
- Detection never installs and never uses the network (`npx --no-install`)
- Closed = a `## Resolution` heading; closed issues stay in place
- Generator is the only TOML writer; purposes match `.writ/manifest.yaml`
- Lean sibling byte-identical; ratchets re-pinned with dated comments

**Experience Design:**
- Entry: Gate 2 automatic; `/create-adr`; `/status`
- Happy path: configured ruleset runs → `arch-lint: dependency-cruiser`
- Moment of truth: forbidden import fails Gate 2 mechanically
- Feedback: one `arch-lint:` line; open-issue count excludes closed issues
- Error: `(not installed)` or `unverifiable (config_unreadable <path>)`

---

## For Testing Agents

**Success Criteria:**
1. `uv run pytest` green on the 3.9 floor
2. `bash scripts/tests/test_*.sh` green
3. `bash scripts/eval.sh` Findings 0

**Shadow Paths to Verify:**
- **Happy path:** repo with `.dependency-cruiser.js` and `node_modules/.bin/depcruise` → `run` + `command:`
- **Nil input:** no ruleset files → `pass`, 0 rulesets
- **Empty input:** empty `package.json` object → no tools, `pass`
- **Upstream error:** invalid JSON `package.json` → `unverifiable config_unreadable package.json`

**Edge Cases:**
- `[tool.importlinter]` only in `pyproject.toml` → detected
- `package.json` script containing `depcruise` → `npm run <name>`
- Hand-edited TOML → `stale`; extra TOML → `orphan`
- `## Resolution` inside a code fence line with other text → not a heading

**Coverage Requirements:**
- New code ≥80%; error paths 100%

**Test Strategy:**
- Temp-dir fixture repos per ruleset; temp copies for generator and `eval.sh`; wiring pins for prose

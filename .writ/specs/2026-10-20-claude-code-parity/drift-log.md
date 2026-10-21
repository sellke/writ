# Drift Log

> Spec: .writ/specs/2026-10-20-claude-code-parity/
> Created: 2026-10-21
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: Generate the CLAUDE.md Template from the Manifest — Drift Report

> Run: 2026-10-21
> Overall Drift: Small

### Deviations

#### [DEV-001] `claude-md` sits after `claude-agents` in `CHECKS`
- **Severity:** Small
- **Spec said:** Add `claude-md` to `CHECKS` after `codex-tomls`.
- **Implementation did:** The order is `codex-tomls`, `claude-agents`, `claude-md`. `claude-md` is still after `codex-tomls`.
- **Reason:** `scripts/tests/test_eval_claude_agents.sh` (spec `2026-10-20-claude-agent-generator`, landed after this spec was written) requires `claude-agents` immediately after `codex-tomls`.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md S1 line says `claude-md` follows `claude-agents`.

#### [DEV-002] Classification note keeps "Six dev-only scripts" and adds a sentence
- **Severity:** Small
- **Spec said:** The note under the Classification table in `.writ/docs/agent-cli-contract.md` names the generator.
- **Implementation did:** The "Six dev-only scripts" sentence is unchanged. A new sentence says `gen-claude-md.py` is dev-only too and why.
- **Reason:** `scripts/tests/test_harness_cuts.py` pins the "Six dev-only scripts" wording.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md S1 line records the separate sentence.

#### [DEV-003] Generator is 236 lines
- **Severity:** Small
- **Spec said:** Story 1 Notes: target under 200 lines.
- **Implementation did:** 236 lines, of which 35 are the template constant and 13 the docstring. `gen-codex-agent-tomls.py` is 233.
- **Reason:** The target is soft; `check_leanness` reports growth as a note.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed; recorded here.

#### [DEV-004] Choices where the spec is silent, and eight agents
- **Severity:** Small
- **Spec said:** Seven agents; no rule for an empty agents folder, the agent import-token name, or summary detail strings.
- **Implementation did:** The template lists eight agents (`writ-visual-qa.md` was added by `2026-10-20-claude-agent-generator`); tests read the set from `claude-code/agents/*.md`. An empty `claude-code/agents/` is `unverifiable` (`agents missing`). An agent's `import-token` reason names the file. Fail summaries count reasons by kind, for example `fail (1 missing, 0 extra)` or `fail (1 stale)`. `check_claude_md` also files a finding when line 1 is not a known verdict.
- **Reason:** Each choice fits the check shape in `.writ/docs/agent-cli-contract.md` and the spec's intent.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md S1 line says the agent count comes from the files (eight today).

---

## Story 3: Correct the Claude Code Adapter — Drift Report

> Run: 2026-10-21
> Overall Drift: Small

### Deviations

#### [DEV-005] Manual Step 1 prose corrects the technical spec's claim
- **Severity:** Small
- **Spec said:** technical-spec.md → Adapter Corrections, Manual Step 1 row: say that later installs and updates replace only the block, and that `install.sh --platform claude` does all of this.
- **Implementation did:** The adapter says a manual install writes no manifest, so later `install.sh` and `update.sh` runs keep a block that differs from the template and report it as locally modified; `--force` replaces only the block in `CLAUDE.md` but also overwrites every other Writ file that differs from upstream; `install.sh --platform claude` does all of Step 1 and writes the manifest.
- **Reason:** The spec's sentence is wrong for a manual install, which has no `CLAUDE.md.writ-block` baseline. Gate 3 confirmed the behavior by running `update.sh` and `install.sh` against a manually installed scratch project. Bytes outside the markers are untouched either way.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md S3 line records the corrected Step 1 wording.

#### [DEV-006] Gotcha 1 names both causes of a stale worktree
- **Severity:** Small
- **Spec said:** Gotcha 1: copying worktree output back can overwrite newer work when the worktree is stale; follow the skill's stale-worktree step.
- **Implementation did:** Adds the two causes from the worktrees docs: with the default base the worktree lacks commits not on the remote default branch, unpushed ones included; with `worktree.baseRef: "head"` it lacks commits made after it was created.
- **Reason:** Business Rule 13 requires the adapter's worktree facts to match the docs. Gate 3 iteration 1 found the first wording gave the wrong cause.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md S3 line.

#### [DEV-007] The parallel-stories line has an extra clause
- **Severity:** Small
- **Spec said:** One line: `/implement-spec` runs independent stories in parallel batches.
- **Implementation did:** Adds "and each `/implement-story` reconciles its agents' worktrees per the skill before it trusts their output".
- **Reason:** `commands/implement-story.md` (Sub-agent worktree integration note) says exactly that.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md S3 line.

#### [DEV-008] Adapter test checks more than task 3.1 lists
- **Severity:** Small
- **Spec said:** Task 3.1: presence and absence checks, the regex `cp\s+\S*claude-code/CLAUDE\.md\s+\./CLAUDE\.md`, and agent names from frontmatter in three places.
- **Implementation did:** The regex also catches a copy onto bare `CLAUDE.md` (`(\./)?CLAUDE\.md\b`) and runs on the whole file. The tier and permission tables must match each agent's frontmatter `model` and `permissionMode`; the worktree agent list must equal the agents with `isolation: worktree`; the import line may appear only inside code; Gotchas are numbered in order; skill step numbers come from the skill's headings; Gotcha 1 and the Step 1 prose are pinned.
- **Reason:** Stricter checks serve Business Rules 13 and 16. No behavior changes.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md S3 line.

---

## Story 2: Install the System Instructions and Import Line on Claude Code — Drift Report

> Run: 2026-10-21
> Overall Drift: Small

### Deviations

#### [DEV-009] Business Rule 5's "no baseline → update" is not Cursor's actual rule
- **Severity:** Small
- **Spec said:** Business Rule 5 and the story Notes: `--force`, no baseline, or local equals baseline → update.
- **Implementation did:** Claude reuses Cursor's `SYSINST_ACTION` scan unchanged. A missing baseline leads to an update only when the manifest file is also absent; with a manifest that lacks the `system-instructions.md` line and a local file that differs from upstream, the result is `⚡ Preserved: system-instructions.md (no baseline, assuming modified)`.
- **Reason:** The contract says update.sh keeps the Claude copy current "the same way it keeps the Cursor copy current", and the story Notes say "Match Cursor, do not improve it". The contract outranks the rule text. The branch matters only for a file a user copied by hand into an installed project; a pre-parity install has no local file and gets `new`.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md S2 line states the rule as Cursor implements it: no baseline updates only when there is no manifest.

#### [DEV-010] Two files changed outside the Story 2 task list
- **Severity:** Small
- **Spec said:** Tasks 2.1–2.7 name the three lifecycle scripts, the three command docs, the new parity test, and the two bundle tests.
- **Implementation did:** One line in `scripts/tests/test_manifest_shipped_baselines.sh` adds `system-instructions.md` to the Claude expected shipped set. One `referenced_paths_allowlist` row in `scripts/eval.sh` names `.claude/system-instructions.md` with creating command `/update-writ`.
- **Reason:** The shipped-set test failed once install recorded the file (Business Rule 4). The `referenced-paths` check raised 4 findings because this repo's `.claude/` is a symlink tree without that file; the allowlist is the check's remedy for paths a command creates in target projects.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md S2 line names both files.

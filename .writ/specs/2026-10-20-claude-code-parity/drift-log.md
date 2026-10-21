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

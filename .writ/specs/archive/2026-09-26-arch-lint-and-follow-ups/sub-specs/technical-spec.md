# Technical Spec: Architecture Lint and Drift-Guard Follow-ups

> Spec: [`../spec.md`](../spec.md)

## 1. Codex TOML freshness (Story 1)

**Files:** `scripts/gen-codex-agent-tomls.py`, `scripts/tests/test_gen_codex_agent_tomls.py`, `scripts/eval.sh`, `scripts/tests/test_eval_codex_tomls.sh` (new), `codex/agents/*.toml` (regenerated).

- Add `evaluator-agent` to `PURPOSES` (the `.writ/manifest.yaml` purpose, verbatim) and to `SANDBOX` as `read-only`.
- Refactor `main()` into `expected_tomls() -> dict[stem, text]` that validates **every** stem first. Write mode: if any stem is unmapped, `SystemExit` naming all unmapped stems, **before** any write.
- `--check` compares `expected_tomls()` to `codex/agents/*.toml`:

| Condition | Line |
|---|---|
| file differs | `reason: stale <stem>` |
| `.md` without `.toml` | `reason: missing <stem>` |
| `.toml` without `.md` | `reason: orphan <stem>` |
| stem not in `PURPOSES`/`SANDBOX` | `reason: unmapped <stem>` (no crash) |

  Output: `pass` or `fail`, the reasons in stem order, then `gen-codex-agent-tomls: <verdict> (<n> stale, <m> missing, <o> orphan, <u> unmapped)`. Exit 0 pass, 1 fail, 2 usage.
- Test: every `PURPOSES` value equals its manifest `agents[].purpose`.
- `eval.sh`: `check_codex_tomls` runs `--check`; `fail` → one `add_finding` per `reason:` with remediation `python3 scripts/gen-codex-agent-tomls.py`; helper missing → `add_finding`. Register it like `check_drift_format`. Bash test uses a temp copy (no mutation of the real repo).
- Regenerate all TOMLs with the CLI. `test_drift_severity_wiring.py::test_codex_bodies_match_agent_sources` must stay green.

## 2. Issue closure (Story 2)

**Files:** `commands/status.md`, `skills/project-context-snapshot/SKILL.md`, `commands/create-issue.md`, `scripts/tests/test_issue_closure_wiring.py` (new), `.writ/context.md` (regenerated).

- **Rule text (same meaning in all three files):** an issue file containing a line that is exactly `## Resolution` is closed.
- `status.md` Step 5: skip closed issues before the age and `spec_ref` checks. The Open Issues line counts open issues only. Net growth ≤ 300 bytes; the file must stay under the governor budget without a new `KNOWN_OVER_BUDGET` entry.
- Snapshot skill: `## Open Issues` → count of issue files without a `## Resolution` heading.
- `create-issue.md`: short "Closing an issue" note: append `## Resolution` with the date and what changed (commit or branch); never delete or move the file.
- Wiring test pins `## Resolution` in all three files and the skip in `status.md` Step 5.

## 3. Ruleset detection and Gate 2 (Story 3)

**Files:** `scripts/arch-lint.py` (new), `scripts/tests/test_arch_lint.py` (new), `commands/implement-story.md`, `scripts/tests/test_quality_gate_wiring.py`, `scripts/tests/test_governor_enforcement.py`, `scripts/tests/test_lean_commands.py`.

`python3 scripts/arch-lint.py detect [--repo .]` — stdlib, 3.9, read-only, no subprocess, no network.

| Tool | Detected by | Mode | Command |
|---|---|---|---|
| dependency-cruiser | `.dependency-cruiser.{js,cjs,mjs,json}` at repo root | `run` if `node_modules/.bin/depcruise` exists, else `not-installed` | a `package.json` script whose value contains `depcruise` → `npm run <name>`; else `npx --no-install depcruise --config <cfg> <src|.>` (`src` when that dir exists) |
| import-linter | `.importlinter`; `[importlinter]` in `setup.cfg`; `[tool.importlinter]` in `pyproject.toml` | `run` if `lint-imports` is on `PATH` (`shutil.which`), else `not-installed` | `lint-imports` |
| eslint-plugin-boundaries | key in `package.json` `dependencies`/`devDependencies` | `via-eslint` | — |
| ArchUnit | `archunit` (case-insensitive) in `pom.xml`, `build.gradle`, `build.gradle.kts` | `via-tests` | — |

Output, in table order:
```
pass
tool: dependency-cruiser run .dependency-cruiser.js
command: npx --no-install depcruise --config .dependency-cruiser.js src
tool: eslint-plugin-boundaries via-eslint package.json
arch-lint detect: 2 ruleset(s), 1 runnable
```
- No ruleset → `pass`, summary `arch-lint detect: 0 ruleset(s), 0 runnable`.
- A config that cannot be read or parsed (`package.json` JSON error, undecodable file) → `unverifiable`, `reason: config_unreadable <path>`; other detections still print.
- Exit 0 when it ran; 2 on usage.

**Gate 2 wiring (prose):** after the existing linters, run `arch-lint.py detect`; run each `command:` line; a non-zero exit takes the existing Gate 2 failure path (no auto-fix exists for these tools → flag for review). Story report line (Step 4 item 8, and Gate 2):

| Detect result | `arch-lint:` line |
|---|---|
| runnable tool(s) | `arch-lint: <names joined ", ">` |
| via-eslint / via-tests | `<name> (via eslint)` / `<name> (via tests)` |
| not-installed | `<name> (not installed)` |
| none | `arch-lint: none — see .writ/docs/architecture-lint.md` |
| unverifiable | `arch-lint: unverifiable (<reason>)` |

`--quick` keeps Gate 2, so it keeps the detection. `spawn-cap.py` must still pass. Re-pin `KNOWN_OVER_BUDGET["commands/implement-story.md"]` and `DEFAULT_SHA256["implement-story"]` with dated comments naming this spec; `commands/implement-story.lean.md` byte-identical.

## 4. Guidance doc and ADR hook (Story 4)

**Files:** `.writ/docs/architecture-lint.md` (new), `commands/create-adr.md`, `scripts/tests/test_architecture_lint_doc.py` (new).

- Doc sections: why (mechanical over judgment); how Gate 2 finds and runs rulesets (the §3 table, linked); one minimal, valid example each for dependency-cruiser (`forbidden` rule), import-linter (`layers` contract), eslint-plugin-boundaries (`dependencies`, formerly `element-types`), ArchUnit (`layeredArchitecture()`); relation to ADRs.
- `create-adr.md` Step 4 "After writing": one numbered step — when the decision constrains layering, import direction, or module dependencies, add an **Enforcement** note naming the lint rule that encodes it and linking `.writ/docs/architecture-lint.md`.
- Test: doc names all four tools and each tool's detection file from §3; `create-adr.md` links the doc. `install.sh --dry-run` lists the new doc (docs ship via the `.writ/docs/*.md` overlay).

## 5. Ratchets and verification

- Re-pins happen only in Story 3 (`implement-story.md`). `status.md` and `create-adr.md` stay under budget.
- Every story: `uv run --python 3.9 pytest` on touched suites; spec end: full `uv run pytest`, bash suite, `bash scripts/eval.sh` Findings 0.

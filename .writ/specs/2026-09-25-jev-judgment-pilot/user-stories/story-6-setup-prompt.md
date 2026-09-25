# Story 6: Provider Setup Prompt

> **Status:** Not Started
> **Priority:** High
> **Dependencies:** Story 3

## User Story

**As a** Writ user who has never configured Jev
**I want to** be asked once, at the step where Jev would help, whether to set it up through TypeSafe or the Vercel AI Gateway
**So that** I learn the option exists and can turn it on without reading docs, and without ever pasting a key into a chat transcript

## Acceptance Criteria

> **AC IDs assigned through:** AC-6.5

- [ ] Given `python3 scripts/jev-judge.py setup --provider {typesafe,vercel-gateway,none} [--repo .]`, when it runs, then it inserts or replaces exactly one `- **Judgment Provider:** <name>` line in `.writ/config.md` (creating the file's Conventions section entry if absent, never duplicating the line), leaves every other line byte-identical, prints `pass`, a `reason: configured` line, and a summary naming the one env var to export (`TYPESAFE_API_KEY` for `typesafe`, `AI_GATEWAY_API_KEY` for `vercel-gateway`, none for `none`), and exits 0; an unknown provider exits 2 `[AC-6.1]`
- [ ] Given `setup` for any provider, when its stdout, stderr, and every file it writes are inspected, then no key value appears in any of them, the command never reads a key from stdin or argv, and it accepts no `--key` flag `[AC-6.2]`
- [ ] Given an interactive `/create-spec` run that reaches Step 2.6c, when `jev-judge.py status` reports `no_config_line`, then the orchestrator presents one AskQuestion titled "Jev judgment provider" with the options TypeSafe direct, Vercel AI Gateway, Not now, and Never, and runs `setup --provider typesafe`, `setup --provider vercel-gateway`, nothing, or `setup --provider none` to match, prints the export instruction the script returned, and continues Step 2.6c on the existing orchestrator path for this run `[AC-6.3]`
- [ ] Given a `/create-spec --recommend` run, a non-interactive run, a config line set to `none`, or a named provider whose key is missing, when Step 2.6c checks status, then no AskQuestion is shown: `--recommend`/non-interactive and `none` add a single `jev:` note, and a missing key adds `jev: unverifiable (no_api_key) — export <VAR>` without re-prompting `[AC-6.4]`
- [ ] Given the `commands/create-spec.md` edit, when the Step 2.6c text is read, then the setup sub-step is at most 4 lines and names `jev-judge.py setup`, and the existing sentence "does **not** open an AskQuestion gate" is amended to exempt the one-time configuration prompt. A bash wiring test in the shape of `scripts/tests/test_spec_analyze_command_hooks.sh` pins both. pytest covers `setup` for every provider, idempotent re-runs, and the no-key-in-output check, and `bash scripts/eval.sh` ends with Findings 0 `[AC-6.5]`

## Implementation Tasks

- [ ] 6.1 Write pytest cases in `scripts/tests/test_jev_judge.py` for `setup`: each provider writes one line and names the right env var; a re-run replaces rather than duplicates; other config lines stay byte-identical; unknown provider exits 2; a key planted in the environment never appears in output or files; no `--key` flag exists `[AC-6.1, AC-6.2, AC-6.5]`
- [ ] 6.2 Implement `setup` in `scripts/jev-judge.py`: stdlib line-level edit of `.writ/config.md` (insert under `## Conventions`, or replace in place), and print the export instruction from technical-spec §2's backend table `[AC-6.1, AC-6.2]`
- [ ] 6.3 Add the Step 2.6c setup sub-step to `commands/create-spec.md` (≤4 lines): on `no_config_line`, in interactive runs only, show one AskQuestion (TypeSafe direct / Vercel AI Gateway / Not now / Never), map it to `setup`, print the export line, then continue on the existing path `[AC-6.3, AC-6.5]`
- [ ] 6.4 Encode the no-prompt cases in the same sub-step: `--recommend` or non-interactive → note; `none` → note; `no_api_key` → note with the export hint and no re-prompt. Amend the "does **not** open an AskQuestion gate" sentence to exempt the configuration prompt `[AC-6.4, AC-6.5]`
- [ ] 6.5 Add a bash wiring test pinning the sub-step (names `jev-judge.py setup`, lists all four options, has the `--recommend` exemption) and the amended sentence `[AC-6.3, AC-6.4, AC-6.5]`
- [ ] 6.6 Verify: `uv run --python 3.9 pytest scripts/tests/test_jev_judge.py` and the wiring test pass; `bash scripts/eval.sh` Findings 0; the closing commit appends `{date} jev-pilot: setup prompt` to `.writ/decision-log.md` `[AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5]`

## Notes

- **Why the prompt never asks for the key.** A key typed into an AskQuestion free-text field lands in the conversation transcript. The prompt tells the user to export the variable in their shell or secret manager instead. If a user pastes a key anyway, the orchestrator must not write it anywhere, and must tell them to rotate it.
- **Why only Step 2.6c.** It is the first Jev-capable step a user meets, and it runs once per spec, so asking there is rare and in context. Gate 3 shadow and `/verify-spec` never prompt; they read `status` only.
- **Depends on Story 3** because both edit Step 2.6c of `commands/create-spec.md`; serialize after it.
- **Leanness.** Writ tracks command size. Keep the sub-step to 4 lines and put the detail in `jev-judge.py`'s output, not in the command.

## Definition of Done

- [ ] All tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Code reviewed
- [ ] Documentation updated

## Context for Agents

- **Error map rows:** [Resolve opt-in]
- **Shadow paths:** [Nil]
- **Business rules:** [Rule 1 (Double opt-in), Rule 12 (Setup prompt, never key collection), Rule 4 (Advisory only)]
- **Experience:** [spec.md → ## 🎯 Experience Design → Entry point; State Catalog rows "Not configured, interactive", "Not configured, `--recommend` or non-interactive", "Provider named, key missing"]

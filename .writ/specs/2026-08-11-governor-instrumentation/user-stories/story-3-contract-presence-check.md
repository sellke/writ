# Story 3: Component Contract Presence Check

> **Status:** Complete
> **Priority:** High
> **Dependencies:** Story 2

## User Story

**As a** Writ maintainer relying on `eval.sh` to tell me whether the framework is sound
**I want to** `eval-leanness.py` to assert that every command and agent declares `problem:`, `outcome:`, and `exit_criteria:` — naming each missing field in each file
**So that** ADR-020's contract stops being aspirational, and the migration specs get a concrete, shrinking work queue instead of a prose mandate nobody enforces

## Acceptance Criteria

- [x] Given a fixture command whose frontmatter carries non-empty `problem:`, `outcome:`, and `exit_criteria:`, when the check runs, then it emits zero findings for that file.
- [x] Given a fixture command missing exactly one of the three fields, when the check runs, then it emits exactly one finding whose `subject` names both the file path and the field (e.g. `commands/example.md → exit_criteria:`) — never an aggregate finding naming only the surface.
- [x] Given a fixture command declaring `exit_criteria:` with no value and no indented continuation lines, when the check runs, then it emits a finding — presence without content asserts nothing and must not pass.
- [x] Given `agents/visual-qa-agent.md`'s real shape (`## Agent Specification` heading with a ```yaml fence) and any of the six agents using `## Agent Configuration` with a plain fence, when the check runs against both, then it recognizes the config block in **both** carriers and emits no carrier-related false finding against either.
- [x] Given a fixture agent with neither `## Agent Configuration` nor `## Agent Specification`, when the check runs, then it emits exactly **one** carrier-level finding for that file, not three field-level findings.
- [x] Given `commands/_preamble.md`, when the check runs, then it is never checked — excluded via the existing `is_infra()` / `INFRA_PREFIXES` rule, with no hardcoded filename anywhere in the new code.
- [x] Given a fixture command with no leading `---` fence, or with unparseable frontmatter, or with a `---` horizontal rule mid-document, when the check runs, then it emits one file-level finding and the script still exits 0 — no traceback, no partial output.
- [x] Given the real repo after this story, when `eval-leanness.py` runs, then all contract findings land in `warnings` (never `structural`), `structural` remains `[]`, and `eval.sh` exits 0.

> **Measured correction, 2026-08-11 (implementation).** The spec's **114** was measured before `2026-08-11-component-contract` landed. It is now merged into this spec's base: all 31 checkable commands and all 7 agents declare `problem:`, `outcome:` and `exit_criteria:`, so this check emits **0** findings against the real repo and `contract_compliance` reports `31/31` and `7/7`. Per this story's own risk note, the **count** is asserted against fixture trees (compliant, one-field-missing, empty `exit_criteria:`, `[]`, no-fence, mid-document `---`, both agent carriers, no-carrier agent, `_preamble.md`, absent directories) and *behaviour* is asserted against the real repo — including by name that `agents/visual-qa-agent.md`'s ` ```yaml ` carrier produces no false finding. A check reading 0 because the surface complies is the migration succeeding, not the check failing.
- [x] Given `metrics` after this story, when it is read, then `contract_compliance` reports `commands_checked`, `commands_with_contract`, `agents_checked`, and `agents_with_contract` as counts.
- [x] Given `scripts/eval-leanness.py` after this story, when the new check function is inspected, then it returns a `list[dict]` and appends to neither `structural` nor `warnings` — routing is the router's job alone.

## Implementation Tasks

- [x] 3.1 Write tests in `scripts/tests/test_eval_leanness_contract.py` (importlib-by-path load of `eval-leanness.py`, same recipe as `test_archive_sweep.py`): compliant command, one-field-missing, empty-`exit_criteria:`, no-fence, mid-document `---`, both agent carriers, no-carrier agent, `_preamble.md` exclusion, and absent `commands/`/`agents/` directories
- [x] 3.2 Add `read_frontmatter(path)` — dependency-free, leading-fence-only, returning `{key: raw_value}` where a block/list value maps to its joined continuation lines, and `None` when there is no leading fence
- [x] 3.3 Add `read_agent_config(path)` handling the dual carrier: `## Agent Configuration` (plain fence) or `## Agent Specification` (```yaml fence), returning the same shape as `read_frontmatter`
- [x] 3.4 Add `CONTRACT_CHECK_SEVERITY = "warnings"` and `emit_contract_findings(findings, structural, warnings, severity=None)`, with the ADR-020 sequencing comment and the "governor-enforcement flips this one string" marker, plus the unrecognized-value → `warnings` fallback
- [x] 3.5 Add `check_component_contract(root)` — pure function, per-file-per-field findings, reusing `all_command_files()` / `is_infra()`
- [x] 3.6 Wire the check into `main()` through the router, and add `contract_compliance` counts to `metrics`
- [x] 3.7 Verify acceptance criteria against the real repo: 114 findings, all in `warnings`, `structural: []`, exit 0, no false finding against `visual-qa-agent.md`
- [x] 3.8 Verify all tests pass — new pytest file, `test_eval_leanness.sh`, full `scripts/tests/*.py` suite, and `bash scripts/eval.sh --check=leanness`

## Notes

**Technical considerations:**

- **This story owns the seam.** `CONTRACT_CHECK_SEVERITY` and `emit_contract_findings()` are introduced here, by the first check that needs them, so the mechanism is exercised from its first line rather than retrofitted around three existing checks. Stories 4, 5, and 6 consume it unchanged; Story 7 proves it.
- **No YAML library.** `eval-leanness.py` imports only stdlib today and must keep it that way — it runs inside `eval.sh` on every CI run. Presence-and-non-emptiness for three keys does not need a parser; a leading-fence line reader does.
- **The dual carrier is verified, not assumed.** 6 agents use `## Agent Configuration` with a plain fence; `visual-qa-agent.md` alone uses `## Agent Specification` with a ```yaml fence. `system-instructions.md` documents this split for `model_tier`, and ADR-020 item 2 explicitly reuses the same carrier. A check recognizing only one produces three false findings against a compliant file — and a false finding is the fastest way to teach a maintainer to ignore the whole channel (Business Rule 5).
- **114 findings on day one is the correct output.** It is the measurement ADR-020 made (2 of 32 commands declare a goal; 0 of 32 carry `problem:` as verified at spec time). Aggregating it into one summary line would violate Business Rule 2 and reproduce the exact defect of the four growth warnings, which name a surface but never a file.
- Field granularity matters for the migration: a command that adds `problem:` and `outcome:` but leaves `exit_criteria:` empty drops from 3 findings to 1. The queue shrinks visibly, which is what makes it a queue rather than a wall.

**Risks / challenges:**

- **Over-parsing.** The temptation is to validate `exit_criteria:` contents (is it a list? are the assertions machine-checkable?). ADR-020 is explicit that this is out of reach: *"the lint can verify the field exists and is non-empty; it cannot verify the assertion is true."* Presence and non-emptiness only.
- **Frontmatter edge cases.** A `---` horizontal rule inside a document must not be mistaken for a fence; only a fence on line 1 counts. Test this explicitly — several command files use `---` as a section separator.
- Adding ~150 lines to `scripts/eval-leanness.py` grows the `scripts` surface past the ceiling Story 2 recorded, so the growth warning returns. That is correct and expected: raise `surfaces.scripts.justifications.lines` / `.chars` to the new measurement with a dated `text` naming this story, as part of this story. Do not pre-emptively silence the surface, and do not batch the raise to the end of the spec — a per-story record is what keeps each raise reviewable.

**Integration points:**

- Depends on Story 2 having emptied the growth-warning channel — this story's "the only new entries are mine" assertion is meaningless otherwise.
- Stories 4, 5, and 6 call `read_frontmatter()` / `read_agent_config()` and `emit_contract_findings()` from this story. They add no parsing or routing of their own.
- Story 7 flips `CONTRACT_CHECK_SEVERITY` in-process and asserts this story's findings become blocking.

## Definition of Done

- [x] All tasks completed
- [x] All acceptance criteria met
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated

## Context for Agents

- **Business rules:** [Rule 2 (every finding names the exact file and field — the primary rule this story implements); Rule 3 (the flip is one named constant plus one router — introduced here); Rule 5 (both agent config-block carriers handled); Rule 7 (infra files excluded by the existing `is_infra()` rule, not a new skip list)] — from spec.md → 📋 Business Rules
- **Detailed requirements:** [Emission seam — the constant, the router, the `main()` wiring; Check 1 — contract presence, per-file-per-field, dual agent carrier, 114 expected findings] — from spec.md → ## Detailed Requirements → ### Emission seam, ### Check 1 — contract presence
- **Error map rows:** [Read a command's frontmatter → one file-level finding, never an exception; Locate an agent's config block → carrier-level finding, not three field findings; Field presence test → empty `exit_criteria:` is a finding; Missing directory → zero findings, no exception] — from sub-specs/technical-spec.md → ## Error & Rescue Map
- **Contract:** [Must include: "They must be written so the later `governor-enforcement` spec flips them to `structural` by changing the emission target, not by rewriting the checks."] — from spec.md → ## Contract (Locked)

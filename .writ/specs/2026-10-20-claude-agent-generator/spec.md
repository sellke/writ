# Claude Agent Generator

> **Status:** Not Started
> **Created:** 2026-10-20
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Origin:** Promoted from issue: `.writ/issues/improvements/2026-10-20-claude-agent-prompt-parity.md`. Discovery found the gap is larger than the issue states: a Claude Code install ships only `claude-code/agents/*.md` (`scripts/install.sh:78`), so the canonical `agents/*.md` prompt templates that `/implement-story` names (`commands/implement-story.md:217`, `:270`) are absent on Claude installs. The orchestrator has only the 45–79-line hand-written bodies. Generating the Claude bodies from canonical fixes the missing prompt contract and the drift together.

## Specification Contract

**Deliverable:** `scripts/gen-claude-agents.py` generates every `claude-code/agents/writ-*.md` from `agents/*.md` plus a per-agent frontmatter overlay, with a `--check` mode and an eval check that fails on drift.

**Must Include:** Every installed Claude agent carries the canonical body verbatim: prompt template, iteration caps, verdict keys, `STATUS: BLOCKED` contract, boundary rules.

**Hardest Constraint:** Keep the Claude-specific parts without hand edits: `name`, routing `description`, `tools`/`disallowedTools`, `model` tier (`haiku`/`inherit`), `permissionMode`, `isolation`, `maxTurns`, `memory`, and the trailing memory lines.

**🎯 Experience Design:**
- **Entry point:** A maintainer edits `agents/coding-agent.md`, then runs `python3 scripts/gen-claude-agents.py`.
- **Happy path:** The generator rewrites the eight `writ-*.md` files. `bash scripts/eval.sh` and `bash scripts/check-agent-parity.sh` pass.
- **Moment of truth:** A maintainer edits a canonical agent and forgets to regenerate. `eval.sh` fails with `stale coding-agent` and names the command that fixes it.
- **Feedback model:** Check-shape output (agent CLI contract): verdict on line 1, one `reason:` line per problem, a summary line last.
- **Error experience:** A new canonical agent without an overlay entry prints `reason: unmapped <stem>`, and write mode writes nothing.

**📋 Business Rules:**
- The generator is the only writer of `claude-code/agents/*.md`. Each generated file carries a "generated — do not hand-edit" comment naming the regenerate command.
- File shape: overlay frontmatter, then the canonical body (YAML frontmatter stripped, retired `model: "fast"` lines stripped as in `gen-codex-agent-tomls.py`), then an optional overlay suffix (memory lines).
- The overlay lives in the generator as dicts, like `PURPOSES`/`SANDBOX`. Agent names and `writ-*` filenames do not change.
- `writ-visual-qa.md` is added: read-only tools, `model: inherit`, `permissionMode: plan`. The visual-qa exclusion is removed from `check-agent-parity.sh` and `commands/refresh-command.md`.
- `check-agent-parity.sh` keeps its presence check and adds content coverage by running both generators' `--check`, adding one `reason:` line per stale, missing, orphan, or unmapped file. Output shape and exit codes stay the same.
- Python 3.9 floor.

**Success Criteria:** `gen-claude-agents.py --check` passes on the committed tree. Changing one canonical line makes it `fail` with `stale`, and `eval.sh` reports a finding. `writ-coder.md` contains `MAX_SELF_FIX_ITERATIONS = 3` and the `boundary_map` rules. The existing tests that pin `claude-code/agents/*` content pass. A dry-run Claude install lists 8 agents.

**Scope Boundaries:**
- Included: generator, eight generated files, eval check `check_claude_agents`, content coverage in `check-agent-parity.sh`, tests, a Claude adapter row mapping `agents/<stem>.md` → `.claude/agents/writ-<x>.md`, `refresh-command.md` parity docs.
- Excluded: rewriting Cursor-shaped `Task({subagent_type: "generalPurpose"})` blocks in bodies, changing how commands spawn agents, re-pointing this repo's `.claude/agents` symlink, plugin distribution (Phase 14).

**⚠️ Technical Concerns:**
- Generated Claude system prompts contain `{placeholders}` and Cursor `Task(...)` wrappers. The Codex TOMLs already ship this way; accepted.
- `update.sh` three-way merge flags every installed `writ-*.md` as upstream-changed once. Users who customized those files see diffs.
- Phase 13 excludes new capability. This generator counts as repair: it aligns shipped artifacts with their source, as the Codex generator does. The roadmap's Claude Code parity feature should name this spec.

**⚠️ Cross-Spec Overlap:**
- The planned `2026-10-20-claude-code-parity` spec (not yet created) also edits `adapters/claude-code.md`. Keep the agent-path row in one place or sequence the two.

## Experience Design

### Maintainer journey

1. Edit a canonical agent in `agents/`.
2. Run `python3 scripts/gen-claude-agents.py` (and `gen-codex-agent-tomls.py`, already required).
3. Commit the canonical edit and the regenerated files together.
4. `eval.sh` (CI) and `/refresh-command --check-parity` confirm alignment.

### State catalog

| State | What the maintainer sees |
|---|---|
| Aligned | `pass`, summary `gen-claude-agents: pass (0 stale, 0 missing, 0 orphan, 0 unmapped)` |
| Canonical edited, not regenerated | `fail`, `reason: stale coding-agent`; eval finding names `python3 scripts/gen-claude-agents.py` |
| Generated file hand-edited | Same as stale — the check compares bytes |
| New canonical agent, no overlay | `fail`, `reason: unmapped <stem>`; write mode writes nothing |
| `writ-*.md` with no canonical source | `fail`, `reason: orphan <stem>` |
| Generated file deleted | `fail`, `reason: missing <stem>` |
| Generator absent beside `check-agent-parity.sh` | Presence check runs; summary says content was not checked; verdict unaffected |

### Installed-user effect

A Claude Code install gets eight `writ-*.md` files whose bodies match `agents/*.md`. Next `update.sh` run shows each as upstream-changed. Non-customized files update silently through the manifest; customized files follow the existing overlay-merge path.

## Business Rules

1. **Single writer.** Only `gen-claude-agents.py` writes `claude-code/agents/*.md`. Hand edits are drift and fail the check.
2. **Body is verbatim.** The canonical body passes through unchanged except for frontmatter stripping and retired `model: "fast"` line removal. No section filtering, no wrapper rewriting.
3. **Overlay owns Claude metadata.** Frontmatter keys and order, and the optional suffix, come from the overlay. Values match today's files exactly, except the new `writ-visual-qa` entry.
4. **Stem → filename map is explicit.** `coding-agent → writ-coder`, `architecture-check-agent → writ-architect`, `documentation-agent → writ-documenter`, `evaluator-agent → writ-evaluator`, `review-agent → writ-reviewer`, `testing-agent → writ-tester`, `user-story-generator → writ-story-gen`, `visual-qa-agent → writ-visual-qa`.
5. **Validate before write.** Write mode checks every stem has an overlay before the first write; an unmapped stem leaves the tree untouched.
6. **Parity check never blocks callers.** `check-agent-parity.sh` stays a warning for `/refresh-command --check-parity`; its contract shape and exit codes (0/1/2) are unchanged.
7. **3.9 floor.** No stdlib behavior newer than Python 3.9.

## Detailed Requirements

- `gen-claude-agents.py` mirrors `gen-codex-agent-tomls.py`'s CLI: no-arg write mode, `--check`, `--agents-dir`, `--out-dir`, check-shape output, exit 0/1/2.
- `--check` reason kinds: `stale`, `missing`, `orphan`, `unmapped`, sorted by stem.
- Generated header comment sits immediately after the frontmatter closing `---`, as an HTML comment, so it doesn't show in rendered markdown and doesn't break Claude's frontmatter parser.
- `eval.sh` gains `check_claude_agents`, structured like `check_codex_tomls`: one `add_finding` per `reason:` line with a kind-specific remedy.
- `check-agent-parity.sh` runs `python3 "$ROOT/scripts/gen-claude-agents.py" --check` and `gen-codex-agent-tomls.py --check` when present and folds their `reason:` lines into its own.
- `adapters/claude-code.md` gains an agent-path mapping so a command's `> **Agent:** agents/<stem>.md` resolves to `.claude/agents/writ-<x>.md` on a Claude install; its agent table lists `writ-evaluator` and `writ-visual-qa`.
- `commands/refresh-command.md` parity section drops the visual-qa exclusion and documents the regenerate command.
- Tests that pin strings in `claude-code/agents/*` keep passing against generated content. `test_jev_shadow_hooks.sh`'s pin on the phrase `then its trailing [AC-N.M] tag` in `writ-evaluator.md` does not exist in `agents/evaluator-agent.md`; it is retargeted to the canonical wording.

## Implementation Approach

- Copy `gen-codex-agent-tomls.py`'s structure: module docstring with CLI contract, `OVERLAY` dict keyed by stem, `source_stems`, `unmapped_stems`, `render`, `write`, `check`, `main`. Reuse its `strip_optional_yaml_frontmatter` and retired-line regex by duplication (scripts are standalone; no shared import exists between them today).
- Seed `OVERLAY` from the current frontmatter and trailing memory lines of the seven existing files, so the first regeneration changes bodies only.
- Wire `check_claude_agents` into `eval.sh` next to `check_codex_tomls`.
- Add a pytest module beside the existing Codex generator tests covering write, check, each reason kind, and validate-before-write.

See `sub-specs/technical-spec.md` for the overlay schema, output format, and error map.

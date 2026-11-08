# Technical Spec: Claude Agent Generator

> Spec: [../spec.md](../spec.md)
> Stories: [1](../user-stories/story-1-generator-and-overlay.md), [2](../user-stories/story-2-regenerate-claude-agents.md), [3](../user-stories/story-3-parity-eval-and-docs.md)

## Files in Scope

| File | Change | Story |
|---|---|---|
| `scripts/gen-claude-agents.py` | New generator | 1 |
| `scripts/tests/test_gen_claude_agents.py` | New pytest module | 1 |
| `claude-code/agents/writ-*.md` (7 existing) | Regenerated | 2 |
| `claude-code/agents/writ-visual-qa.md` | New, generated | 2 |
| `scripts/tests/test_jev_shadow_hooks.sh` | Retarget one string pin | 2 |
| `scripts/check-agent-parity.sh` | Content coverage, drop visual-qa exemption | 3 |
| `scripts/tests/test_shell_check_shape.sh` | Parity fixture update | 3 |
| `scripts/eval.sh` | `check_claude_agents` | 3 |
| `adapters/claude-code.md` | Agent-path mapping, agent table | 3 |
| `commands/refresh-command.md` | Parity docs | 3 |
| `.writ/docs/agent-cli-contract.md` | Classification row for `gen-claude-agents.py` | 1 |
| `scripts/tests/test_agent_cli_contract.py` | Smoke entry | 1 |

## Overlay Schema

```python
OVERLAY: dict[str, dict] = {
    "coding-agent": {
        "file": "writ-coder.md",
        "frontmatter": [                      # ordered (key, value) pairs
            ("name", "writ-coder"),
            ("description", "TDD implementation agent for Writ stories. ..."),
            ("tools", "Read, Write, Edit, Bash, Grep, Glob"),
            ("model", "inherit"),
            ("permissionMode", "acceptEdits"),
            ("isolation", "worktree"),
            ("maxTurns", "50"),
            ("memory", "project"),
        ],
        "suffix": "Update your agent memory with patterns and conventions you discover in this codebase.",
    },
    ...
}
```

- Ordered list, not dict, so key order is stable on 3.9 and explicit.
- `suffix` optional; empty string means none.
- Values for the seven existing stems are copied verbatim from today's files. `writ-visual-qa`: `tools: Read, Grep, Glob, Bash`, `disallowedTools: Write, Edit`, `model: inherit`, `permissionMode: plan`, `maxTurns: 20`, description from `.writ/manifest.yaml` visual-qa purpose, no `memory`, no suffix.

## Output Format

```
---
name: writ-coder
description: ...
tools: ...
model: inherit
...
---

<!-- Generated from agents/coding-agent.md by scripts/gen-claude-agents.py — do not hand-edit. Regenerate: python3 scripts/gen-claude-agents.py -->

<canonical body, frontmatter stripped, retired model:"fast" lines removed>

<suffix, if any>
```

Exactly one trailing newline. Byte comparison in `--check`.

## CLI Contract

| Invocation | stdout | Exit |
|---|---|---|
| `gen-claude-agents.py` | `pass`, `wrote <path>` per file, `gen-claude-agents: pass (<n> written, 0 unmapped)` | 0 |
| same, unmapped stem | `fail`, `reason: unmapped <stem>` each, `gen-claude-agents: fail (0 written, <u> unmapped)` | 1 |
| `--check`, aligned | `pass`, `gen-claude-agents: pass (0 stale, 0 missing, 0 orphan, 0 unmapped)` | 0 |
| `--check`, drift | `fail`, `reason: <kind> <stem>` sorted by stem, summary with counts | 1 |
| bad argument | usage on stderr, nothing on stdout | 2 |

`orphan` is keyed by filename: a `writ-*.md` in `--out-dir` that no overlay `file` maps to; reported with the filename stem (e.g. `orphan writ-foo`).

## Parity Check Integration

`check-agent-parity.sh` after the presence loop:

```bash
for gen in gen-claude-agents.py gen-codex-agent-tomls.py; do
  if [[ -f "$ROOT/scripts/$gen" ]]; then
    out=$(python3 "$ROOT/scripts/$gen" --check 2>&1); rc=$?
    # rc 1: fold each "reason: <kind> <stem>" into drift "<gen>: <kind> <stem>"
    # rc 2 or other: drift "<gen> --check exited <rc>"
  else
    CONTENT_SKIPPED="$CONTENT_SKIPPED $gen"
  fi
done
```

Summary line appends `; content not checked: <gens>` when any generator was absent. Verdict depends only on reasons.

## Error & Rescue Map

| Operation | Failure | Detection | Rescue | Maintainer sees |
|---|---|---|---|---|
| Write mode | Stem has no overlay | `unmapped_stems()` before first write | Abort, write nothing | `reason: unmapped <stem>`, exit 1 |
| Write mode | `--out-dir` missing | `mkdir(parents=True)` | Create it | Normal `wrote` lines |
| `--check` | Generated file edited by hand | Byte mismatch | None — report | `reason: stale <stem>` |
| `--check` | Generated file deleted | Absent path | None — report | `reason: missing <stem>` |
| `--check` | Extra `writ-*.md` | Not in overlay `file` set | None — report | `reason: orphan writ-<x>` |
| Parity script | Generator absent (temp-copy tests) | `-f` test | Skip content check | Summary notes skip; verdict from presence only |
| Parity script | Generator crashes (rc ≥ 2) | Exit code | Record as drift | `reason: <gen> --check exited <rc>` |
| `eval.sh` | Generator missing | `-f` test | Finding | "Claude agent generator is missing" + restore remedy |

## Shadow Paths

- **Happy:** canonical edit → regenerate → check passes.
- **Nil:** `agents/` absent → generator `--check` reports nothing to compare; `check-agent-parity.sh` already prints `unverifiable` before reaching content checks.
- **Empty:** canonical file with only frontmatter → body is empty string; output is frontmatter + header comment + suffix. Valid.
- **Upstream error:** non-UTF-8 canonical file → `read_text` raises; generator exits non-zero with traceback. Accepted: canonical files are repo-controlled markdown.

## Interaction Edge Cases

| Edge | Behavior |
|---|---|
| Canonical body contains `---` lines (horizontal rules) | Frontmatter strip only consumes a leading `---\n…\n---\n` block; later rules pass through |
| Canonical body contains `<!--` comments | Passed through; generator header is a separate comment |
| Overlay `description` contains `:` | Emitted as-is; current descriptions already contain colons-free text. Story 1 test asserts Claude-parseable frontmatter (simple `key: value` lines, no YAML quoting needed for current values) |
| Windows line endings in canonical | Not normalized; repo uses LF |

## Test Strategy

- `test_gen_claude_agents.py` (pytest, 3.9-safe, temp dirs via `tmp_path`): write mode output shape; `--check` pass; each reason kind; validate-before-write leaves out-dir untouched; frontmatter order; suffix placement; retired-line stripping; header comment present; usage error exit 2 with empty stdout.
- Repo-level test: `--check` against the real `agents/` and `claude-code/agents/` passes (guards Story 2's commit).
- `test_shell_check_shape.sh`: parity fixture drops the visual-qa exemption case, adds a stale-content case using a copied generator.
- `test_agent_cli_contract.py`: add a `Smoke("gen-claude-agents.py", ["--agents-dir", "{repo}/agents", "--out-dir", "{tmp}/claude-agents"], {})` entry. `.writ/docs/agent-cli-contract.md` gains a classification row: `gen-claude-agents.py` | check | | commands/refresh-command.md, adapters/claude-code.md. It ships, like `gen-codex-agent-tomls.py`, because the shipped `check-agent-parity.sh` calls it.

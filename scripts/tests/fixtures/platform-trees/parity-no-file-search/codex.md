# Codex CLI Platform Adapter (fixture: every neutral name except file_search)

## Tool Mapping (Cursor → Codex CLI)

### Quick reference — orchestration primitives

| Cursor / Writ generic | Codex CLI | Notes |
|----------------------|-----------|-------|
| `Task({ prompt, readonly })` | Subagent spawn with matching `sandbox_mode` | Use explicit agent names |
| `AskQuestion()` | Structured numbered options in prose | No modal UI |
| `codebase_search` | `Grep` / `Glob` / ripgrep via `Bash` | Prefer native `Grep`/`Glob` when possible |
| `read_file` | `Read(path)` | Direct equivalent |
| `run_terminal_cmd` | `Bash(command)` | Respect sandbox of the active agent |
| `list_dir` | `Glob("pattern")` or `Bash("ls")` | Codex has no dedicated list-dir tool |
| `todo_write` | `Write(".writ/state/...json")` | File-based tracking |
| `canvas-preview` | `Write` one self-contained HTML file per draft | No renderer: write a structural description of each draft and say the drafts were not rendered. |
| `Plan Mode` | No agent-side mode: run discovery as a read-only conversation and say so; Codex's `/plan` is user-side | If the platform has no toggle, say so and proceed read-only. |

#### Verification record — 2026-10-22

| Check | Platform & version | Observed | Source | Status |
|---|---|---|---|---|
| Not a tool table | fixture | The parser must not read this table. | docs | unverified 2026-10-22 |

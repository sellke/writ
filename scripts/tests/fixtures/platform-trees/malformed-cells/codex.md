# Codex CLI Platform Adapter (fixture: a body row with two cells)

## Tool Mapping (Cursor → Codex CLI)

### Quick reference — orchestration primitives

| Cursor / Writ generic | Codex CLI | Notes |
|----------------------|-----------|-------|
| `codebase_search` | `Grep` / `Glob` / ripgrep via `Bash` | Prefer native `Grep`/`Glob` when possible |
| `file_search` | two cells only |
| `read_file` | `Read(path)` | Direct equivalent |

#### Verification record — 2026-10-22

| Check | Platform & version | Observed | Source | Status |
|---|---|---|---|---|
| Not a tool table | fixture | The parser must not read this table. | docs | unverified 2026-10-22 |

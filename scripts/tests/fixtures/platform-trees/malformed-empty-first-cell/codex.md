# Codex CLI Platform Adapter (fixture: a body row with an empty first cell)

## Tool Mapping (Cursor → Codex CLI)

### Quick reference — orchestration primitives

| Cursor / Writ generic | Codex CLI | Notes |
|----------------------|-----------|-------|
| `codebase_search` | `Grep` / `Glob` / ripgrep via `Bash` | Prefer native `Grep`/`Glob` when possible |
| | `Glob("**/pattern*")` | Built-in Glob tool |
| `read_file` | `Read(path)` | Direct equivalent |

# Codex CLI Platform Adapter (fixture: the tool-table heading is missing)

## Tool Mapping (Cursor → Codex CLI)

### Quick reference

The heading above is not the grammar's heading, so the table below is not
the tool table.

| Cursor / Writ generic | Codex CLI | Notes |
|----------------------|-----------|-------|
| `codebase_search` | `Grep` / `Glob` / ripgrep via `Bash` | Prefer native `Grep`/`Glob` when possible |
| `read_file` | `Read(path)` | Direct equivalent |

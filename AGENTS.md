# Working in this repository

`CLAUDE.md` imports this file, so Claude Code, Codex, and Cursor all read the same instructions.

## What this project is

Writ is a way for a product manager and an AI coding agent to work together: agree what to build, let the model build it, see proof it works. The product is ten plain-language skills. There is no application code and no build step.

## Where things are

| Path | What it is |
|---|---|
| `plugins/writ/` | **The product.** `skills/` plus three plugin manifests. This folder is both the source and what installs. Nothing is generated from it and nothing is copied into it. |
| `plugins/writ/skills/writ/rules.md` | The rules every skill reads first: who decides, honest assessment, proof, how to write for the person, where records live. |
| `plugins/writ/skills/writ-jev/jev.py` | The only code that ships. Optional, standard-library Python 3.9+. |
| `scripts/` | Development only: `check.py`, `install.sh`, and `tests/`. |
| `.writ/` | This project's own plan, specs, decisions, and research, kept with Writ. `specs/archive/` and most decision records predate 1.0 and are history. |
| `.claude/skills`, `.agents/skills` | **Symlinks** to `plugins/writ/skills`, so this repository runs the skills it is editing. Do not replace them with copies, and do not run `install.sh` here. |

## Editing skills

- A skill says what must happen, never which tool does it. No platform tool names; `check.py` fails on them.
- Write for a reader who owns the product and does not review code. Plain words, short sentences, reasons over rules.
- Frontmatter is `name` and `description` only. The name is the folder name and starts with `writ`.
- One skill names another by its name or by `../<skill>/SKILL.md`. Shared text goes in `rules.md`, once.
- Before adding a rule or a check, find the recorded mistake it would have caught. If there is none, leave it out.
- Edits under `plugins/writ/` ship to every user. Edits under `.writ/` are this project's own records.

## Commands

```bash
# Skills, manifests, and README hold together. Fast; run it after any edit under plugins/writ/.
python3 scripts/check.py

# Python tests. Name the interpreter: bare `uv run pytest` picks the 3.9 system Python here.
uv run --isolated --python 3.9 --with pytest pytest
uv run --isolated --python 3.14 --with pytest pytest

# Bash tests
for t in scripts/tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done

# Preview an install into another project (run it from that project's root)
WRIT_SRC=/path/to/this/repo bash /path/to/this/repo/scripts/install.sh --dry-run
```

**Python floor: 3.9**, the macOS system interpreter, declared in `pyproject.toml`. `jev.py` and `check.py` must run on it with the standard library alone.

`VERSION`, `pyproject.toml`, and the three plugin manifests carry the same version. A release changes all five in one commit.

## Why it is shaped this way

`.writ/product/mission.md` and `roadmap.md`, and ADR-034 to ADR-037 in `.writ/decision-records/`. Everything before 1.0 is at tag `v0.49.0` and in `.writ/product/roadmap-history.md`.

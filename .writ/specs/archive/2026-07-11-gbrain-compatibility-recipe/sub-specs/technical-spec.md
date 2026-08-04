# Technical Spec: GBrain Compatibility Recipe

> Parent: [`../spec.md`](../spec.md)
> Scope: implementation-level design for the `gbrain-interop` skill and `gbrain-recipe.md`

## Design Decisions

### D1 — Two artifacts, split by ADR-009 boundary

The skill is an **agent capability** (routing: detect → prefer brain search → cite markdown → write markdown-first → degrade). The recipe doc is a **human explainer** (install GBrain, register the source, map artifacts, remove cleanly). Keeping setup mechanics out of the skill keeps it short and load-cheap; keeping routing rules out of the doc keeps it readable. This is the verb/noun/tool boundary from ADR-009 applied deliberately.

### D2 — Detection is a health check, not a PATH probe

"Brain detected" ≡ `gbrain doctor --json` returns `status` of `ok` or `warnings`. A bare `command -v gbrain` is insufficient: an installed-but-unconfigured or broken brain must route to grep, not to a failing search. `error` status ≡ absent for routing purposes.

### D3 — Brain-first, never brain-only

Retrieval prefers GBrain *when detected*, but every result cites the canonical markdown path, and every durable write goes to markdown first (`.writ/` files) followed by `gbrain sync`. GBrain is a read-acceleration and semantic-recall layer, never the write target for canonical knowledge. This is what makes the round-trip guarantee true by construction.

### D4 — Page mapping via frontmatter tags

`gbrain put` stores pages with YAML frontmatter (title/tags). Writ does not push pages manually in the common path — `gbrain sources add` + `gbrain sync` indexes the files directly. The "page type" mapping the roadmap asks for is therefore expressed as a *tagging convention*: index Writ artifacts and tag them by type (`spec`, `adr`, `knowledge-decision`, `knowledge-convention`, `knowledge-glossary`, `knowledge-lesson`) so `gbrain search` can scope by artifact class. The recipe documents the convention; it does not require Writ to run a custom importer.

### D5 — Version-tracking boundary is explicit

Per ADR-011, GBrain ships frequently and the recipe's blast radius is one doc. The recipe pins itself to *stable, documented touchpoints* (`sources add`, `sync`, `doctor`, `search`, `serve`) and labels anything version-sensitive (sync strategies, embedding-provider env keys) as "verify against current GBrain docs" rather than freezing a single form.

### D6 — Disposable index artifacts stay out of the canonical substrate

`gbrain sources add` writes a `.gbrain-source` pin file to the repo root. That file, and all GBrain state (`~/.gbrain/`, PGLite/Postgres), are disposable index artifacts. The recipe adds `.gbrain-source` to recommended `.gitignore` so the index's bookkeeping never masquerades as reviewable canonical data.

## Error & Rescue Map

| Condition | Detection | Rescue |
|---|---|---|
| GBrain not installed | `command -v gbrain` empty / MCP tools absent | Route retrieval to grep; print nothing in the normal workflow |
| GBrain installed, unconfigured/broken | `gbrain doctor --json` → `status: error` | Treat as absent; grep fallback; recipe points to `gbrain doctor` troubleshooting |
| Embeddings unavailable (no provider key) | sync log `embedding failed` / degraded search | Recipe notes semantic search degrades to BM25; symbol/code paths still work; set `VOYAGE_API_KEY`/`OPENAI_API_KEY` |
| Large file blocks sync (>5 MB) | `gbrain sync` watermark stalls (`FILE_TOO_LARGE`) | Recipe documents `gbrain sync --source <id> --skip-failed`; canonical markdown unaffected |
| API/flag drift after a GBrain release | Cited command errors | Version boundary in the recipe directs the user to current GBrain docs; blast radius is this doc |

## Shadow Paths

- **Nil input:** no `.writ/` yet → recipe assumes a Writ project exists; skill's detection still degrades safely.
- **Absent brain (common):** every retrieval routes to grep; the capability is invisible.
- **Healthy brain:** brain-first retrieval; results cite markdown paths; writes remain markdown-first.
- **Removal:** uninstalling GBrain / deleting the source / dropping PGLite leaves `.writ/` byte-for-byte intact — the round-trip guarantee.

## Validation

- `scripts/lint-skill.sh` on the new skill (role convention + lifecycle).
- `scripts/gen-skill.sh` idempotence (`git diff --exit-code SKILL.md`).
- `scripts/eval.sh --check=memory-interop` (sibling-owned) asserts the skill + recipe artifacts.
- Accuracy pass: each GBrain command cross-checked against `garrytan/gbrain` + GStack `USING_GBRAIN_WITH_GSTACK.md`.

## File × Story Matrix

| File | Story 1 | Story 2 |
|---|---|---|
| `skills/gbrain-interop/SKILL.md` | ✅ create | — |
| `.writ/manifest.yaml` | ✅ register | — |
| `SKILL.md` (root) | ✅ regenerate | — |
| `.writ/docs/gbrain-recipe.md` | — | ✅ create |

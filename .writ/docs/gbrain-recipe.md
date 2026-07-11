# GBrain Compatibility Recipe

> **What this is:** an optional, disposable way to point an external
> [GBrain](https://github.com/garrytan/gbrain) index at Writ's markdown so you
> get best-in-class semantic retrieval over your `.writ/` substrate — without
> Writ owning any retrieval infrastructure or taking a hard dependency on GBrain.
>
> **Governing policy:** [ADR-011](../decision-records/adr-011-memory-interop-markdown-canonical.md)
> — markdown in git is canonical; every index is a welcome-but-disposable
> consumer of it.
>
> **Companion skill:** [`skills/gbrain-interop/SKILL.md`](../../skills/gbrain-interop/SKILL.md)
> teaches an agent how to *route* retrieval brain-first when a brain is present.
> This doc is the *human setup* half.

## When to use this

Use it when your Writ corpus has grown large enough that grep-guessing "what did
we decide about X?" is slower than it should be, and you already run (or want to
run) GBrain. On a large project, a semantic query returns the exact ADR or
knowledge entry instead of a lexical near-miss — and the answer still points back
to the reviewable markdown file, never a database row.

**When *not* to bother:** if you don't run GBrain, do nothing. Writ works
identically with no brain installed — this recipe is opt-in and its absence is a
clean no-op. Nothing in the core Writ workflow references or requires GBrain.

## The one invariant that makes this safe

**Canonical data never lives only in GBrain.** Your `.writ/` markdown, versioned
in git, is the single system of record. GBrain is registered as a *federated
source* that indexes those files for retrieval — it reads them, it never owns
them. This is what makes the [round-trip guarantee](#round-trip-guarantee-removing-gbrain-loses-nothing)
true by construction: removing the index cannot lose canonical data, because the
index never held the only copy.

## Prerequisites

- **You install GBrain yourself.** Writ ships zero GBrain code and bundles
  nothing. Install and initialize it via its own tooling — see
  [`garrytan/gbrain`](https://github.com/garrytan/gbrain) and GStack's
  `USING_GBRAIN_WITH_GSTACK.md`.
- A local engine: `gbrain init --pglite` for a local PGLite store, or a Supabase
  backend. *(Engine flags are version-sensitive — verify against current GBrain
  docs.)*
- Optional but recommended for semantic search: an embeddings provider key
  (`VOYAGE_API_KEY` or `OPENAI_API_KEY`). Without one, semantic search degrades
  to BM25 lexical ranking — still useful, just not vector recall. *(Provider keys
  are version/config-sensitive — verify against current GBrain docs.)*

Confirm the brain is healthy before relying on it:

```bash
gbrain doctor --json
# → {"status": "ok" | "warnings" | "error", "health_score": <n>, "checks": [...]}
```

`ok` or `warnings` means healthy enough to use; `error` means fix it first (the
`gbrain-interop` skill treats an `error` brain as absent and falls back to grep).

## Step 1 — Register `.writ/` as a source

Point GBrain at your repo (or specifically at `.writ/`) as a federated source,
then index it:

```bash
gbrain sources add <repo-or-path>   # e.g. gbrain sources add .
gbrain sync                         # index the registered source(s)
```

`gbrain sources add` writes a **`.gbrain-source` pin file** to the repo root.
That file is index bookkeeping, not canonical data — **gitignore it** so it never
masquerades as reviewable substrate:

```gitignore
# GBrain index bookkeeping — disposable, not canonical
.gbrain-source
```

> **Version boundary:** `sources add` and `sync` are stable, documented
> touchpoints, but sync *strategies* and flags evolve. Verify exact flags against
> current GBrain docs rather than freezing a form here.

## Step 2 — Map Writ artifacts to page types (tagging convention)

GBrain indexes your markdown files directly — you do **not** hand-push pages in
the common path. The "page type" mapping the roadmap asks for is expressed as a
**tagging convention** so `gbrain search` can scope by artifact class. GBrain
pages carry YAML frontmatter (title/tags) via `gbrain put`; when indexing files,
tag them by their Writ artifact type:

| Writ artifact | Location | Suggested tag |
|---|---|---|
| Specification | `.writ/specs/**` | `spec` |
| Architecture decision record | `.writ/decision-records/**` | `adr` |
| Knowledge — decision | `.writ/knowledge/decisions/**` | `knowledge-decision` |
| Knowledge — convention | `.writ/knowledge/conventions/**` | `knowledge-convention` |
| Knowledge — glossary | `.writ/knowledge/glossary/**` | `knowledge-glossary` |
| Knowledge — lesson | `.writ/knowledge/lessons/**` | `knowledge-lesson` |

This is a convention you apply, not an importer Writ runs. The canonical files
stay exactly where they are; the tags just let a query narrow to "the ADRs" or
"the lessons."

## Step 3 (optional) — Register the MCP server

To let an MCP-aware agent host call GBrain's tools (e.g. `mcp__gbrain__search`),
run GBrain as an MCP stdio server:

```bash
gbrain serve
```

For **Claude Code**, register it once:

```bash
claude mcp add gbrain -- gbrain serve
```

Other hosts (**Cursor**, **Codex**) register `gbrain serve` manually through
their own MCP configuration. Once registered, the `gbrain-interop` skill's
brain-first routing can use the MCP `search` tool instead of the CLI.

## Retrieval expectations

With a healthy brain registered, an agent following the `gbrain-interop` skill
will:

- **Detect** the brain via `gbrain doctor --json` (health, not a bare PATH hit).
- **Prefer** `gbrain search "…"` (or `mcp__gbrain__search`) for semantic
  knowledge/spec/ADR questions, falling back to grep for exact-string needs.
- **Cite** the canonical markdown path in every result, so you can open and
  verify the source of truth.
- **Write markdown-first:** durable knowledge is edited into `.writ/` files, then
  `gbrain sync` re-indexes. GBrain is never the write target for canonical
  knowledge.

## Round-trip guarantee: removing GBrain loses nothing

Because canonical data never lived in the index, you can remove GBrain at any
time and your `.writ/` markdown remains **byte-for-byte intact** and Writ stays
fully functional. Concrete removal path:

```bash
# 1. Drop the source registration
gbrain sources remove <source-id>     # verify the subcommand against current GBrain docs

# 2. Delete the local index store (PGLite example)
rm -rf ~/.gbrain                       # local engine state; path is version-sensitive

# 3. Remove the pin file from the repo root
rm -f .gbrain-source

# 4. (Optional) uninstall the GBrain CLI via however you installed it
```

After this, `gbrain doctor --json` no longer reports a healthy brain, the
`gbrain-interop` skill detects "absent" and routes retrieval to grep, and nothing
in your Writ workflow changes. Your specs, ADRs, and knowledge entries are
untouched — they were the only copy that ever mattered.

> **Verify the removal step yourself:** `git status` after removal should show no
> changes under `.writ/` attributable to dropping the index. If it does, you
> wrote canonical data into GBrain-only pages somewhere — that is drift against
> ADR-011, and the fix is to move it back into a markdown file.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `gbrain doctor --json` → `status: error` | Unconfigured or broken brain | Follow `gbrain doctor` guidance; until healthy, Writ uses grep — no data at risk |
| Semantic search feels lexical / weak | No embeddings provider key | Set `VOYAGE_API_KEY` or `OPENAI_API_KEY`, then `gbrain sync` (verify key names against current docs) |
| A file never appears in results | Per-file sync limit (5 MB) hit | `gbrain sync --source <id> --skip-failed` advances past the unindexable file; canonical markdown is unaffected |
| A cited GBrain command errors after an upgrade | GBrain API/flag drift | Consult current GBrain docs — the blast radius is this one recipe (ADR-011) |

## Version-tracking boundary

GBrain ships frequently and exact flags may drift. This recipe pins itself to
the **stable, documented touchpoints** — `gbrain sources add`, `gbrain sync`,
`gbrain doctor --json`, `gbrain search`, `gbrain put`/`gbrain get`, and
`gbrain serve` — and marks version-sensitive details (engine init flags,
embedding-provider env keys, sync strategy flags, the exact `sources remove`
subcommand and local-state paths) as **"verify against current GBrain docs."**
Per ADR-011, the blast radius of a moving GBrain API is exactly this file plus
the `gbrain-interop` skill — nothing else in Writ.

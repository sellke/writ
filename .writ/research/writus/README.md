# WritUS — Planning Artifacts

> **Status:** Research / planning only. This folder is not a fork and does not change Writ product source.
> **Date:** 2026-09-01
> **Writ version inventoried:** 0.33.0 (`VERSION`)
> **Name:** WritUS = **Writ + User Stories** (the human story and ceremony layer). Not a geographic region. See [fork-plan.md](./fork-plan.md) § Name.

These files are the starting artifacts for a later team-facing customization. They live under `.writ/research/` so they remain development-workspace material for this repo, not distributable methodology.

| File | What it is |
|---|---|
| [fork-plan.md](./fork-plan.md) | How to *create* WritUS later: overlay strategy, role→primitive map, human checkpoints, asset protocols, squad topology, phased workflow, risks, non-goals |
| [workflow.mmd](./workflow.mmd) | Maintainable Mermaid source for the development-process diagram |
| [workflow.dot](./workflow.dot) | Graphviz source used to render the PNG (same mapping as the Mermaid file) |
| [workflow.png](./workflow.png) | Rendered diagram: commands → human-readable assets → human meetings, with roles and a three-squad callout |

Regenerate the PNG after editing `workflow.dot`:

```bash
dot -Tpng -Gdpi=130 -o .writ/research/writus/workflow.png .writ/research/writus/workflow.dot
```

Keep `workflow.mmd` in sync with the DOT mapping (commands, assets, meetings, roles). The DOT file is the renderer; Mermaid is the portable source for editors that do not run Graphviz.

**Do not** copy these into `commands/`, `agents/`, `adapters/`, or `scripts/`. WritUS, when built, is an overlay that consumes Writ as upstream.

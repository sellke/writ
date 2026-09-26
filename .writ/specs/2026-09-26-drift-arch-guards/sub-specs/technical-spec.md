# Technical Spec: Drift and Architecture Guards

> Spec: [`../spec.md`](../spec.md)

## 1. `boundary-map.py crossings` (Story 1)

```
crossings --map PATH --changed FILE… [--story PATH] [--surface CLASS] [--repo .]
```

| Input | Meaning |
|---|---|
| `--map` | JSON `{owned, readable, out_of_scope}` as printed by `compute` |
| `--changed` | Files the story changed (Gate 2.5's list) |
| `--story` | Story file; its spec folder (ancestor holding `user-stories/`) is excluded |
| `--surface` | `change-surface.py` class; `full-stack` routes review-agent |

Each changed path is normalized repo-relative (absolute paths under `--repo` made relative; `./` dropped; dot-directories kept) and classified in this order:

1. **Excluded** — under the story's spec folder, equal to `.writ/context.md`, or under `.writ/state/`. Not reported.
2. **Owned** — covered by an `owned` entry (exact match, or entry is a directory prefix). Not reported.
3. **`out_of_scope`** — covered by an `out_of_scope` entry.
4. **`readable_modified`** — covered by a `readable` entry.
5. **`outside_boundary`** — covered by nothing.

Output:

```
pass
route: review-agent
reason: outside_boundary scripts/x.py
reason: readable_modified src/lib/y.ts
reason: full_stack_surface
boundary-map crossings: 2 crossing(s), surface full-stack (route review-agent)
```

| Condition | Verdict | Route | Reason |
|---|---|---|---|
| No crossings, surface not `full-stack` | `pass` | `evaluator-agent` | — |
| ≥1 crossing | `pass` | `review-agent` | one line per crossing |
| `--surface full-stack` | `pass` | `review-agent` | `full_stack_surface` |
| Map missing / unreadable / not a JSON object | `unverifiable` | `review-agent` | `map_unreadable` |
| `--changed` omitted or empty | exit 2 | — | usage |

Exit 0 whenever it ran. Reason order: crossings in input order, then `full_stack_surface`.

## 2. Gate wiring (Story 2)

- **Gate 0.5:** save `compute` stdout to `.writ/state/boundary-<story-stem>.json`.
- **Gate 2.5:** after `change-surface.py classify`, run `crossings --map <saved> --changed <files> --story <story-file> --surface <class>`. Keep its output as `gate3_route`.
- **Gate 3:** spawn the agent named on the `route:` line. `review-agent` gets the `reason:` lines as `boundary_overlap_summary`. Story report prints `gate3-route: <agent> (<reasons joined by "; ">)`.
- **Control flow:** the fail counter counts Gate 3 FAILs from whichever agent ran.
- `--quick` skips Gate 3 (no route); `--review-only` skips Gate 0.5, so it runs the evaluator as today; `--full-pipeline` always runs `review-agent`.

## 3. Contract reference and severity (Story 3)

`contract_content` = the `## Specification Contract` section of `spec.md`, heading through the line before the next `## ` heading, verbatim. Empty string when absent; the agent then uses `spec_lite_content` alone.

Architecture-class deviations → **Large**:

| Case | Previously |
|---|---|
| New runtime dependency not named in the contract or spec-lite | Medium |
| Changed interface or data shape at an integration point another story or the contract names | Medium ("at least Medium") |
| Changed architectural approach (framework, protocol, layering, persistence model) | Large (already) — restated |

Medium keeps: scope expansion, extra unrequested features, a different internal data structure with the same interface.

## 4. `drift-format.py summary` (Story 4)

```
summary --drift-log PATH [--since YYYY-MM-DD]
```

Parses `## Story N:` sections split on `---`; reads `> Run:` and each `#### [DEV-NNN] title` with its `- **Severity:**`. With `--since`, keep sections whose Run date ≥ since; a section without a Run date is dropped when `--since` is set.

```
pass
medium: DEV-004 Added retry wrapper (Story 2)
large: DEV-005 GraphQL instead of REST (Story 3)
drift-format summary: 1 small, 1 medium, 1 large since 2026-09-26
```

| Condition | Verdict |
|---|---|
| Log missing | `pass`, zero counts |
| Log unreadable (decode error, directory) | `unverifiable` `drift_log_unreadable` |
| `--since` not `YYYY-MM-DD` | exit 2 |

## 5. Ratchets

- `scripts/tests/test_governor_enforcement.py` `KNOWN_OVER_BUDGET["commands/implement-story.md"]` and `implement-spec.md` if it crosses budget: re-pin with a dated disclosure comment naming this spec.
- `scripts/tests/test_lean_commands.py` default-file SHA for `implement-story`: re-pin with a dated comment; the lean sibling SHA is unchanged.

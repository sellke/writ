# Archived Dependencies Resolve

> **Status:** Not Started
> **Created:** 2026-11-06
> **Owner:** @AdamSellke
> **Dependencies:** []
> **Origin:** Promoted from issue: `.writ/issues/bugs/2026-11-06-archiving-a-spec-breaks-its-dependents.md`. Authored with `/create-spec --from-issue`; decisions in [`recommendation-log.md`](recommendation-log.md).
> **Type:** Bug fix. **Priority:** Medium. **Effort:** Small.

## Specification Contract

**Deliverable:** `scripts/spec-deps.py validate` resolves a dependency id found under `.writ/specs/archive/<id>/spec.md` as a satisfied dependency instead of a `missing_reference` blocker, so archiving a complete spec never breaks the specs that depended on it.

**Must Include:** An active spec that depends on an archived spec validates `ok`, with the archived id reported in a new `archived_dependencies` field, and the archived spec never enters the ordering graph. An id absent from both `.writ/specs/` and `.writ/specs/archive/` still blocks with `missing_reference`, and the summary now names both paths.

**Hardest Constraint:** [`spec-lifecycle.md`](../../docs/spec-lifecycle.md) forbids a second `archive/` check anywhere except where a command deliberately needs to include archived specs. This is that case, and the doc has to say so, or the next reader "fixes" it back out.

**Direction chosen:** fix the reader, not the archiver. The issue offered two outcomes. Refusing to archive while a dependent is open was rejected: a dependency is complete before its dependents by construction, so the `/release` post-merge hook (`commands/release.md` Step 1.3c) would stop archiving in the common case. Rewriting the dependent's header was rejected: it mutates another spec silently and loses the record. `scripts/archive-sweep.py` is unchanged.

**Stories:** one story, seven tasks.
1. `story-1-archived-dependencies-resolve`: tests first (new `scripts/tests/test_spec_deps.py` plus `scripts/eval-spec-deps.py` scenarios), then the `validate_graph` change, then the docs, then a real-repo check that restores `2026-10-25-design-divergence` to the removal-measurement spec's `Dependencies:` header and runs `validate` on `.writ/specs`.

**Files in Scope:**
- `scripts/spec-deps.py`: `validate_graph` gains the archive lookup; the `missing_reference` summary names both paths; module docstring.
- `scripts/eval-spec-deps.py`: four new scenarios.
- `scripts/tests/test_spec_deps.py`: new pytest, mirrors `test_story_deps.py`'s import-by-path recipe.
- `.writ/docs/spec-lifecycle.md`: a short "Deliberate inclusion: dependency resolution" note under *Why one extra path segment is sufficient*.
- `commands/verify-spec.md` Check 3f and `commands/implement-phase.md` Step 2.1: one line each saying an archived dependency is satisfied.
- `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/spec.md`: header restored to its pre-workaround value.
- Never: `scripts/archive-sweep.py`, `scripts/spec-status.py`, `scripts/ac-trace.py`.

**🎯 Experience Design:**
- **Entry point:** `/implement-phase` Step 2.1 and `/verify-spec` Check 3f run `spec-deps.py validate --specs-dir .writ/specs`.
- **Happy path:** a dependency was archived after it shipped; `validate` prints `{"status": "ok", ...}` and the phase plan proceeds.
- **Moment of truth:** the JSON result lists the archived id under `archived_dependencies` instead of a `missing_reference` blocker.
- **Feedback model:** the existing one JSON object on stdout, exit 0.
- **Error experience:** an id in neither place still prints `{"blocker": {"code": "missing_reference", "summary": "<spec>: depends on unknown spec '<id>' (no folder .writ/specs/<id>/ or .writ/specs/archive/<id>/)"}}` and exits 1.

**📋 Business Rules:**
1. An id under `.writ/specs/archive/<id>/spec.md` is satisfied by location alone. `spec-deps.py` orders specs; it has never judged completeness, and archive eligibility is already complete-family only ([Archive Eligibility](../../docs/spec-lifecycle.md#archive-eligibility)).
2. Archived specs are never parsed: their headers, cycles, or malformations cannot block an active graph.
3. An id present both active and archived resolves to the active folder, which keeps its ordering edge.
4. `parse` is unchanged. `order` and `graph` keep their shape; `archived_dependencies` is additive, so the schema stays `spec-deps-graph-v1`.
5. Every existing blocker (`malformed_dependencies`, `self_reference`, `duplicate_reference`, `dependency_cycle`, `missing_reference`) keeps its code and exit.

**Success Criteria:** the four fixture scenarios pass in both pytest (Python 3.9 and 3.14) and `bash scripts/eval.sh --check=spec-dependencies`; `validate --specs-dir .writ/specs` on this repo prints `ok` with the restored header; `check_spec_lifecycle_docs` still passes.

**Scope Boundaries:**
- Included: resolution in `validate`, tests, docs, the real-repo header restore.
- Excluded: any change to `archive-sweep.py`; a status check on archived specs; an `--include-archived` flag; story-level dependencies (`story-deps.py`).

**⚠️ Technical Concerns:**
- `_topo_order` uses `set(deps)` and would never release a spec whose archived dep is still in the set. The active graph passed to the sort and the cycle finder must have archived ids removed, while the reported `graph` keeps the declared lists.

**⚠️ Cross-Spec Overlap:** none. No in-progress spec-lite names the files in scope.

## Experience Design

### User journey

1. A spec ships. `/release` Step 1.3c or `/status --archive` moves it to `.writ/specs/archive/` by `git mv`.
2. A later spec in the same phase still lists it under `Dependencies:`. Today that is correct metadata: the dependency exists and is complete.
3. `/implement-phase` Step 2.1 runs `validate`. Before this spec: `missing_reference`, the phase stops before its confirmation gate, and the maintainer edits a header that was right. After: `ok`, the archived id is listed under `archived_dependencies`, and the order contains only active specs.

### State catalog

| State | Input | Output |
|---|---|---|
| Populated | active spec depends on an archived spec | `status: ok`; `order` holds the active spec; `archived_dependencies: {"<spec>": ["<id>"]}` |
| Empty | no `archive/` folder | `archived_dependencies: {}`; behavior identical to today |
| Edge | id in both `.writ/specs/<id>/` and `.writ/specs/archive/<id>/` | active wins; the id is an ordering edge, not in `archived_dependencies` |
| Edge | archived spec has a malformed header or a cycle of its own | never read; no blocker |
| Error | id in neither place | `missing_reference`, summary names both paths, exit 1 |
| Error | every other existing blocker | unchanged code, summary, and exit |

### Interaction patterns

No new flags, no prompts. The command surface of `spec-deps.py` is unchanged.

## Business Rules (Expanded)

### Location alone satisfies

`spec-deps.py` reads folder names under `specs_dir/archive/*/spec.md` and nothing else. It does not call `spec-status.py`. The reasoning: `validate` never checked an active dependency's status either. A `Not Started` dependency is an ordering edge, not a block. Completeness is `/verify-spec`'s concern, and archive eligibility already requires complete-family status. A spec moved into `archive/` by hand while still open is a lifecycle violation this script does not police.

### Archived specs are never parsed

Only the folder name is used. An archived `spec.md` with a malformed `Dependencies:` header, a self-reference, or a cycle with another archived spec cannot raise a blocker. This keeps the archive truly inert for ordering, matching the lifecycle doc's "nothing about the spec's internal content changes on archival".

### Active wins

`archive_one()` reports `collision` when a folder exists in both places. `validate` does not care: the active folder is discovered by `_discover`, so the id is `known`, and the archive copy is ignored.

### Output is additive

`archived_dependencies` maps each active spec to the ordered list of its declared ids that resolved through the archive. It is present on every `ok` result, `{}` when none resolved. `graph` still holds the declared lists verbatim, so a reader can reconstruct what the header said. The schema string stays `spec-deps-graph-v1`.

## Detailed Requirements

### `validate_graph` (reference shape)

```python
def _archived_ids(specs_dir: Path) -> set[str]:
    archive = specs_dir / "archive"
    return {p.parent.name for p in archive.glob("*/spec.md")} if archive.is_dir() else set()

def validate_graph(specs_dir, roadmap_order):
    graph = _discover(specs_dir)
    known = set(graph)
    archived = _archived_ids(specs_dir)
    active_graph: dict[str, list[str]] = {}
    archived_deps: dict[str, list[str]] = {}
    for spec in sorted(graph):
        active_graph[spec] = []
        for dep in graph[spec]:
            if dep in known:
                active_graph[spec].append(dep)
            elif dep in archived:
                archived_deps.setdefault(spec, []).append(dep)
            else:
                raise ContractError("missing_reference",
                    f"{spec}: depends on unknown spec {dep!r}"
                    f" (no folder .writ/specs/{dep}/ or .writ/specs/archive/{dep}/)")
    cycle = _find_cycle(active_graph)
    ...
    order = _topo_order(active_graph, roadmap_order)
    return {"schema": GRAPH_SCHEMA, "status": "ok", "order": order,
            "graph": graph, "archived_dependencies": archived_deps}
```

`_discover` is unchanged: it still globs `specs_dir/*/spec.md`, which excludes `archive/` by depth. `archive` itself is a folder under `specs_dir` but has no `spec.md`, so it never appears as a spec.

### Tests

`scripts/tests/test_spec_deps.py` (new) loads `spec-deps.py` by path, as `test_story_deps.py` does, and builds fixture folders under `tmp_path`:

| Test | Fixture | Assertion |
|---|---|---|
| archived dependency satisfied | `consumer -> [done]`, `archive/done/spec.md` | exit 0, `status ok`, `order == ["consumer"]`, `archived_dependencies == {"consumer": ["done"]}` |
| archived spec never parsed | `archive/done/spec.md` with `> **Dependencies:** not a list` and `archive/loop/spec.md` depending on `done` | exit 0, no blocker |
| unknown id still blocks | `consumer -> [ghost]`, archive present but without `ghost` | exit 1, `missing_reference`, summary contains both `.writ/specs/ghost/` and `.writ/specs/archive/ghost/` |
| active wins over archive | `done` in both places, `consumer -> [done]` | exit 0, `order == ["done", "consumer"]`, `archived_dependencies == {}` |
| no archive folder | `consumer -> [done]`, both active | exit 0, `archived_dependencies == {}`, every existing key present |

`scripts/eval-spec-deps.py` gains the same four archive scenarios as `emit` lines, so `eval.sh --check=spec-dependencies` covers them in CI as well as pytest.

### Docs

- `.writ/docs/spec-lifecycle.md`, under *Why one extra path segment is sufficient*, after the warning block: a short paragraph titled **Deliberate inclusion: dependency resolution** stating that `scripts/spec-deps.py validate` reads `.writ/specs/archive/*/spec.md` folder names so an archived dependency resolves as satisfied, that this is the one sanctioned inclusion the warning anticipates, and that the archived specs are never ordered or parsed. `check_spec_lifecycle_docs` in `eval.sh` pins the three existing headings and the glob-shape scenarios; the new paragraph adds no heading at `##` level and must leave those checks green.
- `commands/verify-spec.md` Check 3f: `missing reference (no such folder under .writ/specs/) → missing_reference (name it)` becomes `missing reference (no such folder under .writ/specs/ or .writ/specs/archive/) → missing_reference (name it)`.
- `commands/implement-phase.md` Step 2.1, after the sentence naming the executable reference: *A dependency whose folder sits under `.writ/specs/archive/` is satisfied: it is reported under `archived_dependencies` and never ordered.*
- `scripts/spec-deps.py` module docstring: one sentence on archive resolution.

### Real-repo check

The 2026-11-06 workaround removed `2026-10-25-design-divergence` from `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/spec.md` line 6 (commit `04e2045`). Restore the header to `[2026-10-25-design-divergence, 2026-10-25-review-route-rigor, 2026-10-25-repro-first-bug-fixing]` and run:

```bash
python3 scripts/spec-deps.py validate --specs-dir .writ/specs
```

Expected: `status: ok`, `archived_dependencies` contains `{"2026-10-25-gate-upgrade-removal-measurement": ["2026-10-25-design-divergence"]}`.

## Implementation Approach

One small change in one read-only script, tests first. Python 3.9 stdlib only (`from __future__ import annotations` is already present). No new scripts, so no agent-cli-contract row, no `gen-platform-trees.py` run unless `spec-deps.py` is a shipped script whose plugin copy must be regenerated: it is (`update-writ.md` lists it), so run `python3 scripts/gen-platform-trees.py` and `--check` after the edit. Run pytest alone per `CLAUDE.md`.

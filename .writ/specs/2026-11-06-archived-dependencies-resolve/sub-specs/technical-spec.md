# Technical Spec: Archived Dependencies Resolve

> Parent: [`spec.md`](../spec.md). Story: [`story-1-archived-dependencies-resolve.md`](../user-stories/story-1-archived-dependencies-resolve.md).

## Current behavior

`validate_graph(specs_dir, roadmap_order)` in `scripts/spec-deps.py`:

1. `_discover(specs_dir)` globs `specs_dir/*/spec.md` (single level, so `archive/<id>/spec.md` is excluded by depth) and parses each header.
2. `known = set(graph)`. Any declared dep not in `known` raises `missing_reference`.
3. `_find_cycle(graph)` and `_topo_order(graph, roadmap_order)` run on the full declared graph.

Step 2 is the defect: an archived dependency is a real, complete spec, but its folder is one level deeper, so it is unknown.

## Change

### New helper

```python
def _archived_ids(specs_dir: Path) -> set[str]:
    """Folder names of archived specs. Names only; archived headers are never parsed."""
    archive = specs_dir / "archive"
    if not archive.is_dir():
        return set()
    return {p.parent.name for p in archive.glob("*/spec.md")}
```

### `validate_graph`

| Declared dep | Resolution | Effect |
|---|---|---|
| in `known` | active edge | in `active_graph[spec]`; ordered |
| not in `known`, in `archived` | satisfied | appended to `archived_deps[spec]`; not ordered |
| in neither | `missing_reference` | summary `"{spec}: depends on unknown spec {dep!r} (no folder .writ/specs/{dep}/ or .writ/specs/archive/{dep}/)"`, exit 1 |

Order of checks matters for Business Rule 3: `known` is tested first, so an id in both places is an active edge.

`_find_cycle` and `_topo_order` receive `active_graph`. The result adds `"archived_dependencies": archived_deps` (a dict, `{}` when empty) and keeps `"graph": graph` (declared lists, verbatim). `GRAPH_SCHEMA` stays `spec-deps-graph-v1`.

The per-spec checks in `_discover` (self-reference, duplicate) are unchanged and still run before resolution, so `[done, done]` with `done` archived is still `duplicate_reference`.

### Docstring

Add to the module docstring under `validate`: *A dependency whose folder sits under `DIR/archive/` resolves as satisfied and is reported under `archived_dependencies`; archived specs are never parsed or ordered.*

## Tests

### `scripts/tests/test_spec_deps.py` (new)

Load the module by path:

```python
MODULE_PATH = Path(__file__).resolve().parents[1] / "spec-deps.py"
SPEC = importlib.util.spec_from_file_location("spec_deps", MODULE_PATH)
```

Helpers: `make_spec(root, spec_id, header, archived=False)` writes `root/<id>/spec.md` or `root/archive/<id>/spec.md` with the header line (or none). `run_validate(root)` calls `subprocess.run([sys.executable, MODULE_PATH, "validate", "--specs-dir", root])` and returns `(returncode, json)`.

| Test | Asserts |
|---|---|
| `test_archived_dependency_is_satisfied` | exit 0; `status == "ok"`; `order == ["consumer"]`; `archived_dependencies == {"consumer": ["done"]}`; `graph["consumer"] == ["done"]` |
| `test_archived_specs_are_never_parsed` | archive holds `done` with `> **Dependencies:** not a list` and `loop` with `[done]`; `consumer -> [done, loop]`; exit 0; `archived_dependencies["consumer"] == ["done", "loop"]` |
| `test_unknown_id_still_blocks_and_names_both_paths` | `consumer -> [ghost]`, archive holds `done`; exit 1; `blocker.code == "missing_reference"`; both `.writ/specs/ghost/` and `.writ/specs/archive/ghost/` in `summary` |
| `test_active_folder_wins_over_archive` | `done` active (`[]`) and archived; `consumer -> [done]`; exit 0; `order == ["done", "consumer"]`; `archived_dependencies == {}` |
| `test_no_archive_folder_is_unchanged` | `done` and `consumer` active; exit 0; keys `schema, status, order, graph, archived_dependencies` present; `archived_dependencies == {}` |
| `test_existing_blockers_unchanged` | parametrized over self-reference, duplicate, cycle, malformed; each still returns its code and exit 1 with an archive folder present |

### `scripts/eval-spec-deps.py`

Add `scenario_archive()` with four `emit` lines mirroring the first four tests: `validate-archived-dependency-satisfied`, `validate-archived-never-parsed`, `validate-missing-names-archive-path`, `validate-active-wins-over-archive`. `make_spec` gains an `archived: bool = False` parameter that writes under `root / "archive"`. Call it from `main()`.

`check_spec_dependencies` in `eval.sh` reads the TSV and needs no change.

## Docs

| File | Edit |
|---|---|
| `.writ/docs/spec-lifecycle.md` | After the `⚠️ Do not add a second, separate exclusion check` block: a paragraph **Deliberate inclusion: dependency resolution.** `scripts/spec-deps.py validate` reads `.writ/specs/archive/*/spec.md` folder names so that an active spec's dependency on an archived spec resolves as satisfied (`archived_dependencies` in its output). This is the sanctioned inclusion the warning anticipates: archived specs are never parsed or ordered, and the single-level `_discover` glob is unchanged. Also add a row to the call-site table: `scripts/spec-deps.py validate` — `_discover` single-level (No); `_archived_ids` reads `archive/*/spec.md` names only (Yes, deliberately). No new `##` heading, so `check_spec_lifecycle_docs` literals hold. |
| `commands/verify-spec.md` Check 3f | `(no such folder under .writ/specs/)` → `(no such folder under .writ/specs/ or .writ/specs/archive/)` |
| `commands/implement-phase.md` Step 2.1 | After the executable-reference sentence: *A dependency whose folder sits under `.writ/specs/archive/` is satisfied: it is reported under `archived_dependencies` and never ordered.* The three `require_literal` strings in `check_spec_dependencies` are untouched. |

`eval.sh --check=docs-check` (`scripts/docs-check.py`) runs after the doc edits; relative links in the new paragraph must resolve.

## Real-repo check

Restore line 6 of `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/spec.md` to:

```markdown
> **Dependencies:** [2026-10-25-design-divergence, 2026-10-25-review-route-rigor, 2026-10-25-repro-first-bug-fixing]
```

Then `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` must print `status: ok` with `archived_dependencies["2026-10-25-gate-upgrade-removal-measurement"] == ["2026-10-25-design-divergence"]`. This is the regression the issue reports, run against the live tree.

## Shipping

`spec-deps.py` is a shipped runtime script (`commands/update-writ.md` lists it). After the edit run `python3 scripts/gen-platform-trees.py` then `python3 scripts/gen-platform-trees.py --check`, and `bash scripts/eval.sh --check=platform-trees`.

## Error & Rescue Map

| Operation | Failure | Handling |
|---|---|---|
| `_archived_ids` | `archive/` absent | empty set; result identical to today |
| `_archived_ids` | `archive/` present, unreadable entry | `glob` skips it; the id is unknown and blocks as `missing_reference`, which is the fail-closed answer |
| resolution | id in neither place | `missing_reference`, exit 1, summary names both paths |
| resolution | id archived but also declared twice | `duplicate_reference` from `_discover`, before resolution |
| ordering | archived spec has its own cycle | never read; no effect |

## Shadow Paths

- **Happy path:** `consumer -> [done]`, `archive/done/spec.md` → `ok`, `order ["consumer"]`.
- **Nil input:** no `archive/` → `archived_dependencies {}`.
- **Empty input:** `archive/` with no `*/spec.md` → `archived_dependencies {}`.
- **Upstream error:** archived `spec.md` unreadable or malformed → never read; no blocker.

## Out of scope

`archive-sweep.py` (no refusal, no dependent rewrite), a status check on archived folders, an `--include-archived` flag, `story-deps.py`, and `ac-trace.py` (already resolves both locations).

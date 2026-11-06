# Archived Dependencies Resolve (Lite)

> Source: .writ/specs/2026-11-06-archived-dependencies-resolve/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** `scripts/spec-deps.py validate` treats a dependency id whose folder sits under `.writ/specs/archive/<id>/spec.md` as satisfied, reports it under a new `archived_dependencies` key, and never orders or parses the archived spec. Unknown ids still block with `missing_reference`.

**Implementation Approach:**
- Add `_archived_ids(specs_dir)`: folder names from `specs_dir / "archive"` globbed `*/spec.md`; empty set when the folder is absent.
- In `validate_graph`, split each declared list into active edges (`dep in known`), archived (`dep in archived`), or `missing_reference`. Pass only active edges to `_find_cycle` and `_topo_order`; report the declared lists in `graph`.
- `missing_reference` summary: `(no folder .writ/specs/<id>/ or .writ/specs/archive/<id>/)`.
- Schema stays `spec-deps-graph-v1`; `archived_dependencies` is additive, `{}` when none.
- Python 3.9 stdlib. `_discover` and `parse` untouched. Regenerate the plugin copy with `python3 scripts/gen-platform-trees.py`.

**Files in Scope:**
- `scripts/spec-deps.py`: `validate_graph`, new helper, docstring
- `scripts/tests/test_spec_deps.py`: new, import-by-path like `test_story_deps.py`
- `scripts/eval-spec-deps.py`: four archive scenarios
- `.writ/docs/spec-lifecycle.md`: "Deliberate inclusion: dependency resolution" paragraph
- `commands/verify-spec.md` Check 3f, `commands/implement-phase.md` Step 2.1: one line each
- `.writ/specs/2026-10-25-gate-upgrade-removal-measurement/spec.md`: restore `2026-10-25-design-divergence` to `Dependencies:`
- Never: `scripts/archive-sweep.py`, `scripts/spec-status.py`, `scripts/ac-trace.py`

**Error Handling:**
- Id in neither place → `missing_reference`, exit 1, summary names both paths
- Archived spec with a bad header or its own cycle → never read, no blocker
- Id active and archived → active wins, ordering edge kept

**Integration Points:**
- `/implement-phase` Step 2.1 and `/verify-spec` Check 3f call `validate`; `phase-state.py` consumes `order` only

---

## For Review Agents

**Acceptance Criteria:**
1. An active spec depending on an archived spec validates `ok`, `order` holds only active specs, `archived_dependencies` names the id `[AC-1.1]`
2. Archived specs are never parsed: a malformed or cyclic archived header raises nothing `[AC-1.2]`
3. An id absent from both places blocks with `missing_reference` and a summary naming both paths; every other blocker is unchanged `[AC-1.3]`
4. An id present in both places resolves to the active folder with its ordering edge `[AC-1.2]`
5. The lifecycle doc, Check 3f, and Step 2.1 say an archived dependency is satisfied; `eval.sh` checks stay green `[AC-1.4]`
6. The restored removal-measurement header validates `ok` on this repo `[AC-1.5]`

**Business Rules:**
- Location alone satisfies; `spec-deps.py` never judges status
- `parse` unchanged; `order`, `graph`, schema unchanged; one additive key
- `archive-sweep.py` unchanged: archival is never refused or rewritten for dependents

**Experience Design:**
- Entry: `spec-deps.py validate --specs-dir .writ/specs` from `/implement-phase` or `/verify-spec`
- Happy path: one JSON object, `status: ok`, exit 0
- Moment of truth: the archived id under `archived_dependencies`, not a blocker
- Feedback: unchanged JSON on stdout
- Error: `missing_reference` names `.writ/specs/<id>/` and `.writ/specs/archive/<id>/`

---

## For Testing Agents

**Success Criteria:**
1. `scripts/tests/test_spec_deps.py` passes on Python 3.9 and 3.14
2. `bash scripts/eval.sh --check=spec-dependencies` and `--check=spec-lifecycle-docs` pass
3. `python3 scripts/spec-deps.py validate --specs-dir .writ/specs` prints `ok` after the header restore

**Shadow Paths to Verify:**
- **Happy path:** `consumer -> [done]`, `archive/done/spec.md` → ok
- **Nil input:** no `archive/` folder → `archived_dependencies: {}`, result otherwise identical
- **Empty input:** `archive/` present but empty → same as nil
- **Upstream error:** `archive/done/spec.md` malformed → no blocker

**Edge Cases:**
- `done` in both places → `order == ["done", "consumer"]`, `archived_dependencies == {}`
- `consumer -> [ghost]` with an archive present → `missing_reference`

**Coverage Requirements:**
- New code: 100% (one helper, one branch); error paths: 100%

**Test Strategy:**
- Fixture folders under `tmp_path`; run the script by subprocess and the function by import, as `test_story_deps.py` does. Run pytest alone.

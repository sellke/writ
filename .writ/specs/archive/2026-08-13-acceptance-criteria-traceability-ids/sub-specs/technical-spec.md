# Technical Spec — Per-Criterion Traceability IDs

> Parent: [../spec.md](../spec.md)
> Stories: [1](../user-stories/story-1-id-grammar-and-emitter.md) ·
> [2](../user-stories/story-2-the-checker.md) ·
> [3](../user-stories/story-3-verify-spec-wiring.md) ·
> [4](../user-stories/story-4-edit-spec-stability-guard.md)

## CLI Surface

```
python3 scripts/ac-trace.py check --spec .writ/specs/<folder> [--repo .]
```

| Aspect | Contract |
|---|---|
| Side effects | None. Read-only in the strict sense `scripts/exit-criteria.py` documents about itself — writes no file, and any git call stays within `rev-parse`, `log`, `check-ignore` |
| Output | Exactly one JSON object on stdout, schema string `ac-trace-check-v1` |
| Exit 0 | Ran correctly; no blocking findings (informational `legacy_story` entries may be present) |
| Exit 1 | Ran correctly; at least one blocking finding |
| Exit 2 | Could not run correctly — usage error, missing `user-stories/`, unreadable story file |
| Determinism | Byte-identical stdout across runs on identical input; findings sorted by (story number, ID ordinal, code) |

Owned by Story 2. Story 3 names this invocation as Check 3e/3f's executable reference and adds
no parsing of its own.

## Parsing Contract

The tag is **end-anchored**. The reference pattern is:

```python
TAG = re.compile(r"`\[((?:AC-\d+\.\d+)(?:,\s*AC-\d+\.\d+)*)\]`\s*$")
```

Only a match of this pattern is a definition or a citation. An ID-shaped token elsewhere on
the line is prose. See spec.md → ### The tag is end-anchored — Story 4's own criteria are the
proof case, and a naive unanchored scan mis-read them during authoring.

| Element | Source | Pattern |
|---|---|---|
| Marker | First `> **AC IDs assigned through:** AC-<n>.<m>` line inside `## Acceptance Criteria` | Consumed as the marker; **excluded** from both the definition set and the citation set |
| Criterion definition | Lines in `## Acceptance Criteria` matching `- [ ]`/`- [x]` | `TAG` match only; story number must equal the story file's own number |
| Task citation | Lines in `## Implementation Tasks` | `TAG` match only |
| Prose mention | Any ID token not inside a `TAG` match | Neither definition nor citation; ignored |
| Test citation | Bare token `AC-<n>.<m>` in a file outside `.writ/` whose path is test-shaped | Test-shaped: path segment `tests/`, `test/`, `spec/`, `__tests__/`, or basename matching `test_*`, `*_test.*`, `*.test.*`, `*.spec.*` |
| Source citation | Same token outside `.writ/` in a non-test-shaped path | Recorded, informational, does **not** satisfy coverage |

Scan bounds for the citation pass: skip `.git/`, skip git-ignored paths, skip binaries, do not
follow symlinks out of the repo.

## Finding Codes

| Code | Condition | Severity |
|---|---|---|
| `untasked_criterion` | Defined ID cited by no implementation task | Blocking, any status |
| `untested_criterion` | Tasked, no test citation, story reads `Completed ✅` | Blocking |
| `dangling_reference` | Task or test cites an ID no criterion defines | Blocking |
| `duplicate_id` | Same ID on two criterion lines | Blocking |
| `marker_violation` | ID exceeds the marker, or marker missing/malformed while IDs present | Blocking |
| `partial_adoption` | Some criteria in a story carry IDs, others do not | Blocking |
| `legacy_story` | Zero criteria in the story carry IDs | Informational |

## Error & Rescue Map

Written from the outside in — each cell is what the operator sees, not what the code does.

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Resolve `--spec` path | Path does not exist, or is a file rather than a spec folder | Exit 2, naming the path and what was expected (a folder containing `user-stories/`) | Unit test per shape: missing path, file-not-folder, folder without `user-stories/` |
| Read story file | Unreadable (permissions), or invalid UTF-8 | Exit 2, naming the file — never a silent skip that would report clean coverage for an unread story | Unit test with a chmod-000 fixture and an invalid-UTF-8 fixture |
| Parse marker | Marker absent while IDs present; marker malformed; two marker lines | `marker_violation` (blocking, exit 1). Absent marker with **zero** IDs is `legacy_story`, not a violation | Unit test per shape, including the zero-ID case that must not be a violation |
| Parse criterion line | Tag present but ID malformed (`AC-3`, `AC-x.1`, wrong story number for the file) | `marker_violation` naming the offending line; a wrong story number is reported, not silently re-homed | Unit test per malformed form |
| Scan repo for citations | Very large tree makes the scan slow; git-ignored vendor directories | Bounded scan (skip `.git/`, git-ignored, binaries, out-of-repo symlinks); report the count of files scanned in the JSON so a pathological scan is visible | Fixture repo with a git-ignored directory containing a decoy ID; assert it is not counted |
| Scan repo for citations | Repo is not a git worktree, so `git check-ignore` is unavailable | Fall back to scanning without the ignore filter and record `ignore_filter: false` in the output — degraded, disclosed, never silently narrowed | Unit test in a non-git tempdir |
| Emit verdict | Findings ordering depends on filesystem enumeration order | Sort by (story number, ID ordinal, code) before emit; assert byte-identical repeat runs | Determinism test: two runs, compare stdout bytes |

No cell is `[UNPLANNED]`.

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| `ac-trace.py check` | Exit 0, JSON with empty `findings` | `--spec` folder has no `user-stories/` → exit 2 naming the path | Story has zero criterion lines → exit 0, no findings, not an error | Story file unreadable → exit 2 naming the file, never exit 0 |
| Check 3e/3f in `/verify-spec` | Check 3 row reads pass | Legacy spec, zero IDs → informational note, Check 3 row still passes | Spec with no stories → Check 1 already fails on structure; 3e/3f report nothing | Script exits 2 → Check 3 row reads "could not evaluate" with the path, never "pass" |
| `/edit-spec` criterion insert | New ID is mark+1, marker advances, siblings byte-identical | Story has no marker → marker created at first adoption | Insert into a story with zero criteria → `AC-n.1`, marker created | Retired ID still cited → surfaced during the edit for repoint-or-delete |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| Two IDs on one criterion line (`[AC-3.1, AC-3.2]`) | Both defined; `duplicate_id` only fires when an ID repeats across lines |
| Same ID in two different specs | Scoped per spec folder; no cross-spec collision and no cross-spec citation |
| ID appears only in the marker line | `untasked_criterion` — the marker never satisfies its own ID |
| Criterion prose quotes an ID as an example (Story 4's `AC-4.1`) | Not a definition and not a citation — only an end-anchored `TAG` match counts. Regression fixture: Story 4's own criteria must yield exactly four definitions, all `AC-4.*` |
| Definition tag whose story number differs from its file (`AC-2.1` in `story-4-*.md`) | `marker_violation` naming the line — reported, never silently re-homed |
| ID appears only in a commit message or changelog | Not a citation. Source citations require a tracked file; neither satisfies coverage |
| Criterion reworded but ID unchanged | Intended and silent. IDs bind to position-in-history, not to text — the deliberate difference from the rejected content-hash scheme |
| Criterion deleted while a test still cites it | `dangling_reference` from the checker; surfaced earlier by Story 4 during the edit itself |
| Story renumbered (story-3 becomes story-4) | Out of scope. `/edit-spec` archives rather than renumbers stories; if renumbering is ever added, every ID in that story becomes a dangling reference and this row becomes a defect |
| Repeated runs, unchanged input | Byte-identical stdout — the property Story 2's determinism test asserts |

## Not Touched

`scripts/recommend-state.py`, `scripts/eval-recommend-stage.py`,
`scripts/eval-recommend-state-adversarial.py`.

This is the direct consequence of suffix ID placement, and Story 1's task 1.1 verifies the
assumption before anything is built. If a future change moves the ID to a line prefix, both
regexes — `^- \[([ xX])\] Given ` at `recommend-state.py:378` and `(?m)^- \[x\] (Given .+)$` at
`recommend-state.py:2981` — must change first, along with the two eval fixture sets, and this
section is void.

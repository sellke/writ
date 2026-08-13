# Acceptance Criteria IDs

> Parent spec: [`2026-08-13-acceptance-criteria-traceability-ids`](../specs/2026-08-13-acceptance-criteria-traceability-ids/spec.md)
> Produced by: Story 1 (`user-stories/story-1-id-grammar-and-emitter.md`)
> Consumed by: Story 2, which implements `scripts/ac-trace.py` against exactly this grammar and
> finding vocabulary — no rule here, no predicate there.

## Purpose

Every acceptance criterion in a `user-stories/story-*.md` file gets a stable, never-renumbered
ID. Tasks and tests cite the IDs they satisfy. This document is the specification a checker
implements against — the same relationship [`exit-criteria-classification.md`](exit-criteria-classification.md)
has to `scripts/exit-criteria.py`. It defines the ID form, the marker rule, the finding
vocabulary, and the parsing contract precisely enough that an implementer decides nothing new.

## ID Form

`AC-<story>.<n>` — the story number, then a per-story ordinal, e.g. `AC-3.6`.

The ID is rendered as a **trailing backticked tag** on the line it belongs to:

```markdown
- [ ] Given a criterion no task cites, when the check runs, then it reports uncovered. `[AC-3.1]`
```

Multiple IDs on one line are comma-separated inside a single tag:

```markdown
- [ ] 3.2 Implement the orphan scan `[AC-3.1, AC-3.6]`
```

### Why suffix, not prefix

`scripts/recommend-state.py` parses criterion lines with two anchored regexes:

| Site | Pattern | Consequence of a prefixed ID |
|---|---|---|
| `recommend-state.py:378` | `^- \[([ xX])\] Given ` | Counts zero criteria |
| `recommend-state.py:2981` | `(?m)^- \[x\] (Given .+)$` | Matches nothing → raises `ContractError("uat_derivation_mismatch")` |

A trailing tag leaves both regexes matching unchanged — verified directly, not assumed
(Story 1, task 1.1: a criterion line carrying a trailing tag was run against both patterns and
both still matched). `scripts/recommend-state.py` and its two eval fixture sets
(`eval-recommend-stage.py`, `eval-recommend-state-adversarial.py`) are out of scope for this
grammar and must not be touched by anything that implements it. If a future change ever moves
the ID to a line prefix, both regexes above must change first, along with their fixture sets.

## The Tag Is End-Anchored

The reference pattern, used verbatim by the checker:

```python
TAG = re.compile(r"`\[((?:AC-\d+\.\d+)(?:,\s*AC-\d+\.\d+)*)\]`\s*$")
```

Only a match of this pattern at the **end of the line** is a definition or a citation. An
ID-shaped token anywhere else on the line — including one inside its own backticks — is prose
and is neither a definition nor a citation.

This is not a nicety. A criterion whose text *describes* IDs as a fixture — e.g. "Given a story
with criteria `AC-2.1` through `AC-2.4` and a marker reading `AC-2.4` …" — contains three
ID-shaped tokens that are not tags. A scanner that treats any ID-shaped token on a criterion
line as a definition would misread that criterion as defining three IDs and report them
untasked and cross-story. The anchoring rule exists specifically to keep prose-mentioned IDs
inert.

### Definition vs. citation vs. mention

| Category | Where | Rule |
|---|---|---|
| **Definition** | The trailing `TAG` group on a `- [ ]`/`- [x]` line inside `## Acceptance Criteria` | Only an end-anchored `TAG` match counts |
| **Citation (task)** | The trailing `TAG` group on a task line inside `## Implementation Tasks` | Only an end-anchored `TAG` match counts |
| **Citation (test)** | A bare `AC-<n>.<m>` token in a test-shaped file path (see below) | No backticks or trailing-anchor requirement — this is a bare token in a name/docstring, not a markdown line |
| **Citation (source)** | The same bare token outside `.writ/`, in a path that is **not** test-shaped | Recorded, informational; does **not** satisfy coverage |
| **Prose mention** | Any ID-shaped token that is not inside a `TAG` match on a criterion/task line, or not a bare token in a scanned file outside `.writ/` | Neither definition nor citation; ignored |

The same anchoring makes multi-ID groups unambiguous: `` `[AC-3.1, AC-3.6]` `` is one group
defining or citing two IDs, not two separate tags.

### Cross-story guard

A definition tag whose story number differs from the story file's own number (e.g. `AC-2.1`
appearing in `story-4-*.md`) is a `marker_violation`, reported at that line — never silently
re-homed to the story it appears in.

## The High-Water Mark

Each story's `## Acceptance Criteria` section carries exactly one marker line directly beneath
the heading:

```markdown
## Acceptance Criteria

> **AC IDs assigned through:** AC-3.6
```

Rules, structural rather than a prose convention a later editor must remember:

- A new criterion takes `<mark> + 1`, and the marker advances to the new value.
- Siblings are never renumbered when a criterion is inserted or deleted.
- Retired numbers are never reused.
- Reading order and ID order are deliberately independent — a criterion inserted second in
  reading order can hold a higher-numbered ID than one below it, if that one was assigned
  earlier and never moved.

### Marker exclusion

The marker line itself contains an ID-shaped token (`AC-3.6` in the example above). It must be
consumed as *the marker* and **excluded** from both the definition set and the citation set.
Without this exclusion, every marker satisfies its own ID and the checker reports a spec with
zero real coverage as clean.

### Worked example — insert

Before, marker at `AC-3.4`, three criteria:

```markdown
> **AC IDs assigned through:** AC-3.4

- [ ] Given a spec with no marker, when the check runs, then it reports a marker violation. `[AC-3.1]`
- [ ] Given a criterion with no citing task, when the check runs, then it reports uncovered. `[AC-3.3]`
- [ ] Given two criteria sharing an ID, when the check runs, then it reports a duplicate. `[AC-3.4]`
```

A fourth criterion is inserted between the first and second (reading order), addressing a gap
found during review. It takes `mark + 1 = AC-3.5`, and the marker advances. Every existing
sibling tag is byte-identical to before:

```markdown
> **AC IDs assigned through:** AC-3.5

- [ ] Given a spec with no marker, when the check runs, then it reports a marker violation. `[AC-3.1]`
- [ ] Given a criterion with no test citation at Completed status, when the check runs, then it reports untested. `[AC-3.5]`
- [ ] Given a criterion with no citing task, when the check runs, then it reports uncovered. `[AC-3.3]`
- [ ] Given two criteria sharing an ID, when the check runs, then it reports a duplicate. `[AC-3.4]`
```

`AC-3.1`, `AC-3.3`, and `AC-3.4` are unchanged. The new criterion is `AC-3.5` regardless of
where it lands in reading order.

### Worked example — delete

Continuing from the four-criterion state above (marker `AC-3.5`), `AC-3.3` ("no citing task")
is found to duplicate `AC-3.1`'s intent during an `/edit-spec` pass and is deleted outright:

```markdown
> **AC IDs assigned through:** AC-3.5

- [ ] Given a spec with no marker, when the check runs, then it reports a marker violation. `[AC-3.1]`
- [ ] Given a criterion with no test citation at Completed status, when the check runs, then it reports untested. `[AC-3.5]`
- [ ] Given two criteria sharing an ID, when the check runs, then it reports a duplicate. `[AC-3.4]`
```

The marker **does not** move back to `AC-3.4` — it stays at `AC-3.5`, the highest ID ever
assigned in this story. `AC-3.3` is retired permanently and must never be reused by a future
insert (the next insert takes `AC-3.6`). `AC-3.1`, `AC-3.4`, and `AC-3.5` are byte-identical to
before the delete. Any task or test that still cites the deleted `AC-3.3` becomes a
`dangling_reference` at the next check run — that is the intended detection, not a bug in the
delete.

## Task Citation

Implementation tasks carry the same trailing tag, comma-separated for multiple IDs:

```markdown
## Implementation Tasks

- [ ] 3.2 Implement the orphan scan `[AC-3.1, AC-3.6]`
```

Task-line parsers anchor on the `- [ ] N.M` prefix, so a trailing tag is non-breaking there for
the same reason it is non-breaking on criterion lines.

## Test Citation

Tests cite IDs in a test name or docstring:

```python
def test_uncovered_criterion_is_blocking():
    """AC-3.1 — a criterion no task cites reports uncovered."""
```

A citation counts as a **test** citation only when it appears in a test-shaped path. An ID
occurrence elsewhere outside `.writ/` is a **source** citation — informational, and it does not
satisfy coverage. An ID occurrence inside `.writ/` outside a story's own criterion/task lines
(e.g. in a commit-message quote or a changelog entry) is not a citation of either kind.

### Test-shaped path patterns

A path is test-shaped when it has:

- a path segment equal to `tests/`, `test/`, `spec/`, or `__tests__/`, **or**
- a basename matching `test_*`, `*_test.*`, `*.test.*`, or `*.spec.*`

`.writ/config.md` caches a `Test Runner` command but no test globs, and this grammar
deliberately adds no config field to supply them — pattern classification above is the whole
mechanism.

## Finding Codes

Named codes, mirroring the style Check 4d already uses (`malformed_dependencies`,
`missing_reference`, …):

| Code | Condition | Severity |
|---|---|---|
| `untasked_criterion` | A defined ID that no implementation task in the spec cites | **Blocking**, at any story status |
| `untested_criterion` | Tasked, but no test citation, and the story reads `Completed ✅` | **Blocking** |
| `dangling_reference` | A task or test cites an ID that no criterion in the spec defines | **Blocking** |
| `duplicate_id` | The same ID appears on two criterion lines | **Blocking** |
| `marker_violation` | An ID exceeds the marker, or the marker is missing/malformed while IDs are present | **Blocking** |
| `partial_adoption` | Some criteria in a story carry IDs and others do not | **Blocking** |
| `legacy_story` | Zero criteria in the story carry IDs | Informational, never blocking |

### Severity reasoning

- **`untasked_criterion` is blocking at any status** because task tags are written at spec
  *authoring* time, not implementation time. A criterion no task cites is a defect in the spec
  package the moment it is written, and deferring the finding until the story completes would
  let it ship.
- **`untested_criterion` is blocking only at `Completed ✅`** because tests do not exist until
  the work does. Before completion its absence is expected; at completion it is the precise
  failure this grammar exists to catch — a criterion silently dropped mid-build while the story
  still reports `Completed ✅` — and it belongs in the same class as `/verify-spec` Check 3a's
  false completion.
- **`dangling_reference` is blocking** because a task or test that cites a nonexistent ID is
  either pointing at a criterion that was deleted out from under it, or a typo — in either case
  the citation is currently lying about what it proves.
- **`duplicate_id` is blocking** because two criteria sharing an ID makes every citation of that
  ID ambiguous about which criterion it actually covers.
- **`marker_violation` is blocking** because it signals either a broken high-water mark (an ID
  beyond what the marker records, meaning the marker was not advanced on insert) or a
  malformed/missing marker with IDs already present — both mean the stability mechanism itself
  cannot be trusted for this story.
- **`partial_adoption` is blocking, `legacy_story` is not.** Zero IDs is a pre-adoption story
  and reported informationally, mirroring how Check 4d treats a spec with no `Dependencies`
  header as `[]`. Some-but-not-all IDs is not a migration state — it is a half-applied grammar
  in which the unaddressed criteria are invisible to the check while the story appears to
  participate.

## Legacy and Archive Posture

- Archived specs under `.writ/specs/archive/` are never scanned. The single-level glob
  `.writ/specs/*/` that `/verify-spec --all` already uses excludes them by construction.
- No retroactive backfill. IDs assigned to an already-`Completed ✅` story could not be honestly
  bound to tests written without them; a backfilled ID would manufacture the appearance of a
  trace link that never existed.

## Scan Bounds

The citation pass (test and source citations) skips `.git/`, skips git-ignored paths, skips
binaries, and does not follow symlinks out of the repo.

## Not This Document's Job

This document specifies the grammar and the finding vocabulary. It does not specify the CLI
surface, JSON schema, exit codes, or ordering/determinism guarantees of the checker itself —
those belong to `scripts/ac-trace.py` and its owning story's technical spec. See
[technical-spec.md](../specs/2026-08-13-acceptance-criteria-traceability-ids/sub-specs/technical-spec.md)
for that contract.

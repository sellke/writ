# Technical Spec: Governor Instrumentation

> Source: `.writ/specs/2026-08-11-governor-instrumentation/spec.md`

## Current state of `scripts/eval-leanness.py`

The helper is a registry-driven measurement tool with a fixed output contract (module docstring):

```
{
  "structural": [ {"subject","what","fix"} ],   # -> eval.sh FAILs the run
  "warnings":   [ {"subject","what","fix"} ],   # -> non-blocking, exit 0
  "metrics":    { ... "per_surface" ... }
}
exit code: always 0 — the bash check decides FAIL from `structural`.
```

`main()` assembles the two lists directly:

```python
structural = check_parity(root) + check_coverage(root)
base_structural, base_warnings = check_baseline(baseline, err, baseline_path, metrics)
structural += base_structural
warnings = scan_warnings + base_warnings + check_ceilings(metrics)
```

Every existing check is already a **pure function returning `list[dict]`** — `check_parity`, `check_coverage`, `check_ceilings` — with `check_baseline` the sole exception (it returns a `(structural, warnings)` tuple because a missing baseline is blocking while a growth delta is not). The four new checks follow the pure-function convention, not `check_baseline`'s tuple, because their severity is decided by the seam rather than per-finding.

`eval.sh`'s `check_leanness()` reads the JSON, maps `structural` → `add_finding` (FAIL) and `warnings` → `add_note` (informational). Nothing else needs to change in `eval.sh` for this spec — that is the point of the seam.

## The emission seam (Story 7 defines it; Story 3 introduces it)

### Constant

```python
# Phase 10 sequencing (ADR-020, "Enforcement sequencing (load-bearing)"; roadmap
# Phase 10 → Dependencies). Component-contract findings land NON-BLOCKING while
# 2026-08-11-component-contract and 2026-08-11-loop-bounds migrate the surface.
# Landing them blocking on day one turns every eval run red, and a permanently
# red gate becomes invisible — exactly how the four growth warnings were ignored.
#
# THE GOVERNOR-ENFORCEMENT SPEC FLIPS THIS ONE STRING. Nothing else.
CONTRACT_CHECK_SEVERITY = "warnings"   # -> "structural"
```

### Router

```python
def emit_contract_findings(findings, structural, warnings, severity=None):
    """Route a check's findings to the blocking or non-blocking bucket.

    `severity=None` means "follow CONTRACT_CHECK_SEVERITY" — the normal case.
    An explicit "warnings" pins a check non-blocking regardless of the flip
    (required_skills:, per system-instructions.md graceful degradation).
    Any unrecognized value falls back to `warnings`: a typo in the flip must
    never silently disable a check, and must never accidentally block a run.
    """
    target = warnings if (severity or CONTRACT_CHECK_SEVERITY) != "structural" else structural
    target.extend(findings)
```

### Wiring in `main()`

```python
warnings = scan_warnings + base_warnings + check_ceilings(metrics)

emit_contract_findings(check_component_contract(root), structural, warnings)
emit_contract_findings(check_completion_sections(root), structural, warnings)
emit_contract_findings(check_loop_bounds(root), structural, warnings)
emit_contract_findings(check_required_skills(root), structural, warnings,
                       severity="warnings")   # pinned — Business Rule 6
```

The four checks never touch `structural` or `warnings` themselves. Grepping `eval-leanness.py` for `structural.append` inside a `check_*contract*` function must return nothing — that is a testable property, and Story 7 tests it.

### Why a constant and not a CLI flag or env var

A flag or env var makes severity a *runtime* decision, which means `eval.sh`, CI, and any local run can disagree about whether the gate binds. The whole value of this seam is that the flip is a reviewable, single-line, committed diff that changes behavior everywhere at once. A constant is also directly settable in-process by the flip test (`module.CONTRACT_CHECK_SEVERITY = "structural"`), which is what makes Business Rule 3's "verified by a test that throws it" possible without rewriting the script on disk.

## Frontmatter parsing

Commands carry real `---` YAML frontmatter (32/32 verified). No YAML library is imported — `eval-leanness.py` has zero third-party dependencies today and must keep them. A minimal reader is sufficient for the three fields:

```python
def read_frontmatter(path) -> dict[str, str] | None:
    """Leading --- block only. Returns {key: raw_value_string} or None when the
    file has no leading fence. A key with a block/list value (e.g. `exit_criteria:`
    followed by `  - "..."` lines) maps to the joined continuation lines, so
    presence-and-non-emptiness is decidable without a YAML parse."""
```

Rules:

- Only a fence starting on **line 1** counts. A `---` horizontal rule mid-document is not frontmatter.
- A key is **present** if it appears at column 0 followed by `:`.
- A key is **non-empty** if its inline value is a non-blank string, or it is followed by at least one indented continuation line. `exit_criteria:` with nothing under it is a finding — ADR-020's whole point is that the field forces a falsifiable condition, and an empty list asserts nothing.
- Unparseable / no leading fence → one finding naming the file, never an exception (Business Rule 4's read-only posture includes "never crash the eval run").

## Check 1 — `check_component_contract(root)`

### Commands

```
for path in all_command_files(root):
    stem = basename without .md
    if is_infra(stem): continue          # Business Rule 7 — _preamble.md
    fm = read_frontmatter(path)
    for field in ("problem", "outcome", "exit_criteria"):
        if field missing or empty:
            finding(subject=f"commands/{stem}.md → {field}:", ...)
```

### Agents — the dual carrier (Business Rule 5)

Verified layout, 2026-08-11:

| Files | Heading | Fence |
|---|---|---|
| `architecture-check-agent.md`, `coding-agent.md`, `documentation-agent.md`, `review-agent.md`, `testing-agent.md`, `user-story-generator.md` | `## Agent Configuration` | ` ``` ` (plain) |
| `visual-qa-agent.md` | `## Agent Specification` | ` ```yaml ` |

The reader accepts either heading and either fence info-string, extracts the first fenced block after it, and applies the same three-field presence test. A file with neither heading yields one finding (`agents/<name>.md → no Agent Configuration/Specification block`) rather than three field findings — the carrier is missing, so field-level findings would be noise.

`system-instructions.md` already documents this split for `model_tier`; ADR-020 item 2 explicitly reuses the same carrier. Recognizing only `## Agent Configuration` would produce three false findings against `visual-qa-agent.md`, and false findings are precisely how a channel earns its ignore.

### Expected output today

31 × 3 + 7 × 3 = **114 findings**. Every one addressable by a named file and a named field.

## Check 2 — `check_completion_sections(root)`

Exact match on `^## Completion\s*$` for each non-infra command. Verified today: 13 of 32 files contain `^## Completion`; `_preamble.md` is not among them, so **31 checkable commands, 13 compliant, 18 findings**.

Finding text names the required spelling explicitly:

```
subject: commands/create-spec.md → ## Completion
what:    no `## Completion` section; commands/new-command.md's authoring
         template mandates one.
fix:     Add a `## Completion` section (exact H2 spelling — `## Completion
         Criteria` and `### Completion` do not satisfy this check).
```

The parenthetical is load-bearing. A maintainer who writes `## Completion Criteria`, sees the finding persist, and cannot tell why is one step from ignoring the channel.

## Check 3 — `check_loop_bounds(root)`

```python
# The five loop-bearing commands, measured in Phase 10 discovery (roadmap
# Phase 10 → Problem table: "Loop-bearing commands declaring an iteration
# bound: 0 of 5"). Deliberately a fixed list, not inferred from file contents:
# inferring "does this command loop?" from prose needs a heading/keyword
# grammar per variant — the exact fragility ADR-020 rejects for `## Goal`.
# Adding a loop to a sixth command means adding it here, by hand, on purpose.
LOOP_BEARING_COMMANDS = (
    "implement-phase", "implement-spec", "implement-story", "refactor", "verify-spec",
)
```

Asserts frontmatter declares `loop.max_iterations` and `loop.on_exhaustion` — nested under a `loop:` key, or flattened; the presence test accepts either shape, since `2026-08-11-loop-bounds` owns the final form. Expected today: 5 × 2 = **10 findings**.

**Dependency risk, stated plainly:** if `2026-08-11-loop-bounds` chooses different field names, this check's constant and its tests change. Nothing else in this spec does. Story 4 must read that spec's chosen shape before finalizing the field names and record any divergence in the drift log rather than inventing a competing convention.

A named command that does not exist on disk is itself a finding (`commands/refactor.md → missing`), so the constant cannot silently rot the way `GATE_AGENT_FILES` can.

## Check 4 — `check_required_skills(root)`

Scans `commands/*.md` (frontmatter) and `agents/*.md` (config block) for `required_skills:`, dedupes per file (`system-instructions.md`: *"Duplicates are silently deduplicated"*), and asserts `skills/<name>/SKILL.md` exists.

Existing skills, verified: `code-explanation`, `conventional-commits`, `error-rescue-mapping`, `gbrain-interop`, `safe-refactor-loop`, `tdd-cycle`.

**Declarations today: 0.** Verified across the whole product surface — `commands/new-skill.md` (prose guidance), the three adapters, `system-instructions.md`, and `skills/gbrain-interop/SKILL.md` mention the convention, and `system-instructions.md` labels it *"Status: reserve-only … not adopted by any existing agent or command."* ADR-021 item 3 makes progressive disclosure its first real consumer.

So the check emits nothing today. Business Rule 8's guard:

```python
metrics["required_skills_declarations"] = <count of declared (file, skill) pairs>
```

Without it, a permanently-empty finding list reads as a verified surface. With it, `0` is visibly `0`.

**Pinned non-blocking (Business Rule 6).** `system-instructions.md`: *"Unknown skill names produce a warning at consumer load time, not a hard failure (graceful degradation: a pilot extraction may rename a skill mid-flight; consumers shouldn't break catastrophically)."* Hard-failing `eval.sh` on an unresolved name would contradict the root behavioral contract mid-extraction — during exactly the phase that renames skills most. The `severity="warnings"` override at the call site carries this citation as a comment.

## The silencer fix (Story 1)

### The two properties of `justification` that make it a trap

1. **A non-empty value is a permanent, whole-surface mute.** `justification` is read **once per surface at `scripts/eval-leanness.py:527`, outside** the `for metric_key in ("lines", "chars")` loop, and line 533 is `if current_value <= base_value or justification: continue`. Any non-empty string therefore skips **both** metrics for that surface, on **every** future run, at **any** magnitude. "Up costs a sentence" actually reads: one sentence buys unlimited unmonitored growth on that surface.
2. **The prescribed remediation erases its own record.** Line 540 tells the maintainer to *"add a one-line justification … and rerun `--update-baseline`"*; the reseed block at lines 596-615 writes `"justification": ""` for every surface. The instruction deletes what it just told you to write.

The **reset is not the defect** and is preserved. Its defense (`scripts/eval-leanness.py:590-595`) — a justification describes a specific past delta, and that delta ceases to exist once the baseline absorbs it — is sound, and under a bound justification it is more clearly right: a ceiling at or below the new floor is dead data. The defects are (1) unbounded silence and (2) the self-defeating text.

### Current vs. proposed code shape

Current (`scripts/eval-leanness.py:521-543`, abridged):

```python
for entry in SURFACE_REGISTRY:
    name = entry["name"]
    base_entry = surfaces.get(name)
    ...
    justification = str(base_entry.get("justification") or "").strip()   # ← line 527: per SURFACE
    for metric_key in ("lines", "chars"):
        base_value = base_entry.get(metric_key)
        current_value = current.get(metric_key)
        ...
        if current_value <= base_value or justification:                 # ← line 533: unbounded
            continue
        warnings.append({"subject": name, ...})                          # ← subject is the surface
```

Proposed:

```python
def justified_ceiling(base_entry: dict, metric_key: str) -> tuple[float | None, str, str]:
    """Ceiling, text, and date for ONE (surface, metric) justification.

    Schema 3:  surfaces.<name>.justifications.<metric> =
                   {"value": <number>, "date": "YYYY-MM-DD", "text": "<why>"}
    A justification silences growth only up to `value`. Past it, the ratchet
    speaks again and names the ceiling that was passed.

    Returns (None, "", "") when there is no usable justification: key absent,
    `justifications` not a dict, entry not a dict, `value` non-numeric, or
    `text` blank. The legacy schema-2 string form (`justification: "<why>"`)
    carries no bound, so it returns (None, <its text>, "") — the caller warns
    with a migration hint. An unbounded mute must not survive in old data.
    """

for entry in SURFACE_REGISTRY:
    name = entry["name"]
    base_entry = surfaces.get(name)
    ...
    for metric_key in ("lines", "chars"):
        base_value = base_entry.get(metric_key)
        current_value = current.get(metric_key)
        if not isinstance(base_value, (int, float)) or not isinstance(current_value, (int, float)):
            continue
        if current_value <= base_value:
            continue                                   # down is free — first, and unconditional
        ceiling, text, date = justified_ceiling(base_entry, metric_key)   # ← per METRIC
        if ceiling is not None and current_value <= ceiling:
            continue                                   # covers this increment, and nothing more
        warnings.append({"subject": f"{name}.{metric_key}", ...})
```

Three behavioral differences, each independently testable:

| | Today | After |
|---|---|---|
| Justification scope | one string, whole surface | one record per `(surface, metric)` |
| Silence duration | unbounded, forever | up to `value`, then warns again |
| Finding `subject` | `commands` (identical for both metrics) | `commands.lines` / `commands.chars` |

`current_value <= base_value` is evaluated **before** any justification is consulted, so "down is free" cannot be weakened by any justification state — valid, stale, malformed, or legacy.

### Finding text

Three `what` variants, one `fix`:

```
what (no justification):  commands lines grew from 10974 to 10996 (+22) with no
                          justification recorded for this metric.
what (ceiling passed):    commands lines grew from 10974 to 11050 (+76), past the
                          justified ceiling of 10996 recorded 2026-08-11
                          ("<text>"). That justification covered growth to 10996.
what (legacy string):     surfaces.commands carries a legacy unbounded
                          `justification` (schema 2); it silences nothing. commands
                          lines grew from 10974 to 10996 (+22).
fix:                      Prune the surface back down — the delta is the signal — or
                          record the increment: set
                          surfaces.commands.justifications.lines to
                          {"value": 10996, "date": "YYYY-MM-DD", "text": "<why>"} in
                          .writ/leanness-baseline.json. That silences growth to 10996
                          and nothing beyond it. `--update-baseline` is the other
                          option: it moves EVERY surface's floor to its current
                          measurement and records no reason.
```

The old `fix` at line 540 is deleted. Nothing in the new text prescribes a sequence that erases its own output.

Two other places repeat the old promise and must move with it, or the code will document a behavior it no longer has:

- `check_baseline()`'s docstring summary, `scripts/eval-leanness.py:490-492` — *"current > baseline, justification present -> silent (up costs a sentence)"*.
- The reseed payload's `note`, `scripts/eval-leanness.py:613-614` — *"Any increase to a gated surface requires a justification string in its baseline entry, or it warns."* This string is written into every baseline file, so a stale version of it ships with the data.

### Schema handling

- Writer (`--update-baseline`): `"schema": 3`, `"justifications": {}` per surface, legacy `"justification"` key dropped.
- Reader (`check_baseline()`, `scripts/eval-leanness.py:510`): accept `schema in (2, 3)`. Schema 1, an absent `surfaces` map, and a missing or unreadable baseline stay **structural**, unchanged.
- **Ordering:** the reader change lands before or with the first write of schema 3. Writer-first would make the introducing commit fail `eval.sh` on its own run.

### Test matrix for the bound justification

All rows use one gated surface. `j` denotes `justifications.lines = {"value": V, "date": D, "text": T}`.

| # | Baseline | Justification | Current | Expected |
|---|---|---|---|---|
| 1 | lines 100 | none | 100 | silent (equal is not growth) |
| 2 | lines 100 | none | 90 | silent — down is free |
| 3 | lines 100 | none | 120 | 1 warning, `subject: <surface>.lines`, "no justification recorded" |
| 4 | lines 100 | `j(V=120)` | 120 | **silent** — grow → justify → quiet |
| 5 | lines 100 | `j(V=120)` | 121 | **1 warning** naming the ceiling 120 — grow further → warns again |
| 6 | lines 100 | `j(V=120)` | 100 | silent — the ceiling never re-arms a satisfied floor |
| 7 | lines 100 | `j(V=120)` | 90 | silent — down is free even with a justification present |
| 8 | lines 100, chars 1000 | `j(V=120)` only | lines 120, chars 5000 | **exactly 1 warning, for `chars`** — the regression test for line 527 |
| 9 | lines 100 | legacy `"justification": ""` | 120 | 1 warning — identical to today; the six committed entries are this row |
| 10 | lines 100 | legacy `"justification": "because"` | 1_000_000 | **1 warning** — the direct regression test for the old permanent mute |
| 11 | lines 100 | `j(V="120")` (string) | 120 | 1 warning — a non-numeric ceiling never silences |
| 12 | lines 100 | `j(V=120, T="")` | 120 | 1 warning — a bound with no reason is not a justification |
| 13 | lines 100 | `j(V=90)` (below floor) | 120 | 1 warning — stale ceiling, no crash |
| 14 | lines 100 | `justifications: "yes"` (not a dict) | 120 | 1 warning, no exception |
| 15 | schema 2 file, any of the above | — | — | read normally; **no** structural finding |
| 16 | `--update-baseline` output | — | — | `"schema": 3`, every surface `"justifications": {}`, no `"justification"` key |

Rows 4, 5, 7 are the three properties the maintainer named as the acceptance bar. Row 8 is the per-metric requirement. Row 10 is the defect itself.

## Baseline resolution (Story 2)

### The disposition: justify at a recorded ceiling

Story 2 records a bound justification for each of the four live `(surface, metric)` pairs and changes no baseline number:

```json
"commands": {
  "lines": 10974,
  "chars": 514594,
  "justifications": {
    "lines": {"value": <post-Story-1 measurement>, "date": "2026-08-11",
              "text": "a5c5a66 feat(install): fan out runtime scripts and Writ docs on install/update (PR #34, v0.28.0) — reviewed, shipped feature work."},
    "chars": {"value": <post-Story-1 measurement>, "date": "2026-08-11", "text": "same commit"}
  }
}
```

`scripts` takes the same shape. The other four surfaces get no `justifications` key — they have not drifted. `schema` becomes `3` and all six legacy `"justification": ""` keys are deleted in the same edit.

`--update-baseline` is **not** run: it would move all six floors, record no reason, and wipe the entries being written. Keeping the floor at the last true reseed means the ratchet keeps reporting cumulative drift rather than resetting its memory on every accepted increment.

**The ceilings come from a live run, not from this document.** Story 1 grows `scripts/eval-leanness.py`, so `scripts.lines` and `scripts.chars` will exceed the +122/+2596 quoted below. Those figures are pre-Story-1 evidence of the *cause*; the ceiling is whatever the run reports when the entry is written.

### Why `absorbed` was dropped

The original design paired `--update-baseline` with a top-level `absorbed` array holding `date`, `surfaces`, `delta`, `cause`, `disposition` — a key `check_baseline()` never reads. A bound justification carries the same content (`date`, `value`, `text`) attached to the exact `(surface, metric)` it explains, in a field the checker reads **and enforces**. Shipping both is two records of one fact, one of them inert. `absorbed` also had its own self-erasure flaw: `--update-baseline` rewrites the file wholesale and would drop it — a small echo of the defect Story 1 removes.

What is lost: append-only history across absorptions, since a `justifications` entry is overwritten by the next raise. `git log .writ/leanness-baseline.json` is that history and is strictly better — it carries the diff, the date, and the commit that caused it.

### Attribution evidence

`git log <baseline-commit>..HEAD -- commands scripts` returns exactly one commit, `a5c5a66`:

- `commands/update-writ.md` +31/−9 = **+22 lines** — matches the warning exactly.
- `scripts/install.sh` + `update.sh` + `unlink.sh` +306/−184 = **+122 lines** — matches the warning exactly.

One commit accounts for all four warnings. Pruning would mean reverting released v0.28.0 functionality to satisfy a counter, which is the wrong trade and is named out of scope.

## Metrics additions

```python
metrics["contract_compliance"] = {
    "commands_checked": 31,
    "commands_with_contract": 0,
    "commands_with_completion": 13,
    "loop_commands_checked": 5,
    "loop_commands_bounded": 0,
    "agents_checked": 7,
    "agents_with_contract": 0,
}
metrics["required_skills_declarations"] = 0
```

Counts only. The findings list is the actionable channel; metrics are the trend channel that lets the migration specs and `/status` show progress as one number instead of a 114-line diff. `eval.sh`'s `check_leanness()` renders `metrics` keys it knows about; unknown keys are ignored, so adding these is backward-compatible with the existing TSV bridge.

## Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Read a command's frontmatter | No leading `---` fence; malformed YAML; unreadable file | One finding naming that file (`… → no frontmatter block`); never an exception; script still exits 0 | Fixture command with no fence, with a mid-document `---`, and with an unreadable mode bit |
| Locate an agent's config block | Neither `## Agent Configuration` nor `## Agent Specification`; heading present but no fenced block | One carrier-level finding, not three field findings | Fixture agent with each heading, with a ```yaml fence, and with no block at all |
| Field presence test | `exit_criteria:` present but empty, or `[]`, or followed by nothing | Treated as missing → finding. Presence without content asserts nothing (ADR-020 Consequences) | Fixture with `exit_criteria:` empty, `[]`, and with two indented items |
| `LOOP_BEARING_COMMANDS` resolution | A named command file no longer exists | Finding (`commands/<name>.md → missing`) so the constant cannot rot silently | Fixture tree missing one of the five |
| `required_skills:` resolution | Name resolves to no `skills/<name>/SKILL.md`; duplicate entries | Warning per unresolved `(file, name)` pair, deduped; never blocking, even post-flip | Fixture declaring one real skill, one unknown, and one duplicate |
| Severity flip | Constant set to an unrecognized value (typo in the later spec's diff) | Falls back to `warnings` — a typo must never silently disable a check nor accidentally block CI | Set the constant to `"blocking"` and assert findings land in `warnings`, exit 0 |
| Missing `commands/`, `agents/`, or `skills/` directory | Directory absent (e.g. a partial install fixture) | Zero findings, no exception — matches `surface_files()`'s existing "missing directory yields an empty list" contract | Fixture root with each directory absent in turn |
| Read a bound justification | `justifications` not a dict; entry not a dict; `value` non-numeric; `value` at or below the baseline; `text` blank or absent | No usable ceiling → the growth **warns**; never silences by default, never raises | Matrix rows 11-14 |
| Read a legacy `justification` string | Schema-2 entry with a non-empty string | Carries no bound → silences nothing; warning names the bound replacement in its `fix` | Matrix row 10 |
| Baseline schema version | Writer emits 3 while a reader expects only 2 (`scripts/eval-leanness.py:510` makes that structural) | Reader accepts 2 **and** 3; reader change lands first, so no commit fails its own run. Schema 1 / no `surfaces` stays structural | Matrix rows 15-16, plus the committed schema-2 file run end-to-end |

## Shadow Paths

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| Contract presence | Fixture command with all three fields → 0 findings | `commands/` absent → 0 findings, exit 0 | Frontmatter present, all three fields empty → 3 findings | Malformed fence → 1 file-level finding, no traceback |
| `## Completion` | Compliant command → 0 findings | `commands/` absent → 0 findings | Empty `## Completion` section (heading only) → 0 findings; this check asserts presence, not content | Unreadable file → skipped with the existing `measure_files`-style warning, run continues |
| Loop bounds | All five declare both fields → 0 findings | One of the five absent from disk → `missing` finding | `loop:` key present with no children → 2 findings | Frontmatter unparseable → 1 file-level finding |
| `required_skills:` | Declared name resolves → 0 findings | 0 declarations anywhere → 0 findings **and** `required_skills_declarations: 0` in metrics | `required_skills: []` → 0 findings, counted as 0 pairs | `skills/` absent → every declared name unresolved → warnings, exit 0 |
| Bound justification | Growth to the recorded `value` → 0 warnings | No `justifications` key → growth warns "no justification recorded" | `justifications: {}` → identical to absent; `text: ""` → not a justification, warns | Malformed `value`/`justifications` → warns, no exception; legacy string → warns with migration hint |

## Interaction Edge Cases

| Edge Case | Planned Handling |
|---|---|
| `commands/_preamble.md` | Never checked — `is_infra()`, the existing rule (Business Rule 7). A future `commands/_foo.md` is handled with no second convention. |
| `agents/visual-qa-agent.md` | `## Agent Specification` + ```yaml fence recognized; zero false findings. Regression-tested by name. |
| `## Completion Criteria` / `### Completion` | Do not satisfy Check 2; the finding's `fix` names the exact required spelling so the near-miss is diagnosable. |
| The flip lands while `required_skills:` findings exist | Those stay in `warnings` (pinned override); the other three checks become blocking. Tested together, not separately. |
| A command adds `problem:` but leaves `exit_criteria:` empty | 1 finding, not 3. Per-field granularity means the queue shrinks as the migration progresses — which is what makes it a work queue. |
| Story 2 re-runs after Stories 3–6 land | `warnings` is no longer `[]` (the new checks fill it). Story 2's `warnings == []` assertion is scoped to *growth* warnings — assert on the four `subject` values `commands.lines`, `commands.chars`, `scripts.lines`, `scripts.chars`, not on total length. |
| Two surfaces grow again after Story 2 | Growth past a recorded `value` warns again, naming the ceiling it passed — by design. The disposition is a fresh, dated `justifications` entry, raised by the story that caused the growth (Business Rule 9). |
| Every story from 3 onward edits `scripts/eval-leanness.py` | `scripts` passes Story 2's ceiling mid-spec and re-warns. Each story raises its own ceiling with a dated `text` naming itself. Never batch the raises, never widen the silence. |
| Story 1 lands while the four warnings are still live | Expected. Story 1 clears nothing: the same four `(surface, metric)` pairs warn before and after, with new `subject` values and new text. Assert the pairs and the count of four, not the deltas — Story 1's own edit grows `scripts`. |
| A justification whose `value` sits below the baseline | Possible after any `--update-baseline`. Treated as no usable ceiling → warns. Do not special-case a stale ceiling into silence. |

## Testing Strategy

- **Story 1:** The 16-row matrix above, written first, in `scripts/tests/test_eval_leanness_contract.py` via the same importlib-by-path recipe. Rows 4, 5, and 7 are the acceptance bar (grow → justify → silent; grow further → warns again; down → free); row 8 proves per-metric independence; row 10 is the direct regression test against the old permanent mute. Plus a real run against this repo asserting the same four `(surface, metric)` pairs still warn and `structural` is `[]` with the committed schema-2 baseline.
- **Story 2:** Real run against this repo, not a fixture — `python3 scripts/eval-leanness.py --root . --baseline .writ/leanness-baseline.json` must show no growth entry for `commands.lines`, `commands.chars`, `scripts.lines`, or `scripts.chars`. Plus the armed-ratchet check: decrement one recorded `value` by 1, observe the warning return naming the ceiling, restore it.
- **Stories 3–6:** New `scripts/tests/test_eval_leanness_contract.py`, loading `eval-leanness.py` by path via `importlib.util.spec_from_file_location` — the established recipe in `test_archive_sweep.py`, `test_spec_status.py`, `test_story_deps.py` for hyphenated script filenames. Each check gets a fixture tree (compliant / non-compliant / malformed / absent-directory) and an assertion that findings carry file-and-field `subject` values.
- **Story 7:** The flip test — set `module.CONTRACT_CHECK_SEVERITY = "structural"` in-process, re-run the same fixture, assert the **identical** finding dicts moved from `warnings` to `structural`, that `required_skills:` findings did **not** move, and that an unrecognized severity value falls back to `warnings`. Plus a source-level assertion that no `check_*` function in the contract family appends to `structural`/`warnings` directly. Plus one `eval.sh`-boundary scenario proving a `structural` finding actually FAILs the run.
- **Whole-suite regression:** `bash scripts/tests/test_eval_leanness.sh` and the full `scripts/tests/*.py` pytest suite must stay green. `check_parity`, `check_coverage`, and `check_ceilings` are untouched, so any change there is a regression. `check_baseline` is deliberately changed by Story 1; any existing assertion that pins the old `subject` (`commands`, not `commands.lines`) or the old unbounded-mute behavior is updated **in Story 1, with the reason recorded** — never quietly relaxed.

## Non-Goals (restated from spec.md → Out of Scope)

No change to `eval.sh`'s `check_length` limits (the 2000-line command cap stays). No absolute `per_surface.commands.chars` cap. No flip of `CONTRACT_CHECK_SEVERITY` to `"structural"`. No migration of any command or agent into compliance — this spec emits ~142 findings and fixes none of them. No `status:`/`evidence:` extension to commands and agents. No change to `check_parity`, `check_coverage`, or `check_ceilings`. No pruning of `commands/update-writ.md`, `install.sh`, `update.sh`, or `unlink.sh`.

Story 1's change to `check_baseline()` is bounded to the justification semantics, the finding text, the `subject` granularity, and the schema version handling. It does **not** turn any growth warning into a `structural` finding, does not add an absolute ceiling, and does not touch "down is free" — those all remain the later `governor-enforcement` spec's territory or unchanged behavior.

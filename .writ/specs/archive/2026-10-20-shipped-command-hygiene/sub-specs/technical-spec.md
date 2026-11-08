# Technical Spec: Shipped Command Hygiene

> Spec: [`../spec.md`](../spec.md)
> Inventory snapshot: commit `8528726` on `phase/13-subtract-and-repair`, 2026-10-20, before `2026-10-20-harness-cuts` and `2026-10-20-platform-neutral-names` land. Both change command text and pins. Every story re-inventories at implementation time; the counts below set the order of magnitude, not the target.

## Current State

### Internal references in shipped commands

The contract grep (`grep -n -E '\.writ/(specs/archive|research)/|decision-records/adr-|calibrated_against'` over `commands/*.md`, excluding `*.lean.md`) returns 39 lines in 16 files. 18 of them are internal references. 21 are runtime paths or `calibrated_against` values that cite only shipped files, and stay. One more internal reference (`revert.md:178`) names an archived spec by its old, pre-archive path, so the grep misses it.

**Remove or rewrite (19 lines, 12 files):**

| File:line | Kind | Reference | Action |
|---|---|---|---|
| `create-spec.md:74` | ADR link | `(see [ADR-013](../.writ/decision-records/adr-013-…))` | Delete the parenthetical. The bullets below it carry the rule. |
| `implement-phase.md:16` | calibration state | `calibrated_against` cites `.writ/state/phase-execution-20260719-121255.json`, `…-20260811-2030.json`, Writ's roadmap phases | Rewrite (see below) |
| `implement-phase.md:55` | ADR link | `(see [ADR-013](…))` | Delete the parenthetical |
| `implement-phase.md:280` | archived spec | `spec.md § [On Design Principle 4](../.writ/specs/archive/2026-08-12-machine-evaluable-exit-criteria/spec.md#…)` | Replace with one sentence (see below) |
| `implement-spec.md:15` | calibration state | "41 archived specs under .writ/specs/archive/", `.writ/state/execution-20260718-1101.json`, … | Rewrite |
| `implement-story.md:15` | calibration state | "42 'Iteration count' records … in .writ/specs/archive/" | Rewrite |
| `implement-story.md:20` | calibration state | "No recorded run in .writ/specs/archive/ …" | Rewrite |
| `new-command.md:167` | ADR link | `See [ADR-024](…) and [.writ/docs/model-tiers.md](…)` | Keep the `model-tiers.md` link, drop the ADR |
| `new-skill.md:19` | ADR link | `the boundary [ADR-009](…) draws between commands, agents, and skills` | "the boundary between commands, agents, and skills" |
| `new-skill.md:242` | ADR link | `(per [ADR-009](…))` | Delete the parenthetical |
| `new-skill.md:283` | ADR link | References row `Boundary rationale: [ADR-009]` | Delete the row |
| `new-skill.md:284` | ADR link | References row `Lifecycle rationale: [ADR-014]` | Delete the row |
| `refactor.md:15` | calibration state | "zero /refactor executions exist anywhere in .writ/state/" | Rewrite; keep the literal `no recorded run` |
| `refresh-command.md:229` | research | `.writ/research/2026-04-24-writ-vs-gstack-rigor-comparison.md` | Keep the cost reason as plain text (see below) |
| `refresh-command.md:321` | ADR link | `the role convention from [ADR-009](…)` | "the role convention" |
| `release.md:455` | ADR link | `rationale: [ADR-017](…)` | Delete; keep the `git-notes-audit-format.md` link |
| `retro.md:204` | ADR link | References row `Friction signals: [ADR-025]` | Delete the row (ADR-025 is retired; `2026-10-20-harness-cuts` may already have removed it) |
| `revert.md:178` | archived spec (old path) | `· Technical spec: .writ/specs/2026-07-18-logical-unit-revert/sub-specs/technical-spec.md` | Delete the clause; keep the resolver path |
| `ship.md:411` | ADR link | `and [ADR-017](…)` | Delete; keep the `git-notes-audit-format.md` link |

Remove a link together with its `ADR-NNN` label. Do not leave a bare label where the link was.

**Stay (21 lines):**

- Runtime directories and placeholders: `create-adr.md:42,47,153`; `create-spec.md:401`; `implement-spec.md:53`; `migrate.md:26`; `research.md:5,8,130,175,182`; `status.md:268,278,483`; `release.md:170`; `verify-spec.md:47,639,676` (`.writ/decision-records/adr-*.md` and `adr-{NN}-*.md` are globs over the user's own ADRs).
- `calibrated_against` values that cite only shipped files: `implement-phase.md:21` (`scripts/phase-state.py`), `implement-story.md:24` (`agents/coding-agent.md`, `agents/testing-agent.md`), `verify-spec.md:15` (`commands/verify-spec.md`).

**Out of scope, reported:** 23 lines in 10 commands name a Writ ADR as a bare label without a link (for example `(ADR-013)` in `_preamble.md`, `(ADR-014)` in `new-skill.md`, `Design principle (ADR-001)` in `create-spec.md`, `new-command.md`, and `plan-product.md`). `plan-product.md`'s `ADR-000-…` names are the user's own ADR files and are not counted. Some example blocks name real Writ specs (`status.md:273-274`, `create-spec.md:583,600`, a comment at `release.md:365`). None is a link, so this spec leaves them. `create-spec.md`'s instances fall to Story 3 only when the cut removes coaching anyway.

### Literal pins on command files

`scripts/eval.sh` at `8528726`: 221 pin instances that resolve to a file under `commands/`, at 206 call sites, in 30 check functions. 197 are `require_literal`, 22 `forbid_literal`, 2 `forbid_literal_ci`. A loop over several files counts once per file. 8 instances target `.lean.md` files, and 6 of the 9 `check_model_escalation` pins guard the ADR-025 no-op line and its "no sink" sentence. `2026-10-20-harness-cuts` deletes both groups (its technical spec lists the six) and also lowers create-spec's recorded overage, so expect about 207 pins at Story 2 start.

The phase decomposition estimated about 114. The recipe below counts 221, and a reviewer can re-run it.

| Check function | Pins | Targets | Guidance (pin-map.md decides per row) |
|---|---|---|---|
| `check_recommended_spec_implementation` | 13 | `_preamble`, `create-spec` | `--recommend` boundary → keep. The two `###` headings may convert. |
| `check_recommended_staging` | 1 | `implement-spec` | `npm publish` forbid is the production boundary → keep |
| `check_spec_dependencies` | 10 | `create-spec`, `verify-spec`, `implement-phase` | `> **Dependencies:**` is a format `spec-deps.py` parses → keep. "stop before the confirmation gate" → keep. Words that describe what `spec-deps.py` computes (`topological`, `roadmap order`, `self-reference`) → remove candidates. |
| `check_spec_status` | 5 | `create-spec`, `status` | `spec-status.py` → convert. The two forbids block a known-broken substring check → keep unless the row names what else catches it. |
| `check_archive_sweep` | 6 | `status`, `create-spec`, `implement-spec` | `archive-sweep.py` → convert. "never as a side effect" → keep. Three `grep -v archive` forbids → remove candidates. |
| `check_spec_lifecycle_docs` | 2 | `verify-spec` | `specs/**` forbid keeps archive out of `--all` → keep. Doc-link pin → remove candidate. |
| `check_supersession_writeback` | 3 | `create-spec`, `edit-spec` | Two invocations → convert. `Amends` (parsed field) → keep. |
| `check_archive_dogfood` | 1 | `implement-spec` | Spec selection requires `spec.md` → keep |
| `check_post_merge_archival` | 8 | `release` | Two invocations → convert. Best-effort guard, immediate commit → keep. Three "row must remain verbatim" pins → remove candidates. |
| `check_roadmap_sync` | 4 | `release` | Two invocations → convert. "never touches mission.md", "never fails the release" → keep. |
| `check_story_deps` | 5 | `implement-spec` | Invocation → convert. Blocking and stop rules → keep. |
| `check_story_context` | 8 | `implement-story` | Invocation → convert. Two forbids of retired prose → remove candidates. Five routing-table rows → keep or convert. |
| `check_model_escalation` | 9 | `create-spec`, `implement-story` | Whatever harness-cuts leaves. Iteration-accounting sentences are loop bounds → keep. |
| `check_phase_lanes` | 8 | `implement-phase`, `implement-spec` | Lane and merge rules → keep. `scripts/phase-state.py` → convert. |
| `check_phase_challenges` | 8 | `_preamble`, `implement-phase`, `implement-spec` | User Challenge is Prime Directive → keep. `## User Challenge` may convert. |
| `check_phase_quarantine` | 7 | `implement-phase`, `implement-spec`, `status` | Retry and quarantine rules → keep |
| `check_phase_knowledge` | 4 | `implement-phase`, `knowledge` | Heading → convert. `substantive` → remove candidate. |
| `check_phase_health` | 3 | `implement-phase`, `status` | `read-only` → keep |
| `check_phase_closure` | 4 | `implement-phase`, `status` | State names → keep |
| `check_ralph_retirement` | 2 | `status`, `implement-phase` | Retired-name forbids → remove candidates (the loop's other 13 surfaces are not command files) |
| `check_refresh_evidence` | 9 | `refresh-command` | Transcript privacy → keep. `eval.sh --check=refresh-evidence` → convert. Example and design-note pins → remove candidates. |
| `check_knowledge_consolidate` | 7 | `knowledge`, `retro` | Approval, no-commit, read-only → keep. Retro nudge wording → remove candidate. |
| `check_git_notes_audit` | 9 | `ship`, `release`, `status` | Notes ref, opt-out, fetch/merge/push (data loss) → keep. `Last audit note:` label → remove candidate. |
| `check_artifact_integrity` | 13 | `_preamble` + 7 commands | Headings (`## Artifact Integrity`, 7× `## Required Artifacts`) → convert. `## Artifact Map` in `implement-story.md` is inline text naming a section of the regenerated `context.md`, not a heading there → stays literal. HALT, bounded repair → keep. |
| `check_revert` | 18 | `revert`, `refactor`, `implement-story` | Destructive gate class → keep. `#### Step 1.1b: Dirty-Tree Guard` → convert. |
| `check_exit_criteria` | 7 | `implement-phase`, `implement-spec` | Binds `exit-criteria.py` predicates to criterion text (verdict provenance) → keep |
| `check_ac_trace` | 16 | `verify-spec` | Invocation → convert. Report-only and auto-fix boundary → keep. Finding codes → keep. Eight-row-table pins → remove candidates. |
| `check_quality_config_audit` | 10 | `initialize`, `status` | Invocations → convert. Re-baseline and confirmation rules → keep. `/status` no-build forbids → keep. Display-line pins → remove candidates. |
| `check_review_panel` | 8 (4 after harness-cuts) | `implement-story` | Panel block is a Gate 3 FAIL → keep. Report-line naming → remove candidate. |
| `check_product_check_direction` | 13 (9 after harness-cuts) | `verify-spec`, `plan-product`, `implement-phase`, `release` | Wording of a product-flow decision, no safety category → remove candidates. `test_product_check_direction.py` mutates these pins and must change with them. |

The guidance suggests that tens of pins leave, not single digits. There is no numeric target; the success criterion is "lower".

### Create-spec size

- 54,264 bytes on the snapshot. `COMMAND_BYTE_BUDGET` is 24,960 (`scripts/eval-leanness.py`). `KNOWN_OVER_BUDGET["commands/create-spec.md"]` in `scripts/tests/test_governor_enforcement.py` is 29,304, set by PR #59 for the `--from-prototype` source matrix. No other file records a create-spec size; `.writ/leanness-baseline.json` ratchets totals and a shrink is free there.
- `test_the_byte_cap_is_the_half_that_does_not_comply_and_is_not_blocking` asserts `total_overage == sum(KNOWN_OVER_BUDGET.values())`, so the repin must equal the new overage exactly.
- The lean twin at `617037b` is 37,293 bytes. Part of its saving removes behavior (the Jev sub-steps and the `jev:` note), which this spec does not adopt.
- The flagged-harness-cuts null result (`.writ/decision-log.md`, 2026-09-25) ran `/implement-story` on one story, two runs per arm. `/create-spec` was not invoked, so the 2/2 exit-criteria result is no evidence about `create-spec.lean.md`'s cuts. Story 3 therefore judges every cut by its class (coaching or constraint), not by that run.

## Story 1: Shipped-Refs Check

### Rules

`scripts/eval-shipped-refs.py` scans every `commands/*.md` except `*.lean.md` (which never ships). Each line is matched against four rules:

| Kind | Pattern | Fires on | Does not fire on |
|---|---|---|---|
| `archived-spec` | `\.writ/specs/archive/\d{4}-\d{2}-\d{2}-[\w.-]+`, or `\.writ/specs/(\d{4}-\d{2}-\d{2}-[\w-]+)` when `<root>/.writ/specs/archive/<that name>/` exists | `implement-phase.md:280`, `revert.md:178` | `.writ/specs/archive/<name>/`, `.writ/specs/archive/LEDGER.md`, `.writ/specs/archive/**`, example IDs such as `2026-03-15-auth-system` |
| `research` | `\.writ/research/\d{4}-\d{2}-\d{2}-[\w.-]+` | `refresh-command.md:229` | `.writ/research/`, `.writ/research/[DATE]-[topic-name]-research.md`, `<YYYY-MM-DD>` |
| `adr` | `decision-records/adr-\d{3}-[\w.-]+` (any prefix: `../.writ/`, `../../`, `.writ/`) | the 11 ADR links above | `.writ/decision-records/adr-*.md`, `adr-{NN}-*.md`, `ADR-000-[product-posture].md` |
| `calibration-state` | on a line starting `calibrated_against:`, any `\.writ/state(/…)?` or `\.writ/specs/archive(/…)?` token that contains no `*` | the 5 values above | `.writ/state/phase-execution-*.json`, `commands/…`, `scripts/…`, `agents/…` |

A prototype of these rules against the snapshot flags exactly the 19 lines in the table above and none of the 21 that stay.

### Output and wiring

- CLI: `python3 scripts/eval-shipped-refs.py [--root DIR]`. Default root is the repo. Python 3.9, standard library only. Dev-only: `is_shippable_script` already excludes `eval*`.
- Output: PASS/FAIL TSV, one line per scenario, the same shape as the other `eval-*.py` emitters. First, one self-test scenario per rule against synthetic lines (positive and negative), so a regex that silently matches nothing fails the check instead of passing it. Then one `FAIL\tshipped-refs:<file>:<line>\t<kind>: <token>` line per hit on the tree, or one `PASS\tshipped-refs-tree` line when there are none.
- `check_shipped_refs` in `scripts/eval.sh`: missing helper → `RUN_ERRORS` plus a finding (the `check_leanness` pattern). FAIL lines → `add_finding` with the remediation "Remove the link to Writ's development history. If an installed user needs the reason, state it in one plain sentence." PASS lines → scenario counts. Register `shipped-refs` in `CHECKS` after `referenced-paths`.
- Scope is `commands/` only. Keep the scanned directories in one constant so the later `agents/`, `adapters/`, `skills/`, `.writ/docs/` pass widens it in one place.

### Replacement sentences

Only three removals carry a reason an installed user needs:

- `implement-phase.md:280`: "This check does not use a harness `/goal` Stop hook. That hook exists on one platform and asks a model to judge a prose condition; `exit-criteria.py` evaluates predicates over files on disk."
- `refresh-command.md:227-229`: "The LLM-judge variant stays deferred behind an explicit future decision: measured at about $0.15 and 30 seconds per run, it costs more than it is worth at current scale." Keep "Tier 2 is structural only — not an LLM-as-judge." unchanged; `check_refresh_evidence` pins it.
- `new-skill.md:19`: no sentence needed. The Overview already states the boundary (commands are verbs, agents are nouns, skills are tools).

### Calibration value rewrites

`eval-loop-bounds.py` requires the key in every `loop:` entry (assertion 1) and requires its value to carry a path token (`.writ/`, `commands/`, `agents/`, `scripts/`, `skills/`, `adapters/`) or the literal `no recorded run` (assertion 4). It also requires `refactor.md`'s value to contain `no recorded run`. No assertion reads anything else in the value, so the rewrite changes no other check. Proposed values (the implementer may tighten wording; each must keep a shipped path token or `no recorded run` and name no Writ-only path):

- `implement-phase` (`spec`, 12): "Counts distinct specs within one phase; the counter resets at each phase boundary under --all, and a transient retry does not increment it. Set from Writ's own phase runs before release: the largest phase had 5 specs, and 12 is 2.4 times that. Recalibrate against this project's .writ/state/phase-execution-*.json records once they exist."
- `implement-spec` (`story`, 12): "Counts stories dispatched to /implement-story, not the human-selected retry offered on story failure, which stays unbounded because a user's choices are not this bound's business. Set from Writ's own specs before release: the largest had 9 stories, and the bound is that plus 3. Recalibrate against this project's .writ/state/execution-*.json records."
- `implement-story` (`review_cycle`, 3): "One shared counter across four increment sites - Gate 3 FAIL, Gate 3.5 Reject, Gate 3.5 Modify spec, Gate 4.5 script fail - not four separate budgets. Transcribes the prose cap in commands/implement-story.md: 'Review loop: Max 3 iterations across review and Gate 4.5'. In Writ's own story runs before release no story needed more than 2; 3 leaves one iteration of headroom."
- `implement-story` (`testing_cycle`, 2): "Transcribes the Gate 4 prose cap in commands/implement-story.md: '2 fix iterations max (separate from the review loop's 3-iteration cap)'. Writ's own story runs before release never needed a second testing fix. The original derivation of the 2 is not recorded, so do not read it as measured."
- `refactor` (`change`, 10): "no recorded run - Writ had no recorded /refactor execution when this bound was set. Anchor: the Phase 2 advisory in commands/refactor.md recommends splitting plans of 7+ changes into sessions; 10 sits above it so the bound never fires before that advice. This is a runaway guard, not a plan-size policy. Recalibrate against the first recorded run."

Read each unit name from the file before editing; the names above are from the snapshot.

## Story 2: Pin Map and Conversions

### Pin inventory recipe

Run from the repo root as `python3 <recipe>.py scripts/eval.sh`. It prints one TSV row per command-file pin instance (`function, line, kind, target, literal`). On stderr it names unresolved targets and prints the number of pin call lines it parsed. On the snapshot: 221 rows at 206 distinct lines, 579 call lines parsed, and 22 unresolved targets, all spec files read through `resolve_spec_path`. Save it in a scratch location; it is a verification aid, not a shipped or committed tool. Tested on Python 3.9.

```python
"""List every eval.sh literal pin whose target resolves to a commands/ file."""
import re, shlex, sys
raw = open(sys.argv[1] if len(sys.argv) > 1 else "scripts/eval.sh").read().splitlines()
lines, buf, start = [], "", 0
for n, part in enumerate(raw, 1):                      # join "\" continuations
    start = start or n
    if part.endswith("\\"):
        buf += part[:-1] + " "; continue
    lines.append((start, buf + part)); buf, start = "", 0
FUNC = re.compile(r"^([a-z_]+)\(\)\s*\{")
ASSIGN = re.compile(r'^\s*(?:local\s+)?(\w+)="\$PROJECT_ROOT/([^"]+)"')
FOR = re.compile(r"^\s*for\s+(\w+)\s+in\s+(.*?);\s*do")
PIN = re.compile(r'^\s*(require_literal|forbid_literal_ci|forbid_literal)\s+'
                 r'"(?:\$PROJECT_ROOT/([^"]+)|\$\{?(\w+)\}?)"\s+(.*)$')
func, paths, loops, calls = None, {}, {}, 0
def expand(rel):                                       # commands/$cmd.md -> one per loop word
    m = re.search(r"\$\{?(\w+)\}?", rel)
    return [rel.replace(m.group(0), w[1:]) for w in loops.get(m.group(1), [])] if m else [rel]
for n, line in lines:
    if FUNC.match(line):
        func, paths, loops = FUNC.match(line).group(1), {}, {}
    if ASSIGN.match(line):
        var, rel = ASSIGN.match(line).groups(); paths[var] = rel
    m = FOR.match(line)
    if m:
        refs = re.findall(r'"\$PROJECT_ROOT/([^"]+)"|"\$\{?(\w+)\}?"', m.group(2))
        loops[m.group(1)] = ([a or paths.get(b, "?") for a, b in refs] if refs
                             else ["@" + w for w in m.group(2).split()])
    m = PIN.match(line)
    if not m:
        continue
    calls += 1
    kind, inline, var, rest = m.groups()
    if inline:
        targets = expand(inline)
    elif var in paths:
        targets = expand(paths[var])
    else:
        targets = loops.get(var, ["?" + var])
    literal = shlex.split(rest)[0]
    if any(t.startswith("?") for t in targets):         # resolve these by hand
        print(f"unresolved\t{func}\t{n}\t{var}", file=sys.stderr)
    for t in targets:
        if t.startswith("commands/"):
            print(f"{func}\t{n}\t{kind}\t{t}\t{literal}")
print(f"parsed {calls} pin call lines", file=sys.stderr)
```

Cross-check before writing rows: the parsed count on stderr must equal `grep -c -E '^\s*(require_literal|forbid_literal|forbid_literal_ci) ' scripts/eval.sh` (579 on the snapshot). A gap means a call form the recipe does not parse. Every unresolved target must be checked by hand; if one resolves to a command file, add its rows.

### Pin map format

```markdown
# Pin Map: Command-File Literal Pins in scripts/eval.sh

> Inventory commit: <sha> · Recipe: sub-specs/technical-spec.md → Pin inventory recipe
> Before: <N> instances at <M> call sites · After: <N'> instances at <M'> call sites
> Dispositions: keep <k> · convert <c> · remove <r>

| # | Check function | Line | Target | Kind | Literal | Category | Disposition | Reason |
|---|---|---|---|---|---|---|---|---|
| 1 | check_revert | 3246 | commands/revert.md | require | second destructive confirmation | gate-class | keep | Hard reset needs a second confirmation (destructive class) |
```

- One row per instance. A loop over seven files is seven rows.
- `Line` is the eval.sh line at the inventory commit.
- `Literal` is the first argument as written; a variable (`$direction`) is shown with its value in the reason.
- `Reason` is one line a reviewer can check against the command file. For convert rows it names the structural check row that replaces the pin. For remove rows it says why no behavior depends on the wording.
- After the change, the header records the after count and `k + c + r = N`.

### Categories and disposition rules

| Category | Meaning | Allowed dispositions |
|---|---|---|
| `prime-directive` | Anti-sycophancy, User Challenge, transcript privacy | keep, convert |
| `recommend-boundary` | `--recommend` scope and stop rules; no autonomous merge, PR, release, tag, or publish | keep, convert |
| `gate-class` | A human or blocking gate (ADR-022 classes: contract lock, production boundary, design judgment, destructive precondition); approval before a write; read-only guarantees | keep, convert |
| `loop-bound` | Iteration and retry limits and their accounting | keep, convert |
| `script-invocation` | A script call the command must make | keep, convert |
| `verdict-provenance` | Which instrument decides a verdict; report-only and auto-fix boundaries; finding codes a command routes | keep, convert |
| `parsed-format` | A line format a shipped script parses (`> **Dependencies:**`, `> **Commit:**`, `Amends`) | keep, convert |
| `structure` | A heading, table row, or frontmatter key with no safety role | keep, convert, remove |
| `wording` | Prose whose wording can change without changing what the agent does | keep, remove |
| `retired-text` | A forbid that keeps removed text from returning | keep, remove |

The first seven categories never take `remove`. When a row could fit two categories, use the stricter one. A forbid that blocks a known-broken instruction (for example `grep -q "Status: Complete"`) is `verdict-provenance` or `gate-class` when the broken instruction would change a verdict or a gate, and `retired-text` only when it would not.

When a check function loses all of its command-file pins and runs nothing else, delete the function and its `CHECKS` entry in the same commit. A function that also runs scenarios keeps running them.

### Structural checks

Convert rows move into one table-driven helper, `scripts/eval-command-structure.py`, run by a new `check_command_structure` (`command-structure` in `CHECKS`). Each row has `file`, `kind`, `value`, `was` (the original check function), and `message`. Kinds:

| Kind | Passes when |
|---|---|
| `heading` | A line outside fenced code is a heading (`^#{1,6} `) whose text begins with `<value>` (so `User Challenge` matches `## User Challenge (Scope-Degradation Escalation)`) |
| `frontmatter` | The YAML frontmatter block has a top-level `<value>:` key |
| `invocation` | A line contains the script path followed by whitespace and a subcommand or flag (`scripts/ac-trace.py check …`), with or without a leading `python3`/`bash`. `<value>` is the path plus any subcommand the command must use. A bare `ac-trace.py` or `scripts/ac-trace.py` with nothing after it does not pass. |

A heading row fails when the heading text survives only as prose, which a substring pin would accept. An invocation row fails when the script name survives only as a mention. That is the gain over the literal pin. Same TSV output and `--root` flag as `eval-shipped-refs.py`, so tests run it against temp trees. Python 3.9, standard library, dev-only.

Do not move a pin whose literal is a whole sentence or a table row into `heading`. Those stay literal (keep) or are removed.

### Tests that exercise pins

- `scripts/tests/test_product_check_direction.py` and `scripts/tests/test_review_panel.py` run `eval.sh --check=<name>` against mutated copies. A removed or converted pin in those functions needs its mutation case changed in the same commit.
- Other tests assert command text directly (for example `test_jev_setup_hooks.sh`, `test_spec_analyze_command_hooks.sh`, `test_product_check_direction.py`). They are not eval.sh pins and stay out of the pin map. Removing an eval.sh pin never deletes such a test.

## Story 3: Create-Spec Reduction

### Candidate cuts from the lean twin

Recover the twin with `git show 617037b:commands/create-spec.lean.md` and diff it against the current `create-spec.md`. Re-check every row against the post-dependency file.

| Section | Lean-twin change | Decision | Reason |
|---|---|---|---|
| Overview | One sentence instead of two | Adopt | Same rule, less framing |
| `--from-prototype` intro, Step 0 list, Step 1 framing, Step 3 "Why" | Merged into shorter paragraphs | Adopt | Rationale and repeated framing; the source matrix and "never mark Story 1 complete on an exploration record alone" stay |
| `--from-issue` field list, anchor questions | One line each | Adopt | Same fields and topics |
| Step 1.0 comment, follow-up sentence | Trimmed | Adopt | Coaching |
| Step 1.1 bullets, `codebase_search` | One sentence | Adopt | How-to coaching |
| Step 1.2 Plan Mode benefits, `Design principle (ADR-001)` quote | Removed; "run discovery in Plan Mode; the user controls when to switch" moves into Step 1.3 | Adopt | Rationale and an internal label. Keep the heading number gap; do not renumber. |
| Step 1.3 Internal Process bullets | Folded into the four gap lists | Adopt | Duplicate framing |
| Topic Areas to Explore (27 questions) | Removed; "experience first, then rules, then technical constraints" kept | Adopt | Interview coaching; the gap lists name the same areas |
| Critical Analysis bullets | One paragraph, every trigger kept | Adopt | Format only |
| Pushback Phrasing Examples | Removed | Adopt | Phrasing coaching; the Prime Directive in `system-instructions.md` sets the rule |
| Transition to Contract phrases | Removed; "present the contract in Plan Mode and leave room for questions" kept | Adopt | Phrasing coaching |
| Step 1.3b list | Compressed, every rule kept | Adopt | Format only |
| Step 1.4 intro, example business rule 3 | Removed | Adopt | Example padding |
| Step 1.4b, 1.5 "Handling responses" labels, "with vision model" | Trimmed | Adopt | Coaching |
| Step 2.1 Initialize Tracking | Removed | Adopt | Tells the agent to use its task tool; no output depends on it |
| Step 2.2 date and owner lines | Compressed | Adopt | Format only |
| Step 2.4 frontmatter intro "any relevant phase/source metadata" | Dropped by the twin | Decline | It tells authors to add phase and origin lines, which specs rely on |
| Step 2.4 bullets, "per Business Rule 8", supersession example | Compressed | Adopt | Keep "Canonical complete-family spelling" and every rule |
| Step 2.4b two paragraphs, `2026-07-26-leanness-instrumentation` example | One paragraph | Adopt | Keep "never blocks or fails spec package creation" |
| spec-lite template placeholder bullets | Fewer placeholders | Adopt | Sections and the <100-line limit unchanged |
| "ID tags come later", Content Selection Guidelines, Line Budget Enforcement, Backward Compatibility | One sentence or paragraph each | Adopt | Keep the hard <100-line limit and the 35/35/30 targets |
| Step 2.5 numbered list | One sentence | Adopt | Format only |
| Step 2.6 "Context hint generation (new)" and "Timing note" | Merged (they say the same thing twice) | Adopt | Duplication |
| Step 2.6a item 1 rationale, "exactly as today" | Compressed | Adopt | Keep the `--repo` reason |
| Step 2.6a iteration sentence | Twin rewrites "— there is no second regeneration" as "; there is no second regeneration" | Decline | `check_model_escalation` pins the sentence; it is a loop bound |
| Step 2.6b "Why this step exists" | Removed | Adopt | Rationale |
| Step 2.6c "Goal Card Stage 3 said…" | Removed | Adopt | Writ's own history |
| Step 2.6c Jev first, Jev setup, item 3 exception clause | Removed by the twin | Decline | Behavior; `test_jev_setup_hooks.sh` and `test_spec_analyze_command_hooks.sh` pin it |
| Step 2.6c item 1 | One paragraph, all three "Do not" rules kept | Adopt | Format only |
| Step 2.8 failure-mapping rationale | Compressed | Adopt | Keep "`Read skills/error-rescue-mapping/SKILL.md`" and the data-flow heuristic |
| Step 2.9 `jev:` note line | Removed by the twin | Decline | Behavior |
| Example Usage (blockchain chat) | Removed | Adopt | Coaching; about 3.4 KB |
| Lean "Production boundary" line | Added by the twin | Decline | An addition, not a cut |
| References to `_preamble.lean.md` | Twin-only | Decline | The lean preamble is deleted |

The adopted rows remove roughly 8 to 12 KB of coaching on the snapshot. That is an expectation, not a target (ADR-023).

### What the cuts must not touch

- The frontmatter, including the three `exit_criteria` lines.
- Every text a Story 2 `keep` row or a `command-structure` row requires.
- Every text a test asserts: `scripts/tests/test_jev_setup_hooks.sh` and `scripts/tests/test_spec_analyze_command_hooks.sh` (Step 2.6c, Step 2.9).
- Every AskQuestion block (feature selection, contract decision, visual references, Jev provider).
- Every script invocation, the `--recommend` section and invocation matrix, and the Completion section.
- Step numbers. Other files cite `Step 2.6a`, `2.6b`, `2.6c`.

### Cut log format

```markdown
# Cut Log: create-spec.md Reduction

> Start: <sha>, <bytes> bytes, overage <o> · End: <bytes'> bytes, overage <o'>

| # | Section | Change | Class | Reason |
|---|---|---|---|---|
| 1 | Example Usage | Removed | coaching | A worked dialogue; no step reads it |
```

Every hunk of `git diff <start> -- commands/create-spec.md` maps to a row. `Class` is `coaching` for every adopted row. No reason cites bytes.

### Repin

In `scripts/tests/test_governor_enforcement.py`, set `KNOWN_OVER_BUDGET["commands/create-spec.md"]` to the measured overage (`wc -c` minus 24,960) and add a dated comment above it: what was cut and that each cut removed coaching. The new value must be below its value at Story 3 start and below 29,304. Write the guard first: a test that fails while the recorded value is not below 29,304.

## Error & Rescue Map

| Operation | Failure | Detection | Rescue | What the maintainer sees |
|---|---|---|---|---|
| Run `shipped-refs` | Helper missing | `check_shipped_refs` file test | `RUN_ERRORS` + finding | `scripts/eval-shipped-refs.py: helper is missing` and eval exit 2 |
| Run `shipped-refs` | A rule regex broken so it matches nothing | Self-test scenario fails | Fix the regex | `FAIL shipped-refs-rule-<kind>` with the synthetic line |
| Run `shipped-refs` | Runtime path flagged | Negative fixtures in tests and self-test | Narrow the pattern | `FAIL` naming the runtime path |
| Strip a link | A bare `ADR-NNN` label left behind | Review against the table | Delete the label too | Diff shows the label |
| Rewrite `calibrated_against` | No path token and no `no recorded run` | `loop-bounds` assertion 4 | Add a shipped path token | `loop-bounds:<command> … cites no path` |
| Rewrite refactor's value | Literal `no recorded run` dropped | `refactor-no-recorded-run-literal` scenario | Restore the literal | That scenario fails |
| Inventory pins | Recipe misses a pin form | Count cross-check | Add rows by hand | Count mismatch |
| Remove a pin | A test mutates that pin | That test fails (exit 0 where it expects 1) | Change the test in the same commit | Pytest failure naming the mutation |
| Convert a pin | Structural row passes vacuously | Mutation test | Fix the row or the matcher | Test failure naming the row |
| Mark a safety row `remove` | Rubric violation | Review of `pin-map.md`; Story 2 verification task | Change to keep or convert | Row listed in the verification output |
| Cut `create-spec.md` | Pinned or tested text removed | eval keep row or bash test fails | Restore the text | Finding naming the literal |
| Repin | Value not exact | `total_overage` assertion | Re-measure | Assertion shows both numbers |
| Repin | Value not lower | Guard test | More cuts or none; never raise | Guard test failure |
| Start before dependencies land | `commands/*.lean.md` still present | Story 2 task 2.2 check | Stop and report | Lean files listed |

## Files in Scope

| File | Story | Change |
|---|---|---|
| `scripts/eval-shipped-refs.py` | 1 | New |
| `scripts/tests/test_eval_shipped_refs.py` | 1 | New |
| `scripts/eval.sh` | 1, 2 | `check_shipped_refs`; pin removals; `check_command_structure` |
| `commands/create-spec.md`, `implement-phase.md`, `implement-spec.md`, `implement-story.md`, `new-command.md`, `new-skill.md`, `refactor.md`, `refresh-command.md`, `release.md`, `retro.md`, `revert.md`, `ship.md` | 1 | Reference removals and `calibrated_against` rewrites |
| `.writ/specs/2026-10-20-shipped-command-hygiene/pin-map.md` | 2 | New |
| `scripts/eval-command-structure.py` | 2 | New |
| `scripts/tests/test_eval_command_structure.py` | 2 | New |
| `scripts/tests/test_product_check_direction.py`, `scripts/tests/test_review_panel.py`, others found | 2 | Mutation cases for removed or converted pins |
| `commands/create-spec.md` | 3 | Reduction |
| `.writ/specs/2026-10-20-shipped-command-hygiene/cut-log.md` | 3 | New |
| `scripts/tests/test_governor_enforcement.py` | 3 | Repin and guard |

# Technical Spec: Progressive Disclosure — `/ship`

> Source: `.writ/specs/2026-08-12-disclosure-ship/spec.md`

## Measured Baseline (verified against the working tree, 2026-08-12)

Re-measured with `scripts/measure-invocation.py` **after** its `e8f2a09` fix, which corrected two defects: `required_skills:` was treated as conditional when it is eager, and inline `Read skills/…` lines were ignored entirely. The earlier figures in this package (`conditional_bytes: 0`, ceiling 53,331) came from the broken tool; the adjusted 63,316 this spec computed by hand is now what the tool prints.

```
$ python3 scripts/measure-invocation.py --root . --command ship
  base.bytes                    24960   (system-instructions.md 20153 + commands/_preamble.md 4807)
  commands.ship.command_bytes   28371
  commands.ship.command_lines     627
  commands.ship.eager_bytes         0
  commands.ship.floor_bytes     53331
  commands.ship.conditional_bytes 9985   (skills/conventional-commits — ship.md:224)
  commands.ship.ceiling_bytes   63316
  commands.ship.eager_skills       []
  commands.ship.conditional_skills ['conventional-commits']
  commands.ship.base_share_of_floor  0.468
  token_method: estimate:chars/4.0   token_method_validated: false
```

```
floor    = base + command + eagerly-declared skills   # always paid; this spec declares none
ceiling  = floor + inline-read skills                 # worst path; each Read fires only if reached
```

`token_method_validated: false` is load-bearing for how this spec reports. Every number here is **bytes, measured**. No token figure appears in any acceptance criterion — the script's own docstring calls chars/4 an assumption that "has been quoted as though it were measured," and repeating it in a success criterion would be the same defect.

### Section-by-section byte census

Produced by walking `commands/ship.md`'s heading structure outside fenced blocks. This is the input to Story 1's clause ledger, not a substitute for it — a section is not a clause.

| Section | Bytes | Lines | Disposition |
|---|---|---|---|
| frontmatter | 1,901 | 11 | retained **byte-for-byte** — no `required_skills:`, no added key |
| `# Ship Command (ship)` | 22 | 2 | retained |
| `## Overview` | 1,030 | 12 | retained, compressed (~750 B) |
| `## Required Artifacts` | 228 | 7 | retained verbatim |
| `## Invocation` | 455 | 11 | retained verbatim (all six rows) |
| `## Pipeline` (ASCII) | 1,445 | 22 | replaced by the phase list **plus four per-phase `Read` anchors** (~+350 B; this is what replaces the `required_skills:` block) |
| `## Command Process` | 19 | 2 | dropped heading; phases become the list |
| Step 1 — Detect Conventions | 2,821 | 61 | → `repo-convention-detection` |
| Step 2 — Merge Default Branch | 872 | 38 | retained, compressed (~450 B) |
| Step 3 — Run Tests (`--test`) | 1,064 | 35 | retained, compressed (~400 B) |
| Step 4 — Commit Intelligence | 4,182 | 78 | → `commit-organization`; approval gate retained (~450 B) |
| Step 5 — PR Creation | 5,818 | 123 | → `pr-body-composition`; boundary block retained (~900 B) |
| Step 6 — Audit Note | 3,610 | 86 | ~1,200 B → `audit-digest-composition`; rest retained (~1,900 B) |
| `## Dry Run Mode` | 1,138 | 41 | `deduped` into per-skill previews + one retained line (~150 B) |
| `## Error Handling` | 2,076 | 61 | retained, compressed to a rescue table (~900 B) |
| `## When to Use /ship vs Other` | 546 | 13 | merged with the next row (~600 B combined) |
| `## Integration with Writ` | 431 | 10 | merged with the previous row |
| `## Completion` | 532 | 10 | retained verbatim (foundation contract) |
| `## References` | 164 | 5 | retained + skill references (~350 B) |

Retained total projects to ~11,650 bytes against a 24,960-byte cap and a 13,000-byte design target. (~11,300 pre-ruling, plus ~350 for the anchors, minus the ~150 a `required_skills:` block would have cost. The anchors buy ~20,900 bytes of floor for ~350 bytes of command.)

## The Clause Ledger (Story 1 deliverable)

`sub-specs/clause-ledger.md`. One row per normative clause — an imperative, a table row that states behavior, a decision branch, an output block a user would see, or a warning. Prose that only motivates an adjacent clause is not a clause and is not ledgered.

```markdown
| # | Byte offset | Clause (verbatim or ≤12-word précis) | Class | Disposition |
|---|---|---|---|---|
| 41 | 5,102 | "Do not auto-resolve merge conflicts." | gate | retained |
| 42 | 5,180 | rebase variant offers `git rebase --abort` | procedure | skill:repo-... |
```

**Class** is one of `procedure`, `gate`, `provenance`, `contract` (frontmatter / Completion / Invocation), `output`. **Disposition** is written by Story 4 and closed by Story 5, and is one of:

- `retained` — still in `commands/ship.md` after the change.
- `skill:<name>#<section>` — relocated, with the receiving section named.
- `deduped:<row #>` — merged with an identical clause elsewhere in the same file. **Only legitimate use:** `## Dry Run Mode` restates the Step 4 and Step 5 `--dry-run` previews that already appear inline at the end of Step 6. Any other `deduped` needs a note explaining why two clauses were genuinely identical.

Every `gate`-class row must end at `retained` (Business Rule 4). Every `provenance`-class row must end at `retained` except the digest-composition rows (Business Rule 6). A row with an empty disposition is a dropped clause and fails Success Criterion 4.

## Retained Contract — Required Shape

### Frontmatter

**Byte-for-byte unchanged.** `problem:`, `outcome:`, `exit_criteria:` keep their current text and **no key is added**. `required_skills:` is not used (spec.md → *Approved scope change*, Business Rule 3): it is an eager pre-load, so declaring the five skills would move ~20,900 bytes into the floor and raise it from 53,331 to ~57,200.

### The `Read` anchors — what replaces the declaration

Five inline reads, each at the step that consumes it. Four are new; the fifth already exists and is preserved in place.

| Skill | Anchor | Not issued when |
|---|---|---|
| `repo-convention-detection` | Phase 1, at the detection step | — (Phase 1 always runs) |
| `commit-organization` | Step 4, beside the existing `conventional-commits` read | `--no-split`; any run that stops at Steps 2–3 |
| `conventional-commits` | **`ship.md:224`, unchanged** | any run that stops at Steps 2–3 |
| `pr-body-composition` | Phase 5, at the body-assembly step — *before* the retained draft-vs-ready / `gh pr create` block | any run that stops before Phase 5 |
| `audit-digest-composition` | Step 6.2, *after* the `writ.auditNotes` opt-out check and landed-SHA resolution | `writ.auditNotes=false`; no landed commit |

Three placement rules, all checkable:

1. **One read per skill, at a step.** Not in the frontmatter, not in `## Overview`, not in the phase-list table, not batched into a "skills this command uses" block. A hoisted read is `required_skills:` written in prose — every run issues it, the floor absorbs it, and the saving is gone.
2. **`audit-digest-composition`'s anchor sits *after* the opt-out gate**, or a `writ.auditNotes=false` run pays for a skill it will not use and Business Rule 6's seam stops being observable.
3. **`pr-body-composition`'s anchor sits *before* the production-boundary block** and the block itself stays retained — the read supplies material, it never authorizes the PR.

The phrasing convention is the one `ship.md:224` already uses: state the read, then the seam — *"The skill owns how to phrase each commit; this command owns which data populates each component."*

### The audit-note block — minimum retained content

This is the block most at risk of over-trimming. `scripts/eval-git-notes-audit.py` `scenario_ship()` asserts seven conditions against `commands/ship.md`; all seven must still hold:

| Asserted literal / condition | Retained clause it comes from |
|---|---|
| `refs/notes/writ` present | the ref name, stated explicitly |
| `git notes --ref=writ add -f -F` present | the attach command, verbatim, with `-f` |
| one of `never fails the ship` / `non-blocking` / `audit note not attached` | the strictly-non-blocking rule |
| `writ.auditNotes` present | 6.0 opt-out gate, `git config --bool writ.auditNotes` |
| `landed` **and** one of `surviving` / `squash` | 6.1 landed-SHA resolution across the three land strategies |
| one of `minimal digest` / `Fallback` | 6.3's nil-WWB fallback |
| `refs/notes/commits` **and** `never`/`Never` | the prohibition on clobbering the user's default notes ref |

Running `bash scripts/eval.sh` after Story 4 is the cheapest way to catch a violation; running `python3 scripts/eval-git-notes-audit.py` directly gives the per-scenario TSV.

### The production-boundary block — minimum retained content

- The five-row **draft vs. ready** table, including the `--draft` override and the "user can override in both directions" clause.
- `git push -u origin [branch-name]` and `gh pr create --title … --body … --label … [--draft]`.
- The `gh auth login` rescue.
- The completion output block, including the orphaned-commits warning ("commits pushed after merge will be orphaned").
- The `AskQuestion` commit-plan approval and its rationale line ("restructuring git history is not something to auto-proceed on").
- The merge-conflict pause with "Do not auto-resolve merge conflicts" and its cost reasoning.
- The `--test` failure options 1–3, because option 2 forces `--draft` and the `tests-failing` label.

### Spec Reference — the call, not the heuristic

Retained wherever the Spec Reference row lives (command or `pr-body-composition`), byte-faithful in meaning:

```
scripts/resolve-spec-reference.py resolve --branch <branch> --commits "<recent-commit-log>" --specs-dir .writ/specs
```

`result: "matched"` → populate from that spec's folder and story files. `"none"` or `"ambiguous"` → "Standalone change (no spec)". **Never guess between ambiguous candidates.** The script's docstring records that ambiguity is a deliberate safeguard with "no tie-breaking logic"; a skill that reasons about which candidate is likelier reintroduces the defect the script was extracted to remove.

## Skill Authoring Rules

Every new skill is scaffolded with `/new-skill <name>`, which lints the description before writing anything, creates `skills/<name>/SKILL.md`, appends an alphabetically placed `.writ/manifest.yaml` entry, and leaves the root `SKILL.md` to be regenerated with `bash scripts/gen-skill.sh`.

### Frontmatter

```yaml
---
name: <name>
description: "<verb-phrase>"
disable-model-invocation: true
status: candidate
status_evidence: "Extracted 2026-08-12 from commands/ship.md Step N. 1 consumer (commands/ship.md); proven needs >=3 — see ADR-014."
model_tier: orchestration   # advisory only
---
```

`status_evidence` follows the form used by `skills/code-explanation/SKILL.md` and `skills/error-rescue-mapping/SKILL.md`. Do **not** author `evidence:` entries — `scripts/lint-skill.sh` proves state from evidence, and three fabricated entries would forge `proven`.

### Body

`## Purpose` → `## When to Use` → `## How to Apply` → `## Examples` (optional). The lint scans body prose (code blocks exempt) and rejects `Read commands/`, `Read skills/`, `Task(`, and lines beginning with a slash command. Consequences for this spec:

- `commit-organization` cannot point at `conventional-commits` with a `Read` line (`scripts/lint-skill.sh:52`). It states the boundary in prose ("message phrasing is the command's other read at this step") and stops there. **Inline reads are a command instrument:** all five of `/ship`'s live in `commands/ship.md`, and `grep -n 'Read skills/' skills/*/SKILL.md` must return nothing — including inside code fences, which the lint exempts for legitimate examples and which this spec does not treat as a workaround.
- No skill may say "then run `/verify-spec` checks 1–3" as a slash-command line. `pr-body-composition` inlines the three checks' definitions, which is what `ship.md` does today ("definitions identical to the standalone command").

### Naming authority

The convention is **not this spec's to set**. `.writ/docs/skills.md` → *Extraction Patterns*, landed by the dependency spec, is authoritative: kebab-case noun phrase, 2–3 words, ≤30 characters, shaped `<object>-<operation>`, never named after a command, gate, or step; `description:` a bare-imperative verb phrase; a reusable skill carries no consumer vocabulary; and before scaffolding, grep `.writ/manifest.yaml` for the name **and its head noun** — a near-match means declaring the existing skill rather than forking it.

This roster was checked on 2026-08-12 against the convention and against the five sibling disclosure rosters (`implement-story` ×8, `create-spec` ×4, `implement-phase` ×3, `release` ×4) with no collision. Re-check at authoring time.

### Description shapes that pass

| Skill | Description |
|---|---|
| `repo-convention-detection` | "Detect a repository's shipping conventions — default branch, test runner, merge strategy, and PR tool — from config and repo evidence, with a persist-once offer." |
| `commit-organization` | "Group a diff into bisectable commits by architectural layer, and decide when splitting would create broken intermediate states." |
| `pr-body-composition` | "Compose a structured pull-request body from commits, spec artifacts, and drift records, and derive its labels with a never-fail fallback." |
| `audit-digest-composition` | "Aggregate a spec-level audit digest from per-story What Was Built records — verdict, drift, coverage, and file counts — without copying narrative or transcripts." |

Each opens with a verb and none matches `DESC_PATTERNS` (`Acts as`, `Is responsible for`, `The .* agent`, `Run the full`, `Execute the entire`). Verify by running the lint, not by inspection.

## Error & Rescue Map

| Operation | What can fail | Planned handling |
|---|---|---|
| Thin `ship.md` to budget | Cap met by deleting the diagram and the dry-run block, extracting nothing | Design target ≤ 13,000 B **and** the clause ledger; a ledger where every row is `retained` proves nothing was extracted |
| Extract Step 6 | `eval-git-notes-audit.py` `scenario_ship` fails on a missing literal | Run `python3 scripts/eval-git-notes-audit.py` after every edit to the audit block, not only at the end |
| Extract Step 5 | Draft-vs-ready or `gh pr create` lands in `pr-body-composition` | BR4's load test, applied per clause during authoring; the ledger's `gate` class must be 100% `retained` |
| Place the inline `Read`s | A name typoed or a skill not yet written | `measure-invocation.py` reports it under `unresolved_skills` and warns that the figures are a lower bound. `eval-leanness.py check_required_skills` will **not** catch it — it only resolves declarations, and there are none — so its silence proves nothing. Story 4 depends on Stories 2–3 for exactly this reason |
| Place the inline `Read`s | A read hoisted to the frontmatter, `## Overview`, or the phase-list table | Testing Strategy check 9. Move it back to its step; a hoisted read is `required_skills:` in prose and forfeits the saving |
| Place the inline `Read`s | `required_skills:` reintroduced "to be safe" | `measure-invocation.py` reports non-zero `eager_bytes`, or warns that a skill "loads both ways". Delete the declaration — declaring *and* inline-reading is strictly worse than either alone |
| Anchor `audit-digest-composition` | Read placed *before* the `writ.auditNotes` opt-out check | An opted-out run pays for a skill it never uses, and Business Rule 6's seam stops being observable. Anchor at Step 6.2, after the gate and the landed-SHA resolution |
| Author `commit-organization` | It restates `conventional-commits`' type/scope/summary rules | BR5 review read: any row of the type vocabulary appearing in both files is a failure |
| Author any skill | A `Read skills/…` line trips the body lint | `bash scripts/lint-skill.sh` before commit; the fix is prose, not a code-fence workaround to smuggle the line past the scan |
| Register skills | `.writ/manifest.yaml` edited but root `SKILL.md` not regenerated | `bash scripts/gen-skill.sh --check` in each skill story's Definition of Done, not only in Story 5 |
| Grow the `skills` surface | ADR-019's ratchet warns and the warning is dismissed with `--update-baseline` | Business Rule 11: write a bound justification into `.writ/leanness-baseline.json`'s `skills` block by hand. Four such warnings on other surfaces were live and ignored for months — that is the failure mode |
| Name a skill | A name collides with, or near-duplicates, one of the five sibling rosters | Grep `.writ/manifest.yaml` for the name and its head noun at authoring time; declare the existing skill rather than fork it |
| Parallel Stories 2 and 3 | Both append to `.writ/manifest.yaml` and regenerate `SKILL.md` | Alphabetical insertion makes the conflict small but real; sequence or rebase rather than merging two regenerated catalogs |
| Measure the ceiling | Reported as a regression against 53,331, the broken tool's figure | The bar is **63,316**, which the fixed instrument prints directly. Report the `conventional-commits`-excluded pair (53,331 → ~47,525) alongside for symmetry. The projection clears the bar by ~5,800 B, so no justification is expected — and none should be written if none is owed |
| Rely on `spec-deps.py` | A green graph read as proof the dependency's pattern is available | `status: ok` since 2026-08-12 only means the spec folder exists. Story 1 gates on the dependency's **landed** skills, `.writ/docs/skills.md` → Extraction Patterns, and ADR-021 amendments. Never remove the dependency to go green |

## Interaction Edge Cases

| Edge case | Planned handling |
|---|---|
| The dependency spec's pattern differs from § Detailed Requirements | The dependency wins (locked contract). Story 1 records the delta; Story 4 authors to the dependency's shape and the spec's § Detailed Requirements is amended, not quietly diverged from |
| `--no-split` is set, so `commit-organization` has nothing to do | The phase list still names the skill at phase 4, but the run never reaches the composition step, so the `Read` is never issued and ~3,300 B are never paid. Projected path total 48,995 vs a pre-spec 63,316 — **−22.6%** |
| `writ.auditNotes=false` | Phase 6 skips at the opt-out gate, which sits *above* `audit-digest-composition`'s anchor, so ~1,200 B are never paid. Projected 56,295 vs 63,316 — **−11.1%** |
| A `/ship` run never reaches Step 4 (conflict pause at Step 2) | It pays the floor plus `repo-convention-detection` only: ~39,010 against a pre-spec 53,331 — **−26.9%**. This row is the clearest demonstration that the mechanism works, and it is the row the pre-ruling draft said was impossible ("it has already paid the full ceiling"), which was true of `required_skills:` and false of an inline read |
| Comparing a path against the wrong baseline | Runs that stop before Step 4 paid **53,331** pre-spec; runs reaching Step 4 paid **63,316**, because `ship.md:224` sits in Step 4. One before-number across all rows overstates the early rows and understates the late ones |
| `commands/release.md` is thinned concurrently by its sibling spec | `.writ/manifest.yaml` and root `SKILL.md` conflict. Neither spec edits the other's command file (BR9) |
| A reviewer proposes adding an explicit confirm before `gh pr create` | Out of scope. ADR-022's human gate for `/ship` is satisfied by human invocation (`_preamble.md`: no `--recommend` command opens PRs). Adding ceremony is a redesign (BR2) |
| The 400-line tripwire | `eval.sh check_length` still uses 2000 for commands. Report the line count; do not edit `eval.sh` (BR9) |

## Testing Strategy

No application code, no test suite. Verification is structural and runs from the repo root.

```bash
# 1. Budget — command_bytes <= 24960, floor must fall from 53331
python3 scripts/measure-invocation.py --root . --command ship

# 2. Ceiling arithmetic + per-path totals + the conventional-commits-excluded pair
python3 - <<'PY'
import json, os, subprocess
d = json.loads(subprocess.run(["python3","scripts/measure-invocation.py","--root",".","--command","ship"],
                              capture_output=True, text=True).stdout)
r = d["commands"]["ship"]
assert r["eager_bytes"] == 0 and not r["eager_skills"], "FAIL: required_skills: declared"
assert not r["unresolved_skills"], r["unresolved_skills"]
assert not d["warnings"], d["warnings"]
size = lambda n: os.path.getsize(f"skills/{n}/SKILL.md")
cc = size("conventional-commits")   # re-measure, do not trust the recorded 9985
paths = {
  "conflict pause @ Step 2": ["repo-convention-detection"],
  "--no-split @ Step 4":     ["repo-convention-detection", "conventional-commits"],
  "PR open, auditNotes=off": ["repo-convention-detection", "conventional-commits",
                              "commit-organization", "pr-body-composition"],
  "full run (worst path)":   r["conditional_skills"],
}
print("floor", r["floor_bytes"], "ceiling", r["ceiling_bytes"], "ex-cc", r["ceiling_bytes"] - cc)
for name, skills in paths.items():
    print(f"{name:26} {r['floor_bytes'] + sum(size(s) for s in skills):>7,}  {skills}")
PY

# 3. Provenance literals (Business Rule 6) — every one must hit in commands/ship.md
for s in 'refs/notes/writ' 'git notes --ref=writ add -f -F' 'writ.auditNotes' \
         'refs/notes/commits' 'minimal digest' 'landed' 'squash'; do
  printf '%-40s %s\n' "$s" "$(grep -c -- "$s" commands/ship.md)"
done
python3 scripts/eval-git-notes-audit.py    # 7 ship scenarios must PASS

# 4. Invocation surface intact
grep -c -- '--test\|--no-split\|--draft\|--rebase\|--dry-run' commands/ship.md

# 4b. Placement (BR3): five reads, each at a step; none hoisted; none declared
python3 - <<'PY'
import re
t = open('commands/ship.md').read()
fm, body = t.split('\n---', 2)[1], t.split('\n---', 2)[2]
assert 'required_skills:' not in fm, 'FAIL: required_skills: in frontmatter'
print('inline reads:', re.findall(r'Read skills/([a-z0-9-]+)/SKILL\.md', body))
for section in ('## Overview',):
    blk = body.split(section)[1].split('\n## ')[0]
    print(section, 'clean' if 'Read skills/' not in blk else 'FAIL: hoisted read')
tbl = re.search(r'\| # \| Phase \| Gate \| Detail \|.*?(?=\n\n)', body, re.S)
print('phase table', 'clean' if tbl and 'Read skills/' not in tbl.group(0) else 'CHECK BY HAND')
PY

# 5. Shared resolver referenced, not reimplemented, not edited
grep -rn 'resolve-spec-reference.py' commands/ship.md skills/
git diff --name-only -- scripts/          # expect no output

# 6. Skills
bash scripts/lint-skill.sh skills/*/SKILL.md
bash scripts/gen-skill.sh --check
grep -c 'Read skills/' skills/*/SKILL.md  # expect 0 outside code fences

# 7. Regression + spec integrity
bash scripts/eval.sh
bash scripts/eval.sh --check=length
python3 scripts/spec-deps.py validate --specs-dir .writ/specs   # status: ok; the dependency must also have LANDED its skills

# 8. Ownership
git diff --name-only                       # exactly one path under commands/; none under scripts/ agents/ adapters/
```

Checks 1–8 are story evidence run by the implementing agent. **None of them is added to `scripts/eval.sh`** — Business Rule 9, and `2026-08-11-governor-instrumentation` owns enforcement.

## Non-Goals (restated from spec.md → Out of Scope)

No edit to `commands/release.md` or any command other than `ship.md`. No edit under `scripts/` — including `resolve-spec-reference.py`, `check_length`'s 2000-line limit, and `MAX_SKILLS`. No `_preamble.md` change and no cap raise. No new gate. No observable behavior change. No skill promoted past `candidate`. No ADR or roadmap amendment — the Phase 7 non-extraction note is superseded inside `ship.md` itself. No token-based acceptance criterion, because the tokenizer is absent and the script says so.

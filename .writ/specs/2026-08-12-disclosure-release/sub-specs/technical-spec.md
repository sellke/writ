# Technical Spec: Progressive Disclosure — `/release`

> Source: `.writ/specs/2026-08-12-disclosure-release/spec.md`
> All line numbers, byte counts, and file states below were measured against the working tree on **2026-08-12** at `commands/release.md` = 28,589 bytes / 640 lines. Re-measure before editing; a sibling spec landing first shifts nothing in this file, but the base SHA must be recorded.

## Baseline Measurement

Re-measured 2026-08-12 with `scripts/measure-invocation.py` **after** its `e8f2a09` fix. The earlier figures in this package (ceiling 53,549, `conditional_bytes: 0`) came from the broken tool and are superseded.

```
$ python3 scripts/measure-invocation.py --root . --command release --format table

shared base (every invocation): 24,960 bytes
    system-instructions.md               20,153
    commands/_preamble.md                 4,807

command                          floor      cond     ceiling   base%   lines
release                         53,549     9,985      63,534   46.6%     640
```

`eager_bytes` is 0 — `release.md` declares no `required_skills:`, and this spec does not add one (spec.md → *Approved scope change*, Business Rule 3). `conditional_bytes` is 9,985: `commands/release.md:88` inline-reads `skills/conventional-commits/SKILL.md`, which the old tool could not see. Every post-spec comparison is against these two numbers: **floor 53,549, ceiling 63,534.**

The mechanism, stated once so the arithmetic below is readable:

```
floor    = base + command + eagerly-declared skills   # always paid; this spec declares none
ceiling  = floor + inline-read skills                 # worst path; each Read fires only if reached
```

The budget — 24,960 bytes for `command_bytes` — is the `shared base` line, exactly. It is not a round number chosen for feel; it is the load a command cannot avoid, used as the ceiling for the load it can.

## Eval Pin Inventory

`scripts/eval.sh` asserts these literals **against `commands/release.md` itself**. `require_literal` reads the command file; it does not follow `required_skills:`. Relocating any of these into a skill is a failing `eval.sh` run, and `scripts/eval.sh` is out of scope (Business Rule 10).

| # | Literal | Pre-spec line | Asserted by |
|---|---|---|---|
| 1 | `resolve-spec-reference.py resolve --branch "${LAST_MERGED_BRANCH}"` | 156 | `eval.sh:2038` |
| 2 | `archive-sweep.py archive-one --specs-dir .writ/specs --knowledge-dir .writ/knowledge --repo-root . --spec-name` | 158 | `eval.sh:2039` |
| 3 | `is_complete_family` — **must remain absent** | — | `eval.sh:2040` (`forbid_literal`) |
| 4 | `in one best-effort guard` | 154 | `eval.sh:2041` |
| 5 | ``Committing immediately avoids leaving a dangling uncommitted `git mv` `` | 160 | `eval.sh:2042` |
| 6 | `gh CLI unavailable or no merge data — running full test suite` | 144 | `eval.sh:2048` |
| 7 | `Tests skipped — HEAD matches last merged PR` | 145 | `eval.sh:2049` |
| 8 | `\| Otherwise \| Run **full** test suite \|` | 146 | `eval.sh:2050` |
| 9 | `refs/notes/writ` | 408, 446, 460 | `eval.sh:2667`, `eval-git-notes-audit.py:80` |
| 10 | `writ.auditNotes` | 420, 460, 513 | `eval.sh:2668`, `eval-git-notes-audit.py:88` |
| 11 | `git notes --ref=writ add -f -F` | 437, 513 | `eval-git-notes-audit.py:82` |
| 12 | one of `never fails the release` / `non-blocking` / `audit note not attached` | 413–414 | `eval-git-notes-audit.py:85` |
| 13 | `rollup` **and** (`tag` or `TAG_TARGET_SHA`) | 407, 423, 436 | `eval-git-notes-audit.py:90` |
| 14 | `## Required Artifacts` | 20 | `eval.sh:2727` (loop at 2725 over 7 high-traffic commands) |
| 15 | `commands/_preamble.md` (in `## References`) | 639 | `check_preamble()`, `eval.sh:525–546` |

Pins 9, 10, and 11 have multiple occurrences; some of those occurrences sit inside ranges this spec extracts (446, 460, 513). **Each pin must retain at least one occurrence in a range this spec keeps** — 408, 420, and 437 respectively, all inside the retained rollup core. Verify after the rewrite, not before.

### Pin verification command

```bash
python3 - <<'PY'
import sys
t = open('commands/release.md').read()
required = [
 'resolve-spec-reference.py resolve --branch "${LAST_MERGED_BRANCH}"',
 'archive-sweep.py archive-one --specs-dir .writ/specs --knowledge-dir .writ/knowledge --repo-root . --spec-name',
 'in one best-effort guard',
 'Committing immediately avoids leaving a dangling uncommitted `git mv`',
 'gh CLI unavailable or no merge data — running full test suite',
 'Tests skipped — HEAD matches last merged PR',
 '| Otherwise | Run **full** test suite |',
 'refs/notes/writ', 'writ.auditNotes', 'git notes --ref=writ add -f -F',
 'TAG_TARGET_SHA', 'rollup', '## Required Artifacts', 'commands/_preamble.md',
]
missing = [p for p in required if p not in t]
present_any = any(p in t for p in ('never fails the release', 'non-blocking', 'audit note not attached'))
bad = missing + ([] if present_any else ['<non-blocking rollup phrase>'])
if 'is_complete_family' in t:
    bad.append('FORBIDDEN: is_complete_family reintroduced')
print('PINS OK' if not bad else 'PINS BROKEN: ' + '; '.join(bad))
sys.exit(1 if bad else 0)
PY
```

Then the authoritative check:

```bash
bash scripts/eval.sh --check=post-merge-archival
bash scripts/eval.sh --check=git-notes-audit
bash scripts/eval.sh --check=artifact-integrity
bash scripts/eval.sh --check=preamble
bash scripts/eval.sh --check=length
```

## Extraction Map

Fifteen ranges. Line numbers are inclusive and refer to the **pre-spec** `commands/release.md`; record the base SHA in each story's evidence so `git show <base>:commands/release.md` reproduces them.

| ID | Source range | Section | Bytes | Lines | Destination | Story |
|---|---|---|---|---|---|---|
| E1 | 51–76 | Step 1.1 version-source detection chain + release-context gather | 894 | 26 | `semver-version-bump` | 2 |
| E2 | 78–97 | Step 1.2 Analyze Changes | 877 | 20 | `changelog-generation` | 1 |
| E3 | 167–200 | Step 1.4 README Freshness Check | 1,858 | 34 | `readme-freshness-audit` | 1 |
| E4 | 203–209 | Step 1.5 automatic bump-determination table | 370 | 7 | `semver-version-bump` | 2 |
| E5 | 236–292 | Steps 2.1–2.2 changelog format, source priority, quality rules, `CHANGELOG.md` create/prepend | 1,477 | 57 | `changelog-generation` | 1 |
| E6 | 328–367 | Steps 3.1–3.2 version-file updates + release commit | 1,349 | 40 | `semver-version-bump` | 2 |
| E7 | 371–403 | Steps 4.1–4.3 tag, push, `gh release create` | 652 | 33 | `git-tag-publication` | 3 |
| E8a | 425–431 | Step 4.4 rollup composition paragraph | 546 | 7 | `git-tag-publication` | 3 |
| E8b | 443–447 | Step 4.4 summary confirmation line | 130 | 5 | `git-tag-publication` | 3 |
| E9 | 449–470 | Phase 5 Release Summary | 627 | 22 | `git-tag-publication` | 3 |
| E10 | 473–518 | `## Dry Run Mode` detail | 1,957 | 46 | `git-tag-publication` | 3 |
| E11 | 520–545 | `## Monorepo Support` | 588 | 26 | `semver-version-bump` | 2 |
| E12a | 165 | `@sellke/writ` decoupling note inside Step 1.3c | 392 | 1 | `npm-package-publication` | 3 |
| E12b | 600–626 | `## Runtime Helper Publish (manual)` | 2,062 | 27 | `npm-package-publication` | 3 |
| E13 | 548–563 | `## Integration with Writ` table | 689 | 16 | **contracted in place** into `## References` | 4 |

**Totals:** 14,468 bytes / 367 lines leave their current position. 13,779 bytes relocate into skills; 689 are contracted into `## References`.

### Retained ranges — the ones that may not move

| Source range | Section | Bytes | Why it stays |
|---|---|---|---|
| 1–10 | Frontmatter contract | 900 | Phase constraint: `problem:`/`outcome:`/`exit_criteria:` preserved byte-for-byte |
| 11–19 | `## Overview` | 393 | ADR-021 clause 1 |
| 20–26 | `## Required Artifacts` | 278 | Pin 14 |
| 27–38 | `## Modes` → `## Invocation` | 725 | ADR-021 clause 1; carries `--skip-gate` |
| 39–50 | Step 1.1 config-convention load | ~590 | Feeds the gate's Test Runner resolution |
| 98–153 | Step 1.3 release gate (a/b/c + decision table) | 3,836 | BR4, BR6 — pins 6, 7, 8 |
| 154–164 | Step 1.3c post-merge archival hook | 3,188 | BR5, BR6 — pins 1, 2, 4, 5 |
| 211–230 | Step 1.5 `AskQuestion` version proposal | 727 | BR4 |
| 308–324 | Step 2.3 `AskQuestion` release confirmation | 408 | BR4 |
| 405–424, 433–441 | Step 4.4 rollup core: non-blocking, opt-out, attach | 1,236 | BR4, BR6 — pins 9–13 |
| 565–598 | `## Error Handling` | 627 | BR4 |
| 627–634 | `## Completion` | 515 | Phase constraint — byte-for-byte |
| 635–641 | `## References` | 170 | Pin 15 |

### Projected arithmetic

```
pre-spec command_bytes                                28,589
  less relocated into skills                         −13,779
  less contracted (## Integration with Writ)            −689
  plus phase list with gate names (~30 lines)         +1,200
  plus contracted Integration lines in ## References    +250
  plus per-skill reference lines + the retained
    conventional-commits read instruction               +420
  plus five per-phase `Read` anchors (~120 B each)      +600
  no required_skills: block                                0
                                                     ────────
projected command_bytes                                16,591   (budget 24,960 — 34% headroom)
projected floor  = 24,960 + 16,591                     41,551   (from 53,549 — −22.4%)
```

The `+600` replaces the `+140` a `required_skills:` array would have cost, and it is the *only* place this spec spends bytes to buy conditionality. It is a good trade by three orders of magnitude: the array would have added 17,029 bytes to the floor to save 140 in the command.

The projection is a **derived estimate, not a measurement**. The binding criterion is the measured `command_bytes ≤ 24,960` from `measure-invocation.py`. If the actual lands materially above 16.1 KB the spec has not failed; if it lands above 24,960 it has.

### Ceiling arithmetic — path-dependent

All five extracted skills are inline-read, so `conditional_bytes` is their full size plus `conventional-commits`. Scaffolding is taken at ~650 B/skill — the figure the pilot spec derived (`frontmatter + # Title + ## Purpose + ## When to Use + ## How to Apply` framing), not a guess. `measure-invocation.py` deduplicates by name, so a skill read at two anchors (`semver-version-bump`, Phases 1 and 3) is charged once.

**Per-skill sizes** (raw = relocated prose + scaffolding; net = after this skill's Compression Ledger candidates, estimated):

| Skill | Prose | +scaffold | Raw | Ledger | Net |
|---|---|---|---|---|---|
| `changelog-generation` | 2,354 | 650 | 3,004 | C3 −300 | **2,704** |
| `semver-version-bump` | 3,201 | 650 | 3,851 | C7 −150 | **3,701** |
| `git-tag-publication` | 3,912 | 650 | 4,562 | C1 −1,100, C2 −250 | **3,212** |
| `readme-freshness-audit` | 1,858 | 650 | 2,508 | C5 −250 | **2,258** |
| `npm-package-publication` | 2,454 | 650 | 3,104 | C4 −350 | **2,754** |
| **new-skill total** | 13,779 | 3,250 | 17,029 | −2,400 | **14,629** |
| `conventional-commits` (pre-existing, not extracted here) | — | — | 9,985 | — | **9,985** |

C6 (fold `readme-freshness-audit` into `changelog-generation`, −650 B of scaffolding) is **structural** and is not taken in the projection; it is a lever, not a plan.

```
projected floor                                        41,551
  + new skills after ledger                           +14,629
  + conventional-commits                               +9,985
                                                     ────────
tool-reported worst-path ceiling                     ≈ 66,165
bar (corrected pre-spec ceiling)                       63,534
                                                     ────────
OVERAGE on the tool's worst path                       +2,631   (+4.1%)
  less npm-package-publication, which no
  /release run reaches                                 −2,754
                                                     ────────
worst *release* path                                 ≈ 63,411   (−123 vs bar, −0.2%)
```

**Per-path projections.** Each is `floor + Σ(skills that path reads)`. Story 5 measures rather than reproduces these.

| Path | Reads | Projected | Pre-spec | Δ |
|---|---|---|---|---|
| Abort in Phase 1 before Step 1.2 (dirty tree / no releasable changes) | — | **41,551** | 53,549 | −11,998 (−22.4%) |
| Gate blocks at Step 1.3 | semver, changelog, cc | **57,941** | 63,534 | −5,593 (−8.8%) |
| `--no-tag` / `bump_only`, README present | + readme | **60,199** | 63,534 | −3,335 (−5.2%) |
| Full release, README present | + git-tag | **63,411** | 63,534 | −123 (−0.2%) |
| Tool worst path | + npm | **66,165** | 63,534 | +2,631 (+4.1%) |

Two properties of this table are load-bearing and easy to lose:

1. **The pre-spec column is not constant.** Before this spec, a run that aborted before Step 1.2 paid 53,549 and a run that reached Step 1.2 paid 63,534, because `release.md:88`'s inline read sits inside Step 1.2 — earlier than the gate at Step 1.3. Comparing every post-spec path against a single pre-spec number would flatter the early-abort rows and penalise the late ones.
2. **The full-release row is the common one.** `/release` is a pipeline; the normal invocation reaches Phase 5. A −0.2% result on that row is the honest headline for a full release, and Story 5 states it as such rather than leading with the floor.

**`skills/conventional-commits/SKILL.md` (9,985 B) now appears on both sides automatically.** The corrected instrument counts the `release.md:88` inline read in the pre-spec ceiling (63,534) and will count the same read, relocated with its step, in the post-spec ceiling. It is not converted to a declaration and not re-extracted, so no phantom regression can appear. Story 5 additionally reports the excluded pair — pre-spec 53,549 vs post-spec ≈ 56,180 (or ≈ 53,426 excluding npm as well) — so the symmetry is visible rather than asserted.

### Compression Ledger

Candidates, each a permitted contraction under Business Rule 2 — deleting a worked example that illustrates a format specified in the same text, collapsing byte-identical blocks, or replacing a restated list with a pointer to its one authority. **Estimates, to be replaced by measured yields in Story 5.** Never close the gap by dropping a threshold, a fallback, a degradation row, or an "always/never" clause.

| # | Candidate | Range | Est. yield | Why it is contraction, not redesign |
|---|---|---|---|---|
| C1 | Dry-run block's per-phase restatement | E10 | −1,100 | It re-describes procedure specified in E5, E6, E7 in the same skill set; the preview keeps its "does / does NOT" list and its command list |
| C2 | Phase 5 summary template vs. dry-run output block | E9 / E10 | −250 | Two near-identical rendered blocks collapse to one parameterized template |
| C3 | Changelog skeleton placeholder bullets | E5 | −300 | Placeholder bullets illustrate section headings named two lines above them |
| C4 | `publish-writ-runtime.sh` rationale paragraph | E12b | −350 | One long paragraph restating why the README swap exists; the reason survives in one sentence, the trap and the commands survive intact |
| C5 | README discrepancy example block | E3 | −250 | Three sample discrepancy lines illustrate the four-row check table directly above |
| C6 | Consolidate `readme-freshness-audit` into `changelog-generation` | — | −650 | Saves one skill's scaffolding; both are Phase-1 read-side capabilities. **Structural, not textual — take it only if C1–C5 fall short.** Note it also *couples* two paths: a repo with no `README.md` would then load the README procedure anyway, costing ~2,258 B on that path to save 650 B on the worst one |
| C7 | E1 gather-block comments | E1 | −150 | Comments restating the variable names beneath them |
| | **Textual total (C1–C5, C7 — assumed in the projection)** | | **−2,400** | |
| | **Total including structural C6** | | **−3,050** | |

If the measured yield lands short, the named levers are in spec.md → Technical Concerns. Neither lever is an implementer's decision.

## Skill Roster

Names follow the pilot spec `2026-08-12-disclosure-implement-story`'s Business Rule 3: kebab-case noun phrase, 2–3 words, ≤ 30 characters, `<object>-<operation>` or `<operation>-<object>`, never named after the extraction site, `description:` a bare-imperative verb phrase. Head nouns were checked against the pilot's eight names — no collision. Each is scaffolded with `/new-skill <name>` and must pass `bash scripts/lint-skill.sh`.

| Name | Chars | `description:` (bare imperative; lint-checked) | Absorbs | Tags |
|---|---|---|---|---|
| `changelog-generation` | 20 | "Compose a Keep a Changelog entry from completed stories, conventional commits, and spec contracts, categorized and written for readers rather than committers." | E2, E5 | `[changelog, release, documentation]` |
| `semver-version-bump` | 19 | "Resolve a project's version source, derive the next semantic version from detected change classes, and write it consistently across every version file and package scope." | E1, E4, E6, E11 | `[versioning, semver, release]` |
| `git-tag-publication` | 19 | "Tag, push, and publish a cut version — annotated tag, remote push, provider release, audit rollup composition, and the summary a reader can act on." | E7, E8a, E8b, E9, E10 | `[git, tagging, publishing]` |
| `readme-freshness-audit` | 22 | "Cross-reference a README against the repository it documents — command and agent tables, pipeline diagrams, install URLs — and report structural drift without judging descriptions." | E3 | `[documentation, audit, drift]` |
| `npm-package-publication` | 23 | "Publish a small npm package by hand — smoke test, version bump, tarball inspection, and a README swap that never ships the wrong file." | E12a, E12b | `[npm, publishing, runtime]` |

**One rename already happened.** The draft name `release-publication` was rejected against rule 3 — `release` is this skill's extraction site and a command name. `git-tag-publication` names the capability instead, and its `description:` avoids the command's vocabulary per rule 5.

**`conventional-commits` is not declared and not re-extracted.** `commands/release.md:88`'s inline `Read skills/conventional-commits/SKILL.md` stays an inline read in the command — the same mechanism this spec now uses for all five new skills, and the pattern six commands already follow. `scripts/lint-skill.sh:52` forbids it inside a skill; it is not this spec's extraction; and the corrected instrument counts it symmetrically on both sides (see *Ceiling arithmetic*). Converting it to a `required_skills:` entry would move 9,985 bytes into the floor for no benefit and is forbidden by Business Rule 3.

**None of the five new skills is declared either.** Each is reached by one inline `Read` at its anchor. `required_skills:` appears nowhere in `commands/release.md` after this spec.

### Lint hazards in the extracted prose

`scripts/lint-skill.sh`'s body grammar rejects four patterns. The extracted ranges contain three of them today:

- **A line starting with a slash command.** E10's dry-run block contains `Run `/release minor` to execute for real.` — safe (does not open the line), but E5 and E7 reference `/verify-spec` and `/ship`. Verify no extracted line *begins* with `/`.
- **`Read commands/` / `Read skills/`.** E2 line 88 contains `Read skills/conventional-commits/SKILL.md`. Inside `changelog-generation` this is skill chaining and `scripts/lint-skill.sh:52` rejects it. **Resolution:** the read instruction does not move into a skill. It stays in `commands/release.md`, at the Step 1.2 anchor where it already lives — **not** on a phase-list table row, which Business Rule 3 forbids because a table is read as a map rather than executed as a step. `changelog-generation` describes how to categorize entries and points at the type vocabulary without reading it, and no vocabulary is duplicated (ADR-021 clause 4: never copied). The drift-ledger row for E2 records this as `contracted: read instruction retained in the command at its own step`.

  **This constraint generalises into the mechanism.** Inline `Read skills/` lines are a *command* instrument. All six of this command's reads — five new plus `conventional-commits` — live in `commands/release.md`; none may appear in any `skills/*/SKILL.md`, in prose or smuggled inside a code fence. Verify with `grep -n 'Read skills/' skills/*/SKILL.md` in every skill story, not only at the end.
- **Role-shape descriptions.** `Run the full …` and `Execute the entire …` are rejected. Every description above is a verb-phrase; re-lint after any rename.

Code blocks are exempt from the body lint, so the bash and `AskQuestion` fragments in E1, E6, E7, and E10 carry over unchanged.

## The Phase List — what replaces 367 lines of procedure

`## Command Process` becomes a list, one line per phase, each naming its gate and its skill. Shape (exact wording is the implementer's, the structure is not):

```markdown
## Command Process

| Phase | Gate | Detail |
|---|---|---|
| 1 — Release Context Gathering | **Release gate** (inline, below) — `--skip-gate` bypasses | `semver-version-bump`, `changelog-generation`, `readme-freshness-audit` |
| 2 — Changelog Generation | **Human gate:** Step 2.3 confirmation (below) | `changelog-generation` |
| 3 — Version Bump | none — authorized by the Step 2.3 gate | `semver-version-bump` |
| 4 — Tag & Publish | none — authorized by the Step 2.3 gate | `git-tag-publication` |
| 5 — Release Summary | none | `git-tag-publication` |

<!-- The table names skills. It never contains a `Read skills/` string. -->

### Phase 1 — Release Context Gathering

Step 1.1 — resolve the version source and gather release context:
`Read skills/semver-version-bump/SKILL.md` for the detection chain and the bump-determination table. This command owns *when* a bump is proposed and *who approves it*; the skill owns *how* the version is resolved and written.

Step 1.2 — analyze changes: `Read skills/changelog-generation/SKILL.md` …
Step 1.3 — **The Release Gate**  <!-- retained in full: Steps 1.3a/b/c -->
Step 1.4 — README freshness (only if a `README.md` exists): `Read skills/readme-freshness-audit/SKILL.md` …
...
```

Three properties this shape must have. The first two are the point of ADR-021's "keep the phase list and gate names in the command file, so the *shape* stays visible even when the detail does not"; the third is what makes the load conditional at all:

1. **A reader who loads no skills can still see where the human gates are.** Phases 3 and 4 mutate production state and carry no gate of their own — that is only safe to read if the line says *which* gate authorized them.
2. **Every skill appears in the table.** That is half of Business Rule 3's reachability proof; the inline `Read` at its anchor is the other half.
3. **Every `Read` sits at the narrowest step that needs it, and nowhere else.** One per skill, at a step — not in the frontmatter, not in `## Overview`, not in the phase-list table, not batched into a "skills used by this command" block. Placement is the mechanism: a `Read` at Step 1.4 is not issued by a run that never reaches Step 1.4, and a `Read` hoisted anywhere earlier is issued by every run, which reproduces `required_skills:` in prose and forfeits the entire saving. The one deliberate exception is `npm-package-publication`, whose anchor is the `## References` line marking the runtime-helper procedure manual and out-of-band, because that procedure is not a phase of `/release` at all.

The phrasing convention is the established one, visible in `create-spec.md`, `implement-story.md`, `refactor.md`, `research.md`, and `ship.md`: state the read, then the seam — *"the skill owns how; this command owns when and which."*

## Error & Rescue Map

| Failure | Detection | Rescue |
|---|---|---|
| A pinned literal was relocated into a skill | `eval.sh --check=post-merge-archival` or `--check=git-notes-audit` finding | Move the string back into `commands/release.md`. Never edit `eval.sh` (BR10). |
| `is_complete_family` reintroduced while rewriting the hook | `forbid_literal` finding | Delete it. The complete-family check lives only inside `archive-sweep.py`. |
| Skill name already taken by a sibling spec | `ls skills/` before scaffolding | Consume the sibling's skill if it covers the range; otherwise rename (BR8) and record it. |
| `lint-skill.sh` rejects an extracted body | exit 1 with phrase + remediation | Rewrite the offending line. Do **not** reword the procedure's meaning to satisfy the lint — restructure the sentence. |
| Measured ceiling above 63,534 | `measure-invocation.py` in Story 5 | Work the Compression Ledger and record **measured** yields. Report the per-path breakdown alongside — an overage confined to the never-reached `npm-package-publication` path is a different finding from one on the full-release path. If still over, write the three-part Business Rule 1 justification and escalate for explicit maintainer acceptance. Named structural levers: C6, or drop the `npm-package-publication` extraction (−~2,754 B worst-path ceiling, +~2,454 B floor). Never close the gap by deleting a rule. |
| A `Read` hoisted to the frontmatter, `## Overview`, or the phase-list table | Testing Strategy check 6 | Move it back to its step. A hoisted read is `required_skills:` written in prose: every run issues it, the floor absorbs it, and the saving is gone. |
| `required_skills:` reintroduced "to be safe" | check 6b reports non-zero `eager_bytes`, or the tool warns "loads both ways" | Delete the declaration. Declaring *and* inline-reading the same skill is strictly worse than either alone — the tool says so explicitly. |
| A `Read skills/` line lands inside a skill | `bash scripts/lint-skill.sh` (`:52`, skill chaining) | Rewrite as a prose boundary statement. Never move it into a code fence to pass the lint. |
| `command_bytes` above 24,960 after the rewrite | `measure-invocation.py` | Contract retained prose further — never by relocating a BR4 or BR6 item. If the gate and hook alone exceed the budget, that is a finding for ADR-021's owner, not a licence to move them. |
| Three parallel `gen-skill.sh` runs conflict in root `SKILL.md` | git merge conflict | Regenerate once, in Story 4, from the merged manifest. |
| `spec-deps.py validate` reports anything but `status: ok` | Story 5 | The dependency `2026-08-12-disclosure-implement-story` exists and resolves. A `missing_reference` means a sibling spec was renamed or removed — investigate; never delete the dependency to clean the output. |

## Interaction Edge Cases

- **`--skip-gate` and the archival hook.** The hook fires only inside the `LAST_MERGED_SHA == HEAD_SHA` branch, which sits inside the `Unless --skip-gate is set` block. That nesting *is* the `--skip-gate` handling — there is no separate check, and adding one is a redesign. Any rewrite that flattens the nesting breaks the inheritance silently.
- **`--dry-run` is close to the worst path, not close to the floor.** It previews the changelog, the bump determination, *and* the commands Phase 4 would run — and E10's "commands that would run" block lives in `git-tag-publication`. So a dry run reads `changelog-generation`, `semver-version-bump`, `readme-freshness-audit`, `conventional-commits`, and `git-tag-publication`: everything except `npm-package-publication`. Under the eager mechanism this was a curiosity; under conditional loading it is a real result and it is unflattering. **Do not report `--dry-run` as a saving.** Moving E10 elsewhere to improve it would be a redesign of the extraction map, which is out of scope.
- **`--no-tag` / `bump_only`.** These skip Phases 4–5 entirely, which is `git-tag-publication`'s whole load (~3,212 B net). This is the largest real conditional win among completed releases and should be named in the Story 5 report.
- **A repo with no `README.md`.** Step 1.4 has nothing to check, so the `Read` at the Step 1.4 anchor is never issued and `readme-freshness-audit` (~2,258 B) is never paid. Under the withdrawn mechanism it would have been pre-loaded regardless; this is a small, concrete example of what the mechanism change actually buys.
- **Monorepo scope selection sits inside `semver-version-bump`.** A single-package repo pays for prose it will not use, because the skill is read whole. The alternative — a sixth skill for 588 bytes — costs ~650 B of scaffolding to save 588 B of prose, so it makes the worst path worse. Intra-skill conditionality is not something this mechanism provides, and pretending otherwise by splitting skills ever finer trades prose for scaffolding at a loss.
- **`semver-version-bump` is read at two anchors (Step 1.1 and Phase 3) and charged once.** `measure-invocation.py` deduplicates by name. The second anchor exists so a reader of Phase 3 knows where the write mechanics live; it adds no bytes to any figure.
- **The `@sellke/writ` guard inside Step 3.1** (`PKG_NAME != "@sellke/writ"`) stays with the version-file writer in `semver-version-bump`, not with `npm-package-publication`. It is a version-bump behavior; the publish procedure is what moves. Both skills must cross-reference the decoupling in prose so neither reads as the whole story.

## Testing Strategy

There is no application code. Verification is structural and byte-measured.

```bash
BASE=$(git rev-parse HEAD)   # record before Story 4 touches the file

# 1. Budget — the binding criterion
python3 scripts/measure-invocation.py --root . --command release --format table
python3 scripts/measure-invocation.py --root . --command release \
  | python3 -c "import json,sys; d=json.load(sys.stdin)['commands']['release']; \
print('command_bytes', d['command_bytes'], 'PASS' if d['command_bytes']<=24960 else 'FAIL'); \
print('floor', d['floor_bytes'], 'ceiling', d['ceiling_bytes']); \
print('unresolved', d['unresolved_skills'])"

# 2. Pins (script above) + the harness
bash scripts/eval.sh --check=post-merge-archival --check=git-notes-audit
bash scripts/eval.sh --check=artifact-integrity --check=preamble --check=length
bash scripts/eval.sh                      # full run vs pre-spec baseline

# 3. The archival hook is byte-identical
git show $BASE:commands/release.md | sed -n '154,164p' > /tmp/hook-before.txt
# extract the corresponding block from the rewritten file and diff
diff /tmp/hook-before.txt /tmp/hook-after.txt && echo "HOOK VERBATIM"

# 4. Frontmatter contract and ## Completion untouched
git show $BASE:commands/release.md | sed -n '1,10p'   > /tmp/fm-before.txt
git show $BASE:commands/release.md | sed -n '627,634p' > /tmp/comp-before.txt

# 5. Gate vocabulary absent from every skill (BR4)
grep -rn -- '--skip-gate\|AskQuestion\|Proceed with this release\|Block release' skills/*/SKILL.md \
  && echo "FAIL: gate vocabulary found in a skill" || echo "PASS: gates live only in the command"

# 6. Reachability + placement (BR3) — every skill inline-read once, at a step,
#    named in the phase list, and NOT declared or hoisted into the table
python3 - <<'PY'
import re
t = open('commands/release.md').read()
assert 'required_skills:' not in t.split('\n---')[0], 'FAIL: required_skills: declared'
names = re.findall(r'Read skills/([a-z0-9-]+)/SKILL\.md', t)
print('inline reads:', names)
for n in set(names):
    print(n, 'named in phase list' if re.search(rf'\|[^|\n]*{n}[^|\n]*\|', t) else 'NOT IN PHASE LIST')
# the phase-list table itself must carry no Read instruction
table = t.split('## Command Process')[1].split('###')[0]
print('table clean' if 'Read skills/' not in table else 'FAIL: Read hoisted into the phase table')
PY

# 6b. The tool agrees: nothing eager, nothing unresolved, no dual-load warning
python3 scripts/measure-invocation.py --root . --command release \
  | python3 -c "import json,sys; d=json.load(sys.stdin); c=d['commands']['release']; \
print('eager', c['eager_bytes'], c['eager_skills']); \
print('conditional', c['conditional_bytes'], c['conditional_skills']); \
print('unresolved', c['unresolved_skills']); print('warnings', d['warnings'])"

# 7. Skill hygiene
bash scripts/lint-skill.sh skills/*/SKILL.md
bash scripts/gen-skill.sh --check

# 8. Secondary tripwire (non-binding)
wc -l commands/release.md   # target < 400
```

## Non-Goals (restated from spec.md → Out of Scope)

- No edit to `scripts/eval.sh`, `scripts/eval-leanness.py`, `scripts/archive-sweep.py`, or any other `scripts/` file.
- No edit to any other `commands/*.md`, including `commands/_preamble.md`.
- No `MAX_SKILLS` increase, no `check_length` limit change.
- No behavioral change to the release flow — Business Rule 2's ledger is the proof, and `contracted:` is the only permitted deviation from verbatim.
- No ADR amendment. Findings escalate; they do not self-authorize.

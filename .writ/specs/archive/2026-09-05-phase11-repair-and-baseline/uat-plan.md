# UAT Plan: Phase 11 Stage 1: Repair and Baseline

> **Generated:** 2026-09-25
> **Spec:** `.writ/specs/2026-09-05-phase11-repair-and-baseline/`
> **Stories Covered:** 5 of 5 completed
> **Total Scenarios:** 49

## How to Use This Plan

1. Work through scenarios in order (they're grouped by story, ordered by priority)
2. For each scenario, follow the steps exactly as written
3. Mark Pass or Fail — add notes for any unexpected behavior
4. Scenarios marked Fail should be filed as issues or fed back to the spec
5. A feature passes UAT when all scenarios pass (or failures are accepted as known limitations)

**Environment notes for this spec:**

- Run every command from the Writ repo root (`~/Projects/writ`) unless a step says otherwise.
- `bash scripts/eval.sh` runs `git init` in a temp directory. Run it in a normal terminal, not inside a sandboxed agent shell.
- `eval.sh` prints only `Eval report: <path>` to the terminal. Open that file to read `PASS` / `FAIL (N finding(s))` per check and the `## Summary` block. Exit code is 0 for no findings, 1 for findings, 2 for a check that failed to run.
- Scenarios that need a broken file work in a throwaway clone so the real repo stays clean: `git clone -q ~/Projects/writ "$TMPDIR/writ-uat"`. A clone contains committed files only. Delete it with `rm -rf "$TMPDIR/writ-uat"` when done.
- `~/Projects/yuss` has moved since selection (baseline recorded yuss `7c2d043`; HEAD was `578798d` on 2026-09-25). Scenarios that run `select` against the live yuss can return different picks than the committed file. That is expected; the committed file is the record.
- Scenarios marked **Costly** start a real headless `/implement-story` run at Claude Fable 5.1. Recorded runs cost $16.69–$29.66 and 31–56 minutes each. Skip them unless you intend to spend that.

## Coverage Summary

| Story | Status | Scenarios | Source Breakdown |
|-------|--------|-----------|-----------------|
| Story 1: Repair Dead Ends | ✅ Covered | 12 | AC: 11, Errors: 1, Shadow: 0, Edge: 0 |
| Story 2: Validated Token Measurement | ✅ Covered | 7 | AC: 5, Errors: 1, Shadow: 1, Edge: 0 |
| Story 3: Story Selection | ✅ Covered | 10 | AC: 6, Errors: 2, Shadow: 1, Edge: 1 |
| Story 4: Replay Runner | ✅ Covered | 11 | AC: 8, Errors: 2, Shadow: 0, Edge: 0, Experience: 1 |
| Story 5: Baseline Capture and Gate | ✅ Covered | 9 | AC: 7, Errors: 0, Shadow: 1, Edge: 1 |

---

## Story 1: Repair Dead Ends

### Scenario 1: Referenced-paths check passes on the repaired commands

**Source:** Acceptance Criteria (AC-1.1) — Story 1

**Preconditions:**
- Writ repo at `~/Projects/writ`, normal (unsandboxed) terminal

**Steps:**
1. Run `bash scripts/eval.sh --check=referenced-paths; echo "exit=$?"`
2. Open the report file named on the `Eval report:` line.
3. Run `grep -n "objective.md" commands/create-spec.md`
4. Run `grep -n "tech-stack.md" commands/create-spec.md`

**Expected Result:**
- Exit code is `0`; the report shows `## referenced-paths` followed by `PASS` and `- Findings: 0` in the summary
- Step 3 prints nothing
- Step 4 prints a line naming both `.writ/docs/tech-stack.md` and `.writ/docs/code-style.md`, written by `/initialize`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — Files: `scripts/eval.sh` (referenced-paths check, 22-row allowlist), `commands/create-spec.md`

---

### Scenario 2: Referenced-paths check blocks on a dead `.md` reference and names file and line

**Source:** Acceptance Criteria (AC-1.1) + Experience Design (Error experience) — Story 1

**Preconditions:**
- Throwaway clone: `git clone -q ~/Projects/writ "$TMPDIR/writ-uat" && cd "$TMPDIR/writ-uat"`

**Steps:**
1. Append a dead reference: `printf '\nSee `docs/uat-nonexistent-file.md` for details.\n' >> commands/status.md`
2. Note the line number: `grep -n "uat-nonexistent-file.md" commands/status.md`
3. Run `bash scripts/eval.sh --check=referenced-paths; echo "exit=$?"`
4. Open the report file.

**Expected Result:**
- Exit code is `1`
- The `## referenced-paths` section reads `FAIL (1 finding(s))` and the finding names `commands/status.md` with the line number from step 2
- The finding appears as a blocking finding, not under `Notes (non-blocking)`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — Files: `scripts/eval.sh`; bare names resolve by basename anywhere in `git ls-files -co` (DEV-005), so use a name no file in the repo carries

---

### Scenario 3: Skills directory and manifest agree

**Source:** Acceptance Criteria (AC-1.2) — Story 1

**Preconditions:**
- Writ repo, normal terminal

**Steps:**
1. Run `bash scripts/eval.sh --check=skill-manifest-parity; echo "exit=$?"` and open the report.
2. Run `grep -n "subagent-result-completeness\|subagent-worktree-integration" .writ/manifest.yaml SKILL.md`
3. Run `grep -n "^status:" skills/gbrain-interop/SKILL.md` and read the body of that file for a statement about having no consumer.

**Expected Result:**
- Exit `0`; `skill-manifest-parity` shows `PASS`
- Step 2 shows both skill names in `.writ/manifest.yaml` and as rows in root `SKILL.md`
- Step 3 shows `status: candidate`, and the file body says the skill has no consumer by design

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — Files: `.writ/manifest.yaml`, `SKILL.md` (regenerated by `scripts/gen-skill.sh`), `skills/gbrain-interop/SKILL.md`

---

### Scenario 4: Parity check blocks on an unregistered skill directory

**Source:** Acceptance Criteria (AC-1.2) — Story 1

**Preconditions:**
- Throwaway clone: `git clone -q ~/Projects/writ "$TMPDIR/writ-uat" && cd "$TMPDIR/writ-uat"`

**Steps:**
1. Run `mkdir skills/uat-orphan && printf -- '---\nname: uat-orphan\n---\n' > skills/uat-orphan/SKILL.md`
2. Run `bash scripts/eval.sh --check=skill-manifest-parity; echo "exit=$?"` and open the report.
3. Remove the directory (`rm -rf skills/uat-orphan`), then delete one existing skill directory that the manifest lists (for example `rm -rf skills/gbrain-interop`).
4. Run the check again and open the new report.

**Expected Result:**
- Step 2: exit `1`; `FAIL` naming `uat-orphan` as present on disk but absent from the manifest
- Step 4: exit `1`; `FAIL` naming `gbrain-interop` as listed in the manifest but absent from disk

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 5: Knowledge ledger holds reconstructed lessons, not shredded bullets

**Source:** Acceptance Criteria (AC-1.3) — Story 1

**Preconditions:**
- Writ repo, normal terminal

**Steps:**
1. Run `grep -rlE '^- .$' .writ/knowledge/`
2. Open three of the ten 2026-08-11 / 2026-08-12 files in `.writ/knowledge/lessons/` (for example `2026-08-11-cite-anchor-text-not-line-numbers-in-specs-that-a-sibling-spec-will-edit.md`).
3. Run `bash scripts/eval.sh --check=knowledge-integrity; echo "exit=$?"` and open the report.

**Expected Result:**
- Step 1 prints nothing
- Each opened file has a non-empty `## TL;DR` (the lesson title as a sentence) and evidence bullets that are whole sentences, plus a provenance note
- Step 3: exit `0`, `knowledge-integrity` shows `PASS`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — all ten lessons reconstructed, none deleted; TL;DR taken from the H1 title (DEV-007)

---

### Scenario 6: Knowledge-integrity check blocks on a single-character bullet and on an empty TL;DR

**Source:** Acceptance Criteria (AC-1.3) — Story 1

**Preconditions:**
- Throwaway clone: `git clone -q ~/Projects/writ "$TMPDIR/writ-uat" && cd "$TMPDIR/writ-uat"`

**Steps:**
1. Pick one lesson file: `f=.writ/knowledge/lessons/2026-04-24-story-overlap-needs-boundaries.md`
2. Append a shredded bullet: `printf -- '\n- s\n' >> "$f"`
3. Run `bash scripts/eval.sh --check=knowledge-integrity; echo "exit=$?"` and open the report.
4. Restore the file with `git checkout -- "$f"`, then empty its TL;DR text (delete the sentence under `## TL;DR` in an editor, leave the heading).
5. Run the check again and open the report.

**Expected Result:**
- Step 3: exit `1`; `FAIL` naming the file and the line of the `- s` bullet
- Step 5: exit `1`; `FAIL` naming the file's empty TL;DR (this second rule is a recorded scope addition, DEV-001)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 7: Knowledge writeback turns a single-string evidence field into one bullet

**Source:** Acceptance Criteria (AC-1.3) — Story 1

**Preconditions:**
- `uv` installed; Writ repo

**Steps:**
1. Run `uv run --python 3.9 pytest scripts/tests/test_phase_state.py -k "PayloadShape" -v`

**Expected Result:**
- About ten tests run and all pass on Python 3.9, including cases for string evidence, string artifacts, and an empty statement being rejected
- Zero failures, zero errors

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — Files: `scripts/phase-state.py` (knowledge writeback normalizes scalars to lists), `scripts/tests/test_phase_state.py`

---

### Scenario 8: Command-file dead ends are closed

**Source:** Acceptance Criteria (AC-1.4) — Story 1

**Preconditions:**
- Writ repo

**Steps:**
1. `grep -n "\-\-force" commands/implement-spec.md` — read each hit.
2. `grep -c "loop.max_iterations" commands/create-spec.md`
3. `grep -n "no-op until ADR-025 Story 1" commands/create-spec.md commands/implement-story.md`
4. `grep -n "from-issue <path>" commands/create-spec.md | head -1`
5. `grep -n "npx tsc\|npm test" commands/implement-spec.md`
6. `grep -n "If integration fails" commands/implement-spec.md`
7. `grep -n "finds the landed commit" commands/ship.md`
8. `grep -n "Status:\*\* Complete" commands/implement-spec.md`
9. `grep -n "1–6" commands/verify-spec.md`

**Expected Result:**
- Step 1: no Invocation-table row for `--force`; the story-skip rule says to use `/revert` to redo a completed story
- Step 2 prints `0`
- Step 3: one hit in each file, and each hit's line continues with "The line has no sink today"
- Step 4: `--from-issue <path>` appears in the Invocation list
- Step 5 prints nothing
- Step 6: the line offers three options: Fix in place, Revert, Abort
- Step 7: `ship.md` names the next `/ship` or `/release` invocation as where Step 6 runs
- Step 8: the bold unadorned `> **Status:** Complete` form, no date or emoji
- Step 9: the `/release` integration row says checks 1–6

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — Files: `commands/create-spec.md`, `commands/implement-spec.md`, `commands/implement-story.md`, `commands/ship.md`, `commands/verify-spec.md`, `commands/status.md`; dead-end ledger in the story's What Was Built (19/19)

---

### Scenario 9: Adapter dead ends are corrected

**Source:** Acceptance Criteria (AC-1.4) — Story 1

**Preconditions:**
- Writ repo

**Steps:**
1. `grep -n "haiku → sonnet\|haiku -> sonnet" adapters/claude-code.md`
2. Read the model-tier section of `adapters/claude-code.md` (search for `anchor`).
3. Read the install tree near the top of `adapters/cursor.md` and compare its command list with `ls commands/*.md`.
4. `grep -n "unverified" adapters/openclaw.md adapters/codex.md`
5. `grep -rn "after this platform ships" adapters/`

**Expected Result:**
- Step 1 prints nothing
- Step 2: the tier rule is the ADR-024 anchor-as-ceiling rule (floor never exceeds the session's model)
- Step 3: the tree lists the commands, agents, and `skills/` that ship; no command in the tree is missing from `commands/`
- Step 4: every unverified row uses the single form `*(unverified)*`
- Step 5 prints nothing

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 10: Full eval gate ends at zero findings

**Source:** Acceptance Criteria (AC-1.4) — Story 1

**Preconditions:**
- Writ repo on a clean tree (`git status` shows no edits to `scripts/` or `commands/`); normal terminal

**Steps:**
1. Run `bash scripts/eval.sh; echo "exit=$?"`
2. Open the report and read the `## Summary` block.

**Expected Result:**
- Exit `0`
- Summary shows `- Findings: 0` and `- Run errors: 0`
- The report contains sections for `referenced-paths`, `skill-manifest-parity`, and `knowledge-integrity`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 11: Decision log exists and the base files were not touched

**Source:** Acceptance Criteria (AC-1.5) — Story 1

**Preconditions:**
- Writ repo with history (Story 1 commit `1fd9561`)

**Steps:**
1. Run `head -1 .writ/decision-log.md`
2. Run `git show --name-only --format= 1fd9561 | grep -E "system-instructions.md|_preamble.md"`
3. Run `git show --name-only --format= 1fd9561 | grep decision-log`

**Expected Result:**
- Step 1: a line starting `2026-09-06 stage-1:` describing the dead-end repair and the three new checks
- Step 2 prints nothing
- Step 3 prints `.writ/decision-log.md` (created in that commit)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 12: Regression fixture suite covers allowlist self-checks

**Source:** Error Map (Experience Design → Error experience: regression checks name file and line) — Story 1

**Preconditions:**
- Writ repo, normal terminal

**Steps:**
1. Run `bash scripts/tests/test_eval_dead_end_checks.sh; echo "exit=$?"`

**Expected Result:**
- 11 of 11 scenarios pass and exit is `0`
- The output includes the allowlist self-check cases: a malformed allowlist row and a stale allowlist row each produce a blocking finding (DEV-006)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 1 — Files: `scripts/tests/test_eval_dead_end_checks.sh` (synthetic tree, no repo mutation)

---

## Story 2: Validated Token Measurement

### Scenario 13: Without a key, output matches the pre-story script except the note

**Source:** Acceptance Criteria (AC-2.2) + Experience Design (Error experience) — Story 2

**Preconditions:**
- Writ repo; `ANTHROPIC_API_KEY` not set in the shell (`unset ANTHROPIC_API_KEY`)
- No file at `.writ/state/token-cache.json` (move it aside if present)

**Steps:**
1. Run `python3 scripts/measure-invocation.py --root . > "$TMPDIR/after.json"; echo "exit=$?"`
2. Run `git show 0286fab^:scripts/measure-invocation.py > "$TMPDIR/pre.py" && python3 "$TMPDIR/pre.py" --root . > "$TMPDIR/before.json"`
3. Run `diff "$TMPDIR/before.json" "$TMPDIR/after.json"`
4. Run `grep -E '"token_(method|method_validated|model|failures)"' "$TMPDIR/after.json"`
5. Run `ls .writ/state/token-cache.json`

**Expected Result:**
- Step 1 exits `0`
- Step 3 shows exactly one changed line: `token_note`, and the new note names `ANTHROPIC_API_KEY`
- Step 4 shows `token_method` as `estimate:chars/4.0` (or the `tokenizer:` form if `tiktoken` is installed) and `token_method_validated: false`; no `token_model` or `token_failures` keys
- Step 5 reports no such file

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 2 — Files: `scripts/measure-invocation.py`

---

### Scenario 14: With a real key, tokens are counted by the Anthropic API

**Source:** Acceptance Criteria (AC-2.1) + Success Criteria (DONE WHEN 2) — Story 2

**Preconditions:**
- A valid `ANTHROPIC_API_KEY` exported in the shell; network access
- Fresh cache path: `export UAT_CACHE="$TMPDIR/uat-token-cache.json"; rm -f "$UAT_CACHE"`

**Steps:**
1. Run `python3 scripts/measure-invocation.py --root . --cache "$UAT_CACHE" > "$TMPDIR/real.json"; echo "exit=$?"`
2. Run `grep -E '"token_(method|method_validated|model|failures)"' "$TMPDIR/real.json"`
3. Run `python3 scripts/measure-invocation.py --root . --cache "$UAT_CACHE" --format table | head -5`
4. Run `grep -c "$ANTHROPIC_API_KEY" "$TMPDIR/real.json"`

**Expected Result:**
- Exit `0`
- `token_method: "anthropic-count-tokens"`, `token_method_validated: true`, `token_model: "claude-fable-5-1"`, `token_failures: 0`
- The table header shows `[claude-fable-5-1]`
- Step 4 prints `0`

**Status:** [ ] Pass  [ ] Fail

**Notes:** This is the first real-key run. The story recorded it as pending; until it passes, DONE WHEN 2 rests on mocked tests only.

---

### Scenario 15: Token cache stores only hashes and counts, and a warm cache needs no network

**Source:** Acceptance Criteria (AC-2.3) — Story 2

**Preconditions:**
- Scenario 14 completed, so `$UAT_CACHE` exists; `ANTHROPIC_API_KEY` still exported

**Steps:**
1. Run `python3 -c "import json,os,re;d=json.load(open(os.environ['UAT_CACHE']));print(len(d), all(re.fullmatch('[0-9a-f]{64}',k) and isinstance(v,int) for k,v in d.items()))"`
2. Run `grep -c "claude-fable\|Prime Directive\|$ANTHROPIC_API_KEY" "$UAT_CACHE"`
3. Force the network off for Python only: `HTTPS_PROXY=http://127.0.0.1:9 python3 scripts/measure-invocation.py --root . --cache "$UAT_CACHE" | grep -E '"token_(method_validated|failures)"'`

**Expected Result:**
- Step 1 prints about `50 True` (one entry per distinct measured text)
- Step 2 prints `0`: no model name, no source text, no key
- Step 3 shows `token_method_validated: true` and `token_failures: 0` although no request could reach the API

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 16: Partial network failure degrades only the failed texts

**Source:** Acceptance Criteria (AC-2.4) — Story 2

**Preconditions:**
- `$UAT_CACHE` from Scenario 14 exists; `ANTHROPIC_API_KEY` exported

**Steps:**
1. Copy the cache and drop three entries: `python3 -c "import json,os;d=json.load(open(os.environ['UAT_CACHE']));[d.pop(k) for k in list(d)[:3]];json.dump(d,open(os.environ['TMPDIR']+'/partial.json','w'))"`
2. Run `HTTPS_PROXY=http://127.0.0.1:9 python3 scripts/measure-invocation.py --root . --cache "$TMPDIR/partial.json" > "$TMPDIR/degraded.json"; echo "exit=$?"`
3. Run `grep -E '"token_(method|method_validated|failures|note)"' "$TMPDIR/degraded.json"`

**Expected Result:**
- Exit `0`
- `token_method: "anthropic-count-tokens"`, `token_method_validated: false`, `token_failures: 3`
- `token_note` lists the three degraded items by name and gives a first-failure reason

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 17: A rejected key stops counting and never echoes the key

**Source:** Error Map (`count_tokens` request → 401 bad key) — Story 2

**Preconditions:**
- Network access; fresh cache path `$TMPDIR/badkey-cache.json` (absent)

**Steps:**
1. Run `ANTHROPIC_API_KEY=sk-ant-uat-invalid python3 scripts/measure-invocation.py --root . --cache "$TMPDIR/badkey-cache.json" > "$TMPDIR/badkey.json"; echo "exit=$?"`
2. Run `grep -E '"token_(method_validated|failures|note)"' "$TMPDIR/badkey.json"`
3. Run `grep -c "sk-ant-uat-invalid" "$TMPDIR/badkey.json"; ls "$TMPDIR/badkey-cache.json"`

**Expected Result:**
- Exit `0` and the command returns within a few seconds (one request, then no more)
- `token_method_validated: false`; `token_failures` equals the number of distinct texts; the note's first failure says the `x-api-key` header was rejected (HTTP 401)
- Step 3 prints `0` and reports no cache file (failed counts are never cached)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 18: Insisting on the API without a key warns and falls back

**Source:** Shadow Path (`measure-invocation.py --tokenizer anthropic` → Nil input) — Story 2

**Preconditions:**
- `unset ANTHROPIC_API_KEY`

**Steps:**
1. Run `python3 scripts/measure-invocation.py --root . --tokenizer anthropic > "$TMPDIR/nokey.json"; echo "exit=$?"`
2. Run `grep -E '"token_(method|method_validated)"|warnings' -A2 "$TMPDIR/nokey.json" | head -10`

**Expected Result:**
- Exit `0`; no network request is attempted
- The report is an estimate (`token_method_validated: false`) and `warnings` contains a line saying the API was requested but `ANTHROPIC_API_KEY` is not set

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 19: Tokenizer tests pass offline on the Python floor

**Source:** Acceptance Criteria (AC-2.5) — Story 2

**Preconditions:**
- `uv` installed; `unset ANTHROPIC_API_KEY`; optionally disable Wi-Fi

**Steps:**
1. Run `uv run --python 3.9 pytest scripts/tests/test_measure_invocation.py scripts/tests/test_governor_enforcement.py -q`
2. Run `grep -E '^(import|from) ' scripts/measure-invocation.py`

**Expected Result:**
- All tests pass (about 135), no network errors
- Step 2 lists only standard-library modules (`tiktoken` appears only inside a guarded optional import, if at all)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 3: Story Selection

### Scenario 20: `select` writes four stories, one per surface class

**Source:** Acceptance Criteria (AC-3.1) + Experience Design (Happy path step 1) — Story 3

**Preconditions:**
- `~/Projects/yuss` is a git clone; record its state: `git -C ~/Projects/yuss status --porcelain > "$TMPDIR/yuss-before.txt"; git -C ~/Projects/yuss rev-parse HEAD >> "$TMPDIR/yuss-before.txt"`
- `$TMPDIR/uat-sel-claude-fable-5-1.json` does not exist

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py select --yuss ~/Projects/yuss --out "$TMPDIR/uat-sel-claude-fable-5-1.json" --live-test-scope file; echo "exit=$?"`
2. Run `python3 -c "import json,os;d=json.load(open(os.environ['TMPDIR']+'/uat-sel-claude-fable-5-1.json'));print(list(d));print(sorted(s['surface_class'] for s in d['selection']));print(d['runs'], d['runs_per_story']);print([len(s['parent_sha']) for s in d['selection']])"`

**Expected Result:**
- Exit `0`; stdout reads `select: wrote <path> (4 stories, N candidates rejected)`
- Top-level keys: `schema`, `model`, `generated_at`, `yuss_head`, `runs_per_story`, `criteria`, `selection`, `excluded`, `rejection_tally`, `runs`
- Surface classes are exactly `api_route`, `data_model`, `refactor`, `ui`
- `runs` is `[]`, `runs_per_story` is `None`, every `parent_sha` is 40 characters

**Status:** [ ] Pass  [ ] Fail

**Notes:** yuss has advanced past `7c2d043`, so the four picks may differ from the committed baseline.

**Implementation Reference:** Story 3 — Files: `scripts/pipeline-baseline.py` (`select`)

---

### Scenario 21: The committed baseline explains its own selection

**Source:** Acceptance Criteria (AC-3.1) + Spec Recommendation (criteria live in the JSON) — Story 3

**Preconditions:**
- Writ repo

**Steps:**
1. Run `python3 -c "import json;d=json.load(open('.writ/eval/baselines/2026-09-06-claude-fable-5-1.json'));print(d['yuss_head'][:7]);print(json.dumps(d['criteria'],indent=1)[:1500]);[print(s['surface_class'],s['story_commit'][:7],s['eligible_classes'],s['criteria_values']) for s in d['selection']]"`

**Expected Result:**
- `yuss_head` starts `7c2d043`
- The `criteria` block shows the status rule, deny list (`prisma`, `stripe`, `@neondatabase`, `next-auth`), test-file globs, per-class path patterns, refactor rule, tie-break rule, exclusion cap, and `live_test_scope: "file"`
- Four picks: `api_route` @ `79d79ae`, `ui` @ `8d97930`, `data_model` @ `c9350fc`, `refactor` @ `12eea11`; each `criteria_values` shows status Completed, a commit source, a test-file count ≥ 1, and `deny_list_hits: 0`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 22: Rejections are recorded, capped, and carry no source text

**Source:** Acceptance Criteria (AC-3.2) + Error Map (`select` scan → story has no resolvable commit) — Story 3

**Preconditions:**
- Writ repo

**Steps:**
1. Run `python3 -c "import json;d=json.load(open('.writ/eval/baselines/2026-09-06-claude-fable-5-1.json'));e=d['excluded'];print(len(e));[print(x['reason'],len(x['detail']),x['detail']) for x in e];print(d['rejection_tally'], sum(d['rejection_tally'].values()))"`

**Expected Result:**
- 10 entries in `excluded`
- Every `reason` is one of `status_not_completed`, `commit_unresolved`, `git_error`, `no_test_files`, `live_service_import`, `migration_prerequisite`, `no_surface_class`, `class_filled`
- Every `detail` is ≤ 200 characters and holds a path or a count, never a line of code or story prose
- `rejection_tally` totals 364 (`commit_unresolved` 299, `status_not_completed` 30, `no_test_files` 17, `live_service_import` 11, `class_filled` 7)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 23: Admission, tie-break, and merge rules hold on fixture repositories

**Source:** Acceptance Criteria (AC-3.2, AC-3.3) + Edge Cases (merge commit → first parent; two stories in one commit) — Story 3

**Preconditions:**
- `uv` installed

**Steps:**
1. Run `uv run --python 3.9 pytest scripts/tests/test_pipeline_baseline.py -v`

**Expected Result:**
- All tests pass on 3.9 (45 selection tests plus the later validate/compare tests)
- Test names cover: each rejection reason, the `jest.mock` schema-only relaxation to `data_model`, the ten-entry cap and 200-character detail cap, most-recent and same-commit tie-breaks, multi-class assignment, merge first-parent recording, and the short-class message

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 24: A short surface class fails and writes nothing

**Source:** Acceptance Criteria (AC-3.4) + Error Map (`select` → fewer than four admissible stories) — Story 3

**Preconditions:**
- `~/Projects/yuss` present; `$TMPDIR/uat-strict-claude-fable-5-1.json` does not exist

**Steps:**
1. Run the strict default rule: `python3 scripts/pipeline-baseline.py select --yuss ~/Projects/yuss --out "$TMPDIR/uat-strict-claude-fable-5-1.json"; echo "exit=$?"`
2. Run `ls "$TMPDIR/uat-strict-claude-fable-5-1.json"`

**Expected Result:**
- Exit `1`
- One line per short class in the form `select: no admissible story for class data_model (<k> candidates rejected: <reason>=<n>, …)` (at yuss `7c2d043` the strict rule left `data_model` and `refactor` empty)
- Step 2 reports no such file

**Status:** [ ] Pass  [ ] Fail

**Notes:** If yuss has since gained qualifying stories, the strict run can succeed. In that case record the result and rely on Scenario 23 for the short-class test.

---

### Scenario 25: yuss is untouched by any `select` run

**Source:** Acceptance Criteria (AC-3.5) — Story 3

**Preconditions:**
- Scenarios 20 and 24 run in this session; `$TMPDIR/yuss-before.txt` captured before Scenario 20

**Steps:**
1. Run `{ git -C ~/Projects/yuss status --porcelain; git -C ~/Projects/yuss rev-parse HEAD; } > "$TMPDIR/yuss-after.txt"`
2. Run `diff "$TMPDIR/yuss-before.txt" "$TMPDIR/yuss-after.txt"`
3. Run `grep -E '^(import|from) ' scripts/pipeline-baseline.py`

**Expected Result:**
- Step 2 prints nothing
- Step 3 lists only standard-library modules

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 26: `select` refuses a path that is not a git repository

**Source:** Error Map (`select` scan → path missing or not a git repo) — Story 3

**Preconditions:**
- Empty directory: `mkdir -p "$TMPDIR/not-a-repo"`

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py select --yuss "$TMPDIR/not-a-repo" --out "$TMPDIR/x-claude-fable-5-1.json"; echo "exit=$?"`
2. Run `ls "$TMPDIR/x-claude-fable-5-1.json"`

**Expected Result:**
- Exit `2`; stderr reads `select: error:` and names the path as not a git repository
- No output file exists

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 27: `select` refuses to overwrite an existing file or write inside yuss

**Source:** Error Map (select re-run protection, DEV-013) + Business Rule 2 — Story 3

**Preconditions:**
- `$TMPDIR/uat-sel-claude-fable-5-1.json` exists from Scenario 20

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py select --yuss ~/Projects/yuss --out "$TMPDIR/uat-sel-claude-fable-5-1.json" --live-test-scope file; echo "exit=$?"`
2. Run `python3 scripts/pipeline-baseline.py select --yuss ~/Projects/yuss --out ~/Projects/yuss/uat-claude-fable-5-1.json --live-test-scope file; echo "exit=$?"`
3. Run `ls ~/Projects/yuss/uat-claude-fable-5-1.json`

**Expected Result:**
- Step 1: exit `2`, error says the file exists and names `--force`; file modification time unchanged
- Step 2: exit `2`, error says `--out` is inside `<yuss>`
- Step 3 reports no such file

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 28: Missing `--yuss` and an empty archive are refused

**Source:** Shadow Path (`select` → Nil input, Empty input) — Story 3

**Preconditions:**
- A git repo with an empty archive: `mkdir -p "$TMPDIR/empty-yuss/.writ/specs/archive" && git -C "$TMPDIR/empty-yuss" init -q && touch "$TMPDIR/empty-yuss/.writ/specs/archive/.keep" && git -C "$TMPDIR/empty-yuss" add -A && git -C "$TMPDIR/empty-yuss" -c user.email=u@t -c user.name=u commit -qm init`

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py select --out "$TMPDIR/y-claude-fable-5-1.json"; echo "exit=$?"`
2. Run `python3 scripts/pipeline-baseline.py select --yuss "$TMPDIR/empty-yuss" --out "$TMPDIR/y-claude-fable-5-1.json"; echo "exit=$?"`
3. Run `ls "$TMPDIR/y-claude-fable-5-1.json"`

**Expected Result:**
- Step 1: exit `2` with a usage error naming `--yuss`
- Step 2: exit `2` with an error saying there are no candidates
- Step 3 reports no such file

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 29: An output name without the model suffix draws a warning

**Source:** Edge Case (Business Rule 4 — one model per file, `<date>-<model-id>.json`) — Story 3

**Preconditions:**
- `~/Projects/yuss` present; `$TMPDIR/badname.json` absent

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py select --yuss ~/Projects/yuss --out "$TMPDIR/badname.json" --live-test-scope file; echo "exit=$?"`

**Expected Result:**
- stderr shows `select: warning: --out basename 'badname.json' does not end in '-claude-fable-5-1.json' (Business Rule 4)`
- The file is still written and the exit is `0` (warned, not enforced)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 4: Replay Runner

### Scenario 30: `run` refuses when no headless driver is on PATH, with no side effects

**Source:** Acceptance Criteria (AC-4.1) + Experience Design (Error experience: missing driver) — Story 4

**Preconditions:**
- A disposable baseline copy: `cp .writ/eval/baselines/2026-09-06-claude-fable-5-1.json "$TMPDIR/uat-run-claude-fable-5-1.json"; shasum "$TMPDIR/uat-run-claude-fable-5-1.json" > "$TMPDIR/sum.txt"`
- Count existing run dirs: `ls -d "$TMPDIR"/writ-baseline-* 2>/dev/null | wc -l`

**Steps:**
1. Run `env PATH=/usr/bin:/bin python3 scripts/pipeline-baseline.py run --baseline "$TMPDIR/uat-run-claude-fable-5-1.json" --yuss ~/Projects/yuss --model claude-fable-5-1; echo "exit=$?"`
2. Run `shasum -c "$TMPDIR/sum.txt"` and repeat the run-dir count.

**Expected Result:**
- Exit `2`; stderr reads `run: error: claude binary not found on PATH; install it first:` followed by the install hint
- Checksum OK; no new `writ-baseline-*` directory

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 4 — preflight runs before any filesystem or subprocess work

---

### Scenario 31: `run` refuses when `pnpm` is missing

**Source:** Acceptance Criteria (AC-4.1) — Story 4

**Preconditions:**
- Baseline copy from Scenario 30
- A PATH with `claude` but not `pnpm`: `mkdir -p "$TMPDIR/uatbin" && ln -sf "$(command -v claude)" "$TMPDIR/uatbin/claude"`

**Steps:**
1. Run `env PATH="$TMPDIR/uatbin:/usr/bin:/bin" python3 scripts/pipeline-baseline.py run --baseline "$TMPDIR/uat-run-claude-fable-5-1.json" --yuss ~/Projects/yuss --model claude-fable-5-1; echo "exit=$?"`

**Expected Result:**
- Exit `2`; stderr reads `run: error: pnpm not found on PATH (yuss's package manager); install it first:` with an install hint
- Baseline copy unchanged; no `writ-baseline-*` directory created

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 32: A model with no headless driver is sent to `ingest`

**Source:** Acceptance Criteria (AC-4.1) + Approved Scope Addition (driver ≠ model) — Story 4

**Preconditions:**
- Baseline copy from Scenario 30

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py run --baseline "$TMPDIR/uat-run-claude-fable-5-1.json" --yuss ~/Projects/yuss --model grok-4; echo "exit=$?"`
2. Run `python3 scripts/pipeline-baseline.py run --baseline "$TMPDIR/uat-run-claude-fable-5-1.json" --yuss ~/Projects/yuss --model gpt-6-astra; echo "exit=$?"`

**Expected Result:**
- Both exit `2`
- Step 1 names `grok-4`, says it has no headless driver, and tells you to run `/implement-story` in a CLI or IDE and capture with `pipeline-baseline.py ingest --checkout --transcript`
- Step 2 says the model maps to the `codex` driver, which has no headless argv yet, with the same `ingest` instruction
- Neither message mentions an API key

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 33: No vendor API key is required to start a run

**Source:** Acceptance Criteria (AC-4.1) + Business Rule 3 — Story 4

**Preconditions:**
- `claude` and `pnpm` on PATH; `unset ANTHROPIC_API_KEY`; baseline copy from Scenario 30

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py run --baseline "$TMPDIR/uat-run-claude-fable-5-1.json" --yuss ~/Projects/yuss --story no-such-story; echo "exit=$?"`

**Expected Result:**
- Exit `2` with an error that `--story` matched nothing (preflight passed)
- No error mentions `ANTHROPIC_API_KEY`
- Baseline copy unchanged

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 34: Re-running a finished baseline skips every recorded pair

**Source:** Acceptance Criteria (AC-4.5) + Experience Design (State catalog: `run` complete) — Story 4

**Preconditions:**
- `claude` and `pnpm` on PATH; fresh baseline copy: `cp .writ/eval/baselines/2026-09-06-claude-fable-5-1.json "$TMPDIR/uat-resume-claude-fable-5-1.json"; shasum "$TMPDIR/uat-resume-claude-fable-5-1.json" > "$TMPDIR/sum2.txt"`

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py run --baseline "$TMPDIR/uat-resume-claude-fable-5-1.json" --yuss ~/Projects/yuss --model claude-fable-5-1 --runs 2; echo "exit=$?"`
2. Run `shasum -c "$TMPDIR/sum2.txt"`

**Expected Result:**
- Eight lines of the form `run: <story_id> run <n>: skip (already recorded)`, then exit `0`
- No headless session starts; checksum OK

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 35: Committed run records carry verdicts beside re-derivations and no secrets

**Source:** Acceptance Criteria (AC-4.2, AC-4.4) + Business Rules 1, 2, 5 — Story 4

**Preconditions:**
- Writ repo

**Steps:**
1. Run `python3 -c "import json;d=json.load(open('.writ/eval/baselines/2026-09-06-claude-fable-5-1.json'));r=d['runs'][0];print(list(r));print(r['isolation']);print(r['writ']);print(r['invocation']['permission_mode'], r['yuss_head_unchanged']);[print(g,v) for g,v in r['gates'].items()]"`
2. Run `grep -c "sk-ant-" .writ/eval/baselines/2026-09-06-claude-fable-5-1.json`

**Expected Result:**
- `isolation` shows `reachable_commits: 1`, `expected: 1`, `asserted: true`, `answer_scrub_asserted: true`
- `writ.source` is `overlay`; `permission_mode` is `bypass`; `yuss_head_unchanged` is `True`
- Each gate has `verdict`, `source`, `rederived`; Gate 2 and Gate 4 have a re-derived value, Gates 0, 3, 5 have `rederived: None` (no script existed at capture time)
- Step 2 prints `0`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 4 — record contract (`RUN_KEYS`, `GATE_NAMES`) in `scripts/pipeline-baseline.py`; DEV-018 to DEV-024

---

### Scenario 36: One live replay runs isolated and records a full metrics line (Costly)

**Source:** Acceptance Criteria (AC-4.2, AC-4.3, AC-4.4, AC-4.5) + Experience Design (Feedback model) — Story 4

**Preconditions:**
- `claude` logged in and `pnpm` on PATH; about $25 and 45 minutes available
- A fresh selection file from Scenario 20 (`$TMPDIR/uat-sel-claude-fable-5-1.json`) with `runs: []`
- Pick one selected story stem: `python3 -c "import json,os;print([s['story_id'] for s in json.load(open(os.environ['TMPDIR']+'/uat-sel-claude-fable-5-1.json'))['selection']])"`

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py run --baseline "$TMPDIR/uat-sel-claude-fable-5-1.json" --yuss ~/Projects/yuss --story <stem> --runs 1 --cap 1800 --budget-usd 25 --keep`
2. Read the single progress line.
3. In the kept run dir (`$TMPDIR/writ-baseline-<stem>-1/checkout`): run `git rev-list --all --count`, `git remote -v`, `ls .git/FETCH_HEAD`
4. Run `git -C ~/Projects/yuss rev-parse HEAD` and compare with the HEAD recorded before the run.
5. Run `python3 scripts/pipeline-baseline.py validate "$TMPDIR/uat-sel-claude-fable-5-1.json"` — expect a runs-count violation only, since one of eight runs exists.

**Expected Result:**
- Progress line format: `run: <story_id> run 1: <status> exit=<met|unmet> tests=<passed>/<total> tokens=<in>/<out>/<cache_read> wall=<s>s interrupts=<n>`
- `status` is `complete` or `budget`; the run finished inside the cap
- Step 3: `1`, no remotes, no `FETCH_HEAD`
- Step 4: yuss HEAD unchanged
- The selection file now has one record with `isolation.asserted: true` and `answer_scrub_asserted: true`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 37: Deferred smoke-run checklist holds on a live transcript

**Source:** Experience Design / Technical Concern (headless invocation unverified; task 4.2 deferred) — Story 4

**Preconditions:**
- The kept run dir from Scenario 36

**Steps:**
1. Run `head -c 2000 "$TMPDIR/writ-baseline-<stem>-1/transcript.jsonl"` and find the `system`/`init` event.
2. Run `grep -c '"parent_tool_use_id":"[^n]' "$TMPDIR/writ-baseline-<stem>-1/transcript.jsonl"`
3. Open the new record and compare `tokens` with `tokens_main_thread`, and read each `gates.<g>.source`.
4. Run `grep -o 'ARCH_CHECK: [A-Z]*\|REVIEW_RESULT: [A-Z]*' "$TMPDIR/writ-baseline-<stem>-1/transcript.jsonl" | head`

**Expected Result:**
- The init event shows the model, `apiKeySource`, and Claude Code version; the record's `invocation.model_resolved` is populated
- Subagent events carry `parent_tool_use_id` (step 2 is > 0)
- Gate `source` values read `tool_result` (the gate agent's own output), not `assistant_text`
- `tokens_main_thread` is lower than `tokens` in fields where subagents ran (Story 4 checklist item 8)

**Status:** [ ] Pass  [ ] Fail

**Notes:** The committed baselines show `tokens_main_thread` larger than `tokens` in several fields (e.g., story-2 main-thread cache-read 28.2M vs 15.7M total). Check whether this holds live; if so, file it against the token accounting.

---

### Scenario 38: `ingest` rebuilds an identical record from a kept checkout

**Source:** Acceptance Criteria (AC-4.5) — Story 4

**Preconditions:**
- Kept run dir from Scenario 36; a second fresh selection copy: `cp` the Scenario 20 output (before Scenario 36 ran) to `$TMPDIR/uat-ingest-claude-fable-5-1.json`, or strip `runs` back to `[]` and `runs_per_story` to `null`

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py ingest --baseline "$TMPDIR/uat-ingest-claude-fable-5-1.json" --yuss ~/Projects/yuss --checkout "$TMPDIR/writ-baseline-<stem>-1/checkout" --transcript "$TMPDIR/writ-baseline-<stem>-1/transcript.jsonl"; echo "exit=$?"`
2. Compare the key lists of the ingested record and the Scenario 36 record.
3. Repeat step 1 without `--force`.
4. Run `ingest` with `--checkout "$TMPDIR/not-a-repo"`.

**Expected Result:**
- Step 1: exit `0`; one record appended
- Step 2: identical key order and nested key sets
- Step 3: exit `2`, refused because the pair is already recorded
- Step 4: exit `2`, `--checkout ... is not a git checkout`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 39: A refused fetch records an error run without calling the model

**Source:** Error Map (Isolation → fetch refused) — Story 4. Built behavior differs from the plan: no `git archive` fallback exists; a refused fetch is a `fetch_failed` error record (DEV-025).

**Preconditions:**
- `claude` and `pnpm` on PATH; a fresh selection file from Scenario 20 copied to `$TMPDIR/uat-fetch-claude-fable-5-1.json`
- Set the first story's `parent_sha` to 40 zeros: `python3 -c "import json,os;p=os.environ['TMPDIR']+'/uat-fetch-claude-fable-5-1.json';d=json.load(open(p));d['selection'][0]['parent_sha']='0'*40;json.dump(d,open(p,'w'),indent=2)"`

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py run --baseline "$TMPDIR/uat-fetch-claude-fable-5-1.json" --yuss ~/Projects/yuss --story <first story stem> --runs 1; echo "exit=$?"`
2. Read the appended record's `status`, `reason`, `cost_usd`, `tokens`.

**Expected Result:**
- Progress line shows status `error (fetch_failed)`; returns within a minute
- Record: `status: "error"`, `reason: "fetch_failed"`, `cost_usd: null`, all token counts zero or null; no headless session was started

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 40: A wall-clock cap breach records a timeout (Costly, small)

**Source:** Error Map (Headless run → wall-clock cap hit) — Story 4

**Preconditions:**
- `claude` and `pnpm` on PATH; a fresh selection file from Scenario 20 copied to `$TMPDIR/uat-cap-claude-fable-5-1.json`; roughly $2 of model spend

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py run --baseline "$TMPDIR/uat-cap-claude-fable-5-1.json" --yuss ~/Projects/yuss --story <stem> --runs 1 --cap 120; echo "exit=$?"`
2. Read the appended record.
3. Run `ps aux | grep "claude -p" | grep -v grep`

**Expected Result:**
- Progress line status `timeout`; exit `0`
- Record has `status: "timeout"` and whatever tests and re-derivation the tree supported
- Step 3 shows no leftover headless process (the process group was terminated)

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Story 5: Baseline Capture and Gate

### Scenario 41: The committed Fable 5.1 baseline validates and holds eight complete records

**Source:** Acceptance Criteria (AC-5.1) + Experience Design (Entry point) — Story 5

**Preconditions:**
- Writ repo

**Steps:**
1. Run `ls .writ/eval/baselines/*.json`
2. Run `python3 scripts/pipeline-baseline.py validate .writ/eval/baselines/2026-09-06-claude-fable-5-1.json; echo "exit=$?"`
3. Run `python3 -c "import json,collections;d=json.load(open('.writ/eval/baselines/2026-09-06-claude-fable-5-1.json'));r=d['runs'];print(d['schema'],d['model'],d['runs_per_story'],len(r));print(collections.Counter(x['story_id'] for x in r));print(round(sum(x['cost_usd'] for x in r),2), sum(x['tokens']['output'] for x in r), sum(x['tokens']['cache_read'] for x in r));print([x['exit_criteria']['rederived'] for x in r])"`

**Expected Result:**
- Step 1 lists files named `<date>-claude-fable-5-1.json` (one per capture date)
- Step 2 exits `0` with no output
- Step 3: `pipeline-baseline-v1 claude-fable-5-1 2 8`; each of the four stories appears twice; cost sum `187.6`; output tokens `584368`; cache-read `93235659`; all eight `met`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

**Implementation Reference:** Story 5 — Files: `.writ/eval/baselines/2026-09-06-claude-fable-5-1.json`, `scripts/pipeline-baseline.py` (`validate`)

---

### Scenario 42: With no baseline file, the eval check notes and passes

**Source:** Acceptance Criteria (AC-5.2) + Shadow Path (`eval.sh --check=pipeline-baseline` → Nil input) — Story 5

**Preconditions:**
- Throwaway clone: `git clone -q ~/Projects/writ "$TMPDIR/writ-uat" && cd "$TMPDIR/writ-uat"`

**Steps:**
1. Run `rm .writ/eval/baselines/*.json`
2. Run `bash scripts/eval.sh --check=pipeline-baseline; echo "exit=$?"` and open the report.

**Expected Result:**
- Exit `0`; `pipeline-baseline` shows `PASS`
- Under `Notes (non-blocking)`: `NOTE [.writ/eval/baselines]: no baseline JSON found. Create one with python3 scripts/pipeline-baseline.py select.`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 43: `validate` names each schema or leak violation

**Source:** Acceptance Criteria (AC-5.3) — Story 5

**Preconditions:**
- Writ repo; write this helper to make broken copies:
  `mk(){ python3 -c "import json,sys;d=json.load(open('.writ/eval/baselines/2026-09-06-claude-fable-5-1.json'));exec(sys.argv[2]);json.dump(d,open(sys.argv[1],'w'))" "$@"; }`

**Steps:**
1. `mk "$TMPDIR/v1-claude-fable-5-1.json" "del d['model']"`
2. `mk "$TMPDIR/v2-claude-fable-5-1.json" "d['selection']=d['selection'][:3]"`
3. `mk "$TMPDIR/v3-claude-fable-5-1.json" "d['runs']=d['runs'][:7]"`
4. `mk "$TMPDIR/v4-claude-fable-5-1.json" "del d['runs'][0]['tokens']"`
5. `mk "$TMPDIR/v5-claude-fable-5-1.json" "d['runs'][0]['reason']='x'*300"`
6. `mk "$TMPDIR/v6-claude-fable-5-1.json" "d['runs'][0]['reason']='sk-ant-abc'"`
7. `mk "$TMPDIR/v7-claude-fable-5-1.json" "d['runs'][0]['reason']='Human: hello'"`
8. `mk "$TMPDIR/v8-claude-fable-5-1.json" "d['schema']='pipeline-baseline-v0'"`
9. For each file run `python3 scripts/pipeline-baseline.py validate <file>; echo "exit=$?"`

**Expected Result:**
- Every file exits `1`
- Each prints a `path: reason` line naming the offending field: `model`; `selection` (count ≠ 4); `runs` (≠ runs_per_story × 4); `runs[0].tokens` missing; `runs[0].reason` over 200 characters; `runs[0].reason` key-like; `runs[0].reason` turn marker; `schema`
- The unmodified committed file (Scenario 41) exits `0`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 44: The eval check blocks on a broken baseline and clears when fixed

**Source:** Acceptance Criteria (AC-5.3) — Story 5

**Preconditions:**
- Throwaway clone: `git clone -q ~/Projects/writ "$TMPDIR/writ-uat" && cd "$TMPDIR/writ-uat"`

**Steps:**
1. Break one committed file: `python3 -c "import json;p='.writ/eval/baselines/2026-09-06-claude-fable-5-1.json';d=json.load(open(p));del d['criteria'];json.dump(d,open(p,'w'))"`
2. Run `bash scripts/eval.sh --check=pipeline-baseline; echo "exit=$?"` and open the report.
3. Run `git checkout -- .writ/eval/baselines/` and repeat step 2.

**Expected Result:**
- Step 2: exit `1`; `FAIL` with a finding naming `.writ/eval/baselines/2026-09-06-claude-fable-5-1.json` and the `criteria` field
- Step 3: exit `0`; `PASS`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 45: `compare` prints a per-story, per-metric delta table

**Source:** Acceptance Criteria (AC-5.4) + Experience Design (Moment of truth) — Story 5

**Preconditions:**
- Writ repo with both committed baselines (2026-09-06 and 2026-09-07)

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py compare .writ/eval/baselines/2026-09-06-claude-fable-5-1.json .writ/eval/baselines/2026-09-07-claude-fable-5-1.json; echo "exit=$?"`
2. Run the same command with the 2026-09-06 file as both arguments.

**Expected Result:**
- Step 1: header `story  metric  a  b  delta`; for each of the four stories, rows for wall-clock, turns, tokens (input, output, cache read, cache creation, main-thread variants), `interrupts.ask_user_question`, `interrupts.status_blocked`, `review_iterations`, `cost_usd`, and an `exit_criteria` row shown as `met/runs` (e.g. `2/2`); exit `0`
- Step 2: every delta is `0`; exit `0`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 46: `compare` uses per-story medians when run counts differ

**Source:** Acceptance Criteria (AC-5.4) + Edge Case (`compare` across `runs_per_story` 2 vs 3) — Story 5

**Preconditions:**
- A one-run copy: `python3 -c "import json,os;d=json.load(open('.writ/eval/baselines/2026-09-06-claude-fable-5-1.json'));d['runs']=[r for r in d['runs'] if r['run']==1];d['runs_per_story']=1;json.dump(d,open(os.environ['TMPDIR']+'/one-claude-fable-5-1.json','w'))"`

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py compare "$TMPDIR/one-claude-fable-5-1.json" .writ/eval/baselines/2026-09-06-claude-fable-5-1.json | grep cost_usd`

**Expected Result:**
- Exit `0`; four `cost_usd` rows
- Column `a` equals the run-1 cost of each story; column `b` equals the mean of its two runs (median of two values), e.g. story-2 `b` ≈ `27.46`
- `exit_criteria` rows read `1/1` vs `2/2`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 47: `compare` refuses mismatched selections

**Source:** Acceptance Criteria (AC-5.5) + Error Map (`compare` → different `selection` blocks) — Story 5

**Preconditions:**
- A copy with one changed parent SHA: `python3 -c "import json,os;d=json.load(open('.writ/eval/baselines/2026-09-06-claude-fable-5-1.json'));d['selection'][1]['parent_sha']='f'*40;json.dump(d,open(os.environ['TMPDIR']+'/mism-claude-fable-5-1.json','w'))"`

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py compare .writ/eval/baselines/2026-09-06-claude-fable-5-1.json "$TMPDIR/mism-claude-fable-5-1.json"; echo "exit=$?"`

**Expected Result:**
- Only one output line: `compare: selection mismatch: first differing story is <second story's path or id>`
- No table rows; exit `2`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 48: `compare` handles bad inputs cleanly

**Source:** Shadow Path (`compare` → Nil input, Empty input) — Story 5

**Preconditions:**
- A zero-run copy: `python3 -c "import json,os;d=json.load(open('.writ/eval/baselines/2026-09-06-claude-fable-5-1.json'));d['runs']=[];json.dump(d,open(os.environ['TMPDIR']+'/zero-claude-fable-5-1.json','w'))"`

**Steps:**
1. Run `python3 scripts/pipeline-baseline.py compare .writ/eval/baselines/2026-09-06-claude-fable-5-1.json; echo "exit=$?"`
2. Run `python3 scripts/pipeline-baseline.py compare "$TMPDIR/zero-claude-fable-5-1.json" "$TMPDIR/zero-claude-fable-5-1.json"; echo "exit=$?"`
3. Run `python3 scripts/pipeline-baseline.py compare "$TMPDIR/missing.json" "$TMPDIR/zero-claude-fable-5-1.json"; echo "exit=$?"`

**Expected Result:**
- Step 1: argparse usage error, exit `2`
- Step 2: prints `nothing to compare`, exit `0`
- Step 3: `compare: error: <path> does not exist`, exit `2`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

### Scenario 49: Baseline test suites pass on the Python floor

**Source:** Acceptance Criteria (AC-5.1 to AC-5.5 verification) — Story 5

**Preconditions:**
- `uv` installed; normal terminal

**Steps:**
1. Run `uv run --python 3.9 pytest scripts/tests/test_pipeline_baseline.py scripts/tests/test_pipeline_baseline_run.py -q`
2. Run `bash scripts/tests/test_eval_pipeline_baseline.sh; echo "exit=$?"`

**Expected Result:**
- Step 1: all tests pass (149 at capture time; more after later specs added cases)
- Step 2: 5 assertions pass, exit `0`

**Status:** [ ] Pass  [ ] Fail

**Notes:**

---

## Planned Behavior Not Built (for reference, not scenarios)

These technical-spec rows were replaced during implementation. The drift log records each one; no scenario tests the original plan.

- **`git archive` fallback when fetch is refused** → not built; a refused fetch is a `fetch_failed` error record (DEV-025). Scenario 39 tests the built behavior.
- **`<json>.lock` against concurrent `run`s** → not built (DEV-025). Two concurrent runs on one file interleave writes; run them one at a time.
- **`writ_scripts: current|checkout`** → replaced by a full current-Writ overlay and a `writ{...}` block (DEV-021). Scenario 35 checks it.
- **`run` refuses without `ANTHROPIC_API_KEY`** → reversed by the 2026-09-07 scope addition; Scenario 33 checks that no key is required.
- **`--permission-mode acceptEdits`** → bypass mode with compensating controls (DEV-019). Scenarios 35 and 36 check the controls.

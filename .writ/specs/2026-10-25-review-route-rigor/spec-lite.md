# Review-Route Rigor (Lite)

> Source: .writ/specs/2026-10-25-review-route-rigor/spec.md
> Purpose: Efficient AI context for implementation

## For Coding Agents

**Deliverable:** On the review-agent route, Gate 3 names the one fact the change is safe because of and the evidence rung it reached, and a script re-derives the rung. All reviewers apply three lead-judgment filters. Two config-line switches turn each upgrade on or off.

**Implementation Approach:**
- `review-override.py switch --name safety-fact|reviewer-filters` reads `- **Safety Fact:**` / `- **Reviewer Filters:**` in `.writ/config.md`; absent → on; only `off` turns off.
- `change-surface.py blast-radius` lists tracked files outside the change that reference each changed file (path or non-generic stem); `consumers` vs `tests`; cap per file.
- `review-override.py safety-fact` parses `### Safety Fact` (Fact, Holds, Rung, Evidence) and re-derives the measured rung; floor `traced`.
- Upgrade text lives only in `skills/review-judgment-filters/` and `skills/blast-radius/`. Agent bodies carry input rows and one conditional `Read` line each, so the off arm is clean (Claude Code loads native agent bodies verbatim).
- Python 3.9 floor. Regenerate trees with `python3 scripts/gen-platform-trees.py`.

**Files in Scope:**
- `scripts/review-override.py` — `switch`, `safety-fact` subcommands
- `scripts/change-surface.py` — `blast-radius` subcommand, new test-like helper
- `agents/review-agent.md`, `agents/evaluator-agent.md` — input rows, conditional reads
- `commands/review.md` — Step 3 switch + read; header `> Reviewer filters:`
- `commands/implement-story.md` — `#### Gate 2.5` and `#### Gate 3` only (≤1,800 bytes net)
- `skills/review-judgment-filters/SKILL.md`, `skills/blast-radius/SKILL.md`, `.writ/manifest.yaml`, README Skills rows, root `SKILL.md` (gen-skill.sh), `.writ/docs/config-format.md`
- `scripts/tests/test_review_override.py`, `test_change_surface.py`, `test_review_route_rigor.py`
- generated trees (regenerated, never hand-edited)

**Error Handling:**
- Missing/unreadable config or bad value → switch on, reason printed
- No git → filesystem walk (`no_git_walked`); bad `--repo` → `unverifiable`
- Unreadable review output → `unverifiable`, Gate 3 continues, not DEGRADED
- Cited path outside `--repo` or missing → evidence rejected, rung falls

**Integration Points:** Gate 2.5 → `blast_radius` → Gate 3 review-agent; `2026-10-25-gate-upgrade-removal-measurement` flips the switches and reads the report lines.

---

## For Review Agents

**Acceptance Criteria:**
1. Switch resolver prints `on`/`off` with the right reason for every config state; unknown name exits 2 `[AC-1.1, AC-1.2, AC-1.3, AC-1.4]`
2. Filters skill holds three filters (3 before 2) and lints clean; reviewers read it only when the switch is on `[AC-2.1, AC-2.2, AC-2.3]`
3. `/review` header records `Reviewer filters: on|off` `[AC-2.4]`
4. Filter and ladder text appear only in their skills, never in `agents/`, `commands/`, `claude-code/agents/` `[AC-2.5, AC-4.5]`
5. Blast radius lists consumers and tests, honors exclusions, caps, and fallbacks; `classify` unchanged `[AC-3.1, AC-3.2, AC-3.3, AC-3.4]`
6. Gate 2.5 writes the blast-radius file only on the review-agent route with the switch on `[AC-3.5]`
7. Verifier measures each rung, enforces the `traced` floor and the consumers rule, and prints each fail reason `[AC-4.1, AC-4.2, AC-4.3]`
8. Gate 3 routes verifier reasons with one re-review per attempt `[AC-4.4]`

**Business Rules:**
- Safety fact required only when `gate3_route` names `review-agent` and the switch is on
- Measured rung, not claimed rung, decides the floor; overclaim is printed, not blocking
- `Holds: no` with PASS → Gate 3 FAIL
- Filter 3 overrides filter 2: a security finding is dismissed only by a cited guard
- `unverifiable` never fails Gate 3 or marks DEGRADED

**Experience Design:**
- Entry: `/implement-story` Gate 2.5/3 and `/review`, unchanged invocation
- Happy path: route → blast radius → fact traced and cited → measured ≥ `traced`
- Moment of truth: `safety-fact: tested (claimed tested) — <fact>`
- Feedback: `safety-fact:` and `reviewer-filters:` story report lines
- Error: one re-review, then recode asking for a test of the fact

**Gate 3 routing:** see spec.md → Business Rules (Expanded) → Verifier outcomes.

---

## For Testing Agents

**Success Criteria:**
1. `uv run --python 3.9 pytest` green, bash tests green
2. `python3 scripts/gen-platform-trees.py --check` and `bash scripts/eval.sh` pass
3. `bash scripts/lint-skill.sh` passes on both new skills

**Shadow Paths to Verify:**
- **Happy path:** switch `off` → `off`; measured ≥ `traced` → `pass`
- **Nil input:** no config → `on`; no `--review-output` → exit 2; no `--changed` → exit 2
- **Empty input:** empty switch value → `on`; section with no evidence → `claimed` → below floor
- **Upstream error:** no git → walk; unreadable review output → `unverifiable`

**Edge Cases:**
- Generic stem (`index`) → path-only match
- `review-override-v2` does not match `review-override`
- `traced: none` with non-empty consumers → rejected
- Cited path `../../x:1` → rejected

**Coverage Requirements:**
- New code: ≥80%
- Critical paths: 100%
- Error paths: 100%

**Test Strategy:** subprocess CLI tests with `TemporaryDirectory` fixtures; text-placement tests over repo files.

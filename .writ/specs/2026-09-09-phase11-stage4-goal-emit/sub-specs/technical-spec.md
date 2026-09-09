# Technical Spec — Phase 11 Stage 4a: Goal Emit

> Spec: `.writ/specs/2026-09-09-phase11-stage4-goal-emit/`
> Stories: 1 (CLI), 2 (hooks), 3 (adapter + eval + gold)

Shared helper family: Python 3.9 stdlib, argparse, exit 0 (`pass` or `unverifiable`), 1 (`fail`), 2 (usage). One verdict line, optional `reason:` lines, summary last. `--repo` / `--project` alias. No LLM API.

## 1. CLI — `scripts/goal-emit.py` (Story 1)

```
python3 scripts/goal-emit.py emit --card PATH [--out DIR]
python3 scripts/goal-emit.py check --card PATH [--out DIR]
```

| Flag | Required | Meaning |
|---|---|---|
| `--card` | yes for a conclusive run | Path to `.writ/issues/goals/*.md` |
| `--out` | no | Default `.writ/goals/<card-stem>/` (`<card-stem>` = filename without `.md`) |

`emit` writes `GOAL.md` and `VERIFY.md` and prints the invoke line to stdout after the summary. `check` validates those files (and the card) without rewriting the card.

### Required card fields

- Header `> **loop:** yes` or `no`
- `## OBJECTIVE`, `## DONE WHEN`, `## STOP-CAPS`

### Emitted files

**GOAL.md** must contain: card title, OBJECTIVE body, DONE WHEN list, STOP-CAPS list, ADR-013 sentence, an invoke fenced block whose text equals the adapter `/goal` template.

**VERIFY.md** must contain: QUALITY body when the card has that section, a “how to check DONE WHEN” paragraph (name `exit-criteria.py` when a promoted spec exists; otherwise “count DONE WHEN lines on the card”), ADR-013 sentence.

**ADR-013 sentence (verbatim, Decision point 4):**

`No --recommend command merges, opens PRs, or releases. Production remains a human decision.`

Markdown may wrap `--recommend` in backticks. Other words and punctuation must match.

**Invoke template source:** copy the three-way `/goal` block from `adapters/claude-code.md` § The /goal Stop Hook. Do not rewrite clauses (a)/(b)/(c). Pin the copy in the script or read the adapter file; Story 3 gold must match whichever method is chosen.

### Verdict table

| Situation | verdict | reason | exit |
|---|---|---|---|
| `loop: yes`; required sections present; emit/check ok; ADR sentence in both files | `pass` | — | 0 |
| `loop: yes` but missing required section | `fail` | `malformed_card` | 1 |
| Written files lack ADR sentence | `fail` | `missing_boundary` | 1 |
| Missing/unreadable `--card` | `unverifiable` | `missing_card` | 0 |
| `loop: no` | `unverifiable` | `loop_no` | 0 |
| Usage | (stderr) | — | 2 |

Never print accept / reject / modify-spec. Never register a hook.

## 2. Command hooks (Story 2)

**create-goal:** after Phase 3 writes a `loop: yes` card, run `emit --card <path>`. Print the invoke line. `loop: no` → skip emit (`unverifiable` `loop_no` as a note). Package/save still succeeds.

**implement-phase:** when the phase origin resolves to a Goal Card path, run the same emit. No origin → `unverifiable` note. Do not register `/goal`. Do not edit `implement-story.md` spawn paths.

`add_note` for emit verdicts. `add_finding` only if the helper is missing or exits 2.

## 3. Adapter + eval + gold (Story 3)

`adapters/claude-code.md`: add that the human pastes the emitter’s printed invoke line unchanged. Keep the existing three-way template as the source. Cursor / Codex / OpenClaw: no new `/goal` section.

`CHECKS` includes `goal-emit`. Missing helper / exit 2 → `add_finding`. Emit verdicts → `add_note`.

Fixtures: `scripts/tests/fixtures/goal-emit/` — at least `loop-yes/` (card + gold `GOAL.md` / `VERIFY.md` / `invoke.txt`) and `loop-no/` (card only; expect `unverifiable` `loop_no`). No `AC-n.m` tokens in fixture files (keeps `ac-trace` from scanning them as citations).

## 4. Error & Rescue Map

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| `emit --card` | Path missing / unreadable | `unverifiable` `missing_card`; commands continue | Fixture: missing path |
| `emit` on `loop: no` | Card is not a loop | `unverifiable` `loop_no`; no dir created | `loop-no` fixture |
| Parse card | Missing OBJECTIVE / DONE WHEN / STOP-CAPS | `fail` `malformed_card` | Truncated card fixture |
| `check` written files | ADR sentence absent | `fail` `missing_boundary` | Mutated gold |
| `eval.sh` live | No Goal Card in the run | `add_note` unverifiable; Findings 0 | eval-wiring bash |
| Helper missing | File not shipped | `add_finding`; eval fails that check | bash missing-helper |

## 5. Shadow Paths

| Path | Input | Expected |
|---|---|---|
| Happy | Valid `loop: yes` card | `pass`; files + invoke match gold |
| Nil | No `--card` | `unverifiable` `missing_card` |
| Empty | `loop: no` | `unverifiable` `loop_no`; no `--out` dir |
| Upstream | Helper exit 2 | Command `add_finding` |

## 6. Out of scope (do not implement here)

Five-agent demotion, fresh-context evaluator, live `/goal` registration, rewrite of the three-way disjunction, yuss, eight-run, Stage 3 blocking, Codex goal-mode emit.

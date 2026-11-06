# Rating Handoff: Divergence Trial

> Spec: [`spec.md`](spec.md) — Story 5 stops here; Story 6 starts after the rating.
> Written: 2026-10-26 by the `/implement-phase` lane for Phase 15.
> Status: waiting for the human rater. The lane did not rate.

## Who rates

Adam Sellke (@AdamSellke), the spec owner and maintainer, rates once. No agent fills the sheet or runs `rate`.

## What to open

Open one file: `.writ/eval/divergence-trial/rating-sheet.md`.

You may also open the brief files in `.writ/eval/divergence-trial/briefs/` and the rendered UI pages in `.writ/eval/divergence-trial/render/ui-1/` and `.writ/eval/divergence-trial/render/ui-2/` (named `<set>-<n>.html`, for example `X-2.html` is Set X, Draft 2). Both were produced without the key.

Do not open these before you have run `rate`. They reveal which set is which:

- `.writ/eval/divergence-trial/raw/` (the drafts as generated, and the axes plans)
- `.writ/eval/divergence-trial/key.json`
- `.writ/eval/divergence-trial/2026-10-26-divergence-trial.json` (the trial JSON)

Blinding is honor-system: the key and raw drafts are committed so they survive the lane worktree. `trial-report.md` will say so.

## What to fill

Each brief in the sheet has two sets (X and Y) of three drafts, and one `### Rating: <brief>` block with five lines. Fill only those lines and change nothing else in the file; `rate` refuses a sheet whose draft text changed.

| Field | Values | Meaning |
|---|---|---|
| `distinct_X` | 1, 2, or 3 | How many structurally different drafts Set X holds. Count structure (where state lives, how many calls, which table owns identity), not naming. |
| `distinct_Y` | 1, 2, or 3 | The same for Set Y. |
| `more_distinct` | X, Y, or tie | Which set is more distinct. A tie counts as a win for neither. |
| `render_only_enough` | yes or no | Could you choose a direction from these drafts without running code? |
| `note` | one line, at most 200 characters | Anything worth keeping. |

If you edit a draft by accident, restore the sheet with `git checkout .writ/eval/divergence-trial/rating-sheet.md` and fill it again.

## Commands

From the repository root, after filling every field on all six briefs:

```bash
python3 scripts/divergence-trial.py rate --trial .writ/eval/divergence-trial/2026-10-26-divergence-trial.json --sheet .writ/eval/divergence-trial/rating-sheet.md --rated-by "Adam Sellke"
python3 scripts/divergence-trial.py report --trial .writ/eval/divergence-trial/2026-10-26-divergence-trial.json
```

`rate` stores your ratings by set label. `report` then reads `key.json` and prints `keep`, `remove`, or `unverifiable`. The rule: `keep` when the declared-axes set is more distinct on at least 4 of 6 briefs and its total distinct count is higher than the naive set's; otherwise `remove`.

Then run Story 6 (`/implement-story story-6` in this spec). It commits the report verbatim as `trial-report.md` with the rated trial file before it keeps or removes anything.

## State at handoff

- All twelve arms recorded (six briefs × axes and naive), same model and tier in one session.
- This is the second generation. Gate 3 found that the first sheet showed which set was which in several briefs: the axes prompt asked drafts to report changes to the caller lines, and the two arms' drafts differed in length. Both prompts were amended, then both arms were regenerated, re-blinded, and re-rendered. The amendments: the caller lines are private input that drafts must not quote or mention; Structure is 15 to 25 lines for both arms; each draft stands alone. The first generation was discarded before anyone rated.
- One axes draft (ui-1, draft 1) was regenerated once with the identical prompt after `record` refused it for a missing `Trade-off:` line. No draft was hand-edited.
- Content tells may remain that follow from the arm design itself. The three drafts in a naive set come from one response and may share wording or style, while the three drafts in an axes set come from separate spawns. Rate structure, not style.
- `rating-sheet.md` and `key.json` written by `blind`; twelve UI renders written from the blinded text with one shared prompt (`prompts/render.md`).
- `report` before rating prints `unverifiable` with `reason: unrated`; `rated_by` is null.
- The lane did not rate, did not run `rate`, and did not act on any verdict.

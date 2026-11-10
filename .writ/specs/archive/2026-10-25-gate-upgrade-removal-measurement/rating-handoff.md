# Rating Handoff: Gate Upgrade Removal Measurement

> Spec: [`spec.md`](spec.md) · Trial run: 2026-10-29 · Status: awaiting human labels

The lane ran every trial arm and wrote the labeling sheet. It did not label anything, did not fill the sheet, and did not run `label`. Story 4 waits until you do.

## Who labels

The maintainer (@AdamSellke), once. `label` refuses an empty `--labeled-by` and any name containing `claude`, `agent`, `gpt`, `codex`, `cursor`, `gemini`, `grok`, `model`, or `bot`.

## What to open

1. `.writ/eval/gate-upgrade-trial/labeling-sheet.md`: the only file you edit. It has 6 findings (`F01` to `F06`) and 1 acknowledgment.
2. The excerpt for each finding, at the path on its `excerpt:` line: `.writ/state/gate-upgrade-trial/findings/Fnn.md` in the primary checkout (gitignored).
3. The code at the story commit, read-only, when an excerpt is not enough. For example: `git -C ~/Projects/yuss show <story_commit>:<path>`.

| Story | Story commit |
|---|---|
| `2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow` | `79d79ae4a2fb18ba1b5318823f6dc2479f73fa7e` |
| `2026-07-23-quick-split-single-transaction/story-3-settlement-view-share-link` | `8d97930a73bf2d7fd6c29323d5c395402c31095c` |
| `2026-07-24-per-event-fee-revenue-model/story-3-fee-sharing-pro-exemption` | `c9350fca11ca673fab2000066e0118e369faffab` |
| `2026-07-24-per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard` | `12eea11e766c9a9b282ce84fd55fc885fa6fdb40` |

The story's acceptance criteria at that commit are in its story file, e.g. `git -C ~/Projects/yuss show <story_commit>:.writ/specs/<spec_folder>/user-stories/<story>.md`. The sheet's `ac:AC-N.M` keys number each story's criteria in order: `AC-<story number>.<position>`.

## Honor-system blinding

Do not open the trial JSON (`.writ/eval/gate-upgrade-trial/2026-10-29-gate-upgrade-trial.json`) or the raw outputs under `.writ/state/gate-upgrade-trial/<story slug>/` before you finish labeling. They show which upgrade raised each finding. The sheet hides that, but Gate 0 excerpts show themselves through their `**Avoided by:**` line.

## Label rule (spec.md Business Rule 6)

For each finding, set `label:` to `valid` or `invalid`.

- `valid` only when the finding names a real unmet acceptance criterion, or a real Critical or Major security or architecture defect, in the story commit, judged against the story's acceptance criteria at that commit. Later fixes do not count.
- For a Gate 0 finding (its excerpt has an `**Avoided by:**` line), the quoted sketch line must also avoid the defect. If it does not, label it `invalid`.
- `note:` is optional: one line, at most 200 characters, no backticks, no quoted source.

## Acknowledgment rule (spec.md Business Rule 7)

One upgrade was never exercised. Fill its `ack:` with `remove` or `amend`.

- `remove` applies the roadmap's literal rule: an upgrade the baseline never exercised is removed.
- `amend` keeps the upgrade unchanged and leaves this spec open until `/edit-spec` adds an accepted substitute baseline.

## Exercise counts

| Upgrade | Exercised | Upgrade-only findings | Not exercised on |
|---|---|---|---|
| Gate 0 Divergence | 3/4 | 3 | quick-split story-3 (Gate 0 predicted route `evaluator-agent`) |
| Safety Fact | 4/4 | 2 | — |
| Reviewer Filters | 4/4 | 1 | — |
| Repro First | 0/4 | 0 | all four: the coding agent reported `Kind: not a bug fix` on each (each spec's Origin cites a feature issue) |

An upgrade-only finding is a key the upgrade's arm raised on a story that neither "current gates" run (`off-1`, `off-2`) raised on that story.

## Commands

From the repository root, after filling the sheet:

```bash
python3 .writ/eval/gate-upgrade-trial/gate-upgrade-trial.py label \
  --trial .writ/eval/gate-upgrade-trial/2026-10-29-gate-upgrade-trial.json \
  --sheet .writ/eval/gate-upgrade-trial/labeling-sheet.md \
  --labeled-by "<your name>"

python3 .writ/eval/gate-upgrade-trial/gate-upgrade-trial.py report \
  --trial .writ/eval/gate-upgrade-trial/2026-10-29-gate-upgrade-trial.json
```

`label` refuses the sheet if any line other than `label:`, `note:`, or `ack:` changed. After `label` succeeds, run `/implement-spec` on this spec to resume at Story 4.

## Caveats

- **Small sample.** 4 stories, two "current gates" runs per story, one run per upgrade arm. One valid catch keeps an upgrade: a low bar, not a cost case.
- **Proxies.** The Gate 0 arm is a retrospective sketch comparison: a reviewer listed defects in the shipped diff that the chosen sketch avoids. The Repro First arm is a recognition run plus a repro re-run; no story was recognized as a bug fix, so no repro ran. Neither is a replay of `/implement-story`.
- **Coarse keys.** Keys are `ac:AC-N.M` or `<category>:<path>`, so two defects in one file share a key.
- **Thin baseline on two stories.** One "current gates" run produced zero finding keys on story-4 (a FAIL whose only issue is a `criterion` issue with every criterion line checked) and one on fee-sharing story-3 (a PAUSE). On those two stories the baseline is effectively one run, so a finding there counts as upgrade-only more easily. The spec says to amend the key rule before labeling, not after, if that matters to you.
- **Design-divergence blind trial still open.** This trial ran while `2026-10-25-design-divergence` waits on its own human rating (Story 6). Gate 0 was measured as shipped. If both trials decide on Gate 0, spec.md Business Rule 12 settles the outcome.
- **yuss.** HEAD, refs, and `git status --porcelain` were identical before and after the run.

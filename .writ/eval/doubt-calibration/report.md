# Doubt Calibration: Writ's Own Answers (2026-11-05)

> **Question:** can Jev score its confidence that a recommendation is right well enough that a confident decision skips the question ([ADR-033](../../decision-records/adr-033-doubt-gated-autonomy.md))?
> **Data:** every `AskUserQuestion` in this repository's Claude Code transcripts (and its worktrees) that carried exactly one `(Recommended)` option and has a recorded answer. 98 decisions: the maintainer took the recommendation 88 times and overrode it 10 times.
> **Method:** `mine.py` (this folder) extracts the decisions to the gitignored `.writ/state/doubt-calibration/`. With evidence, each row also carries the person's last request and what the assistant said between that request and the question; nothing after the question is read. `python3 scripts/jev-judge.py doubt-calibrate --extra <rows> --live --save <scored>` scored each decision on `vercel-gateway`, model `typesafe-ai/jev`, and applied the fixed rule in `DOUBT_RULE` (`jev-judge.py`). Runs A to D used the first rule: fit the threshold on a dev half, then require zero overrides acted on in the held-out half. Runs E and F use the current rule (below). The confidence question was written once, before any of its scores were seen, and not tuned. Question and evidence text stay out of this repository; the tables below carry ids, outcomes, and scores only.

## Result

Jev's confidence score ranks overrides as more doubtful than accepted decisions about 80% of the time, and every run agrees on what acting on it would cost: about 1 in 10 future overrides would score above the threshold, so about 2 to 3% of the decisions Jev settles would be ones the maintainer would have overridden. The 95% upper bound on that share is 8 to 10%, and the cap is 10%, so whether a run passes depends on Jev's noise. No threshold is written and Jev still shadows. Ten overrides are too few to settle it.

## The current rule

- **Score every decision 3 times.** A live decision is scored once, and Jev's score for the same decision moves between runs (median spread across three draws 0.03, largest 0.12). The threshold is the highest draw of any override, rounded up to 0.01; Jev acts only above it. A row keeps every draw it has, so pooled runs fit on more.
- **Leave one out.** For each override, fit the threshold on the other nine and check whether any of its draws is above it. An override that is counts as one Jev would have acted on.
- **Bound the false-act share.** Overrides × that rate, against accepted decisions × the share of their draws above the threshold, gives the share of Jev's acts the person would have overridden. The rate's one-sided 95% upper bound must put that share at 10% or less. The cap is the maintainer's call (2026-11-05).

The first rule was a coin flip by construction. Over 20,000 random dev/test splits of run D's scores it passed 50% of the time: it passed exactly when the highest-scoring override landed in the dev half.

| Run | Draws per decision | Threshold | Accepted acted on (of 88) | Overrides that slip (of 10) | False-act share | 95% bound | Calibration |
|---|---|---|---|---|---|---|---|
| E: D, D repeat, one new draw | 3 | 0.57 | 34.0 | 1 | 2.9% | 10.4% | refused |
| F: three new draws | 3 | 0.49 | 46.3 | 1 | 2.1% | 7.8% | **passed** |
| E and F pooled | 6 | 0.57 | 34.0 | 1 | 2.9% | 10.4% | refused |

- **The estimate holds; the verdict does not.** Every run finds one slipping override and a 2 to 3% false-act share. The cap sits inside the range the bound moves through.
- **One decision sets the threshold.** Override `7767586a8bff40f5` drew 0.48, 0.57, 0.47, 0.42, 0.45, and 0.49. A run that catches the 0.57 sets the threshold at 0.57 and acts on 34 accepted decisions; one that does not sets 0.49 and acts on 46, which brings the bound under the cap.
- **More draws push toward refusal.** Taking random subsets of the six draws per decision, 3,000 times each: the rule passes 84% of the time with 1 draw, 68% with 2, 49% with 3, 34% with 4, and 17% with 5; all six refuse. The maximum of a few draws underestimates a decision whose score sometimes jumps.
- **Ranking is unchanged.** On the mean of six draws, overrides rank as more doubtful 80.5% of the time.
- **A lead, found after seeing these scores.** A threshold from each override's mean plus a margin from the noise pooled over all 98 decisions (standard deviation 0.023; margin 1.645 of them) is steadier: 99% of 3-draw subsets pass, the threshold stays between 0.50 and 0.55, and all six draws give a bound of 8.7%. It assumes every decision's noise has the same shape, and the decision that matters drew 0.09 above its mean once. It was designed with these labels in view, so it can be tested only on new labels, not adopted on these.

## Earlier runs (first rule)

| Run | Jev's question | Evidence | Ranking, all 98 | Ranking, held-out | Calibration | Threshold | Held-out acted | Overrides acted on |
|---|---|---|---|---|---|---|---|---|
| A | does this need a person? | no | 0.66 | 0.47 | refused | ask at 0.38 | 16 of 47 | 2 |
| B | does this need a person? | yes | 0.70 | 0.48 | refused | ask at 0.34 | 16 of 47 | 2 |
| C | is the recommendation right? | no | 0.75 | 0.60 | refused | act above 0.37 | 19 of 47 | 1 |
| D | is the recommendation right? | yes | 0.80 | 0.76 | **passed** | act above 0.50 | 20 of 47 | 0 |
| D, repeated | is the recommendation right? | yes | 0.78 | 0.68 | refused | act above 0.43 | 27 of 47 | 1 |


"Ranking" is the chance that a random override scores as more doubtful than a random accepted decision: 0.5 is a coin flip, 1.0 is a perfect split. "Held-out" is the half of the 98 the first rule did not fit on.

- **The question matters more than the evidence.** Switching to confidence raised the ranking from 0.66 to 0.75 without evidence. Evidence added a little on top under either question.
- **The repeat failed on noise and the split.** Rescoring the same 98 rows gave a median change of 0.02 and a largest change of 0.11. The dev half's highest-scoring override dropped from 0.50 to 0.43, which lowered the threshold, and one held-out override rose from 0.48 to 0.57, past it.

## What this decided

- **Jev's question is confidence in the recommendation.** `doubt_request` asks whether the recommended option is right: sound on the evidence, and the option the person would choose. A high score acts and a low score asks. The decision record's `evidence` should carry what the person asked for, because the miner's evidence did and the score is calibrated on it.
- **Scores carry the name of the question that produced them.** A log row, a scored file, and a thresholds file record `judgment: recommendation_holds`. A score or threshold from the earlier `needs_person` question is ignored, so a reworded question never calibrates on its predecessor's scale.
- **Calibration scores each decision three times and bounds the false-act share** (the current rule, above). The held-out split is gone.
- **Jev still shadows.** No threshold is written. The site decides, as before.
- **What moves the answer is overrides.** With one slip in 20 overrides and acts in proportion, the bound would be about 6%. Every answered question `/retro` labels adds one.
- **Open: the threshold estimator.** The maximum of three draws flips on one decision; the pooled-noise margin is steadier but untested on unseen labels.

## Re-running

```bash
python3 .writ/eval/doubt-calibration/mine.py
python3 scripts/jev-judge.py doubt-calibrate --log .writ/state/doubt-calibration/none.jsonl \
  --extra .writ/state/doubt-calibration/labeled.jsonl --live --save .writ/state/doubt-calibration/scored.jsonl
```

`--live` scores each row until it holds three draws. To fit on more, concatenate the `draws` lists of two scored files by id (run E and F pooled were built that way) and pass the result as `--extra` without `--live`. `mine.py --no-evidence` writes the rows without evidence, as runs A and C used. Changing the wording in `doubt_request` changes every score: rename `DOUBT_QUESTION` and re-run both steps.

## Scores

Columns A and B score whether the decision needs a person, so higher is more doubtful. The other columns score confidence in the recommendation, so lower is more doubtful. E is run E's new draw (its first two are D and D repeat); F 1 to F 3 are run F's draws. Rows are sorted by the mean of the six confidence draws with evidence (D through F 3). The first rule's dev/test split is in this file's git history.

| Id | Outcome | A | B | C | D | D repeat | E | F 1 | F 2 | F 3 | Mean of six |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `2e5292e6c61e7762` | as_recommended | 0.39 | 0.56 | 0.63 | 0.08 | 0.07 | 0.09 | 0.07 | 0.08 | 0.09 | 0.08 |
| `cadbccb0dd9584f0` | as_recommended | 0.77 | 0.76 | 0.13 | 0.08 | 0.08 | 0.07 | 0.07 | 0.10 | 0.08 | 0.08 |
| `03a43fe759133a64` | overridden | 0.83 | 0.92 | 0.11 | 0.08 | 0.09 | 0.08 | 0.09 | 0.08 | 0.08 | 0.08 |
| `bc8741aba8445ef3` | overridden | 0.72 | 0.88 | 0.07 | 0.08 | 0.09 | 0.09 | 0.08 | 0.09 | 0.08 | 0.08 |
| `4f5147ca6a7f0cc9` | as_recommended | 0.47 | 0.58 | 0.26 | 0.08 | 0.10 | 0.09 | 0.09 | 0.10 | 0.08 | 0.09 |
| `c387e38106b51c81` | overridden | 0.49 | 0.91 | 0.37 | 0.14 | 0.12 | 0.12 | 0.15 | 0.15 | 0.11 | 0.13 |
| `f30fefe577751132` | as_recommended | 0.41 | 0.42 | 0.16 | 0.17 | 0.16 | 0.16 | 0.16 | 0.17 | 0.19 | 0.17 |
| `7ba2029e23bf780d` | as_recommended | 0.53 | 0.60 | 0.37 | 0.16 | 0.19 | 0.15 | 0.20 | 0.19 | 0.13 | 0.17 |
| `12a8f3f7d1f6e675` | as_recommended | 0.72 | 0.76 | 0.14 | 0.22 | 0.20 | 0.21 | 0.21 | 0.21 | 0.26 | 0.22 |
| `e953dd7edbb06f26` | as_recommended | 0.59 | 0.43 | 0.16 | 0.21 | 0.24 | 0.22 | 0.21 | 0.23 | 0.20 | 0.22 |
| `288343a996fccc63` | as_recommended | 0.14 | 0.18 | 0.40 | 0.23 | 0.19 | 0.26 | 0.23 | 0.24 | 0.18 | 0.22 |
| `1a0f94b2205554e2` | as_recommended | 0.53 | 0.76 | 0.59 | 0.24 | 0.23 | 0.21 | 0.23 | 0.21 | 0.22 | 0.22 |
| `b693e9c41bd0166d` | overridden | 0.73 | 0.74 | 0.16 | 0.25 | 0.24 | 0.20 | 0.23 | 0.21 | 0.23 | 0.23 |
| `fe324820629b7bad` | as_recommended | 0.34 | 0.31 | 0.54 | 0.24 | 0.22 | 0.24 | 0.25 | 0.23 | 0.24 | 0.24 |
| `6c79d6d8c2585693` | as_recommended | 0.52 | 0.65 | 0.13 | 0.23 | 0.22 | 0.28 | 0.25 | 0.25 | 0.21 | 0.24 |
| `2350413964c96c64` | as_recommended | 0.67 | 0.69 | 0.24 | 0.26 | 0.22 | 0.25 | 0.24 | 0.24 | 0.24 | 0.24 |
| `3a733cc3ba77ba1b` | overridden | 0.47 | 0.51 | 0.23 | 0.22 | 0.23 | 0.23 | 0.26 | 0.25 | 0.26 | 0.24 |
| `7f90b9ed1584e6c2` | as_recommended | 0.29 | 0.30 | 0.67 | 0.23 | 0.28 | 0.25 | 0.21 | 0.24 | 0.27 | 0.25 |
| `c406c1035a1d6ff1` | as_recommended | 0.40 | 0.61 | 0.14 | 0.29 | 0.26 | 0.26 | 0.25 | 0.24 | 0.25 | 0.26 |
| `44da7c7f9de94ebd` | as_recommended | 0.50 | 0.43 | 0.15 | 0.33 | 0.26 | 0.21 | 0.24 | 0.31 | 0.27 | 0.27 |
| `5aad91c62430e109` | as_recommended | 0.52 | 0.68 | 0.26 | 0.29 | 0.27 | 0.27 | 0.27 | 0.26 | 0.28 | 0.27 |
| `82035bd2e6e84e41` | as_recommended | 0.38 | 0.25 | 0.23 | 0.37 | 0.26 | 0.28 | 0.28 | 0.27 | 0.23 | 0.28 |
| `d7fbd9579888292f` | as_recommended | 0.30 | 0.63 | 0.67 | 0.27 | 0.29 | 0.30 | 0.31 | 0.29 | 0.28 | 0.29 |
| `63047d92ac51a656` | as_recommended | 0.55 | 0.67 | 0.36 | 0.33 | 0.33 | 0.32 | 0.29 | 0.29 | 0.31 | 0.31 |
| `2235270692cd1a07` | overridden | 0.77 | 0.69 | 0.10 | 0.30 | 0.35 | 0.34 | 0.29 | 0.33 | 0.28 | 0.32 |
| `a3c9b7e150aac81e` | as_recommended | 0.25 | 0.60 | 0.90 | 0.32 | 0.24 | 0.31 | 0.30 | 0.35 | 0.38 | 0.32 |
| `faec10f684e0f773` | as_recommended | 0.88 | 0.74 | 0.08 | 0.31 | 0.32 | 0.31 | 0.33 | 0.31 | 0.33 | 0.32 |
| `6669524189cc8020` | as_recommended | 0.58 | 0.50 | 0.44 | 0.32 | 0.36 | 0.32 | 0.30 | 0.32 | 0.33 | 0.33 |
| `7bf950546370a6b0` | overridden | 0.13 | 0.15 | 0.42 | 0.32 | 0.33 | 0.33 | 0.34 | 0.32 | 0.31 | 0.33 |
| `55813916c5f75e7e` | as_recommended | 0.80 | 0.74 | 0.11 | 0.32 | 0.35 | 0.33 | 0.31 | 0.32 | 0.34 | 0.33 |
| `1ddcf0ffc3fbd3fd` | as_recommended | 0.39 | 0.38 | 0.46 | 0.33 | 0.32 | 0.35 | 0.33 | 0.32 | 0.34 | 0.33 |
| `5d82f4ea5143cd0c` | as_recommended | 0.83 | 0.44 | 0.03 | 0.32 | 0.35 | 0.33 | 0.39 | 0.33 | 0.32 | 0.34 |
| `0ff668c33d5b5562` | as_recommended | 0.47 | 0.53 | 0.42 | 0.34 | 0.35 | 0.35 | 0.35 | 0.34 | 0.34 | 0.34 |
| `6dbf580d705e84d6` | as_recommended | 0.50 | 0.62 | 0.37 | 0.38 | 0.32 | 0.37 | 0.36 | 0.32 | 0.37 | 0.35 |
| `f23c4fd1fb061814` | as_recommended | 0.27 | 0.31 | 0.71 | 0.40 | 0.35 | 0.38 | 0.39 | 0.42 | 0.36 | 0.38 |
| `45e5d1cef701c2d0` | overridden | 0.55 | 0.49 | 0.15 | 0.38 | 0.38 | 0.39 | 0.41 | 0.39 | 0.36 | 0.39 |
| `d28b0ba6831e7b0d` | as_recommended | 0.24 | 0.40 | 0.30 | 0.43 | 0.35 | 0.41 | 0.39 | 0.41 | 0.39 | 0.40 |
| `dc4e0745c81e3f53` | as_recommended | 0.47 | 0.45 | 0.58 | 0.43 | 0.39 | 0.44 | 0.38 | 0.34 | 0.41 | 0.40 |
| `906472783d424a7d` | as_recommended | 0.43 | 0.46 | 0.45 | 0.36 | 0.45 | 0.39 | 0.39 | 0.40 | 0.42 | 0.40 |
| `ea4c92f58d59c933` | as_recommended | 0.37 | 0.37 | 0.52 | 0.41 | 0.45 | 0.41 | 0.44 | 0.39 | 0.42 | 0.42 |
| `5b7b8c655c62a048` | as_recommended | 0.62 | 0.50 | 0.35 | 0.42 | 0.45 | 0.38 | 0.39 | 0.48 | 0.42 | 0.42 |
| `4dafc784ae8a2589` | as_recommended | 0.48 | 0.44 | 0.47 | 0.39 | 0.45 | 0.44 | 0.44 | 0.42 | 0.43 | 0.43 |
| `82d9dd9c58868b26` | as_recommended | 0.53 | 0.31 | 0.15 | 0.40 | 0.42 | 0.41 | 0.43 | 0.41 | 0.50 | 0.43 |
| `3e20e27679b0c40a` | as_recommended | 0.75 | 0.47 | 0.09 | 0.44 | 0.43 | 0.40 | 0.47 | 0.43 | 0.43 | 0.43 |
| `a1653031383340e8` | as_recommended | 0.63 | 0.45 | 0.33 | 0.45 | 0.44 | 0.46 | 0.42 | 0.43 | 0.40 | 0.43 |
| `c9d5300117a0176a` | as_recommended | 0.54 | 0.40 | 0.22 | 0.43 | 0.45 | 0.44 | 0.45 | 0.45 | 0.45 | 0.45 |
| `59c85eab6fe14245` | overridden | 0.38 | 0.34 | 0.30 | 0.50 | 0.43 | 0.44 | 0.45 | 0.45 | 0.45 | 0.45 |
| `7767586a8bff40f5` | overridden | 0.34 | 0.31 | 0.36 | 0.48 | 0.57 | 0.47 | 0.42 | 0.45 | 0.49 | 0.48 |
| `8ea0a67f9edae2e6` | as_recommended | 0.34 | 0.39 | 0.76 | 0.51 | 0.48 | 0.49 | 0.48 | 0.49 | 0.48 | 0.49 |
| `8510583678400f27` | as_recommended | 0.56 | 0.44 | 0.33 | 0.48 | 0.49 | 0.49 | 0.53 | 0.47 | 0.48 | 0.49 |
| `d2bb0f7501dd0a04` | as_recommended | 0.53 | 0.51 | 0.51 | 0.49 | 0.50 | 0.51 | 0.46 | 0.48 | 0.50 | 0.49 |
| `90d6fb028423e3c9` | as_recommended | 0.60 | 0.56 | 0.54 | 0.47 | 0.46 | 0.51 | 0.50 | 0.49 | 0.52 | 0.49 |
| `25df3d6bce5773ab` | as_recommended | 0.70 | 0.63 | 0.44 | 0.48 | 0.52 | 0.52 | 0.51 | 0.50 | 0.44 | 0.49 |
| `8ee5901cbe4bc0da` | as_recommended | 0.68 | 0.55 | 0.44 | 0.48 | 0.52 | 0.51 | 0.50 | 0.51 | 0.53 | 0.51 |
| `628468472f7305ff` | as_recommended | 0.23 | 0.24 | 0.41 | 0.47 | 0.54 | 0.50 | 0.51 | 0.52 | 0.52 | 0.51 |
| `66e6223a60ab8f37` | as_recommended | 0.35 | 0.72 | 0.35 | 0.54 | 0.47 | 0.49 | 0.57 | 0.52 | 0.49 | 0.51 |
| `88f8fa71bc31a127` | as_recommended | 0.83 | 0.56 | 0.10 | 0.54 | 0.49 | 0.53 | 0.51 | 0.53 | 0.49 | 0.52 |
| `ab2026a3f136623f` | as_recommended | 0.17 | 0.28 | 0.73 | 0.52 | 0.54 | 0.53 | 0.47 | 0.50 | 0.53 | 0.52 |
| `292234bf39beac07` | as_recommended | 0.35 | 0.34 | 0.57 | 0.51 | 0.50 | 0.48 | 0.56 | 0.55 | 0.53 | 0.52 |
| `2595f2d3e2928d2e` | as_recommended | 0.38 | 0.66 | 0.22 | 0.59 | 0.50 | 0.56 | 0.52 | 0.55 | 0.50 | 0.54 |
| `26681acb40d79719` | as_recommended | 0.53 | 0.86 | 0.23 | 0.57 | 0.51 | 0.58 | 0.54 | 0.57 | 0.57 | 0.56 |
| `305cef138688bddc` | as_recommended | 0.38 | 0.27 | 0.41 | 0.55 | 0.52 | 0.55 | 0.59 | 0.60 | 0.55 | 0.56 |
| `23438d9d4dabfe12` | as_recommended | 0.26 | 0.38 | 0.75 | 0.55 | 0.56 | 0.59 | 0.54 | 0.57 | 0.56 | 0.56 |
| `593ff8b57bd3818d` | as_recommended | 0.48 | 0.35 | 0.60 | 0.60 | 0.55 | 0.56 | 0.61 | 0.53 | 0.54 | 0.57 |
| `19992d2af5814259` | as_recommended | 0.44 | 0.32 | 0.15 | 0.60 | 0.56 | 0.55 | 0.57 | 0.55 | 0.61 | 0.57 |
| `a43709bfb9386bd1` | as_recommended | 0.59 | 0.74 | 0.09 | 0.52 | 0.60 | 0.56 | 0.61 | 0.55 | 0.64 | 0.58 |
| `0b0484af6b6b7698` | as_recommended | 0.29 | 0.37 | 0.30 | 0.59 | 0.60 | 0.63 | 0.62 | 0.59 | 0.58 | 0.60 |
| `8b7e4d158f063184` | as_recommended | 0.72 | 0.60 | 0.13 | 0.63 | 0.59 | 0.61 | 0.62 | 0.60 | 0.58 | 0.60 |
| `c16e593cc469335c` | as_recommended | 0.38 | 0.33 | 0.68 | 0.64 | 0.65 | 0.64 | 0.61 | 0.63 | 0.65 | 0.64 |
| `f685dbb4048c4d93` | as_recommended | 0.27 | 0.40 | 0.81 | 0.67 | 0.66 | 0.67 | 0.66 | 0.62 | 0.60 | 0.65 |
| `4809e54a9b45ca90` | as_recommended | 0.23 | 0.29 | 0.60 | 0.68 | 0.67 | 0.64 | 0.63 | 0.67 | 0.65 | 0.66 |
| `1c082bc9fa3ea509` | as_recommended | 0.18 | 0.15 | 0.81 | 0.70 | 0.69 | 0.64 | 0.66 | 0.61 | 0.66 | 0.66 |
| `6ad1cf51a773ba5f` | as_recommended | 0.29 | 0.35 | 0.77 | 0.63 | 0.66 | 0.67 | 0.69 | 0.67 | 0.70 | 0.67 |
| `c72a7d7fc1cd748c` | as_recommended | 0.39 | 0.35 | 0.54 | 0.69 | 0.67 | 0.69 | 0.68 | 0.66 | 0.67 | 0.68 |
| `855214ece56cfb69` | as_recommended | 0.28 | 0.26 | 0.33 | 0.70 | 0.69 | 0.64 | 0.71 | 0.66 | 0.67 | 0.68 |
| `48f7c98d63125e92` | as_recommended | 0.21 | 0.49 | 0.80 | 0.67 | 0.70 | 0.70 | 0.68 | 0.67 | 0.72 | 0.69 |
| `e9776b0064f825d9` | as_recommended | 0.30 | 0.39 | 0.73 | 0.72 | 0.72 | 0.66 | 0.68 | 0.68 | 0.69 | 0.69 |
| `c1621984e70cb4c6` | as_recommended | 0.42 | 0.43 | 0.45 | 0.71 | 0.71 | 0.70 | 0.68 | 0.68 | 0.68 | 0.69 |
| `45ad5193e9377426` | as_recommended | 0.42 | 0.19 | 0.25 | 0.70 | 0.70 | 0.66 | 0.72 | 0.68 | 0.71 | 0.69 |
| `12ec16c3109bf321` | as_recommended | 0.29 | 0.34 | 0.69 | 0.72 | 0.74 | 0.71 | 0.71 | 0.66 | 0.69 | 0.70 |
| `a6d7b4d24254a021` | as_recommended | 0.07 | 0.07 | 0.96 | 0.74 | 0.71 | 0.79 | 0.74 | 0.68 | 0.75 | 0.73 |
| `28dff195798b578f` | as_recommended | 0.24 | 0.17 | 0.80 | 0.73 | 0.78 | 0.72 | 0.76 | 0.75 | 0.70 | 0.74 |
| `778173afe9522eae` | as_recommended | 0.62 | 0.48 | 0.13 | 0.76 | 0.76 | 0.75 | 0.75 | 0.73 | 0.76 | 0.75 |
| `4bbaab95010debef` | as_recommended | 0.20 | 0.30 | 0.67 | 0.76 | 0.77 | 0.76 | 0.76 | 0.74 | 0.76 | 0.76 |
| `44046c1135a8ff07` | as_recommended | 0.47 | 0.16 | 0.13 | 0.75 | 0.78 | 0.75 | 0.77 | 0.77 | 0.78 | 0.77 |
| `dcd86df87d8e4365` | as_recommended | 0.29 | 0.22 | 0.34 | 0.79 | 0.76 | 0.77 | 0.77 | 0.74 | 0.77 | 0.77 |
| `0b3d276bcbde0b8c` | as_recommended | 0.21 | 0.20 | 0.71 | 0.76 | 0.75 | 0.82 | 0.75 | 0.79 | 0.76 | 0.77 |
| `725d3f32ddb0ceec` | as_recommended | 0.13 | 0.30 | 0.81 | 0.79 | 0.77 | 0.77 | 0.78 | 0.78 | 0.76 | 0.78 |
| `5a7c53f4249c77d2` | as_recommended | 0.20 | 0.24 | 0.85 | 0.77 | 0.78 | 0.78 | 0.80 | 0.79 | 0.80 | 0.79 |
| `a3a80d7c47090de3` | as_recommended | 0.12 | 0.24 | 0.90 | 0.79 | 0.80 | 0.77 | 0.77 | 0.80 | 0.79 | 0.79 |
| `949c24cd139045eb` | as_recommended | 0.13 | 0.16 | 0.81 | 0.81 | 0.80 | 0.78 | 0.79 | 0.79 | 0.79 | 0.79 |
| `4a255bf982a5af76` | as_recommended | 0.09 | 0.07 | 0.85 | 0.80 | 0.80 | 0.82 | 0.81 | 0.80 | 0.81 | 0.81 |
| `e93d3e241bc8caa4` | as_recommended | 0.13 | 0.15 | 0.85 | 0.82 | 0.80 | 0.79 | 0.82 | 0.81 | 0.84 | 0.81 |
| `f1c5dc9ac76c7508` | as_recommended | 0.20 | 0.09 | 0.81 | 0.86 | 0.84 | 0.84 | 0.83 | 0.83 | 0.85 | 0.84 |
| `995d1f1586fce9dd` | as_recommended | 0.52 | 0.20 | 0.12 | 0.86 | 0.84 | 0.87 | 0.85 | 0.84 | 0.86 | 0.85 |
| `432df2564c1b2f42` | as_recommended | 0.12 | 0.22 | 0.86 | 0.88 | 0.88 | 0.88 | 0.87 | 0.89 | 0.87 | 0.88 |
| `03780907c4ec99e3` | as_recommended | 0.51 | 0.05 | 0.27 | 0.93 | 0.92 | 0.92 | 0.93 | 0.92 | 0.93 | 0.93 |
| `6d95a7f2f30254f8` | as_recommended | 0.43 | 0.27 | 0.22 | 0.93 | 0.93 | 0.93 | 0.93 | 0.95 | 0.94 | 0.94 |

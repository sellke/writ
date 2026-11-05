# Doubt Calibration: Writ's Own Answers (2026-11-05)

> **Question:** can Jev score its confidence that a recommendation is right well enough that a confident decision skips the question ([ADR-033](../../decision-records/adr-033-doubt-gated-autonomy.md))?
> **Data:** every `AskUserQuestion` in this repository's Claude Code transcripts (and its worktrees) that carried exactly one `(Recommended)` option and has a recorded answer. 98 decisions: the maintainer took the recommendation 88 times and overrode it 10 times.
> **Method:** `mine.py` (this folder) extracts the decisions to the gitignored `.writ/state/doubt-calibration/`. With evidence, each row also carries the person's last request and what the assistant said between that request and the question; nothing after the question is read. `python3 scripts/jev-judge.py doubt-calibrate --extra <rows> --live --save <scored>` scored each decision on `vercel-gateway`, model `typesafe-ai/jev`, and applied one fixed rule (`DOUBT_RULE` in `jev-judge.py`): fit the threshold on the dev half, then require zero overrides acted on in the held-out half. The confidence question was written once, before any of its scores were seen, and not tuned. Question and evidence text stay out of this repository; the tables below carry ids, splits, outcomes, and scores only.

## Result

Asking Jev for its confidence that the recommendation is right, with the evidence attached, separates overrides from accepted decisions better than asking whether the decision needs a person. It passed calibration once and failed on an identical repeat, so no threshold is written and Jev still shadows.

| Run | Jev's question | Evidence | Ranking, all 98 | Ranking, held-out | Calibration | Threshold | Held-out acted | Overrides acted on |
|---|---|---|---|---|---|---|---|---|
| A | does this need a person? | no | 0.66 | 0.47 | refused | ask at 0.38 | 16 of 47 | 2 |
| B | does this need a person? | yes | 0.70 | 0.48 | refused | ask at 0.34 | 16 of 47 | 2 |
| C | is the recommendation right? | no | 0.75 | 0.60 | refused | act above 0.37 | 19 of 47 | 1 |
| D | is the recommendation right? | yes | 0.80 | 0.76 | **passed** | act above 0.50 | 20 of 47 | 0 |
| D, repeated | is the recommendation right? | yes | 0.78 | 0.68 | refused | act above 0.43 | 27 of 47 | 1 |

"Ranking" is the chance that a random override scores as more doubtful than a random accepted decision: 0.5 is a coin flip, 1.0 is a perfect split. Run A is the first calibration; its held-out ranking was no better than chance.

- **The question matters more than the evidence.** Switching to confidence raised the ranking from 0.66 to 0.75 without evidence. Evidence added a little on top under either question.
- **Jev's scores move between identical runs.** Rescoring the same 98 rows gave a median change of 0.02 and a largest change of 0.11. That was enough to fail: the dev half's highest-scoring override dropped from 0.50 to 0.43, which lowered the threshold, and one held-out override rose from 0.48 to 0.57, past it.
- **Run D's pass is weak evidence even before the repeat.** The held-out half holds 4 overrides. Acting on 20 of its 47 decisions at random would miss all 4 about one time in ten.
- **One pattern, found after looking at all the data:** in both scored runs, no decision above 0.60 was overridden; about 30 of the 98 scored above it. That cut was chosen with every label in view, so it is a lead for the next calibration, not a calibration.

## What this decided

- **Jev's question is now confidence in the recommendation.** `doubt_request` asks whether the recommended option is right: sound on the evidence, and the option the person would choose. A high score acts and a low score asks. The decision record's `evidence` should carry what the person asked for, because the miner's evidence did and the score is calibrated on it.
- **Scores carry the name of the question that produced them.** A log row, a scored file, and a thresholds file record `judgment: recommendation_holds`. A score or threshold from the earlier `needs_person` question is ignored, so a reworded question never calibrates on its predecessor's scale.
- **Jev still shadows.** No threshold is written. The site decides, as before.
- **Open: run-to-run noise.** The calibration rule fits a threshold to one scoring, but a live decision is scored once more, with the same noise. A threshold has to clear that noise, for example by scoring each calibration row more than once and fitting to the highest override score seen. Not built yet.

## Re-running

```bash
python3 .writ/eval/doubt-calibration/mine.py
python3 scripts/jev-judge.py doubt-calibrate --log .writ/state/doubt-calibration/none.jsonl \
  --extra .writ/state/doubt-calibration/labeled.jsonl --live --save .writ/state/doubt-calibration/scored.jsonl
```

`mine.py --no-evidence` writes the rows without evidence, as runs A and C used. Changing the wording in `doubt_request` changes every score: rename `DOUBT_QUESTION` and re-run both steps.

## Scores

Columns A and B score whether the decision needs a person, so higher is more doubtful. Columns C, D, and the repeat score confidence in the recommendation, so lower is more doubtful. Rows are sorted by run D.

| Id | Split | Outcome | A | B | C | D | D repeat |
|---|---|---|---|---|---|---|---|
| `bc8741aba8445ef3` | dev | overridden | 0.72 | 0.88 | 0.07 | 0.08 | 0.09 |
| `2e5292e6c61e7762` | test | as_recommended | 0.39 | 0.56 | 0.63 | 0.08 | 0.07 |
| `cadbccb0dd9584f0` | dev | as_recommended | 0.77 | 0.76 | 0.13 | 0.08 | 0.08 |
| `03a43fe759133a64` | dev | overridden | 0.83 | 0.92 | 0.11 | 0.08 | 0.09 |
| `4f5147ca6a7f0cc9` | dev | as_recommended | 0.47 | 0.58 | 0.26 | 0.08 | 0.10 |
| `c387e38106b51c81` | dev | overridden | 0.49 | 0.91 | 0.37 | 0.14 | 0.12 |
| `7ba2029e23bf780d` | dev | as_recommended | 0.53 | 0.60 | 0.37 | 0.16 | 0.19 |
| `f30fefe577751132` | test | as_recommended | 0.41 | 0.42 | 0.16 | 0.17 | 0.16 |
| `e953dd7edbb06f26` | test | as_recommended | 0.59 | 0.43 | 0.16 | 0.21 | 0.24 |
| `12a8f3f7d1f6e675` | test | as_recommended | 0.72 | 0.76 | 0.14 | 0.22 | 0.20 |
| `3a733cc3ba77ba1b` | test | overridden | 0.47 | 0.51 | 0.23 | 0.22 | 0.23 |
| `6c79d6d8c2585693` | test | as_recommended | 0.52 | 0.65 | 0.13 | 0.23 | 0.22 |
| `288343a996fccc63` | dev | as_recommended | 0.14 | 0.18 | 0.40 | 0.23 | 0.19 |
| `7f90b9ed1584e6c2` | test | as_recommended | 0.29 | 0.30 | 0.67 | 0.23 | 0.28 |
| `fe324820629b7bad` | dev | as_recommended | 0.34 | 0.31 | 0.54 | 0.24 | 0.22 |
| `1a0f94b2205554e2` | dev | as_recommended | 0.53 | 0.76 | 0.59 | 0.24 | 0.23 |
| `b693e9c41bd0166d` | dev | overridden | 0.73 | 0.74 | 0.16 | 0.25 | 0.24 |
| `2350413964c96c64` | dev | as_recommended | 0.67 | 0.69 | 0.24 | 0.26 | 0.22 |
| `d7fbd9579888292f` | dev | as_recommended | 0.30 | 0.63 | 0.67 | 0.27 | 0.29 |
| `c406c1035a1d6ff1` | dev | as_recommended | 0.40 | 0.61 | 0.14 | 0.29 | 0.26 |
| `5aad91c62430e109` | test | as_recommended | 0.52 | 0.68 | 0.26 | 0.29 | 0.27 |
| `2235270692cd1a07` | test | overridden | 0.77 | 0.69 | 0.10 | 0.30 | 0.35 |
| `faec10f684e0f773` | test | as_recommended | 0.88 | 0.74 | 0.08 | 0.31 | 0.32 |
| `7bf950546370a6b0` | test | overridden | 0.13 | 0.15 | 0.42 | 0.32 | 0.33 |
| `a3c9b7e150aac81e` | test | as_recommended | 0.25 | 0.60 | 0.90 | 0.32 | 0.24 |
| `55813916c5f75e7e` | test | as_recommended | 0.80 | 0.74 | 0.11 | 0.32 | 0.35 |
| `5d82f4ea5143cd0c` | dev | as_recommended | 0.83 | 0.44 | 0.03 | 0.32 | 0.35 |
| `6669524189cc8020` | dev | as_recommended | 0.58 | 0.50 | 0.44 | 0.32 | 0.36 |
| `1ddcf0ffc3fbd3fd` | test | as_recommended | 0.39 | 0.38 | 0.46 | 0.33 | 0.32 |
| `63047d92ac51a656` | test | as_recommended | 0.55 | 0.67 | 0.36 | 0.33 | 0.33 |
| `44da7c7f9de94ebd` | test | as_recommended | 0.50 | 0.43 | 0.15 | 0.33 | 0.26 |
| `0ff668c33d5b5562` | dev | as_recommended | 0.47 | 0.53 | 0.42 | 0.34 | 0.35 |
| `906472783d424a7d` | test | as_recommended | 0.43 | 0.46 | 0.45 | 0.36 | 0.45 |
| `82035bd2e6e84e41` | test | as_recommended | 0.38 | 0.25 | 0.23 | 0.37 | 0.26 |
| `45e5d1cef701c2d0` | dev | overridden | 0.55 | 0.49 | 0.15 | 0.38 | 0.38 |
| `6dbf580d705e84d6` | dev | as_recommended | 0.50 | 0.62 | 0.37 | 0.38 | 0.32 |
| `4dafc784ae8a2589` | dev | as_recommended | 0.48 | 0.44 | 0.47 | 0.39 | 0.45 |
| `82d9dd9c58868b26` | test | as_recommended | 0.53 | 0.31 | 0.15 | 0.40 | 0.42 |
| `f23c4fd1fb061814` | dev | as_recommended | 0.27 | 0.31 | 0.71 | 0.40 | 0.35 |
| `ea4c92f58d59c933` | dev | as_recommended | 0.37 | 0.37 | 0.52 | 0.41 | 0.45 |
| `5b7b8c655c62a048` | test | as_recommended | 0.62 | 0.50 | 0.35 | 0.42 | 0.45 |
| `c9d5300117a0176a` | test | as_recommended | 0.54 | 0.40 | 0.22 | 0.43 | 0.45 |
| `dc4e0745c81e3f53` | test | as_recommended | 0.47 | 0.45 | 0.58 | 0.43 | 0.39 |
| `d28b0ba6831e7b0d` | dev | as_recommended | 0.24 | 0.40 | 0.30 | 0.43 | 0.35 |
| `3e20e27679b0c40a` | test | as_recommended | 0.75 | 0.47 | 0.09 | 0.44 | 0.43 |
| `a1653031383340e8` | test | as_recommended | 0.63 | 0.45 | 0.33 | 0.45 | 0.44 |
| `628468472f7305ff` | dev | as_recommended | 0.23 | 0.24 | 0.41 | 0.47 | 0.54 |
| `90d6fb028423e3c9` | dev | as_recommended | 0.60 | 0.56 | 0.54 | 0.47 | 0.46 |
| `8510583678400f27` | test | as_recommended | 0.56 | 0.44 | 0.33 | 0.48 | 0.49 |
| `25df3d6bce5773ab` | dev | as_recommended | 0.70 | 0.63 | 0.44 | 0.48 | 0.52 |
| `8ee5901cbe4bc0da` | test | as_recommended | 0.68 | 0.55 | 0.44 | 0.48 | 0.52 |
| `7767586a8bff40f5` | test | overridden | 0.34 | 0.31 | 0.36 | 0.48 | 0.57 |
| `d2bb0f7501dd0a04` | dev | as_recommended | 0.53 | 0.51 | 0.51 | 0.49 | 0.50 |
| `59c85eab6fe14245` | dev | overridden | 0.38 | 0.34 | 0.30 | 0.50 | 0.43 |
| `8ea0a67f9edae2e6` | test | as_recommended | 0.34 | 0.39 | 0.76 | 0.51 | 0.48 |
| `292234bf39beac07` | dev | as_recommended | 0.35 | 0.34 | 0.57 | 0.51 | 0.50 |
| `a43709bfb9386bd1` | test | as_recommended | 0.59 | 0.74 | 0.09 | 0.52 | 0.60 |
| `ab2026a3f136623f` | dev | as_recommended | 0.17 | 0.28 | 0.73 | 0.52 | 0.54 |
| `88f8fa71bc31a127` | dev | as_recommended | 0.83 | 0.56 | 0.10 | 0.54 | 0.49 |
| `66e6223a60ab8f37` | dev | as_recommended | 0.35 | 0.72 | 0.35 | 0.54 | 0.47 |
| `305cef138688bddc` | dev | as_recommended | 0.38 | 0.27 | 0.41 | 0.55 | 0.52 |
| `23438d9d4dabfe12` | dev | as_recommended | 0.26 | 0.38 | 0.75 | 0.55 | 0.56 |
| `26681acb40d79719` | dev | as_recommended | 0.53 | 0.86 | 0.23 | 0.57 | 0.51 |
| `2595f2d3e2928d2e` | test | as_recommended | 0.38 | 0.66 | 0.22 | 0.59 | 0.50 |
| `0b0484af6b6b7698` | test | as_recommended | 0.29 | 0.37 | 0.30 | 0.59 | 0.60 |
| `593ff8b57bd3818d` | dev | as_recommended | 0.48 | 0.35 | 0.60 | 0.60 | 0.55 |
| `19992d2af5814259` | dev | as_recommended | 0.44 | 0.32 | 0.15 | 0.60 | 0.56 |
| `6ad1cf51a773ba5f` | test | as_recommended | 0.29 | 0.35 | 0.77 | 0.63 | 0.66 |
| `8b7e4d158f063184` | test | as_recommended | 0.72 | 0.60 | 0.13 | 0.63 | 0.59 |
| `c16e593cc469335c` | test | as_recommended | 0.38 | 0.33 | 0.68 | 0.64 | 0.65 |
| `f685dbb4048c4d93` | test | as_recommended | 0.27 | 0.40 | 0.81 | 0.67 | 0.66 |
| `48f7c98d63125e92` | dev | as_recommended | 0.21 | 0.49 | 0.80 | 0.67 | 0.70 |
| `4809e54a9b45ca90` | test | as_recommended | 0.23 | 0.29 | 0.60 | 0.68 | 0.67 |
| `c72a7d7fc1cd748c` | dev | as_recommended | 0.39 | 0.35 | 0.54 | 0.69 | 0.67 |
| `1c082bc9fa3ea509` | test | as_recommended | 0.18 | 0.15 | 0.81 | 0.70 | 0.69 |
| `855214ece56cfb69` | test | as_recommended | 0.28 | 0.26 | 0.33 | 0.70 | 0.69 |
| `45ad5193e9377426` | test | as_recommended | 0.42 | 0.19 | 0.25 | 0.70 | 0.70 |
| `c1621984e70cb4c6` | test | as_recommended | 0.42 | 0.43 | 0.45 | 0.71 | 0.71 |
| `12ec16c3109bf321` | dev | as_recommended | 0.29 | 0.34 | 0.69 | 0.72 | 0.74 |
| `e9776b0064f825d9` | dev | as_recommended | 0.30 | 0.39 | 0.73 | 0.72 | 0.72 |
| `28dff195798b578f` | dev | as_recommended | 0.24 | 0.17 | 0.80 | 0.73 | 0.78 |
| `a6d7b4d24254a021` | dev | as_recommended | 0.07 | 0.07 | 0.96 | 0.74 | 0.71 |
| `44046c1135a8ff07` | test | as_recommended | 0.47 | 0.16 | 0.13 | 0.75 | 0.78 |
| `778173afe9522eae` | test | as_recommended | 0.62 | 0.48 | 0.13 | 0.76 | 0.76 |
| `0b3d276bcbde0b8c` | test | as_recommended | 0.21 | 0.20 | 0.71 | 0.76 | 0.75 |
| `4bbaab95010debef` | test | as_recommended | 0.20 | 0.30 | 0.67 | 0.76 | 0.77 |
| `5a7c53f4249c77d2` | dev | as_recommended | 0.20 | 0.24 | 0.85 | 0.77 | 0.78 |
| `dcd86df87d8e4365` | test | as_recommended | 0.29 | 0.22 | 0.34 | 0.79 | 0.76 |
| `a3a80d7c47090de3` | test | as_recommended | 0.12 | 0.24 | 0.90 | 0.79 | 0.80 |
| `725d3f32ddb0ceec` | dev | as_recommended | 0.13 | 0.30 | 0.81 | 0.79 | 0.77 |
| `4a255bf982a5af76` | dev | as_recommended | 0.09 | 0.07 | 0.85 | 0.80 | 0.80 |
| `949c24cd139045eb` | test | as_recommended | 0.13 | 0.16 | 0.81 | 0.81 | 0.80 |
| `e93d3e241bc8caa4` | dev | as_recommended | 0.13 | 0.15 | 0.85 | 0.82 | 0.80 |
| `995d1f1586fce9dd` | dev | as_recommended | 0.52 | 0.20 | 0.12 | 0.86 | 0.84 |
| `f1c5dc9ac76c7508` | dev | as_recommended | 0.20 | 0.09 | 0.81 | 0.86 | 0.84 |
| `432df2564c1b2f42` | dev | as_recommended | 0.12 | 0.22 | 0.86 | 0.88 | 0.88 |
| `03780907c4ec99e3` | dev | as_recommended | 0.51 | 0.05 | 0.27 | 0.93 | 0.92 |
| `6d95a7f2f30254f8` | dev | as_recommended | 0.43 | 0.27 | 0.22 | 0.93 | 0.93 |

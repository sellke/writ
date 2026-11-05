# Doubt Calibration: Writ's Own Answers (2026-11-05)

> **Question:** can Jev decide whether a decision needs a person ([ADR-033](../../decision-records/adr-033-doubt-gated-autonomy.md))?
> **Data:** every `AskUserQuestion` in this repository's Claude Code transcripts (and its worktrees) that carried exactly one `(Recommended)` option and has a recorded answer. 98 decisions: the maintainer took the recommendation 88 times and overrode it 10 times.
> **Method:** `mine.py` (this folder) extracts the decisions to the gitignored `.writ/state/doubt-calibration/labeled.jsonl`. `python3 scripts/jev-judge.py doubt-calibrate --extra <that file> --live --save <scored file>` scored each one with the `doubt` question (`jev-judge.py` → `doubt_request`) on `vercel-gateway`, model `typesafe-ai/jev`. Only the question and option text was sent. Question text stays out of this repository; the table below has ids, splits, outcomes, and scores only.

## Result

Jev does not yet separate the decisions a person would change from the ones they would not. `doubt-calibrate` refuses to write a threshold:

```
unverifiable
reason: holdout_false_act
jev-judge: unverifiable (holdout_false_act) labels=98 scored=98 ask=0.38 test_acted=16/47 test_false_acts=2 written=0
```

| Split | Decisions | Overridden | Acted at ask 0.38 | Overrides acted on |
|---|---|---|---|---|
| dev (fit) | 51 | 6 | 22 | 0 |
| test (held out) | 47 | 4 | 16 | 2 |

Held out, 2 of the 16 acted-on decisions were overrides (12.5%), against a 10% override rate overall: no better than acting on everything. The high end carries some signal (4 of the 13 decisions scored 0.70 or more were overrides), the low end does not, and the low end is the side that would skip a question.

## What this decided

- **Jev runs first and shadows.** `doubt` calls Jev on every decision the rules pass and logs `p`, but without a calibrated threshold the decision's site decides (`commands/_preamble.md` → Doubt Rule). Labels collected with `doubt-label` refit it; `doubt-calibrate` writes a threshold only when the held-out split shows no false act.
- **The site carries the decision today.** Read by hand, five of the ten overrides were scope or direction calls (how far a CLI goes, which way the roadmap goes, what a feature means, whether a removal ships, whether to supersede a trial); the fallback asks on those. The other five were reversible method calls (cherry-pick or merge, research first or draft, how to record scenarios, how to resolve a refresh, which route); the fallback acts on those, and the decision log records them. By the same hand reading, about 40 of the 98 questions were method calls the fallback would have acted on. This is one reader's classification, not a script's.

## Re-running

```bash
python3 .writ/eval/doubt-calibration/mine.py
python3 scripts/jev-judge.py doubt-calibrate --log .writ/state/doubt-calibration/none.jsonl \
  --extra .writ/state/doubt-calibration/labeled.jsonl --live --save .writ/state/doubt-calibration/scored.jsonl
```

Changing the wording in `doubt_request` changes every score; re-run both steps.

## Scores

| Id | Split | Outcome | p |
|---|---|---|---|
| `a6d7b4d24254a021` | dev | as_recommended | 0.07 |
| `4a255bf982a5af76` | dev | as_recommended | 0.09 |
| `a3a80d7c47090de3` | test | as_recommended | 0.12 |
| `432df2564c1b2f42` | dev | as_recommended | 0.12 |
| `7bf950546370a6b0` | test | overridden | 0.13 |
| `e93d3e241bc8caa4` | dev | as_recommended | 0.13 |
| `949c24cd139045eb` | test | as_recommended | 0.13 |
| `725d3f32ddb0ceec` | dev | as_recommended | 0.13 |
| `288343a996fccc63` | dev | as_recommended | 0.14 |
| `ab2026a3f136623f` | dev | as_recommended | 0.17 |
| `1c082bc9fa3ea509` | test | as_recommended | 0.18 |
| `4bbaab95010debef` | test | as_recommended | 0.20 |
| `5a7c53f4249c77d2` | dev | as_recommended | 0.20 |
| `f1c5dc9ac76c7508` | dev | as_recommended | 0.20 |
| `0b3d276bcbde0b8c` | test | as_recommended | 0.21 |
| `48f7c98d63125e92` | dev | as_recommended | 0.21 |
| `628468472f7305ff` | dev | as_recommended | 0.23 |
| `4809e54a9b45ca90` | test | as_recommended | 0.23 |
| `28dff195798b578f` | dev | as_recommended | 0.24 |
| `d28b0ba6831e7b0d` | dev | as_recommended | 0.24 |
| `a3c9b7e150aac81e` | test | as_recommended | 0.25 |
| `23438d9d4dabfe12` | dev | as_recommended | 0.26 |
| `f685dbb4048c4d93` | test | as_recommended | 0.27 |
| `f23c4fd1fb061814` | dev | as_recommended | 0.27 |
| `855214ece56cfb69` | test | as_recommended | 0.28 |
| `dcd86df87d8e4365` | test | as_recommended | 0.29 |
| `0b0484af6b6b7698` | test | as_recommended | 0.29 |
| `12ec16c3109bf321` | dev | as_recommended | 0.29 |
| `6ad1cf51a773ba5f` | test | as_recommended | 0.29 |
| `7f90b9ed1584e6c2` | test | as_recommended | 0.29 |
| `d7fbd9579888292f` | dev | as_recommended | 0.30 |
| `e9776b0064f825d9` | dev | as_recommended | 0.30 |
| `8ea0a67f9edae2e6` | test | as_recommended | 0.34 |
| `7767586a8bff40f5` | test | overridden | 0.34 |
| `fe324820629b7bad` | dev | as_recommended | 0.34 |
| `66e6223a60ab8f37` | dev | as_recommended | 0.35 |
| `292234bf39beac07` | dev | as_recommended | 0.35 |
| `ea4c92f58d59c933` | dev | as_recommended | 0.37 |
| `305cef138688bddc` | dev | as_recommended | 0.38 |
| `2595f2d3e2928d2e` | test | as_recommended | 0.38 |
| `82035bd2e6e84e41` | test | as_recommended | 0.38 |
| `c16e593cc469335c` | test | as_recommended | 0.38 |
| `59c85eab6fe14245` | dev | overridden | 0.38 |
| `c72a7d7fc1cd748c` | dev | as_recommended | 0.39 |
| `1ddcf0ffc3fbd3fd` | test | as_recommended | 0.39 |
| `2e5292e6c61e7762` | test | as_recommended | 0.39 |
| `c406c1035a1d6ff1` | dev | as_recommended | 0.40 |
| `f30fefe577751132` | test | as_recommended | 0.41 |
| `c1621984e70cb4c6` | test | as_recommended | 0.42 |
| `45ad5193e9377426` | test | as_recommended | 0.42 |
| `906472783d424a7d` | test | as_recommended | 0.43 |
| `6d95a7f2f30254f8` | dev | as_recommended | 0.43 |
| `19992d2af5814259` | dev | as_recommended | 0.44 |
| `44046c1135a8ff07` | test | as_recommended | 0.47 |
| `3a733cc3ba77ba1b` | test | overridden | 0.47 |
| `0ff668c33d5b5562` | dev | as_recommended | 0.47 |
| `4f5147ca6a7f0cc9` | dev | as_recommended | 0.47 |
| `dc4e0745c81e3f53` | test | as_recommended | 0.47 |
| `593ff8b57bd3818d` | dev | as_recommended | 0.48 |
| `4dafc784ae8a2589` | dev | as_recommended | 0.48 |
| `c387e38106b51c81` | dev | overridden | 0.49 |
| `44da7c7f9de94ebd` | test | as_recommended | 0.50 |
| `6dbf580d705e84d6` | dev | as_recommended | 0.50 |
| `03780907c4ec99e3` | dev | as_recommended | 0.51 |
| `6c79d6d8c2585693` | test | as_recommended | 0.52 |
| `995d1f1586fce9dd` | dev | as_recommended | 0.52 |
| `5aad91c62430e109` | test | as_recommended | 0.52 |
| `82d9dd9c58868b26` | test | as_recommended | 0.53 |
| `d2bb0f7501dd0a04` | dev | as_recommended | 0.53 |
| `7ba2029e23bf780d` | dev | as_recommended | 0.53 |
| `26681acb40d79719` | dev | as_recommended | 0.53 |
| `1a0f94b2205554e2` | dev | as_recommended | 0.53 |
| `c9d5300117a0176a` | test | as_recommended | 0.54 |
| `63047d92ac51a656` | test | as_recommended | 0.55 |
| `45e5d1cef701c2d0` | dev | overridden | 0.55 |
| `8510583678400f27` | test | as_recommended | 0.56 |
| `6669524189cc8020` | dev | as_recommended | 0.58 |
| `a43709bfb9386bd1` | test | as_recommended | 0.59 |
| `e953dd7edbb06f26` | test | as_recommended | 0.59 |
| `90d6fb028423e3c9` | dev | as_recommended | 0.60 |
| `778173afe9522eae` | test | as_recommended | 0.62 |
| `5b7b8c655c62a048` | test | as_recommended | 0.62 |
| `a1653031383340e8` | test | as_recommended | 0.63 |
| `2350413964c96c64` | dev | as_recommended | 0.67 |
| `8ee5901cbe4bc0da` | test | as_recommended | 0.68 |
| `25df3d6bce5773ab` | dev | as_recommended | 0.70 |
| `bc8741aba8445ef3` | dev | overridden | 0.72 |
| `12a8f3f7d1f6e675` | test | as_recommended | 0.72 |
| `8b7e4d158f063184` | test | as_recommended | 0.72 |
| `b693e9c41bd0166d` | dev | overridden | 0.73 |
| `3e20e27679b0c40a` | test | as_recommended | 0.75 |
| `cadbccb0dd9584f0` | dev | as_recommended | 0.77 |
| `2235270692cd1a07` | test | overridden | 0.77 |
| `55813916c5f75e7e` | test | as_recommended | 0.80 |
| `88f8fa71bc31a127` | dev | as_recommended | 0.83 |
| `03a43fe759133a64` | dev | overridden | 0.83 |
| `5d82f4ea5143cd0c` | dev | as_recommended | 0.83 |
| `faec10f684e0f773` | test | as_recommended | 0.88 |

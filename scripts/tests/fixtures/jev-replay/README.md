# Jev replay fixtures

`WRIT_JEV_REPLAY=<this dir>` makes `scripts/jev-judge.py` read
`<sha256 of the canonical request body>.json` instead of opening a socket.
pytest and `eval.sh` use only this transport. The canonical body is
`json.dumps(build_body(state, questions, backend), sort_keys=True,
separators=(",", ":"))`. Any change to the state, the question wording, the
question IDs, or the backend's `model` changes the hash, and the old file
stops matching (`replay_miss`).

There are two kinds of file:

- **Live** files were written by `calibrate --live` from real `vercel-gateway`
  responses. Each holds the full response body plus a `writ_recording` object
  (`source: "live"`, `backend`, `recorded_on`, `fixture`). `calibrate` scores
  only these.
- **Synthetic** files were written by hand to drive shadow paths. They carry no
  `writ_recording` object, and `calibrate` never scores them.

## Story 2 probe files

| File (hash) | Backend | Request | Origin |
|---|---|---|---|
| `577735abb4e699090b75299ae23594fc4c3d06d26a6cc997876e0f9eda1c8ecd` | `typesafe` | `probe` on `inputs/state.json` + `inputs/questions.json` | Story 2; see its What Was Built |
| `586660c068e5ad4cd8619ca24c9668e7177b63bb4ef46e488232635aaed72a34` | `vercel-gateway` | same `probe` request | Story 2; see its What Was Built |

## Synthetic spec-findings and ac-shadow files

| File (hash) | Backend | Request | Origin |
|---|---|---|---|
| `da5e253fbb0aef0a6fa39f407fd893b872c42b5e75e3707d8f4abbeeeceace94` | `typesafe` | `spec-findings` on `spec-analyze/story-2-event-creation-payment-flow` | **Synthetic** (Story 3; rehashed in Story 4) |
| `5dfa56b8ad38aa8566d523451e2fdde356e46f8d95a4a5934d25baf740db62c7` | `typesafe` | `spec-findings` on the four legacy `spec-analyze/` stories in one spec | **Synthetic** (Story 3; rehashed in Story 4) |
| `f3866c5ff7d39405d6cfdf5b6cc627657192367db4e0cc705a6a7aa46bf98699` | `typesafe` | `ac-shadow` on `ac-shadow/` (story, tests output, diff, review) | **Synthetic** (Story 5) |

No live model produced these. The request hashes come from the code's own
`spec_request` / `shadow_request` and `build_body` output. The response
bodies drive the shadow paths:

- **Happy (single story):** `contradiction` 0.94, `gap` 0.08, each
  `ambiguity` 0.06. One finding, nothing escalated. This matches the
  fixture's `gold.json` label.
- **Partial (four stories):** contradiction story `contradiction` 0.93;
  ambiguity story criterion 3 `ambiguity` 0.91; gap story `gap` 0.90; clean
  story `gap` 0.50, inside the calibrated gap band (0.29 to 0.72). Every other
  answer is 0.03 to 0.09. Story 4 lowered the old 0.10 and 0.12 answers to
  0.09 so they stay below the calibrated `escalate` values (0.10 for
  contradiction and ambiguity). Result: three findings, and the clean story
  is escalated.
- **ac-shadow (Story 5):** inputs in `ac-shadow/`: a three-criterion story
  (`AC-9.1`..`AC-9.3`), a test output where two criteria pass and the third
  has no test, a diff with two ordinary files plus `.env.local` and
  `deploy/tls.key` (both excluded, `excluded_paths=2`), and an evaluator
  output tagged `[AC-9.1]` satisfied, `[AC-9.2]` satisfied, `[AC-9.3]` not.
  Answers: 0.96, 0.93, 0.07, so every criterion agrees at the 0.9
  `ac_shadow.satisfied` threshold. The secret-file lines carry marker text
  only, never real values.

`input_tokens` and the gateway `cost` values in these files are
placeholders. Their p values say nothing about how Jev scores these stories.

## Live calibration files (Story 4)

There is one file per labeled fixture under `../spec-analyze/`. All were
recorded on 2026-09-25 through `vercel-gateway` (`typesafe-ai/jev`, routing
restricted to `typesafe-ai`). Only fixture content was sent. The fixture
labels are **model-authored**: the coding agent wrote them, not a person.
The split column comes from `../spec-analyze/splits.json`.

### Method

- Question wording was tuned against the `dev` split only. Every example word
  in the questions is generic or taken from dev fixture text. A token audit
  (content words of each question against the words of each split's stories)
  finds no content word that occurs only in test-split fixtures; the only
  test-only tokens left are function words (`both`, `do`, `also`, `up`).
- The 12 `dev` files come from one dev-only trial: `calibrate --live` over a
  copy holding only the dev fixtures. The 12 `test` files were then recorded
  once, with the wording already fixed, and were scored without further
  changes.
- Thresholds are fit on `dev` only (`calibration.rule` in
  `../../../jev-thresholds.json`), then applied unchanged to `test`.

### History and disclosures

- **First calibration withdrawn.** The first Story 4 gap question listed the
  example inputs "a keyword, file, card, link, id, form field, or import row".
  `card`, `id` (a user-supplied identifier), and `import row` occur only in
  the three test-split gap fixtures, so that run's test gap recall was not
  held out. Gate 3 review failed it. Its 24 recordings were deleted, and the
  gap and ambiguity examples were rewritten from dev content: gap uses
  keyword, file, link, token, form field; ambiguity drops `soon`, `charged`,
  `status code`, and "which record wins". Then everything was re-recorded as
  described above.
- **A dev clean fixture was edited after a live run.**
  `synthetic-clean-api-rate-limit` AC-4.1 read "then each request is served
  normally". In the first dev wording trial, an earlier ambiguity variant
  ("does the Then use a word with no stated rule") scored that criterion 0.81;
  two other variants in the same request scored it 0.12 and 0.17. The
  ambiguity wording finally used was never asked on the pre-edit text, so its
  pre-edit score is unknown. "Normally" is genuinely vague, so the criterion
  was changed to "then no request receives a `429` response" to make the
  clean label true. Every recording here was made after that edit.

| File (hash) | Fixture | Split | Origin |
|---|---|---|---|
| `81b646ff952bf670418e305d4868ea04fa87da0c5a173521f8079e31c0b82859` | `story-2-event-creation-payment-flow` | dev | **Live** |
| `2274ea80e146cd83503ee7da0c10a349204487fbaa9307c56572f7ad38048870` | `story-3-fee-sharing-pro-exemption` | dev | **Live** |
| `6c8218db6cca559e1e18b25122568e515af25a4f7e31faecf8e2adbb97d77b8b` | `story-3-settlement-view-share-link` | dev | **Live** |
| `ccbd6901f88ad9bdf4c74f495f76ec78a1c714488cc62f8f4cdd4b98af7a4e0c` | `story-4-messaging-migration-quick-split-guard` | dev | **Live** |
| `48249469d12d089c76b94a234fae836fe128de7cb6ee2755a0ff93b6d4209972` | `synthetic-ambiguity-alert-burst` | dev | **Live** |
| `292991da93627d287147a7553288767df04f3ce8b7e74f80531c5666daa3b29f` | `synthetic-ambiguity-cart-merge` | test | **Live** |
| `7f6494d491b5ab0174a8bc2a3574f003e14941ed8a245e71784233c0beb809ab` | `synthetic-ambiguity-discount-rounding` | test | **Live** |
| `c0a4d1c9cfadee05fd7ad167cf93862f513e6ed89b5a8a1d04bcd525fb95a7aa` | `synthetic-ambiguity-inactive-projects` | test | **Live** |
| `feb3aba0ee76298549a956a57716b519ca1f09ae3cbf7de0f82db4c23bb69759` | `synthetic-ambiguity-relevant-orders` | dev | **Live** |
| `d8e3a6700d85eeaf3f33b9b3549cdfaecd8e676c957de63b2756d742d1af9319` | `synthetic-clean-api-rate-limit` | dev | **Live** |
| `960275a13b0dfac9670b352aa8ea80d13a20d6c65d460b8db6ef13e2cf95c664` | `synthetic-clean-dark-mode` | test | **Live** |
| `38061286f157ed1691cd6a0920012cb87a9231e19838d933b44c483c0a1c78a2` | `synthetic-clean-email-verification` | test | **Live** |
| `44621ccdc43b31f65f9fd968f46d1074901163e4c6a6527d12f9379e46c8170c` | `synthetic-clean-task-due-dates` | test | **Live** |
| `bb65177bdd1c510f3f957bb562423e51881564dfff850ed881e205440eac998f` | `synthetic-clean-workspace-rename` | dev | **Live** |
| `3e550f98ce81d238fbe7d980f1706e6ba86806d866fd903e86b16090d32c88a2` | `synthetic-contradiction-account-deletion` | test | **Live** |
| `eeb6368388e431a9be2328403d5234c9a0bdc9698cb15723d7da877a51c120f0` | `synthetic-contradiction-export-header` | dev | **Live** |
| `31be57f52ad75c1e5718b2dbb04beefc05bb772a459b4ef066bb4c945c3100df` | `synthetic-contradiction-invite-expiry` | test | **Live** |
| `1849d72eff408077b016cecbebbdecf9949b54df1fbf0987b6e5ad73403a899a` | `synthetic-contradiction-session-timeout` | dev | **Live** |
| `76e0d9207210b96706b830cba5d0cae90b333465f3c0354f4019ba23943df5af` | `synthetic-contradiction-webhook-retries` | test | **Live** |
| `bd5eb6e2049debf33ba1f7a00c18895adc4402e7648362fcc0ba789b92f664b2` | `synthetic-gap-avatar-upload` | dev | **Live** |
| `04f1a340c4a51e12242b8bbc53136607ce5adadfa62fa6cdeb5bbc0221787b4c` | `synthetic-gap-card-declined` | test | **Live** |
| `d0eb81926bfe775644b11586800287c72d90e74636e17603ca7a3851141211ee` | `synthetic-gap-csv-import` | test | **Live** |
| `0ca69bca1f24ac51b7d5fb2361fc8509cafd763672da37ac723920d87cc9b91c` | `synthetic-gap-profile-endpoint` | test | **Live** |
| `17ebe77f4b9ae5774328a5ff64873174309284643150ae23536cc9617e593b98` | `synthetic-gap-search-no-results` | dev | **Live** |

Score them offline (no network):

```bash
python3 scripts/jev-judge.py calibrate --fixtures scripts/tests/fixtures/spec-analyze \
  --backend vercel-gateway            # add --write-thresholds to rewrite jev-thresholds.json
```

## Regenerating

After changing the question wording or the state shape:

1. Rebuild each synthetic file's hash from the code, then write a response
   with one `{"type": "noul", "noul": p}` answer per question ID:

   ```python
   state, questions, index = jj.spec_request(jj.load_stories(spec_dir))
   body = jj.build_body(state, questions, jj.BACKENDS[backend])
   name = jj.request_hash(jj.canonical_body(body)) + ".json"
   ```

   For `ac-shadow`, build the request from `story_criteria`, `slice_diff`,
   and `shadow_request` instead (see
   `test_ac_shadow_replay_fixture_is_keyed_by_build_body`).
2. Re-record the live files. Use a scratch repo whose `.writ/config.md` has
   `- **Judgment Provider:** vercel-gateway`. Export `AI_GATEWAY_API_KEY` and
   unset `WRIT_JEV_REPLAY`. Then run
   `calibrate --fixtures scripts/tests/fixtures/spec-analyze --repo <scratch> --live`,
   which requests only the fixtures that have no live file. Run it again
   offline with `--write-thresholds`. Delete the stale files and update the
   tables above.

Until every recording matches, `test_spec_findings_fixtures_are_keyed_by_build_body`
and `test_every_fixture_has_a_committed_live_recording` fail and name the
missing file.

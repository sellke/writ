# Jev replay fixtures

`WRIT_JEV_REPLAY=<this dir>` makes `scripts/jev-judge.py` read
`<sha256 of the canonical request body>.json` instead of opening a socket.
pytest and `eval.sh` use only this transport. The canonical body is
`json.dumps(build_body(state, questions, backend), sort_keys=True,
separators=(",", ":"))`. Any change to the state, the question wording, the
question IDs, or the backend's `model` changes the hash, and the old file
stops matching (`replay_miss`).

## Files

| File (hash) | Backend | Request | Origin |
|---|---|---|---|
| `577735abb4e699090b75299ae23594fc4c3d06d26a6cc997876e0f9eda1c8ecd` | `typesafe` | `probe` on `inputs/state.json` + `inputs/questions.json` | Story 2; see its What Was Built |
| `586660c068e5ad4cd8619ca24c9668e7177b63bb4ef46e488232635aaed72a34` | `vercel-gateway` | same `probe` request | Story 2; see its What Was Built |
| `586fb8600c258bce667161cdf3e48d72da814ef2159ae1c71a37a2b650e5ce7e` | `typesafe` | `spec-findings` on `spec-analyze/story-2-event-creation-payment-flow` | **Synthetic** (Story 3) |
| `ab84393bf3b3f2e3020a79950f35ecc5e11ffbf222e909b7609df03ed83e9284` | `vercel-gateway` | `spec-findings` on `spec-analyze/story-2-event-creation-payment-flow` | **Synthetic** (Story 3) |
| `93091fc5d967ea8b8e71dd87a6ed89023b4f93c30f8078cf5e3566c4bec38f74` | `typesafe` | `spec-findings` on all four `spec-analyze/` fixture stories in one spec | **Synthetic** (Story 3) |
| `f3866c5ff7d39405d6cfdf5b6cc627657192367db4e0cc705a6a7aa46bf98699` | `typesafe` | `ac-shadow` on `ac-shadow/` (story, tests output, diff, review) | **Synthetic** (Story 5) |

## Synthetic recordings

The three `spec-findings` files and the `ac-shadow` file are synthetic. No live model produced them.
The request hashes come from the code's own `spec_request` and `build_body`
output. The response bodies were written by hand to drive the Story 3 shadow
paths:

- **Happy (single story):** `contradiction` 0.94, `gap` 0.08, each
  `ambiguity` 0.06. One finding, nothing escalated. This matches the
  fixture's `gold.json` label.
- **Partial (four stories):** contradiction story `contradiction` 0.93;
  ambiguity story criterion 3 `ambiguity` 0.91; gap story `gap` 0.90; clean
  story `gap` 0.50, which is inside the default escalation band. Every
  other answer is 0.03 to 0.12. Result: three findings, and the clean story
  is escalated.

- **ac-shadow (Story 5):** inputs in `ac-shadow/`: a three-criterion story
  (`AC-9.1`..`AC-9.3`), a test output where two criteria pass and the third
  has no test, a diff with two ordinary files plus `.env.local` and
  `deploy/tls.key` (both excluded, `excluded_paths=2`), and an evaluator
  output tagged `[AC-9.1]` satisfied, `[AC-9.2]` satisfied, `[AC-9.3]` not.
  Answers: 0.96, 0.93, 0.07, so every criterion agrees at the 0.9
  `ac_shadow.satisfied` threshold. The secret-file lines carry marker text
  only, never real values.

`input_tokens` and the gateway `cost` values are placeholders. The p values
say nothing about how Jev actually scores these stories. Story 4
(`calibrate --live`) records real responses and must not score thresholds
against these files.

## Regenerating

After changing the question wording or the state shape, rebuild each hash
from the code:

```python
state, questions, index = jj.spec_request(jj.load_stories(spec_dir))
body = jj.build_body(state, questions, jj.BACKENDS[backend])
name = jj.request_hash(jj.canonical_body(body)) + ".json"
```

For `ac-shadow`, build the request from `story_criteria`, `slice_diff`,
and `shadow_request` instead (see
`test_ac_shadow_replay_fixture_is_keyed_by_build_body`). Then write a
response with one `{"type": "noul", "noul": p}` answer per question ID. `test_spec_findings_fixtures_are_keyed_by_build_body` fails,
naming the missing file, until every recording matches.

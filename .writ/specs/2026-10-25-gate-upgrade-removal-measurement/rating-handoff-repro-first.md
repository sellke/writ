# Rating Handoff: Repro First Substitute Trial

> Trial: [`.writ/eval/gate-upgrade-trial/2026-11-09-repro-first-substitute-trial.json`](../../eval/gate-upgrade-trial/2026-11-09-repro-first-substitute-trial.json)
> Sheet: [`.writ/eval/gate-upgrade-trial/labeling-sheet-repro-first.md`](../../eval/gate-upgrade-trial/labeling-sheet-repro-first.md)
> Baseline: [`.writ/eval/gate-upgrade-trial/2026-11-09-repro-first-substitute-baseline.json`](../../eval/gate-upgrade-trial/2026-11-09-repro-first-substitute-baseline.json)
> Run: 2026-11-09 (Story 5). The lane did not label.

## Result

Repro First was exercised on all three stories. Each repro failed at the parent commit and passed at the story commit, so no repro yields a key and there are **zero upgrade-only findings**. The sheet has no `label:` and no `ack:` fields.

`report` prints `unverifiable` with `reason: repro-first unlabeled 0`. That is only because `labeled_by` is still null (technical-spec § Verdict step 4). Once Story 6 runs `label`, `report` gives `remove` (exercised, no valid catch).

| Story | Fix commit | Kind | Repro targets | At parent | At story commit | Result |
|---|---|---|---|---|---|---|
| `2026-09-20-custom-covers-not-saving/story-1-production-cover-origin-save` | `ed15bba` | bug | AC-1.1 | fail | pass | fixed |
| `2026-04-16-event-limit-upgrade-modal-wiring/story-1-wire-limit-error-to-upgrade-modal` | `d0f5f1a` | bug | AC-1.1 (AC1, DEV-015) | fail | pass | fixed |
| `2026-03-03-days-present-stretch-miscount/story-1-fix-counting-logic` | `403a9cc` | bug | AC-1.1 (reading order, DEV-015) | fail | pass | fixed |

"Fixed" means the shipped fix made the repro pass. Under Business Rule 5, only a repro that still fails at the story commit counts as a catch.

## Who labels, and how

The maintainer delegated this run's labels to the assistant on 2026-11-09 (spec.md Business Rule 9). With zero findings there is nothing to judge. Story 6 still has to set `labeled_by`:

```bash
python3 .writ/eval/gate-upgrade-trial/gate-upgrade-trial.py label --trial .writ/eval/gate-upgrade-trial/2026-11-09-repro-first-substitute-trial.json --sheet .writ/eval/gate-upgrade-trial/labeling-sheet-repro-first.md --labeled-by "Adam Sellke (delegated to assistant)"
```

```bash
python3 .writ/eval/gate-upgrade-trial/gate-upgrade-trial.py report --trial .writ/eval/gate-upgrade-trial/2026-11-09-repro-first-substitute-trial.json
```

Honor-system rule, unchanged: the labeler does not open the trial JSON or the raw outputs under `.writ/state/gate-upgrade-trial/<slug>/` before labeling. The sheet header still says "See rating-handoff.md". The scoped sheet reuses the unscoped header so unscoped output stays byte-identical; this file is the one it means.

## What the "current gates" arms found

These findings came from the `off-1` and `off-2` reviews. They don't change the Repro First verdict; they are recorded for completeness:
- **Cover story:** `off-1` FAIL with one Major key: the production `NEXTAUTH_URL` was never measured, and the contract's env check is missing. `off-2` PASS (same point, rated Minor).
- **Event-limit story:** both PASS. `off-2` notes that the `apiCall` `console.error` still fires (Medium drift).
- **Stretch story:**
  - `off-1` PASS.
  - `off-2` FAIL on a Major finding with no executed evidence, so advisory under the evidence gate. The finding: stale integration tests under `tests/integration/`, which sit outside the change set.

Neither "current gates" run produced a key the repro arm also raised.

## Caveats

- **Leans toward remove.** Accepted fixes rarely still fail at the story commit, so this design can almost never produce a catch. A `remove` here means "no shipped fix in the sample was incomplete". It does not mean "repro-first adds nothing".
- **Three stories.** The fourth candidate (`73f34d4`) fails the prepare-input clause (DEV-014). One run per arm.
- **Legacy AC IDs.** Two stories have no `AC-N.M` IDs and are mapped by reading order (DEV-015).
- **Cherry-pick conflict.** The cover repro (`a42153b`) conflicted with the fix commit's own edit to `lib/__tests__/event-cover-http.test.ts`. It was resolved as a union: the fix commit's tests were kept and the repro test appended. The other two repros applied cleanly.
- **Arm isolation (DEV-017).**
  - The repros were applied to `checkout/` while two review arms (cover `off-1`, stretch `off-2`) were still reading it. Both noticed the extra test, reviewed `HEAD` and `diff.patch`, and ignored the working tree.
  - The cover repro arm also made HTTP requests to the live `yuss.app` and `www.yuss.app` hosts to see the redirect.
- **Transcribed outputs.** Review agents cannot write files. The orchestrator saved each reply to `out-<arm>.md` in the run directory. Every `### Issues Found` and `### Drift Analysis` section is kept in full; some Checklist and Recommendations text was shortened.
- **Environment.** Dependencies came from `pnpm install --frozen-lockfile --prefer-offline --ignore-scripts` in each temporary checkout, and `parent/` linked to the same `node_modules`. Each fix commit's own tests passed at its story commit before any arm ran.
- **yuss.** HEAD, refs, and `git status --porcelain` were identical before and after (`yuss: unchanged`). yuss has the maintainer's own uncommitted edits; the run did not touch them.

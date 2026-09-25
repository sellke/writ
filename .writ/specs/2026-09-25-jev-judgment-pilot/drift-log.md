# Drift Log

> Spec: .writ/specs/2026-09-25-jev-judgment-pilot/
> Created: 2026-09-25
> ⚠️ Append-only — do not modify existing entries.

---

## Story 1: ADR-027 and Opt-in Resolution — Drift Report

> Run: 2026-09-25
> Overall Drift: Small

### Deviations

#### [DEV-001] Key set with no config line reports `no_config_line`, not `provider_disabled`
- **Severity:** Small
- **Spec said:** Task 1.1, the story Notes, and the technical-spec §5 "Resolve opt-in" row say a key with no config line gives `provider_disabled`. AC-1.3 and technical-spec §1 map a missing line to `no_config_line`.
- **Implementation did:** `no_config_line`. The provider stays disabled and no request is built.
- **Reason:** The acceptance criterion controls, and Story 6's setup prompt fires on `no_config_line`. The intent (a key alone never enables) holds.
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite.md "Nil input" shadow path and the technical-spec §5 "Resolve opt-in" row now name `no_config_line` for a missing line and `provider_disabled` for `none` or an unknown value. The spec.md Success Criteria wording is unchanged (spec.md is never auto-modified).

#### [DEV-002] `vercel-gateway` status outputs add `reason: model_unpinned`
- **Severity:** Small
- **Spec said:** AC-1.3: `pass` and `reason: enabled`.
- **Implementation did:** The primary reason comes first, then `reason: model_unpinned` on every `vercel-gateway` output.
- **Reason:** Business Rule 5 and technical-spec §1 require `model_unpinned` on every gateway output.
- **Resolution:** Auto-amended
- **Spec amendment:** None needed; this matches Business Rule 5.

#### [DEV-003] Summary adds `key_env=<var>` and `export=<var>`
- **Severity:** Small
- **Spec said:** Summary `backend=<name> model=<backend model>`; `no_api_key` names the env var to export.
- **Implementation did:** Adds `key_env=` on pass and `export=` on `no_api_key`.
- **Reason:** Operator clarity. Only variable names are printed, never values; tests confirm this.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-004] `--repo` pointing at a non-directory exits 2
- **Severity:** Small
- **Spec said:** Exit 2 for usage errors; this case is not specified.
- **Implementation did:** stderr message, exit 2.
- **Reason:** A bad path argument is a usage error under Business Rule 2.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-005] No test pins the decision-log line
- **Severity:** Small
- **Spec said:** AC-1.5: the closing commit appends a `jev-pilot:` line.
- **Implementation did:** The line is appended and included in the closing commit; no test checks it.
- **Reason:** The AC requires the line, not a test. It is a workspace artifact.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

## Story 2: Client Transport and eval Check — Drift Report

> Run: 2026-09-25
> Overall Drift: Medium

### Deviations

#### [DEV-006] `jev-thresholds.json` not shipped by install.sh / update.sh
- **Severity:** Small
- **Spec said:** "`install.sh` copies `scripts/*`". The thresholds file "ships beside the script". Task 2.5: ship alongside `jev-judge.py`.
- **Implementation did:** The file sits in `scripts/`, but `is_shippable_script` (install.sh:922–937, update.sh:569) ships only `*.py`/`*.sh`. The loader falls back to §4 defaults and adds `thresholds_missing`.
- **Reason:** A false spec assumption. Installed behavior is correct while the defaults equal the shipped file. Story 4 adds the file to both installers' shipped set.
- **Resolution:** Auto-amended
- **Spec amendment:** None to spec-lite. Carried to Story 4 as an installer task.

#### [DEV-007] New `probe` subcommand not in technical-spec §1
- **Severity:** Medium
- **Spec said:** Subcommands are `status`, `setup`, `spec-findings`, `calibrate`, `ac-shadow`, and `shadow-report`. The eval check runs replay-mode `spec-findings`.
- **Implementation did:** Added `probe --state-file --questions-file [--backend]`. It runs live only when the double opt-in holds, and replay always wins. The eval check uses `probe` under replay because `spec-findings` lands in Story 3.
- **Reason:** Story 2 needed a CLI surface for the transport before Story 3 exists. Business Rule 1 is enforced on the live path.
- **Resolution:** Warned
- **Spec amendment:** None (spec.md is never auto-modified). Story 3 decides whether eval moves to `spec-findings`.

#### [DEV-008] Error-status mapping wider than the spec
- **Severity:** Small
- **Spec said:** 401 → `auth_error`; 422 or gateway 404 → `request_invalid`; everything else → `transport_error`.
- **Implementation did:** 403 → `auth_error`. Every other 4xx except 429 → `request_invalid`.
- **Reason:** A 4xx is a client-side rejection. Every outcome stays `unverifiable`, exit 0.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-009] Retry schedule is 1 s then 2 s; `retry-after` capped at 30 s
- **Severity:** Small
- **Spec said:** 3 attempts; sleep `retry-after`, else 1, 2, 4.
- **Implementation did:** Two sleeps (1 s, 2 s), which is all 3 attempts allow. `retry-after` is capped at 30 s. A non-numeric value falls back to the backoff.
- **Reason:** A third sleep cannot happen with 3 attempts. The cap prevents a hung run.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-010] `judge()` takes `backend`, `environ`, `transport`, `sleep` and returns a `Judgment`
- **Severity:** Small
- **Spec said:** `judge(state, questions) -> response | Unverifiable(reason)`.
- **Implementation did:** `judge(state, questions, backend, environ, transport=None, sleep=...) -> Judgment`. Server `model`/`cost` are sanitized once there (`_safe_token`); the raw model is used only for the pin check.
- **Reason:** Injectable transport and sleep for tests. The Gate 3 iteration-1 security fix centralizes sanitizing.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-011] New informational reason `thresholds_missing`
- **Severity:** Small
- **Spec said:** Not in the technical-spec §1 table.
- **Implementation did:** A missing thresholds file adds `thresholds_missing`. The verdict is unchanged.
- **Reason:** Makes a lost calibrated file visible (DEV-006).
- **Resolution:** Auto-amended
- **Spec amendment:** spec-lite Error Handling line added.

## Story 3: Spec-Findings Producer and Step 2.6c Cascade — Drift Report

> Run: 2026-09-25
> Overall Drift: Medium

### Deviations

#### [DEV-012] Replay-only `--backend` flag on `spec-findings`
- **Severity:** Small
- **Spec said:** §1 args `--spec PATH --out FILE [--repo .]`.
- **Implementation did:** Added `--backend`, replay-only as on `probe` (DEV-007). Without replay it exits 2.
- **Reason:** Lets eval replay without a config line. It cannot bypass Business Rule 1.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-013] Every non-pass outcome writes `[]` plus an escalate-all sidecar
- **Severity:** Small
- **Spec said:** §5: `state_too_large` escalates the story; a transport error runs the full orchestrator pass.
- **Implementation did:** Any unverifiable or fail outcome escalates every story. With one request per spec, the whole spec is over budget.
- **Reason:** The most conservative reading of Business Rule 3.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-014] A broken thresholds file exits 2 before any request
- **Severity:** Small
- **Spec said:** Unspecified (a missing file → defaults, DEV-011).
- **Implementation did:** A malformed or out-of-range band exits 2. `create-spec` falls back to the full pass, and eval raises a finding.
- **Reason:** A corrupt committed thresholds file must be visible.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-015] Summary adds `findings=` and `answers=` counts
- **Severity:** Small
- **Spec said:** Model, input tokens, and judged/escalated counts.
- **Implementation did:** Adds integer counts. No server text.
- **Reason:** Informational.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-016] Retry and transport scenarios use an injected fake HTTP, not replay
- **Severity:** Small
- **Spec said:** AC-3.5 says replay-mode runs cover retry and transport failure.
- **Implementation did:** Happy, partial, and empty use replay. Retry and transport use a fake HTTP under the socket guard.
- **Reason:** Replay serves 200 bodies only. The Test Strategy allows a fake handler for status codes.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-017] AC tag tails stripped from the text sent to Jev; one generic Step 2.9 note form
- **Severity:** Small
- **Spec said:** State holds each story's criteria; Step 2.9 carries a `jev:` note.
- **Implementation did:** Strips the `` `[AC-N.M]` `` tails (IDs are kept code-side for `ac_ids`). Uses one note template with a `jev: <verdict> (<reason>)` fallback.
- **Reason:** Intent preserved; less noise for the model.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-018] verify-spec 3g lacked create-spec's exit-1/2 fallback
- **Severity:** Small
- **Spec said:** AC-3.4: the same conditional as Step 2.6c.
- **Implementation did:** The evaluator found the fallback clause missing. The orchestrator added "if it exits 1 or 2, judge every story" before commit, and re-pinned the verify-spec SHA and size ratchet (10863 → 10902).
- **Reason:** Exit 2 writes no sidecar, so a stale sidecar could have shrunk the pass.
- **Resolution:** Auto-amended
- **Spec amendment:** None.

#### [DEV-019] Gap and ambiguity questions show no separation on live Jev; Story 4 may reword questions
- **Severity:** Medium
- **Spec said:** Story 3 fixes the request structure; Story 4 calibrates thresholds.
- **Implementation did:** Raw live p values (vercel-gateway, one fixture per class) were:
  - contradiction: 0.48 on contradiction-gold vs ≤0.12 elsewhere. This separates.
  - gap: highest on clean-gold (0.61 vs 0.47). Inverted.
  - ambiguity: lowest on ambiguity-gold (0.29). Inverted.

  At the 0.85/0.35 thresholds every story escalates, so the cascade stays safe but saves nothing.
- **Reason:** Thresholds cannot fix an inverted signal.
- **Resolution:** Warned. Story 4 is authorized to reword the gap and ambiguity (and, if needed, contradiction) question instructions and criteria in `_story_questions` / `_criterion_question`, and to regenerate the synthetic replay recordings. Story 3's structural contract (one request, Noul per story and per criterion, schema, sidecar) stays fixed.
- **Spec amendment:** None to spec.md. This is an autonomous scope decision; it is reversible.

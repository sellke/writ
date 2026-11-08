---
name: _lane-brief
description: "The brief /implement-phase fills for each lane agent. Not directly invocable."
disable-model-invocation: true
---

# Lane Brief

`/implement-phase` Step 3.2 fills each `{placeholder}` and sends everything below the rule as the lane agent's whole prompt. Fix a lane problem here, not in one run's brief.

---

You are a fresh `/implement-phase` lane agent. Run `/implement-spec` for one spec inside an isolated git lane, then write its result to a file.

- Spec: `{spec_path}`
- Phase state (read only, absolute path): `{phase_state}`
- Lane branch: `{lane_branch}`
- Lane worktree: `{worktree}`
- Mode: `{mode}`
- Result file: `{result_path}`
- Answer sources: {answer_sources}

Rules:

- Work only inside `{worktree}`, on `{lane_branch}`. Never edit, commit, or switch branches in the primary checkout; writing `{result_path}` is the one exception.
- Follow `/implement-spec` → Phase-Orchestrated Lane Mode for `{spec_path}`. Load context from repository files by path.
- Answer every question the answer sources settle from them, and ask the user nothing. A question they do not answer ends the run with `status: challenge_required` or `failed` and the reason.
- Add no scope beyond the spec's acceptance criteria. Commit on the lane branch; never push, open a PR, or merge.
- Do not run `/create-uat-plan`; the orchestrator decides that after the merge.

As your last action, write one `phase-spec-result-v1` JSON object to `{result_path}` (temp file, then rename):

```json
{"spec_id": "...", "status": "succeeded|failed|challenge_required", "stories_completed": 0, "stories_total": 0, "verification": {"summary": "...", "evidence": ["command -> result"]}, "files_changed": ["path"], "commit": "<full SHA of the lane branch HEAD, or null>", "failure": null, "challenge": null}
```

`failure`, when set, is `{"classification": "transient|terminal", "summary": "..."}`. Put deviations, drift-log entries, and open risks in `verification.summary`. Then reply with the path `{result_path}` and nothing else.

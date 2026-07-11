# Eval `recommended-spec-implementation` Check Is Spawn-Heavy (Looked Like a Hang)

> **Type:** Improvement
> **Priority:** Normal
> **Effort:** Medium
> **Created:** 2026-07-11
> **Status:** Mitigated 2026-07-11 (fixture-setup spawns cut; one optional lever remains)
> **spec_ref:** _(set automatically when promoted via `/create-spec --from-issue`)_

## TL;DR

The `recommended-spec-implementation` check in `scripts/eval.sh` spawns ~1,100+
subprocesses in a single check (git fixtures + the `recommend-state.py` helper +
`install.sh`/`update.sh`/`unlink.sh` sandbox runs across all three platforms,
each doing a real `git clone`). This is fine on native hardware but degraded
into an apparent 0%-CPU hang under the old x86_64 Python 3.7.3 running through
Rosetta. The hard hang is resolved (native arm64 Python 3.14), and the
fixture-setup spawns have since been cut via a one-time template + copytree in
both Python phases (see Mitigation below). One optional lever remains for
maximum Rosetta resilience.

## Root Cause (traced 2026-07-11)

- **Not git.** A `git` shim logging START/END for every invocation recorded
  ~1,130 git calls, all returning `rc=0`. No git process ever persisted.
- **Not the helper.** The process tree showed the check's Python spawning
  `recommend-state.py` (`helper_run`), both actively consuming CPU — never idle.
- **Aggregate spawn cost.** The check re-clones a source repo per platform per
  sandbox scenario and rebuilds many git fixtures (`init`/`add`/`commit`). Under
  Rosetta, each cross-arch `fork`/`exec` of native-arm64 `git` from x86_64
  Python paid a translation tax that lived in kernel/Rosetta time (so `sample`
  showed ~0% user CPU → "hang"). A single-spawn repro completed instantly; only
  the ~1,100× aggregate exposed the pathology.

## Current State (after native Python 3.14)

- `--check=recommended-spec-implementation`: completes in ~75s, 36/36 static
  assertions pass.
- Full `all` eval: completes in ~105s, 0 findings, 0 run errors.

## Expected Outcome

- Reduce redundant subprocess spawns so the check is resilient on slow or
  emulated environments, not just native hardware.
- Reuse a single git-scaffolded fixture template instead of re-running
  `init`/`config` per fixture (biggest realized lever).
- Emit a progress heartbeat so a slow run is visibly progressing, not hung.
- Optionally cap/parallelize fixture builds, or gate the heaviest sandbox
  scenarios behind a flag so the default Tier 1 run stays fast.

## Mitigation Implemented (2026-07-11)

Both Python phases of the check now build the git repo once and `copytree` it
per fixture, and both emit stderr heartbeats:

- `scripts/eval.sh` (inline scenario phase): one fully-committed fixture
  template, copied per `fixture()` call; heartbeats for template build, sandbox
  source build, and each platform in the install/update/unlink loop.
- `scripts/eval-recommend-state-adversarial.py`: one bare (init + config)
  template copied per `fixture()` call — content still committed per fixture
  because scenario contents vary; one heartbeat marking the adversarial suite.

Measured (native arm64, git-shim spawn count):

| Metric | Before | After |
|---|---|---|
| `git init` spawns | 40 | 3 |
| `git config` spawns | 80 | 6 |
| total git spawns | ~1,364 | ~1,253 |
| scenarios | pass | pass (36/36, 0 findings) |
| wall time (native) | ~70s | ~70s |

Native wall time is unchanged by design — spawns are cheap natively, so the win
is spawn-count resilience against the Rosetta amplification that caused the
original apparent hang (fixture setup spawns dropped from ~120 to ~9). Under
Rosetta (~200ms+/spawn) that is tens of seconds saved.

## Remaining Optional Lever

- The adversarial suite still emits ~39 `commit -m fixture` spawns (one content
  commit per fixture). Keying fully-built templates by
  `(baseline_story_1, totals)` would collapse those ~39 add+commit pairs to ~4,
  saving another ~70 spawns. Deferred: adds caching complexity for a path that
  is already fine natively; pull forward only if maximum Rosetta resilience is
  needed.
- Wall-time floor is dominated by `install.sh`/`update.sh`/`unlink.sh` internals
  and their `git clone`s. Reducing those means editing the product install
  scripts — out of scope for an eval-robustness change.

## Relevant Files

- `scripts/eval.sh` — `check_recommended_spec_implementation` (~line 673),
  `fixture()` / `_build_fixture_template()` (~line 953), `beat()` heartbeat
  helper, install/update/unlink sandbox scenarios (~lines 1500–1625).
- `scripts/eval-recommend-state-adversarial.py` — `fixture()` /
  `_bare_repo_template()` (~line 57).
- `scripts/recommend-state.py` — the `helper_run` target invoked per transition.

## Notes

- Environmental prerequisite already handled: use native-arch Python (arm64 on
  Apple Silicon), not an x86_64 interpreter under Rosetta.

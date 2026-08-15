# Drift Log — Git-Notes Audit Channel

> Parent: [`spec.md`](spec.md)

Deviations recorded against this spec. The spec shipped and was archived on
2026-07-18; entries below are post-archive defect corrections found while the
channel was in use.

| ID | Story | Severity | Title |
|---|---|---|---|
| DEV-007 | — | Medium | The sync refspec silently destroyed unpushed local notes |

---

## DEV-007 — The sync refspec silently destroyed unpushed local notes

**Severity:** Medium · **Found:** 2026-08-15, while shipping
`2026-08-14-script-backed-quality-gates` · **Fixed:** 2026-08-15

**What happened.** `install.sh` configured the audit channel's fetch refspec as
`+refs/notes/writ:refs/notes/writ`. Because Writ writes audit notes to
`refs/notes/writ` *locally*, and the `+` forces the update, any `git fetch`
overwrote the local notes ref with the remote's — discarding every note added
since the last push. Silently: no rejection line, no non-zero exit, nothing a
user would notice.

It was found by tripping it. `/ship` attached the spec digest for
script-backed-quality-gates to the landed commit, then ran `git fetch` to check
whether the notes ref was fast-forwardable before pushing. The fetch destroyed
the note it was about to verify. The digest was re-attached and pushed, and the
ancestry check that "passed" had by then been rendered meaningless — it compared
the remote's ref against itself.

**Why the original design missed it.** The spec treated notes sync as a
transport concern and reused the shape of a branch refspec, where `+` is
routine because local branches are not written by the same tooling that fetches
them. Notes refs break that assumption: they are not fast-forward-only, and here
both sides write to the same ref name. The spec also never specified a
reconciliation step, so the force flag *was* the reconciliation — by discarding
one side.

**Two defects, one root cause.** Neither `/ship` Step 6.4 nor `/release` Step
4.4 ever pushed `refs/notes/writ` at all. Every note the channel produced was
local-only unless the user pushed by hand, which makes the destroyed-on-fetch
behavior nearly undetectable: there was usually nothing on the remote to
overwrite *with*, and nothing on the remote to notice missing. The push was
added in the same fix.

**The fix.** The canonical git-notes pattern — fetch into a ref local
operations never write, then merge deliberately:

```
fetch = +refs/notes/writ:refs/notes/origin-writ    # was: :refs/notes/writ
push  = refs/notes/writ
```

`/ship` and `/release` now run `git fetch` → `git notes --ref=writ merge -s
cat_sort_uniq refs/notes/origin-writ` → attach → `git push origin
refs/notes/writ`. `cat_sort_uniq` concatenates and de-duplicates, so notes
written on two machines both survive; `-f` on the add still makes a re-ship
supersede its own prior digest. Push failure remains non-blocking, consistent
with the channel's existing rule.

`install.sh` migrates repos carrying the old refspec: it is removed before the
new one is added, in both the enabled and the opted-out paths, so opting out
cannot leave a clobbering fetch behind.

**Verified by construction, not by assertion.** The bug was first reproduced in
a scratch repo (local note added after last push; `git fetch`; note replaced by
the remote's), then the fix was shown to leave the local ref byte-identical
across a fetch, and a genuine two-machine divergence was built — machine B
pushing a note on one commit while machine A held an unpushed note on another —
and both notes survived the merge, with the reconciled ref pushing as a
fast-forward.

**Files changed.** `scripts/install.sh` (refspec, migration, opt-out residue),
`commands/ship.md` §6.4, `commands/release.md` §4.4,
`.writ/docs/git-notes-audit-format.md` (sync section + the reasoning),
`scripts/eval.sh` and `scripts/eval-git-notes-audit.py` (five new bindings,
including one asserting the clobbering refspec is *absent* from install.sh),
`scripts/tests/test_governor_enforcement.py` (disclosed byte-ratchet increment).

**Instrument note.** `scripts/eval.sh` stayed green throughout — the per-command
byte ratchet lives in `test_governor_enforcement.py`, which CI does not run.
Same gap already recorded in the quality-gates spec's scripts justification.

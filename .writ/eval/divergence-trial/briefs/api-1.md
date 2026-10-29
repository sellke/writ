id: api-1
medium: api

The command-line contract of pr-ready.py, a read-only script that says whether a pull request is ready to merge.
Who uses it: the /ship --watch loop, which calls it after each change it makes to a PR, and a developer running it by hand.
It reports blockers by type: merge conflicts, unresolved review threads, failing checks, and merge gates such as a required approval. A PR can have several at once.
Each blocker type needs its own exit code, so the caller can branch without parsing text.
Output follows Writ's agent CLI contract: verdict first, then `reason:` lines, then one summary line last.
It never polls or waits; the caller decides when to run it again.

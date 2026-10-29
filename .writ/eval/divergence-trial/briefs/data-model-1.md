id: data-model-1
medium: data-model

A verification ledger that records which pull request heads Writ has verified.
Who uses it: /ship --watch and pr-ready.py, which ask whether a PR's current head is verified, and a developer auditing past verdicts.
Each verdict is keyed by PR number, head commit SHA, and patch-id.
A new head reads NOT VERIFIED unless its patch-id matches one already verified, so a rebase that changes no content keeps its verdict.
It must answer "is this head verified, and by which verdict?" and list every verdict a PR has received.

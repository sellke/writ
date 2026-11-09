# Recommendation Log: Delete Merged Branches

| Decision | Evidence | Alternatives | Risk / reversibility | Result |
|---|---|---|---|---|
| Delete at the merging step, not in `/release` | `/release` runs on main and cannot tell Writ's branches from the user's; a release can be cancelled while branches pile up | release-time sweep | low; local deletes only | user agreed |
| Squash/rebase proof: PR `MERGED` and tip equals `headRefOid` | `--merged` never lists a squash-merged branch | `--merged` only (squash repos keep every branch) | `-D` only when the tip is the merged head, so no unpushed commit is lost | in contract |
| New helper script for `/ship` cleanup | ten ordered checks need tests; prose cannot be tested | prose in Step 6b | small new surface; follows agent-cli-contract | in contract |
| Opt-out `writ.deleteMergedBranches` | `writ.auditNotes` precedent | always on | none; absent = true | user chose "Lock and create" over "Drop the opt-out" |
| Remote heads excluded | `ship.md` forbids `--delete-branch`; GitHub repo setting covers remotes | `git push --delete` | none | in contract |
| Contract lock | doubt id `cb97f74eff25` asked (`doubt_uncalibrated`); user locked | — | — | labeled `as_recommended` |

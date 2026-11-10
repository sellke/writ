pass
scope: repro-first
story: 2026-09-20-custom-covers-not-saving/story-1-production-cover-origin-save gate3_route=review-agent gate0_route=evaluator-agent repro=bug arms=off-1,off-2,repro-first
story: 2026-04-16-event-limit-upgrade-modal-wiring/story-1-wire-limit-error-to-upgrade-modal gate3_route=review-agent gate0_route=skip repro=bug arms=off-1,off-2,repro-first
story: 2026-03-03-days-present-stretch-miscount/story-1-fix-counting-logic gate3_route=review-agent gate0_route=evaluator-agent repro=bug arms=off-1,off-2,repro-first
upgrade: repro-first verdict=remove exercised=3/3 upgrade_only=0 valid=0 invalid=0 off_only=0
sample: 3 stories, two current-gates runs, one run per upgrade arm; one valid catch keeps an upgrade — a low bar, not a cost case
proxy: Gate 0 and Repro First arms are retrospective proxies (sketch comparison, repro re-run), not replays
blinding: honor system — the sheet hides which upgrade raised a finding, but the trial file and raw outputs map IDs to arms, and Gate 0 excerpts show their Avoided by line
yuss: unchanged
gate-upgrade-trial: keep 0, remove 1, unverifiable 0, absent 0 — 3 stories

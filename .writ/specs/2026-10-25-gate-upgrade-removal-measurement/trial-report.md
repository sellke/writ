unverifiable
reason: repro-first amendment_requested
story: 2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow gate3_route=review-agent gate0_route=review-agent repro=not-a-bug-fix arms=off-1,off-2,reviewer-filters,safety-fact,gate0-divergence,repro-first
story: 2026-07-23-quick-split-single-transaction/story-3-settlement-view-share-link gate3_route=review-agent gate0_route=evaluator-agent repro=not-a-bug-fix arms=off-1,off-2,reviewer-filters,safety-fact,repro-first
story: 2026-07-24-per-event-fee-revenue-model/story-3-fee-sharing-pro-exemption gate3_route=review-agent gate0_route=review-agent repro=not-a-bug-fix arms=off-1,off-2,reviewer-filters,safety-fact,gate0-divergence,repro-first
story: 2026-07-24-per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard gate3_route=review-agent gate0_route=review-agent repro=not-a-bug-fix arms=off-1,off-2,reviewer-filters,safety-fact,gate0-divergence,repro-first
upgrade: gate0-divergence verdict=keep exercised=3/4 upgrade_only=3 valid=2 invalid=1 off_only=0
upgrade: safety-fact verdict=keep exercised=4/4 upgrade_only=2 valid=2 invalid=0 off_only=0
upgrade: reviewer-filters verdict=keep exercised=4/4 upgrade_only=1 valid=1 invalid=0 off_only=0
upgrade: repro-first verdict=unverifiable exercised=0/4 reason=amendment_requested
sample: 4 stories, two current-gates runs, one run per upgrade arm; one valid catch keeps an upgrade — a low bar, not a cost case
proxy: Gate 0 and Repro First arms are retrospective proxies (sketch comparison, repro re-run), not replays
blinding: honor system — the sheet hides which upgrade raised a finding, but the trial file and raw outputs map IDs to arms, and Gate 0 excerpts show their Avoided by line
yuss: unchanged
gate-upgrade-trial: keep 3, remove 0, unverifiable 1, absent 0 — 4 stories

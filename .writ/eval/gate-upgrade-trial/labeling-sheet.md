# Gate Upgrade Trial — Labeling Sheet

> Fill every `label:` with `valid` or `invalid` (spec.md Business Rule 6), optionally a one-line `note:` (at most 200 characters, no backticks), and every `ack:` with `remove` or `amend` (Rule 7). Do not change any other line. See rating-handoff.md.

## Findings

### F01
story: 2026-07-24-per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard
key: ac:AC-4.3
severity: Critical
excerpt: .writ/state/gate-upgrade-trial/findings/F01.md
label:
note:

### F02
story: 2026-07-24-per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard
key: ac:AC-4.1
severity: Critical
excerpt: .writ/state/gate-upgrade-trial/findings/F02.md
label:
note:

### F03
story: 2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow
key: architecture:app/dashboard/page.tsx
severity: Major
excerpt: .writ/state/gate-upgrade-trial/findings/F03.md
label:
note:

### F04
story: 2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow
key: architecture:app/api/events/route.ts
severity: Major
excerpt: .writ/state/gate-upgrade-trial/findings/F04.md
label:
note:

### F05
story: 2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow
key: ac:AC-2.5
severity: Critical
excerpt: .writ/state/gate-upgrade-trial/findings/F05.md
label:
note:

### F06
story: 2026-07-24-per-event-fee-revenue-model/story-3-fee-sharing-pro-exemption
key: architecture:app/api/expenses/[id]/route.ts
severity: Major
excerpt: .writ/state/gate-upgrade-trial/findings/F06.md
label:
note:

## Not exercised

### not exercised: repro-first
exercised: 0/4
- 2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow: not-a-bug-fix
- 2026-07-23-quick-split-single-transaction/story-3-settlement-view-share-link: not-a-bug-fix
- 2026-07-24-per-event-fee-revenue-model/story-3-fee-sharing-pro-exemption: not-a-bug-fix
- 2026-07-24-per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard: not-a-bug-fix
ack:

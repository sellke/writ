# Gate Upgrade Trial — Labeling Sheet

> Fill every `label:` with `valid` or `invalid` (spec.md Business Rule 6), optionally a one-line `note:` (at most 200 characters, no backticks), and every `ack:` with `remove` or `amend` (Rule 7). Do not change any other line. See rating-handoff.md.

## Findings

### F01
story: 2026-07-24-per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard
key: ac:AC-4.3
severity: Critical
excerpt: .writ/state/gate-upgrade-trial/findings/F01.md
label: valid
note: Assistant-assessed, maintainer-delegated. premium-features.md still states the delete-to-make-room hard block as current free-tier behavior in the Event Archiving rationale.

### F02
story: 2026-07-24-per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard
key: ac:AC-4.1
severity: Critical
excerpt: .writ/state/gate-upgrade-trial/findings/F02.md
label: valid
note: Assistant-assessed, maintainer-delegated. The Unlimited Events gate still implies deleting to make room, and 402s on direct-entry paths get a generic toast. Both sketch lines avoid it.

### F03
story: 2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow
key: architecture:app/dashboard/page.tsx
severity: Major
excerpt: .writ/state/gate-upgrade-trial/findings/F03.md
label: valid
note: Assistant-assessed, maintainer-delegated. Three entry points and the fail-open path skip the fork, so a saved card is charged from a modal that shows no price.

### F04
story: 2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow
key: architecture:app/api/events/route.ts
severity: Major
excerpt: .writ/state/gate-upgrade-trial/findings/F04.md
label: valid
note: Assistant-assessed, maintainer-delegated. The server charges with no fee-acceptance signal, which lets the F03 paths charge. The acceptFee sketch avoids it. Overlaps F03.

### F05
story: 2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow
key: ac:AC-2.5
severity: Critical
excerpt: .writ/state/gate-upgrade-trial/findings/F05.md
label: invalid
note: Assistant-assessed, maintainer-delegated. Code records the refund then deletes, as AC-2.5 says, and the spec's own schema chose cascade. The lost ledger is a spec contradiction.

### F06
story: 2026-07-24-per-event-fee-revenue-model/story-3-fee-sharing-pro-exemption
key: architecture:app/api/expenses/[id]/route.ts
severity: Major
excerpt: .writ/state/gate-upgrade-trial/findings/F06.md
label: valid
note: Assistant-assessed, maintainer-delegated. PUT and participant removal can re-split the platform fee onto Pro users with no platform-fee check, against the spec's server-side rule.

## Not exercised

### not exercised: repro-first
exercised: 0/4
- 2026-07-24-per-event-fee-revenue-model/story-2-event-creation-payment-flow: not-a-bug-fix
- 2026-07-23-quick-split-single-transaction/story-3-settlement-view-share-link: not-a-bug-fix
- 2026-07-24-per-event-fee-revenue-model/story-3-fee-sharing-pro-exemption: not-a-bug-fix
- 2026-07-24-per-event-fee-revenue-model/story-4-messaging-migration-quick-split-guard: not-a-bug-fix
ack: amend

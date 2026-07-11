---
name: error-rescue-mapping
description: "Map a data-flow feature's failure modes into Error & Rescue, Shadow Path, and edge-case tables, flagging unplanned handling explicitly."
disable-model-invocation: true
status: candidate
status_evidence: "Extracted 2026-07-10 from create-spec Step 2.8; candidate until consumer transcripts prove reuse (a review pass is the natural second consumer)."
---

# Error & Rescue Mapping

## Purpose

Turn a data-flow feature's failure surface into a small set of explicit tables —
an **Error & Rescue Map**, **Shadow Paths**, and **Interaction Edge Cases** — so
that every way the feature can fail has a *planned* response before any code is
written. The defining move is the **`[UNPLANNED]` marker**: any failure whose
handling has not been decided is marked in place, forcing a real decision rather
than a silent gap.

This capability owns *how to build the failure map*. The consumer owns *when* to
build one — which features warrant it and which sub-specs carry it. The tables
are deliberately written in the same shape a code reviewer would use to describe
a diff's actual handling, so the plan and the eventual code can be compared cell
for cell.

## When to Use

- Specifying or reviewing a feature that touches real data flow: API routes,
  auth flows, payments, file operations, or external integrations.
- Any point where "what happens when this fails?" must be answered before build,
  not discovered in production.
- Preparing a plan that a later review pass will compare against actual code —
  the shared table shape makes the comparison mechanical.
- Not warranted for pure UI/CSS, documentation, configuration, or internal
  refactors with no failure surface; when genuinely in doubt, build the map.

## How to Apply

### Principle: describe what the user sees, not what the system does

Every cell is written from the outside in. "422 with inline field errors" and
"503 with a retry prompt" are user-visible outcomes; "throws ValidationError" is
an internal mechanism and does not belong in these tables. This framing is what
lets a non-implementer read the map and what lets a reviewer check the code
against a promise about behavior rather than about internals.

### 1. Error & Rescue Map

One row per operation that can fail. Columns: **Operation**, **What Can Fail**,
**Planned Handling**, **Test Strategy**. Start with the operations that touch
external services (databases, third-party APIs, payment providers) — they fail
most and cost most.

| Operation | What Can Fail | Planned Handling | Test Strategy |
|---|---|---|---|
| Create session | DB unavailable | Retry 3×, then a clear error page | Integration test with the DB down |

When the planned handling for a failure has **not** been decided, write
`[UNPLANNED]` in that cell rather than inventing an answer. The `[UNPLANNED]`
marker is the highest-value output of the whole technique: it converts a hidden
gap into a visible decision. Every `[UNPLANNED]` must be resolved before
implementation — either by filling in real handling or by declaring it
`[OUT OF SCOPE — reason]` so the omission is deliberate and recorded. A plan
that still carries an unresolved `[UNPLANNED]` is not ready to build.

### 2. Shadow Paths

The happy path is one column; the failure columns are the shadows that get
skipped in casual planning. One row per flow, each cell a user-visible outcome.

| Flow | Happy Path | Nil Input | Empty Input | Upstream Error |
|---|---|---|---|---|
| User registration | Account created → welcome email | 422 + field errors | 422 + "required" message | 503 + retry prompt |

Nil, empty, and upstream-error inputs are where real systems break; naming the
user-visible outcome for each forces the design to account for them up front.

### 3. Interaction Edge Cases

The standard four for any interactive feature — double-submit, rapid repeat,
stale/expired state, and concurrent action — plus whatever is specific to *this*
feature. A payment form needs "card declined"; a search box needs "rapid
keystrokes." The feature-specific rows are the ones worth the most thought.

| Edge Case | Planned Handling |
|---|---|
| Double-click submit | Debounce — disable the control after the first click |

### Shared shape enables drift detection

Because these tables are written in the same structure a reviewer uses to
describe a diff, they double as a contract: a reviewer compares the map to the
code's actual handling, and any discrepancy is a **drift signal**. An
`[UNPLANNED]` that reaches code still unhandled, or a planned rescue the code
never implements, is a critical gap — not a stylistic nit. Keeping the plan and
the review in one shape is what makes that comparison cheap and honest.

## Examples

**An external-integration operation, planned vs. flagged:**

```text
| Operation            | What Can Fail        | Planned Handling                 | Test Strategy            |
|----------------------|----------------------|----------------------------------|--------------------------|
| Charge card (Stripe) | Network timeout      | Idempotency key + retry 2×       | Mock 504 from provider   |
| Charge card (Stripe) | Card declined        | Show decline reason, keep form   | Test each decline code   |
| Charge card (Stripe) | Webhook never arrives| [UNPLANNED]                      | —                        |
```

The `[UNPLANNED]` webhook row is the point of the exercise: it must become real
handling ("reconcile via a scheduled poll after 10 min") or an explicit
`[OUT OF SCOPE — reconciliation handled by billing service]` before build.

**Shadow paths phrased as user-visible outcomes:**

```text
| Flow          | Happy Path              | Nil Input          | Empty Input             | Upstream Error        |
|---------------|-------------------------|--------------------|-------------------------|-----------------------|
| File upload   | Preview + "Saved" toast | 400 "no file"      | 400 "file is empty"     | 503 "try again" toast |
```

Every failure cell says what the user sees, so the same table can be checked
against the shipped behavior without reading the implementation.

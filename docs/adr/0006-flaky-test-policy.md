# ADR 0006: Flaky test policy

- Status: Accepted
- Date: 2026-10-06

## Context

Silent reruns hide flakiness; no reruns let one unstable third-party call block a release.

## Decision

- e2e runs rerun failed tests (default 2). Tests that pass only on rerun are listed as flaky in the job summary.
- Persistent flakiness is tracked with a Flaky test issue. If not fixed quickly, the test gets `@pytest.mark.quarantine(reason=...)`; the reason is mandatory and checked at collection.
- Quarantined tests run in a separate non-blocking step, so they keep producing evidence without blocking the gate.

## Consequences

- Flakiness stays visible and owned. Quarantine is cheap to apply, so it must be reviewed regularly to avoid becoming permanent.

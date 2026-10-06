# ADR 0005: Measure test effectiveness, not only coverage

- Status: Accepted
- Date: 2026-10-06

## Context

Line coverage shows which code ran, not whether a test would notice it breaking. A framework that other teams rely on needs stronger evidence.

## Decision

- Coverage gate of 90% on `core/` and `adapters/`.
- Mutation testing with mutmut on `core/`, gated at an 80% score on every PR. The baseline run scored 74%; reviewing survivors led to new tests (environment overlay default, per-client cache keys, exact report layout) and raised it to 81%.
- Property-based tests (Hypothesis) for parsers and renderers, where hand-picked examples miss edge cases such as pipes, angle brackets or control characters in Markdown cells.

## Consequences

- Mutation testing adds about 30 seconds to CI for the current code size.
- Survivors in log-message strings are accepted; the gate is a ratchet, raised as tests improve, never lowered silently.

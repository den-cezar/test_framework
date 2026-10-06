# ADR 0007: Requirements traceability through a scenario marker

- Status: Accepted
- Date: 2026-10-06

## Context

Scenario ids used to live in docstrings, where nothing could check them. Release decisions need "which requirements were verified", not "how many tests passed".

## Decision

- Each e2e test declares `@pytest.mark.scenario("ID")`; requirement titles live in `test_scripts/data/requirements.json`.
- Collection fails for missing or unknown ids. `--require-full-traceability` (run in CI) also fails when a requirement has no test.
- Each run produces a requirement-level matrix (job summary and optional Markdown file) and writes ids to JUnit properties.

## Consequences

- The catalog becomes a reviewed artifact: adding a requirement without a test, or a test without a requirement, fails the PR.
- Ids can be mapped to Jira or Xray later without touching the tests.

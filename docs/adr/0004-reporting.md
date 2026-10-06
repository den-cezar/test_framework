# ADR 0004: Reporting with JUnit, pytest-html, job summaries and a Pages history

- Status: Accepted
- Date: 2026-10-06

## Context

Considered options: Allure, ReportPortal, pytest-html, JUnit XML with GitHub-native summaries. Allure and ReportPortal give rich dashboards but add a Java/Node toolchain or a server to operate.

## Decision

- JUnit XML for tools, with requirement ids as properties.
- pytest-html, self-contained, with failure screenshots embedded.
- A Markdown job summary written by a pytest hook: counts, failures, flaky tests, traceability matrix. Coverage and mutation score are added by their jobs.
- Playwright traces uploaded as a separate artifact only when a run fails.
- A static history page on GitHub Pages (`tools/report_history.py`): last 50 runs, pass-rate trend, link to each HTML report.

## Consequences

- No extra infrastructure; everything is visible from the pull request or the run page.
- Trend analysis is basic (pass rate and duration). If deeper analytics are needed, ReportPortal can consume the same JUnit output.

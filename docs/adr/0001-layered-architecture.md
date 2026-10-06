# ADR 0001: Layered test architecture

- Status: Accepted
- Date: 2026-10-06

## Context

Test suites decay when tests call HTTP clients and browser APIs directly: selectors and URLs get duplicated, a client library change touches every test, and nothing can be unit-tested without a live system.

## Decision

Four layers with one-way dependencies:

| Layer | Contains | May depend on |
|---|---|---|
| `test_scripts/` | Tests, fixtures, test data | `domain`, `core` |
| `domain/` | `ApiService`, `UiService`, page objects, API contract models | `adapters`, `core` |
| `adapters/` | `HttpClient` (httpx), `PlaywrightAdapter` (Playwright, axe) | `core` |
| `core/` | Config, auth, logging, artifacts, reporting, errors | Standard library and small utilities only |

Page objects return Playwright `Locator`s so tests can use Playwright's auto-retrying `expect` assertions, instead of re-implementing waits.

## Consequences

- Replacing httpx or Playwright touches one adapter.
- `core/` is unit-testable without network, which makes the coverage and mutation gates possible.
- Tests read as business steps; the cost is one more indirection when adding a new UI element.

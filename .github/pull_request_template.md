## Summary

<!-- What changes and why. Link the issue: "Closes #123". -->

## Type of change

- [ ] Bug fix
- [ ] New or changed tests
- [ ] Framework feature (core, adapters, domain)
- [ ] CI / tooling
- [ ] Documentation

## How it was tested

<!-- Commands you ran and their result. For e2e changes, link a dispatched e2e.yml run if possible. -->

- [ ] `poetry run poe check`
- [ ] `poetry run poe test-unit`
- [ ] Affected e2e tests, e.g. `poetry run poe test-smoke`

## Checklist

- [ ] Tests use `domain` services or page objects, not httpx or Playwright directly
- [ ] New tests have a layer marker (`api` / `ui`) and a suite marker (`smoke` / `regression`)
- [ ] New e2e tests have a `scenario` marker, and new requirements are added to `requirements.json`
- [ ] UI changes pass on Chromium, Firefox and WebKit
- [ ] New settings are added to `.env.example`, the `e2e.yml` step env, and the README
- [ ] No secrets, tokens, or real credentials in code, logs, or test data
- [ ] README updated if usage changed

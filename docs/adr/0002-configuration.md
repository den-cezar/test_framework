# ADR 0002: Configuration from env files and environment variables

- Status: Accepted
- Date: 2026-10-06

## Context

Developers want a local file; CI must not store secrets in files in the repository. The same code path should serve both.

## Decision

- Settings are loaded once per process into an immutable `FrameworkSettings`.
- Env file precedence: `--env-file`, then `ENV_FILE`, then `.env.dev` if present.
- Non-empty process environment variables override file values. CI provides every setting from a GitHub environment (`vars` for configuration, `secrets` for credentials), passed only to the test steps.
- Invalid or missing values raise `ConfigError` at startup with the offending key.

## Consequences

- One code path for local and CI; adding an environment is a GitHub setting, not a code change.
- A stray variable in a developer's shell overrides the file. This is standard twelve-factor behaviour and is documented.

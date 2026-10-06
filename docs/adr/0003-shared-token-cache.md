# ADR 0003: Shared OAuth token cache with a file lock

- Status: Accepted
- Date: 2026-10-06

## Context

pytest-xdist runs tests in separate processes. Without coordination every worker requests its own token, multiplying load on the identity provider and risking rate limits.

## Decision

Tokens are cached in a JSON file keyed by environment, client, client id and scope. The whole check, fetch and store sequence runs under a `filelock` lock, so at most one token request per key happens across all workers. Writes are atomic (temporary file and rename); a corrupt cache is treated as empty. Tokens are refreshed 30 seconds before expiry.

## Consequences

- One token request per client per run, verified by a concurrency unit test.
- Workers briefly serialise on the lock when the token is missing; cache hits are a single file read.
- The cache file holds bearer tokens, so it lives in the git-ignored `.cache/` directory.

#!/usr/bin/env bash
# Runs once after the container is created. Safe to re-run.
set -euo pipefail

# Named volumes are created root-owned; the browsers and Poetry caches must belong to the dev user.
sudo chown -R "$(id -u):$(id -g)" "$HOME/.cache/ms-playwright" "$HOME/.cache/pypoetry"

pipx install --force poetry==2.5.1
poetry install --no-interaction

# All three engines, so cross-browser runs work locally exactly as in CI.
poetry run playwright install --with-deps chromium firefox webkit
poetry run pre-commit install

if [[ ! -f .env.dev ]]; then
  cp .env.example .env.dev
  echo "Created .env.dev from .env.example (public demo targets)."
fi

cat <<'EOF'

Dev container ready. Try:
  poetry run poe check          # lint, format, types, traceability
  poetry run poe test-unit      # unit + property tests with coverage
  poetry run poe test-smoke     # e2e smoke against the demo targets
  poetry run poe show-trace .artifacts/<run>/<test>/<file>_trace.zip   # trace viewer on port 9323
EOF

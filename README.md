# New Hybrid API/UI Test Framework

This directory contains the next-generation test framework with clean module boundaries, hybrid API/UI capabilities, and parallel-safe execution.

## Setup

### Prerequisites

- Python 3.11+
- macOS, Linux, or Windows
- (Optional) Playwright browsers for UI tests

### Install dependencies

1. Create and activate a virtual environment.
2. Install project dependencies.

If this project uses a requirements file, install from it. Otherwise, use the project configuration:

- For Poetry (pyproject.toml): `poetry install`

### Install Playwright browsers (UI tests only)

If you plan to run UI tests, install Playwright and its browsers:

- `playwright install`

## Configuration

Framework settings live in [core/config/settings.py](core/config/settings.py). Configure environment-specific values (base URLs, auth, timeouts) there or via environment variables if supported.

Common locations:

- API settings: [domain/api/api_service.py](domain/api/api_service.py)
- UI settings: [domain/ui/ui_service.py](domain/ui/ui_service.py)
- Auth settings: [core/auth/oauth_client.py](core/auth/oauth_client.py)

## How to start using the framework

### Run all tests

- `pytest`

### Run a specific test suite

- API tests: `pytest test_scripts/api`
- UI tests: `pytest test_scripts/ui`
- Hybrid tests: `pytest test_scripts/hybrid`

### Run a single test

- `pytest test_scripts/api/test_api_health.py`

## Writing tests

### API test example

See [test_scripts/api/test_api_health.py](test_scripts/api/test_api_health.py).

### UI test example

See [test_scripts/ui/test_ui_example.py](test_scripts/ui/test_ui_example.py).

### Hybrid test example

See [test_scripts/hybrid/test_hybrid_example.py](test_scripts/hybrid/test_hybrid_example.py).

## Logging

Logs are written per test session under `.artifacts/<YYYYMMDD_HHMMSS>/` in the repo root. Each worker writes to `<workerId>.log` (for example, `master.log`).

Logging is initialized by the `loggerInstance` fixture in `conftest.py`, which calls `Logger.get_instance(...)` and creates both console and file handlers.

## Playwright configuration

UI tests launch Chromium with `headless=True` in `conftest.py`. You can pass custom browser launch arguments via `PLAYWRIGHT_LAUNCH_ARGS` in your env file, using a comma-separated list.

Example:

`PLAYWRIGHT_LAUNCH_ARGS=--no-sandbox,--disable-dev-shm-usage,--disable-gpu`

## Troubleshooting

- If UI tests fail to launch a browser, ensure Playwright browsers are installed.
- If API calls fail, verify base URLs and auth settings in [core/config/settings.py](core/config/settings.py).
- For framework-specific exceptions, see [core/errors](core/errors).

## Utils and test data

Framework utilities live in `core/utils/`. Test-only helpers and shared test data live under `test_scripts/utils/` and `test_scripts/data/`.

Example usage:

- `core/utils/data_loader.py` provides a JSON loader utility.
- `test_scripts/utils/test_data.py` loads `test_scripts/data/test_data.json` for API and UI tests.

## License

This project is licensed under the GNU General Public License v3.0. See `LICENSE` for details.

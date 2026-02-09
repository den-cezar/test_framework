"""
Pytest configuration and fixtures for the new test framework.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from adapters.http_client import HttpClient
from adapters.playwright_adapter import PlaywrightAdapter
from core.artifacts.screenshot_manager import ScreenshotManager
from core.auth.oauth_client import OAuthClient
from core.auth.token_cache import SharedTokenCache
from core.config.settings import FrameworkSettings, load_settings
from core.logging.logger import Logger
from domain.api.api_service import ApiService
from domain.ui.ui_service import UiService

FRAMEWORK_ROOT = Path(__file__).resolve().parent
GLOBAL_OPTIONS: dict[str, Any] = {"envFile": None}
LOGGER_INSTANCE: Logger | None = None


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Register custom command-line options for the framework.

    :param parser: Mandatory, Pytest CLI parser.
    """
    logger = Logger.get_logger("Conftest")
    logger.debug("Registering pytest command-line options.")

    parser.addoption("--env-file", action="store", default=None, help="Path to .env file for the framework.")


def pytest_configure(config: pytest.Config) -> None:
    """
    Configure pytest markers and global options.

    :param config: Mandatory, Pytest config.
    """
    logger = Logger.get_logger("Conftest")
    logger.debug("Configuring pytest markers and global options.")

    config.addinivalue_line("markers", "api: mark test as API")
    config.addinivalue_line("markers", "ui: mark test as UI")

    GLOBAL_OPTIONS["envFile"] = config.getoption("--env-file")

    env_file_path = _resolve_env_file(GLOBAL_OPTIONS.get("envFile"))
    load_settings(env_file_path)


def _resolve_env_file(env_file_value: str | None) -> Path:
    """
    Resolve the environment file path.

    :param env_file_value: Optional, Path from CLI option.
    :return: Resolved Path to the env file.
    """
    logger = Logger.get_logger("Conftest")
    logger.debug("Resolving env file path.")

    if env_file_value:
        return Path(env_file_value).expanduser().resolve()
    return FRAMEWORK_ROOT.joinpath(".env.dev")


def _create_test_run_dir(timezone_name: str) -> Path:
    """
    Create a directory for the current test run.

    :param timezone_name: Mandatory, Timezone name for timestamp.
    :return: Path to the test run directory.
    """
    logger = Logger.get_logger("Conftest")
    logger.debug("Creating test run directory.")

    if timezone_name not in {"UTC", "LOCAL"}:
        raise ValueError("timezone_name must be UTC or LOCAL.")

    now_value = datetime.now(UTC) if timezone_name == "UTC" else datetime.now()
    run_stamp = now_value.strftime("%Y%m%d_%H%M%S")
    run_dir = FRAMEWORK_ROOT.joinpath(".artifacts", run_stamp)
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


@pytest.fixture(scope="session")
def framework_settings() -> FrameworkSettings:
    """
    Load and provide framework settings for the session.

    :return: FrameworkSettings instance.
    """
    logger = Logger.get_logger("Conftest")
    logger.debug("Loading framework settings fixture.")
    env_file_path = _resolve_env_file(GLOBAL_OPTIONS.get("envFile"))
    settings = load_settings(env_file_path)

    env_override = os.getenv("ENV_FILE")
    if env_override:
        settings = load_settings(Path(env_override))

    return settings


@pytest.fixture(scope="session")
def test_run_dir(framework_settings: FrameworkSettings) -> Path:
    """
    Create and provide the test run directory.

    :param framework_settings: Mandatory, Framework settings.
    :return: Path to the test run directory.
    """
    logger = Logger.get_logger("Conftest")
    logger.debug("Providing test run directory.")

    if not isinstance(framework_settings, FrameworkSettings):
        raise ValueError("framework_settings must be FrameworkSettings.")

    return _create_test_run_dir(framework_settings.timezone)


@pytest.fixture(scope="session")
def logger_instance(test_run_dir: Path) -> Logger:
    """
    Initialize and provide the framework logger.

    :param test_run_dir: Mandatory, Directory for test run logs.
    :return: Logger instance.
    """
    global LOGGER_INSTANCE
    worker_id = os.getenv("PYTEST_XDIST_WORKER", "master")
    LOGGER_INSTANCE = Logger.get_instance(worker_id, test_run_dir)
    LOGGER_INSTANCE.debug("Logger initialized in conftest.")
    return LOGGER_INSTANCE


@pytest.fixture(scope="session")
def shared_token_cache(framework_settings: FrameworkSettings, logger_instance: Logger) -> SharedTokenCache:
    """
    Provide the shared token cache.

    :param framework_settings: Mandatory, Framework settings.
    :param logger_instance: Mandatory, Logger instance.
    :return: SharedTokenCache instance.
    """
    logger_instance.debug("Providing shared token cache.")

    if not isinstance(framework_settings, FrameworkSettings):
        raise ValueError("framework_settings must be FrameworkSettings.")

    cache_path = framework_settings.token_cache_path
    if not cache_path.is_absolute():
        cache_path = FRAMEWORK_ROOT.joinpath(cache_path)

    return SharedTokenCache(cache_path)


@pytest.fixture(scope="session")
def oauth_client(
    framework_settings: FrameworkSettings, shared_token_cache: SharedTokenCache, logger_instance: Logger
) -> OAuthClient:
    """
    Provide the OAuth client.

    :param framework_settings: Mandatory, Framework settings.
    :param shared_token_cache: Mandatory, Shared token cache.
    :param logger_instance: Mandatory, Logger instance.
    :return: OAuthClient instance.
    """
    logger_instance.debug("Providing OAuth client.")
    return OAuthClient(framework_settings, shared_token_cache)


@pytest.fixture(scope="session")
def screenshot_manager(
    framework_settings: FrameworkSettings, test_run_dir: Path, logger_instance: Logger
) -> ScreenshotManager:
    """
    Provide the screenshot manager.

    :param framework_settings: Mandatory, Framework settings.
    :param test_run_dir: Mandatory, Test run directory.
    :param logger_instance: Mandatory, Logger instance.
    :return: ScreenshotManager instance.
    """
    logger_instance.debug("Providing screenshot manager.")

    return ScreenshotManager(test_run_dir, framework_settings.timezone)


@pytest.fixture(scope="session")
def http_client(
    framework_settings: FrameworkSettings, oauth_client: OAuthClient, logger_instance: Logger
) -> HttpClient:
    """
    Provide the HTTP client adapter.

    :param framework_settings: Mandatory, Framework settings.
    :param oauth_client: Mandatory, OAuth client.
    :param logger_instance: Mandatory, Logger instance.
    :return: HttpClient instance.
    """
    logger_instance.debug("Providing HTTP client adapter.")

    return HttpClient(framework_settings, oauth_client)


@pytest.fixture(scope="session")
def api_service(http_client: HttpClient, logger_instance: Logger) -> ApiService:
    """
    Provide the API service wrapper.

    :param http_client: Mandatory, HTTP client adapter.
    :param logger_instance: Mandatory, Logger instance.
    :return: ApiService instance.
    """
    logger_instance.debug("Providing API service.")
    return ApiService(http_client)


def _parse_playwright_launch_args(raw_value: str | None) -> list[str]:
    """
    Parse Playwright launch args from a comma-separated env var.

    :param raw_value: Optional, Raw env var value.
    :return: List of args.
    """
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


@pytest.fixture(scope="function")
def playwright_page(framework_settings: FrameworkSettings, logger_instance: Logger) -> Any:
    """
    Provide a Playwright page instance for UI tests.

    :param framework_settings: Mandatory, Framework settings.
    :param logger_instance: Mandatory, Logger instance.
    :return: Playwright page instance.
    """
    logger_instance.debug("Providing Playwright page instance.")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is not available.") from exc

    launch_args = _parse_playwright_launch_args(os.getenv("PLAYWRIGHT_LAUNCH_ARGS"))

    with sync_playwright() as playwright_value:
        browser_value = playwright_value.chromium.launch(headless=True, args=launch_args)
        context_value = browser_value.new_context()
        page_value = context_value.new_page()
        yield page_value
        context_value.close()
        browser_value.close()


@pytest.fixture(scope="function")
def ui_service(playwright_page: Any, screenshot_manager: ScreenshotManager, logger_instance: Logger) -> UiService:
    """
    Provide the UI service wrapper.

    :param playwright_page: Mandatory, Playwright page instance.
    :param screenshot_manager: Mandatory, Screenshot manager.
    :param logger_instance: Mandatory, Logger instance.
    :return: UiService instance.
    """
    logger_instance.debug("Providing UI service.")
    adapter_value = PlaywrightAdapter(playwright_page)
    return UiService(adapter_value, screenshot_manager)


@pytest.fixture(autouse=True)
def set_test_name(logger_instance: Logger, request: pytest.FixtureRequest) -> None:
    """
    Update logger context with the current test name.

    :param logger_instance: Mandatory, Logger instance.
    :param request: Mandatory, Pytest fixture request.
    """
    logger_instance.set_test_name(request.node.nodeid)


@pytest.fixture(autouse=True)
def ensure_ui_screenshot_manager(request: pytest.FixtureRequest, screenshot_manager: ScreenshotManager) -> None:
    """
    Ensure the screenshot manager is available for UI tests.

    :param request: Mandatory, Pytest fixture request.
    :param screenshot_manager: Mandatory, Screenshot manager.
    """
    if request.node.get_closest_marker("ui") is None:
        return


def pytest_runtest_makereport(item: Any, call: Any) -> None:
    """
    Capture UI screenshots on test failure when a page fixture is available.

    :param item: Mandatory, The test item.
    :param call: Mandatory, The call report.
    """
    logger = Logger.get_logger("Conftest")

    if call.when != "call" or call.excinfo is None:
        return

    page_value = item.funcargs.get("page") or item.funcargs.get("playwright_page")
    if page_value is None:
        return

    logger.debug("Processing test report for UI screenshot capture.")

    screenshot_manager_value = item.funcargs.get("screenshot_manager")
    if screenshot_manager_value is None:
        return

    try:
        screenshot_manager_value.capture(page_value, item.nodeid)
    except Exception as exc:
        logger = Logger.get_logger("Conftest")
        logger.debug(f"Screenshot capture failed: {exc}")


def pytest_sessionfinish(**finish_kwargs: Any) -> None:
    """
    Clean up logging resources at session end.

    :param finish_kwargs: Mandatory, Keyword arguments containing session info.
    """
    logger = Logger.get_logger("Conftest")
    logger.debug("Finalizing pytest session.")
    if LOGGER_INSTANCE:
        LOGGER_INSTANCE.cleanup()

"""
Pytest fixtures for end-to-end (API/UI) tests. Requires an env file; see README.
"""

from __future__ import annotations

import base64
import os
from collections.abc import Generator, Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
import pytest_html
from playwright.sync_api import Browser, Page, sync_playwright

from adapters.http_client import HttpClient
from adapters.playwright_adapter import PlaywrightAdapter
from core.artifacts.artifact_manager import ArtifactManager
from core.auth.oauth_client import OAuthClient
from core.auth.token_cache import SharedTokenCache
from core.config.settings import FrameworkSettings, load_settings, resolve_env_file
from core.logging.logger import Logger
from domain.api.api_service import ApiService
from domain.ui.ui_service import UiService
from test_scripts.utils.test_data import load_json_file

FRAMEWORK_ROOT = Path(__file__).resolve().parents[1]
TEST_SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_ENV_FILE = FRAMEWORK_ROOT.joinpath(".env.dev")
CALL_REPORT_KEY = pytest.StashKey[pytest.TestReport]()

logger = Logger.get_logger("Fixtures")


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """
    Enforce traceability before marker deselection: every e2e test maps to a known requirement,
    and every quarantined test states why. Scenario ids are copied into JUnit/report properties.

    :param config: Mandatory, Pytest config.
    :param items: Mandatory, Collected items (all of them, before -m/-k deselection).
    """
    catalog = load_json_file("requirements.json")
    problems: list[str] = []
    covered: set[str] = set()
    for item in items:
        if not item.path.is_relative_to(TEST_SCRIPTS_DIR):
            continue
        scenario = item.get_closest_marker("scenario")
        if scenario is None or not scenario.args:
            problems.append(f"{item.nodeid}: missing @pytest.mark.scenario('<ID>')")
            continue
        scenario_id = str(scenario.args[0])
        if scenario_id not in catalog:
            problems.append(f"{item.nodeid}: scenario {scenario_id} is not in test_scripts/data/requirements.json")
        covered.add(scenario_id)
        item.user_properties.append(("scenario", scenario_id))

        quarantine = item.get_closest_marker("quarantine")
        if quarantine is not None and not quarantine.kwargs.get("reason"):
            problems.append(f"{item.nodeid}: quarantine needs reason='<issue link and cause>'")

    if config.getoption("--require-full-traceability"):
        problems += [f"{sid}: no test covers this requirement" for sid in sorted(catalog.keys() - covered)]
    if problems:
        raise pytest.UsageError("Traceability check failed:\n  " + "\n  ".join(problems))


@pytest.fixture(scope="session")
def framework_settings(pytestconfig: pytest.Config) -> FrameworkSettings:
    """
    Load settings once per process.

    Env file precedence: --env-file, then ENV_FILE, then .env.dev if present. Non-empty environment
    variables override file values, which is how CI injects GitHub environment variables and secrets.

    :param pytestconfig: Mandatory, Pytest config.
    :return: FrameworkSettings instance.
    """
    env_file = resolve_env_file(pytestconfig.getoption("--env-file"), os.getenv("ENV_FILE"), DEFAULT_ENV_FILE)
    return load_settings(env_file)


@pytest.fixture(scope="session")
def test_run_dir(framework_settings: FrameworkSettings) -> Path:
    """
    Create the directory for this run. All xdist workers share it because the start time comes from the controller.

    :param framework_settings: Mandatory, Framework settings.
    :return: Path to the test run directory.
    """
    started_at = float(os.environ["TEST_RUN_STARTED_AT"])
    tz = UTC if framework_settings.timezone == "UTC" else None
    run_dir = FRAMEWORK_ROOT.joinpath(".artifacts", datetime.fromtimestamp(started_at, tz).strftime("%Y%m%d_%H%M%S"))
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


@pytest.fixture(scope="session", autouse=True)
def logger_instance(framework_settings: FrameworkSettings, test_run_dir: Path) -> Iterator[Logger]:
    """
    Configure framework logging for this worker.

    :param framework_settings: Mandatory, Framework settings.
    :param test_run_dir: Mandatory, Directory for test run logs.
    :return: Logger instance.
    """
    instance = Logger.get_instance(
        os.getenv("PYTEST_XDIST_WORKER", "master"),
        test_run_dir,
        framework_settings.log_console_level,
        framework_settings.log_file_level,
    )
    yield instance
    instance.cleanup()


@pytest.fixture(autouse=True)
def set_test_name(logger_instance: Logger, request: pytest.FixtureRequest) -> None:
    """
    Tag log records with the current test id.

    :param logger_instance: Mandatory, Logger instance.
    :param request: Mandatory, Pytest fixture request.
    """
    logger_instance.set_test_name(request.node.nodeid)


@pytest.fixture(scope="session")
def artifact_manager(framework_settings: FrameworkSettings, test_run_dir: Path) -> ArtifactManager:
    """
    Provide the artifact manager.

    :param framework_settings: Mandatory, Framework settings.
    :param test_run_dir: Mandatory, Test run directory.
    :return: ArtifactManager instance.
    """
    return ArtifactManager(test_run_dir, framework_settings.timezone)


# --- API ---------------------------------------------------------------------------------------------------------


@pytest.fixture(scope="session")
def shared_token_cache(framework_settings: FrameworkSettings) -> SharedTokenCache:
    """
    Provide the token cache shared by all xdist workers.

    :param framework_settings: Mandatory, Framework settings.
    :return: SharedTokenCache instance.
    """
    return SharedTokenCache(FRAMEWORK_ROOT.joinpath(framework_settings.token_cache_path))


@pytest.fixture(scope="session")
def oauth_client(framework_settings: FrameworkSettings, shared_token_cache: SharedTokenCache) -> Iterator[OAuthClient]:
    """
    Provide the OAuth client.

    :param framework_settings: Mandatory, Framework settings.
    :param shared_token_cache: Mandatory, Shared token cache.
    :return: OAuthClient instance.
    """
    client = OAuthClient(framework_settings, shared_token_cache)
    yield client
    client.close()


@pytest.fixture(scope="session")
def http_client(framework_settings: FrameworkSettings, oauth_client: OAuthClient) -> Iterator[HttpClient]:
    """
    Provide the HTTP client adapter.

    :param framework_settings: Mandatory, Framework settings.
    :param oauth_client: Mandatory, OAuth client.
    :return: HttpClient instance.
    """
    client = HttpClient(framework_settings, oauth_client)
    yield client
    client.close()


@pytest.fixture(scope="session")
def api_service(http_client: HttpClient) -> ApiService:
    """
    Provide the API domain service.

    :param http_client: Mandatory, HTTP client adapter.
    :return: ApiService instance.
    """
    return ApiService(http_client)


# --- UI ----------------------------------------------------------------------------------------------------------


@pytest.fixture(scope="session")
def browser(framework_settings: FrameworkSettings) -> Iterator[Browser]:
    """
    Launch one browser per worker; the engine comes from PLAYWRIGHT_BROWSER.

    :param framework_settings: Mandatory, Framework settings.
    :return: Playwright Browser.
    """
    engine = framework_settings.playwright_browser
    # Launch args are Chromium command-line switches; Firefox and WebKit reject them.
    args = list(framework_settings.playwright_launch_args) if engine == "chromium" else []
    with sync_playwright() as playwright:
        browser_value = getattr(playwright, engine).launch(headless=framework_settings.playwright_headless, args=args)
        yield browser_value
        browser_value.close()


@pytest.fixture
def playwright_page(
    browser: Browser, artifact_manager: ArtifactManager, request: pytest.FixtureRequest
) -> Iterator[Page]:
    """
    Provide a page in a fresh browser context. A Playwright trace is kept only when the test fails.

    :param browser: Mandatory, Session browser.
    :param artifact_manager: Mandatory, Artifact manager.
    :param request: Mandatory, Pytest fixture request.
    :return: Playwright Page.
    """
    context = browser.new_context()
    context.tracing.start(screenshots=True, snapshots=True)
    page = context.new_page()
    yield page

    call_report = request.node.stash.get(CALL_REPORT_KEY, None)
    if call_report is not None and call_report.failed:
        trace_path = artifact_manager.trace_path(request.node.nodeid)
        context.tracing.stop(path=trace_path)
        logger.info("Saved Playwright trace (open with `playwright show-trace`): %s", trace_path)
    else:
        context.tracing.stop()
    context.close()


@pytest.fixture
def ui_service(playwright_page: Page, framework_settings: FrameworkSettings) -> UiService:
    """
    Provide the UI domain service.

    :param playwright_page: Mandatory, Playwright page.
    :param framework_settings: Mandatory, Framework settings.
    :return: UiService instance.
    """
    return UiService(PlaywrightAdapter(playwright_page, framework_settings.ui_base_url))


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    """
    Remember the call-phase report and attach a screenshot to the HTML report when a UI test fails.

    :param item: Mandatory, The test item.
    :param call: Mandatory, The call info.
    :return: The test report.
    """
    report = yield
    if report.when != "call":
        return report

    item.stash[CALL_REPORT_KEY] = report
    funcargs = getattr(item, "funcargs", {})
    page = funcargs.get("playwright_page")
    manager = funcargs.get("artifact_manager")
    if report.failed and page is not None and manager is not None:
        try:
            path, png = manager.capture_screenshot(page, item.nodeid)
        except Exception as exc:  # a broken page must not hide the original failure
            logger.warning("Screenshot capture failed: %s", exc)
        else:
            logger.info("Saved failure screenshot: %s", path)
            extras = getattr(report, "extras", [])
            extras.append(pytest_html.extras.png(base64.b64encode(png).decode("ascii"), "Failure screenshot"))
            report.extras = extras  # type: ignore[attr-defined]  # attribute read by pytest-html
    return report

# pylint: disable=redefined-outer-name
import datetime
import os
from typing import Any, Callable, Optional

import pytest
from _pytest.config import Config

from pytest_sosu.config import SosuConfig, build_sosu_config
from pytest_sosu.logging import get_struct_logger
from pytest_sosu.plugin_helpers import parametrize_capabilities
from pytest_sosu.webdriver import (
    Browser,
    Capabilities,
    Platform,
    SauceOptions,
    WebDriverTestFailed,
    WebDriverTestInterrupted,
    WebDriverUrlData,
    remote_webdriver_ctx,
)

logger = get_struct_logger(__name__)


def pytest_addoption(parser):
    group = parser.getgroup("sosu plugin sauce labs configuration")

    group.addoption(
        "--sosu-username",
        action="store",
        metavar="SAUCE_USERNAME",
        help="Sauce Labs username",
    )
    group.addoption(
        "--sosu-access-key",
        action="store",
        metavar="SAUCE_ACCESS_KEY",
        help="Sauce Labs access key",
    )
    group.addoption(
        "--sosu-region",
        action="store",
        metavar="SAUCE_REGION",
        help="Sauce Labs region",
    )
    group.addoption(
        "--sosu-webdriver-url",
        action="store",
        metavar="SAUCE_WEBDRIVER_URL",
        help="Sauce Labs WebDriver URL",
    )


def pytest_configure(config: Config):
    logger.debug("pytest_configure", config=config)
    # register an additional marker
    config.addinivalue_line("markers", "sosu(type): mark test to run with Sauce Labs")

    sosu_config = build_sosu_config(config.option, os.environ)
    setattr(config, "sosu", sosu_config)


def _get_sosu_config(config: Config) -> SosuConfig:
    return getattr(config, "sosu")


def pytest_runtest_setup(item: pytest.Item):
    logger.debug("pytest_runtest_setup", item=item)
    sosu_markers = list(item.iter_markers(name="sosu"))
    if sosu_markers:
        logger.debug("sosu marker(s) found", sosu_markers=sosu_markers)


def pytest_generate_tests(metafunc):
    logger.debug(
        "pytest_generate_tests",
        metafunc=metafunc,
        fixturenames=metafunc.fixturenames,
    )

    parametrize_capabilities(metafunc)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Execute all other hooks to obtain the report object.
    outcome = yield
    report = outcome.get_result()

    # Set a report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"
    setattr(item, "report_when_" + report.when, report)


@pytest.fixture(scope="session")
def sosu_build_basename() -> Optional[str]:
    return None


@pytest.fixture(scope="session")
def sosu_build_time_tag() -> str:
    now = datetime.datetime.now()
    date_str = f"{now.year}{now.month:02d}{now.day:02d}"
    time_str = f"{now.hour:02d}{now.minute:02d}"
    return f"{date_str}_{time_str}"


@pytest.fixture(scope="session")
def sosu_build_version(sosu_build_time_tag: str) -> str:
    return sosu_build_time_tag


@pytest.fixture(scope="session")
def sosu_build_name(
    sosu_build_basename: Optional[str], sosu_build_version: str
) -> Optional[str]:
    if sosu_build_basename is None:
        return None
    return f"{sosu_build_basename}_{sosu_build_version}"


@pytest.fixture
def sosu_webdriver_url_data(pytestconfig: Config) -> WebDriverUrlData:
    sosu_config = _get_sosu_config(pytestconfig)
    return sosu_config.webdriver_url_data_with_credentials


@pytest.fixture
def sosu_test_name(request: pytest.FixtureRequest) -> str:
    path = get_function_path(request.node.function)
    return f"{path}::{request.node.name}"


def get_function_path(func: Callable[..., Any]) -> str:
    rel_path = func.__module__.replace(".", "/")
    return f"{rel_path}.py"


@pytest.fixture
def sosu_webdriver_platform() -> Optional[Platform]:
    return Platform.default()


@pytest.fixture
def sosu_webdriver_browser() -> Optional[Browser]:
    return Browser.default()


@pytest.fixture
def sosu_sauce_options(sosu_test_name: str, sosu_build_name: str) -> SauceOptions:
    return SauceOptions(
        name=sosu_test_name,
        build=sosu_build_name,
    )


@pytest.fixture
def sosu_webdriver_capabilities(
    sosu_sauce_options: SauceOptions,
    sosu_webdriver_platform: Optional[Platform],
    sosu_webdriver_browser: Optional[Browser],
) -> Capabilities:
    return Capabilities(
        browser=sosu_webdriver_browser,
        platform=sosu_webdriver_platform,
        sauce_options=sosu_sauce_options,
    )


@pytest.fixture
def sosu_webdriver_parameter_capabilities() -> Capabilities:
    return Capabilities()


@pytest.fixture
def sosu_webdriver_combined_capabilities(
    sosu_webdriver_capabilities: Capabilities,
    sosu_webdriver_parameter_capabilities: Capabilities,
) -> Capabilities:
    return sosu_webdriver_capabilities.merge(sosu_webdriver_parameter_capabilities)


@pytest.fixture
def sosu_webdriver(
    request,
    sosu_webdriver_url_data: WebDriverUrlData,
    sosu_webdriver_combined_capabilities: Capabilities,
):
    with remote_webdriver_ctx(
        sosu_webdriver_url_data,
        sosu_webdriver_combined_capabilities,
    ) as webdriver:
        yield webdriver
        # Using attribute defined in `pytest_runtest_makereport`.
        if not hasattr(request.node, "report_when_call"):
            # No report for test call set - assuming the test was interrupted.
            # Use marker exception for the `remote_webdriver_ctx`.
            raise WebDriverTestInterrupted()
        if request.node.report_when_call.failed:
            # Use marker exception for the `remote_webdriver_ctx`.
            raise WebDriverTestFailed()

# pylint: disable=redefined-outer-name
import datetime
import logging
from typing import Optional

import pytest

from pytest_sosu.webdriver import (
    Browser,
    Capabilities,
    Platform,
    SauceOptions,
    WDTestFailed,
    WDTestInterrupted,
    WDUrlData,
    get_remote_webdriver_url_data,
    remote_webdriver_ctx,
)

logger = logging.getLogger(__name__)


def pytest_configure(config):
    logger.debug("pytest_runtest_setup %s", config)
    # register an additional marker
    config.addinivalue_line("markers", "sosu(type): mark test to run with Sauce Labs")


def pytest_runtest_setup(item):
    logger.debug("pytest_runtest_setup %s", item)
    sosu_markers = list(item.iter_markers(name="sosu"))
    if sosu_markers:
        logger.info("sosu marker(s) found %s", sosu_markers)


def pytest_generate_tests(metafunc):
    logger.debug("pytest_generate_tests %s %s", metafunc, metafunc.fixturenames)
    if "sosu_webdriver_capabilities" in metafunc.fixturenames:
        return
        if "sosu_webdriver_browser" in metafunc.fixturenames:
            browsers = [Browser("Chrome"), Browser("Firefox")]
            metafunc.parametrize(
                "sosu_webdriver_browser", [pytest.param(b, id=str(b)) for b in browsers]
            )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Execute all other hooks to obtain the report object.
    outcome = yield
    report = outcome.get_result()

    # Set a report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"
    setattr(item, "report_when_" + report.when, report)


@pytest.fixture(scope="session")
def sosu_build_basename():
    return None


@pytest.fixture(scope="session")
def sosu_build_time_tag() -> str:
    now = datetime.datetime.now()
    date_str = f"{now.year}-{now.month:02d}-{now.day:02d}"
    time_str = f"{now.hour:02d}:{now.minute:02d}"
    return f"{date_str} {time_str}"


@pytest.fixture(scope="session")
def sosu_build_version(sosu_build_time_tag) -> str:
    return sosu_build_time_tag


@pytest.fixture(scope="session")
def sosu_build_name(sosu_build_basename, sosu_build_version) -> Optional[str]:
    if sosu_build_basename is None:
        return None
    return f"{sosu_build_basename} {sosu_build_version}"


@pytest.fixture
def sosu_webdriver_url_data(request) -> WDUrlData:
    return get_remote_webdriver_url_data()


@pytest.fixture
def sosu_test_name(request) -> str:
    return f"{request.node.function.__module__}::{request.node.name}"


@pytest.fixture
def sosu_webdriver_platform(request) -> Optional[Platform]:
    return Platform.default()


@pytest.fixture
def sosu_webdriver_browser(request) -> Optional[Browser]:
    return Browser.default()


@pytest.fixture
def sosu_webdriver_capabilities(
    sosu_test_name, sosu_build_name, sosu_webdriver_platform, sosu_webdriver_browser
) -> Capabilities:
    sauce_options = SauceOptions(
        name=sosu_test_name,
        build=sosu_build_name,
    )
    return Capabilities(
        browser=sosu_webdriver_browser,
        platform=sosu_webdriver_platform,
        sauce_options=sauce_options,
    )


@pytest.fixture
def sosu_webdriver(
    request,
    sosu_webdriver_url_data: WDUrlData,
    sosu_webdriver_capabilities: Capabilities,
):
    with remote_webdriver_ctx(
        sosu_webdriver_url_data,
        sosu_webdriver_capabilities,
    ) as webdriver:
        yield webdriver
        # Using attribute defined in `pytest_runtest_makereport`.
        if not hasattr(request.node, "report_when_call"):
            # No report for test call set - assuming the test was interrupted.
            # Use marker exception for the `remote_webdriver_ctx`.
            raise WDTestInterrupted()
        if request.node.report_when_call.failed:
            # Use marker exception for the `remote_webdriver_ctx`.
            raise WDTestFailed()

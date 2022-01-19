# pylint: disable=redefined-outer-name
import datetime
from typing import List, Optional

import pytest

from pytest_sosu.logging import get_struct_logger
from pytest_sosu.webdriver import (
    Browser,
    Capabilities,
    CapabilitiesMatrix,
    Platform,
    SauceOptions,
    WebDriverTestFailed,
    WebDriverTestInterrupted,
    WebDriverUrlData,
    get_remote_webdriver_url_data,
    remote_webdriver_ctx,
)

logger = get_struct_logger(__name__)


def pytest_configure(config):
    logger.debug("pytest_runtest_setup", config=config)
    # register an additional marker
    config.addinivalue_line("markers", "sosu(type): mark test to run with Sauce Labs")


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
    sosu_markers = [
        item for item in metafunc.definition.own_markers if item.name == "sosu"
    ]
    if not sosu_markers:
        return
    logger.debug("generate tests sosu marker(s) found", sosu_markers=sosu_markers)

    if "sosu_webdriver_parameter_capabilities" not in metafunc.fixturenames:
        return

    caps_matrix_list: List[CapabilitiesMatrix] = [
        m.kwargs.get("capabilities_matrix") for m in sosu_markers
    ]
    caps_matrix_list = [cm for cm in caps_matrix_list if cm is not None]

    assert len(caps_matrix_list) <= 1

    if not caps_matrix_list:
        return

    caps_matrix = caps_matrix_list[0]

    metafunc.parametrize(
        "sosu_webdriver_parameter_capabilities",
        [pytest.param(c, id=c.slug) for c in caps_matrix.iter_capabilities()],
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
def sosu_build_basename() -> Optional[str]:
    return None


@pytest.fixture(scope="session")
def sosu_build_time_tag() -> str:
    now = datetime.datetime.now()
    date_str = f"{now.year}-{now.month:02d}-{now.day:02d}"
    time_str = f"{now.hour:02d}:{now.minute:02d}"
    return f"{date_str} {time_str}"


@pytest.fixture(scope="session")
def sosu_build_version(sosu_build_time_tag: str) -> str:
    return sosu_build_time_tag


@pytest.fixture(scope="session")
def sosu_build_name(sosu_build_basename: str, sosu_build_version: str) -> Optional[str]:
    if sosu_build_basename is None:
        return None
    return f"{sosu_build_basename} {sosu_build_version}"


@pytest.fixture
def sosu_webdriver_url_data() -> WebDriverUrlData:
    return get_remote_webdriver_url_data()


@pytest.fixture
def sosu_test_name(request: pytest.FixtureRequest) -> str:
    return f"{request.node.function.__module__}::{request.node.name}"


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
def sosu_webdriver_base_capabilities(
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
def sosu_webdriver_capabilities(
    sosu_webdriver_base_capabilities: Capabilities,
    sosu_webdriver_parameter_capabilities: Capabilities,
) -> Capabilities:
    return sosu_webdriver_base_capabilities.merge(sosu_webdriver_parameter_capabilities)


@pytest.fixture
def sosu_webdriver(
    request,
    sosu_webdriver_url_data: WebDriverUrlData,
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
            raise WebDriverTestInterrupted()
        if request.node.report_when_call.failed:
            # Use marker exception for the `remote_webdriver_ctx`.
            raise WebDriverTestFailed()

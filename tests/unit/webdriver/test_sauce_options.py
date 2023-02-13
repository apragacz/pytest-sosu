from typing import Any, Dict

import pytest
import selenium

from pytest_sosu.webdriver import SauceOptions


@pytest.mark.parametrize(
    "opts1,opts2,expected_result",
    [
        pytest.param(
            SauceOptions(name="test name 1"),
            SauceOptions(),
            SauceOptions(name="test name 1"),
            id="first",
        ),
        pytest.param(
            SauceOptions(),
            SauceOptions(name="test name 2"),
            SauceOptions(name="test name 2"),
            id="second",
        ),
        pytest.param(
            SauceOptions(name="test name 1"),
            SauceOptions(build="test build 2"),
            SauceOptions(name="test name 1", build="test build 2"),
            id="mixed",
        ),
        pytest.param(
            SauceOptions(name="test name 1", build="test build 1"),
            SauceOptions(name="test name 2"),
            SauceOptions(name="test name 2", build="test build 1"),
            id="mixed override",
        ),
    ],
)
def test_merge(opts1: SauceOptions, opts2: SauceOptions, expected_result: SauceOptions):
    assert opts1.merge(opts2) == expected_result


@pytest.mark.parametrize(
    "opts,"
    "expected_result",
    [
        pytest.param(
            SauceOptions(name="test name"),
            {
                "name": "test name",
            },
            id="name",
        ),
        pytest.param(
            SauceOptions(record_video=False),
            {
                "recordVideo": False,
            },
            id="record video",
        ),
        pytest.param(
            SauceOptions(name="test name", auto_include_selenium_version=True),
            {
                "name": "test name",
                "seleniumVersion": selenium.__version__,
            },
            id="name",
        ),
        pytest.param(
            SauceOptions(record_video=False, auto_include_selenium_version=True),
            {
                "recordVideo": False,
                "seleniumVersion": selenium.__version__,
            },
            id="record video",
        ),
    ],
)
def test_to_dict(opts: SauceOptions, expected_result: Dict[str, Any]):
    assert opts.to_dict() == expected_result

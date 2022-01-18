import pytest

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

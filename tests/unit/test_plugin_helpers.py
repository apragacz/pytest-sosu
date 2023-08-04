import pytest

from pytest_sosu.config import DEFAULT_SAUCE_BUILD_FORMAT
from pytest_sosu.plugin_helpers import build_sosu_build_name


@pytest.mark.parametrize(
    "basename,version,fmt,output",
    (
        (None, "123", DEFAULT_SAUCE_BUILD_FORMAT, None),
        ("foo", "123", "", None),
        ("foo", "123", DEFAULT_SAUCE_BUILD_FORMAT, "foo_123"),
    ),
)
def test_build_sosu_build_name(basename, version, fmt, output):
    assert build_sosu_build_name(basename, version, fmt) == output

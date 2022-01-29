import pytest

from pytest_sosu.webdriver import Platform


def test_init():
    assert Platform("windows").version is None
    assert Platform("windows", "10").version == "10"
    assert Platform("windows", 11).version == "11"


def test_full_name(platform_win, platform_win11):
    assert platform_win.full_name == "windows"
    assert platform_win11.full_name == "windows 11"


def test_slug(platform_win, platform_win11):
    assert platform_win.slug == "windows"
    assert platform_win11.slug == "windows-11"


def test_to_dict(platform_win):
    assert platform_win.to_dict() == {"name": "windows", "version": None}


@pytest.fixture
def platform_win():
    return Platform("windows")


@pytest.fixture
def platform_win11():
    return Platform("windows", 11)

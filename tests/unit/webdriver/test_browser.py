import pytest

from pytest_sosu.webdriver import Browser


def test_init():
    assert Browser("firefox").version == "latest"
    assert Browser("firefox", "94").version == "94"
    assert Browser("firefox", 96).version == "96"


def test_slug(browser_ff):
    assert browser_ff.slug == "firefox-latest"


def test_full_name(browser_ff):
    assert browser_ff.full_name == "firefox latest"


def test_to_dict(browser_ff):
    assert browser_ff.to_dict() == {"name": "firefox", "version": "latest"}


@pytest.fixture
def browser_ff():
    return Browser("firefox")

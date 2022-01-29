import pytest

from pytest_sosu.webdriver import WebDriverUrlData


def test_from_url():
    wd_url_data = WebDriverUrlData.from_url(
        "https://testuser:testkey@ondemand.us-west-1.saucelabs.com/wd/hub"
    )
    assert wd_url_data.host == "ondemand.us-west-1.saucelabs.com"
    assert wd_url_data.port is None
    assert wd_url_data.path == "/wd/hub"
    assert wd_url_data.username == "testuser"
    assert wd_url_data.access_key == "testkey"


def test_with_credentials(
    wd_url_data_without_creds: WebDriverUrlData, wd_url_data: WebDriverUrlData
):
    assert (
        wd_url_data_without_creds.with_credentials("testuser", "testkey") == wd_url_data
    )


def test_to_url(
    wd_url_data: WebDriverUrlData, wd_url_data_without_creds: WebDriverUrlData
):
    assert (
        wd_url_data.to_url()
        == "https://testuser:testkey@ondemand.us-west-1.saucelabs.com/wd/hub"
    )
    assert (
        wd_url_data_without_creds.to_url()
        == "https://ondemand.us-west-1.saucelabs.com/wd/hub"
    )


def test_to_safe_url(
    wd_url_data: WebDriverUrlData, wd_url_data_without_creds: WebDriverUrlData
):
    assert (
        wd_url_data.to_safe_url()
        == "https://testuser:*******@ondemand.us-west-1.saucelabs.com/wd/hub"
    )
    assert (
        wd_url_data_without_creds.to_safe_url()
        == "https://ondemand.us-west-1.saucelabs.com/wd/hub"
    )


@pytest.fixture
def wd_url_data():
    return WebDriverUrlData(
        scheme="https",
        username="testuser",
        access_key="testkey",
        host="ondemand.us-west-1.saucelabs.com",
        path="/wd/hub",
    )


@pytest.fixture
def wd_url_data_without_creds():
    return WebDriverUrlData(
        scheme="https",
        host="ondemand.us-west-1.saucelabs.com",
        path="/wd/hub",
    )

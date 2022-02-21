# Pytest-Sosu

Pytest-Sosu (pronounced Sōsu, ソース) is an unofficial Pytest plugin for running tests
on Sauce Labs platforms.

## Installation

You can install pytest-sosu latest version via pip:

    pip install pytest-sosu

## Basic Usage

Assuming you have `SAUCE_USERNAME` and `SAUCE_ACCESS_KEY` environment variables set
(credentials can be obtained [here](https://app.saucelabs.com/user-settings)),
you can write a simple test:

```python
def test_visit(sosu_webdriver):
    driver = sosu_webdriver
    driver.get("http://example.com/")
    assert driver.title == "Example Domain"
```

## Examples

```python
from pytest_sosu.webdriver import CapabilitiesMatrix, Browser


# running given test on multiple browsers
@pytest.mark.sosu(
    capabilities_matrix=CapabilitiesMatrix(
        browsers=[Browser("chrome"), Browser("firefox")],
    ),
)
def test_visit_many_browsers(driver):
    driver.get("http://example.com/")
    assert driver.title == "Example Domain"

# when build basename is set, tests running in given pytest session
# have a build assigned
@pytest.fixture(scope="session")
def sosu_build_basename():
    return 'my-project-name'


# alias for sosu_webdriver
@pytest.fixture
def driver(sosu_webdriver):
    yield sosu_webdriver
```

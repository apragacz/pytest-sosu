import os

from pytest_sosu.utils import int_or_none

SAUCE_USERNAME = os.environ.get("SAUCE_USERNAME")
SAUCE_ACCESS_KEY = os.environ.get("SAUCE_ACCESS_KEY")
SAUCE_REGION = os.environ.get("SAUCE_REGION", "us-west-1")
SAUCE_WEBDRIVER_URL = os.environ.get("SAUCE_WEBDRIVER_URL")
SAUCE_WEBDRIVER_HOST = os.environ.get("SAUCE_WEBDRIVER_HOST")
SAUCE_WEBDRIVER_PORT = int_or_none(os.environ.get("SAUCE_WEBDRIVER_PORT"))
SAUCE_WEBDRIVER_SCHEME = os.environ.get("SAUCE_WEBDRIVER_SCHEME", "https")
SAUCE_WEBDRIVER_PATH = os.environ.get("SAUCE_WEBDRIVER_PATH", "/wd/hub")

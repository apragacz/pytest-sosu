from __future__ import annotations

import contextlib
import enum
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse

import selenium  # type: ignore
import selenium.webdriver  # type: ignore

from pytest_sosu import settings

logger = logging.getLogger(__name__)

REGION_MAP = {
    "us": "us-west-1",
    "eu": "eu-central-1",
    "apac": "apac-southeast-1",
    "headless": "us-east-1",
}


class TestResultsVisibility(enum.Enum):
    PUBLIC = "public"
    PUBLIC_RESTRICTED = "public restricted"
    SHARE = "share"
    TEAM = "team"
    PRIVATE = "private"


@dataclass(frozen=True)
class WDUrlData:
    host: str
    port: Optional[int] = None
    scheme: str = "https"
    username: Optional[str] = None
    access_key: Optional[str] = None
    path: str = "/wd/hub"

    @classmethod
    def from_url(cls, url: str) -> WDUrlData:
        result = urlparse(url)
        if ":" in result.netloc:
            host, port_str = result.netloc.rsplit(":", 1)
            port: Optional[int] = int(port_str)
        else:
            host = result.netloc
            port = None
        return cls(
            scheme=result.scheme,
            username=result.username,
            access_key=result.password,
            host=host,
            port=port,
            path=result.path,
        )

    @property
    def address(self) -> str:
        if self.port is None:
            return self.host
        return f"{self.host}:{self.port}"

    @property
    def _access_key_starred(self) -> Optional[str]:
        if self.access_key is None:
            return None
        return "*" * len(self.access_key)

    @property
    def has_credentials(self) -> bool:
        return bool(self.username and self.access_key)

    def __repr__(self) -> str:
        url = self.to_safe_url()
        return f"{self.__class__.__name__}({url!r})"

    def to_url(self) -> str:
        return self._to_url(self.access_key)

    def to_safe_url(self) -> str:
        return self._to_url(self._access_key_starred)

    def _to_url(self, access_key: Optional[str]) -> str:
        auth_prefix = ""
        if self.username and access_key:
            auth_prefix = f"{self.username}:{access_key}@"
        return f"{self.scheme}://{auth_prefix}{self.address}{self.path}"  # noqa: E501

    def with_credentials(self, username, access_key) -> WDUrlData:
        return self.__class__(
            host=self.host,
            port=self.port,
            scheme=self.scheme,
            username=username,
            access_key=access_key,
            path=self.path,
        )


class WDTestMarkerException(Exception):
    pass


class WDTestFailed(WDTestMarkerException):
    pass


class WDTestInterrupted(WDTestMarkerException):
    pass


@dataclass(frozen=True)
class Browser:
    name: str
    version: str = "latest"

    @classmethod
    def default(cls) -> Optional[Browser]:
        return cls(name="chrome")

    def __str__(self) -> str:
        return f"{self.name} {self.version}"


@dataclass(frozen=True)
class Platform:
    name: str
    version: Optional[str] = None

    @classmethod
    def default(cls) -> Optional[Platform]:
        return None

    @classmethod
    def windows_default(cls) -> Optional[Platform]:
        return cls(name="Windows")

    @property
    def full_name(self) -> str:
        if self.version is None:
            return f"{self.name}"
        return f"{self.name} {self.version}"

    def __str__(self) -> str:
        return self.full_name


@dataclass(frozen=True)
class SauceOptions:
    name: str = "pytest-sosu test"
    build: Optional[str] = None
    max_duration: int = 1800
    idle_timeout: int = 90
    command_timeout: int = 300
    visibility: Optional[TestResultsVisibility] = None

    @classmethod
    def default(cls) -> SauceOptions:
        return cls()

    def to_dict(self) -> Dict[str, Union[str, int, float]]:
        data = {
            "name": self.name,
            "seleniumVersion": selenium.__version__,
            "maxDuration": self.max_duration,
            "idleTimeout": self.idle_timeout,
            "commandTimeout": self.command_timeout,
        }
        if self.visibility:
            data["public"] = self.visibility.value
        if self.build:
            data["build"] = self.build
        return data


@dataclass(frozen=True)
class Capabilities:
    browser: Optional[Browser] = Browser.default()
    platform: Optional[Platform] = Platform.default()
    sauce_options: SauceOptions = SauceOptions.default()

    def to_dict(self, w3c: bool = True) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        if w3c:
            data.update(
                {
                    "sauce:options": {},
                }
            )
            if self.platform is not None:
                data.update(
                    {
                        "platformName": self.platform.full_name,
                    }
                )
            if self.browser is not None:
                data.update(
                    {
                        "browserName": self.browser.name,
                        "browserVersion": self.browser.version,
                    }
                )
        else:
            if self.platform is not None:
                data.update(
                    {
                        "platform": self.platform.full_name,
                    }
                )
            if self.browser is not None:
                data.update(
                    {
                        "browserName": self.browser.name,
                        "version": self.browser.version,
                    }
                )

        sauce_options_data = data["sauce:options"] if w3c else data
        sauce_options_data.update(self.sauce_options.to_dict())

        return data


@contextlib.contextmanager
def remote_webdriver_ctx(
    url_data: WDUrlData,
    capabilities: Capabilities,
    quit_on_finish: bool = True,
    mark_result_on_finish: bool = True,
    setup_timeouts: bool = True,
):
    logger.debug("Driver starting with caps %s...", capabilities)
    driver = create_remote_webdriver(
        url_data, capabilities, setup_timeouts=setup_timeouts
    )
    logger.debug("Driver %r started", driver)
    logger.info("Session %s started", driver.session_id)
    job_result: Optional[str] = "failed"
    try:
        yield driver
        job_result = "passed"
    except WDTestFailed:
        pass
    except (WDTestInterrupted, KeyboardInterrupt):
        job_result = None
    finally:
        if mark_result_on_finish:
            if job_result is not None:
                logger.debug("Marking test as %s...", job_result)
                driver.execute_script(f"sauce:job-result={job_result}")
            else:
                logger.debug("Not marking test as it was interrupted")
        if quit_on_finish:
            logger.debug("Driver %r quitting...", driver)
            driver.quit()
            logger.debug("Driver %r quitted", driver)
        logger.info("Session %s stopped", driver.session_id)


def create_remote_webdriver(
    url_data: WDUrlData, capabilities: Capabilities, setup_timeouts: bool = True
) -> selenium.webdriver.Remote:
    url = url_data.to_url()
    caps = capabilities.to_dict()
    safe_url = url_data.to_safe_url()
    logger.info("Using webdriver URL: %s", safe_url)
    driver = selenium.webdriver.Remote(
        command_executor=url,
        desired_capabilities=caps,
    )
    if setup_timeouts:
        timeout = capabilities.sauce_options.command_timeout
        driver.set_page_load_timeout(timeout)
        driver.implicitly_wait(timeout)
        driver.set_script_timeout(timeout)
    return driver


def get_remote_webdriver_url_data() -> WDUrlData:
    if settings.SAUCE_WEBDRIVER_URL:
        url_data = WDUrlData.from_url(settings.SAUCE_WEBDRIVER_URL)
    else:
        if settings.SAUCE_WEBDRIVER_HOST:
            host = settings.SAUCE_WEBDRIVER_HOST
        else:
            host = get_host_by_region(settings.SAUCE_REGION)
        url_data = WDUrlData(
            host=host,
            port=settings.SAUCE_WEBDRIVER_PORT,
            scheme=settings.SAUCE_WEBDRIVER_SCHEME,
            path=settings.SAUCE_WEBDRIVER_PATH,
        )
    if not url_data.has_credentials:
        url_data = url_data.with_credentials(
            settings.SAUCE_USERNAME, settings.SAUCE_ACCESS_KEY
        )
    return url_data


def get_host_by_region(region: str) -> str:
    if not region or region == "global":
        return "ondemand.saucelabs.com"
    host_region = REGION_MAP.get(region, region)
    return f"ondemand.{host_region}.saucelabs.com"

from __future__ import annotations

import contextlib
import dataclasses
import enum
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union
from urllib.parse import urlparse

import selenium  # type: ignore
import selenium.webdriver  # type: ignore
import selenium.webdriver.common.by  # type: ignore
from selenium.webdriver import Remote as WebDriver
from selenium.webdriver.common.by import By  # noqa: F401

from pytest_sosu.exceptions import WebDriverTestFailed, WebDriverTestInterrupted
from pytest_sosu.logging import get_struct_logger
from pytest_sosu.utils import (
    ImmutableDict,
    convert_snake_case_to_camel_case,
    str_or_none,
    try_one_of_or_none,
)

logger = get_struct_logger(__name__)


class SauceTestResultsVisibility(enum.Enum):
    PUBLIC = "public"
    PUBLIC_RESTRICTED = "public restricted"
    SHARE = "share"
    TEAM = "team"
    PRIVATE = "private"


@dataclass(frozen=True)
class WebDriverUrlData:
    host: str
    port: Optional[int] = None
    scheme: str = "https"
    username: Optional[str] = None
    access_key: Optional[str] = None
    path: str = "/wd/hub"

    @classmethod
    def from_url(cls, url: str) -> WebDriverUrlData:
        result = urlparse(url)
        if result.hostname is None:
            raise ValueError("missing hostname")
        return cls(
            scheme=result.scheme,
            username=result.username,
            access_key=result.password,
            host=result.hostname,
            port=result.port,
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

    def with_credentials(self, username, access_key) -> WebDriverUrlData:
        return self.__class__(
            host=self.host,
            port=self.port,
            scheme=self.scheme,
            username=username,
            access_key=access_key,
            path=self.path,
        )


@dataclass(frozen=True)
class BaseBrowser:
    name: str
    version: str = "latest"


@dataclass(frozen=True)
class Browser(BaseBrowser):
    @classmethod
    def default(cls) -> Optional[Browser]:
        return cls(name="chrome")

    def __init__(self, name: str, version: Union[str, int] = "latest") -> None:
        super().__init__(name=name, version=str(version))

    @property
    def full_name(self) -> str:
        return f"{self.name} {self.version}"

    @property
    def slug(self) -> str:
        return f"{self.name}-{self.version}"

    def __str__(self) -> str:
        return self.full_name

    def __structlog__(self) -> Dict[str, Any]:
        return self.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class BasePlatform:
    name: str
    version: Optional[str] = None


@dataclass(frozen=True)
class Platform(BasePlatform):
    @classmethod
    def default(cls) -> Optional[Platform]:
        return None

    @classmethod
    def windows_default(cls) -> Optional[Platform]:
        return cls(name="Windows")

    def __init__(self, name: str, version: Optional[Union[str, int]] = None) -> None:
        super().__init__(name=name, version=str_or_none(version))

    @property
    def full_name(self) -> str:
        if self.version is None:
            return f"{self.name}"
        return f"{self.name} {self.version}"

    @property
    def slug(self) -> str:
        if self.version is None:
            return f"{self.name}"
        return f"{self.name}-{self.version}"

    def __str__(self) -> str:
        return self.full_name

    def __structlog__(self) -> Dict[str, Any]:
        return self.to_dict()

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclass(frozen=True)
class SauceOptions:
    name: Optional[str] = None
    build: Optional[str] = None
    tags: Optional[List[str]] = None
    username: Optional[str] = None
    access_key: Optional[str] = None
    custom_data: Optional[Dict[str, Any]] = None
    visibility: Optional[SauceTestResultsVisibility] = None
    tunnel_name: Optional[str] = None
    tunnel_identifier: Optional[str] = None
    tunnel_owner: Optional[str] = None
    parent_tunnel: Optional[str] = None
    record_video: Optional[bool] = None
    video_upload_on_pass: Optional[bool] = None
    record_screenshots: Optional[bool] = None
    record_logs: Optional[bool] = None
    max_duration: Optional[int] = None
    idle_timeout: Optional[int] = None
    command_timeout: Optional[int] = None
    screen_resolution: Optional[str] = None
    extras: ImmutableDict[str, Any] = dataclasses.field(
        default_factory=lambda: ImmutableDict({}),
    )

    auto_include_selenium_version: bool = True

    TO_DICT_AUTO_EXCLUDES = (
        "custom_data",
        "visibility",
        "auto_include_selenium_version",
        "extras",
    )

    @classmethod
    def default(cls) -> SauceOptions:
        return cls()

    def __structlog__(self):
        return self.to_dict()

    def merge(self, other: SauceOptions) -> SauceOptions:
        kwargs: Dict[str, Any] = {}
        for field in dataclasses.fields(self):
            name = field.name
            kwargs[name] = self._merge_field(other, name)
        new_opts = SauceOptions(**kwargs)
        return new_opts

    def _merge_field(self, other, name):
        return try_one_of_or_none(
            getattr(other, name),
            lambda: getattr(self, name),
        )

    def to_dict(
        self, auto_include_selenium_version: Optional[bool] = None
    ) -> Dict[str, Union[str, int, float]]:
        if auto_include_selenium_version is None:
            auto_include_selenium_version = self.auto_include_selenium_version

        data = {}
        if auto_include_selenium_version:
            data["seleniumVersion"] = selenium.__version__
        for field in dataclasses.fields(self):
            name = field.name
            if name in self.TO_DICT_AUTO_EXCLUDES:
                continue
            value = getattr(self, name)
            if value is None:
                continue
            dict_name = convert_snake_case_to_camel_case(name)
            data[dict_name] = value
        if self.custom_data is not None:
            data["custom-data"] = self.custom_data
        if self.visibility is not None:
            data["public"] = self.visibility.value
        data.update(self.extras)
        return data


@dataclass(frozen=True)
class Capabilities:
    browser: Optional[Browser] = Browser.default()
    platform: Optional[Platform] = Platform.default()
    sauce_options: SauceOptions = SauceOptions.default()
    extras: ImmutableDict[str, Any] = dataclasses.field(
        default_factory=lambda: ImmutableDict({}),
    )

    w3c_mode: bool = True

    @property
    def slug(self):
        if self.browser is None and self.platform is None:
            return "default"
        if self.platform is None:
            return self.browser.slug
        if self.browser is None:
            return self.platform.slug
        return f"{self.browser.slug}-on-{self.platform.slug}"

    def __structlog__(self):
        return self.to_dict()

    def merge(self, other: Capabilities) -> Capabilities:
        new_caps = Capabilities(
            browser=try_one_of_or_none(other.browser, lambda: self.browser),
            platform=try_one_of_or_none(other.platform, lambda: self.platform),
            sauce_options=self.sauce_options.merge(other.sauce_options),
        )
        return new_caps

    def to_dict(
        self,
        w3c_mode: Optional[bool] = None,
        auto_include_selenium_version: Optional[bool] = None,
    ) -> Dict[str, Any]:
        if w3c_mode is None:
            w3c_mode = self.w3c_mode

        data: Dict[str, Any] = {}
        if w3c_mode:
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

        sauce_options_data = data["sauce:options"] if w3c_mode else data
        sauce_options_data.update(
            self.sauce_options.to_dict(
                auto_include_selenium_version=auto_include_selenium_version,
            )
        )

        data.update(self.extras)

        return data


@dataclass(frozen=True)
class CapabilitiesMatrix:
    browsers: Optional[List[Browser]] = None
    platforms: Optional[List[Platform]] = None
    sauce_options_list: Optional[List[SauceOptions]] = None

    def __structlog__(self) -> Dict[str, Any]:
        return self.to_dict()

    def iter_capabilities(self) -> Iterator[Capabilities]:
        browsers: Sequence[Optional[Browser]] = [None]
        if self.browsers is not None:
            browsers = self.browsers
        platforms: Sequence[Optional[Platform]] = [None]
        if self.platforms is not None:
            platforms = self.platforms
        sauce_options_list = (
            [SauceOptions.default()]
            if self.sauce_options_list is None
            else self.sauce_options_list
        )
        for browser in browsers:
            for platform in platforms:
                for sauce_options in sauce_options_list:
                    yield Capabilities(
                        browser=browser,
                        platform=platform,
                        sauce_options=sauce_options,
                    )

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@contextlib.contextmanager
def remote_webdriver_ctx(
    url_data: WebDriverUrlData,
    capabilities: Capabilities,
    quit_on_finish: bool = True,
    mark_result_on_finish: bool = True,
    setup_timeouts: bool = True,
):
    wd_safe_url = url_data.to_safe_url()
    logger.debug("Driver starting", capabilities=capabilities, wd_url=wd_safe_url)
    driver = create_remote_webdriver(
        url_data,
        capabilities,
        setup_timeouts=setup_timeouts,
    )
    session_id = driver.session_id
    logger.debug(
        "Driver started",
        capabilities=capabilities,
        wd_url=wd_safe_url,
        driver=driver,
    )
    logger.info("Session started", wd_url=wd_safe_url, session_id=session_id)
    job_result: Optional[str] = "failed"
    try:
        yield driver
        job_result = "passed"
    except WebDriverTestFailed:
        pass
    except (WebDriverTestInterrupted, KeyboardInterrupt):
        job_result = None
    finally:
        if mark_result_on_finish:
            if job_result is not None:
                logger.debug(
                    "Marking test",
                    session_id=session_id,
                    job_result=job_result,
                )
                driver.execute_script(f"sauce:job-result={job_result}")
            else:
                logger.debug(
                    "Not marking test as it was interrupted",
                    session_id=session_id,
                )
        if quit_on_finish:
            logger.debug("Driver quitting", driver=driver)
            driver.quit()
            logger.debug("Driver quitted", driver=driver)
        logger.info("Session stopped", session_id=session_id)


def create_remote_webdriver(
    wd_url_data: WebDriverUrlData,
    capabilities: Capabilities,
    setup_timeouts: bool = True,
) -> WebDriver:
    wd_url = wd_url_data.to_url()
    caps = capabilities.to_dict()
    wd_safe_url = wd_url_data.to_safe_url()
    logger.debug("Using webdriver URL", wd_url=wd_safe_url)
    driver = WebDriver(
        command_executor=wd_url,
        desired_capabilities=caps,
    )
    if setup_timeouts:
        timeout = capabilities.sauce_options.command_timeout
        if timeout is not None:
            driver.set_page_load_timeout(timeout)
            driver.implicitly_wait(timeout)
            driver.set_script_timeout(timeout)
    return driver

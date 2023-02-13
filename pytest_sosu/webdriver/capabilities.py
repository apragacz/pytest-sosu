from __future__ import annotations

import dataclasses
import enum
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union

import selenium  # type: ignore
import selenium.webdriver  # type: ignore
import selenium.webdriver.common.by  # type: ignore

from pytest_sosu.logging import get_struct_logger
from pytest_sosu.utils import (
    ImmutableDict,
    convert_snake_case_to_camel_case,
    try_one_of,
    try_one_of_or_none,
)
from pytest_sosu.webdriver.platforms import Browser, Platform

logger = get_struct_logger(__name__)


class SauceTestResultsVisibility(enum.Enum):
    PUBLIC = "public"
    PUBLIC_RESTRICTED = "public restricted"
    SHARE = "share"
    TEAM = "team"
    PRIVATE = "private"


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

    auto_include_selenium_version: Optional[bool] = None

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
            if name == "extras":
                continue
            kwargs[name] = self._merge_field(other, name)
        kwargs["extras"] = self.extras.merge(other.extras)
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
        auto_include_selenium_version = try_one_of(
            auto_include_selenium_version,
            lambda: self.auto_include_selenium_version,
            default=False,
        )

        data: Dict[str, Any] = {}
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

    w3c_mode: Optional[bool] = None

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
            extras=self.extras.merge(other.extras),
            w3c_mode=try_one_of_or_none(other.w3c_mode, lambda: self.w3c_mode),
        )
        return new_caps

    def to_dict(
        self,
        w3c_mode: Optional[bool] = None,
        auto_include_selenium_version: Optional[bool] = None,
    ) -> Dict[str, Any]:
        w3c_mode = try_one_of(w3c_mode, lambda: self.w3c_mode, default=True)

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

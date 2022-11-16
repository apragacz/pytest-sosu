import argparse
import os
from dataclasses import dataclass
from typing import Optional

from _pytest.config import UsageError

from pytest_sosu.logging import get_struct_logger
from pytest_sosu.webdriver import WebDriverUrlData

logger = get_struct_logger(__name__)


@dataclass
class SosuConfig:
    username: str
    access_key: str
    region: Optional[str]
    webdriver_url_data: WebDriverUrlData

    @property
    def webdriver_url_data_with_credentials(self) -> WebDriverUrlData:
        if not self.webdriver_url_data.has_credentials:
            return self.webdriver_url_data.with_credentials(
                self.username, self.access_key
            )
        return self.webdriver_url_data


def build_sosu_config(args: argparse.Namespace, env: os._Environ) -> SosuConfig:
    logger.debug("build_sosu_config", args=args, env=env)
    username = args.sosu_username or env.get("SAUCE_USERNAME")
    access_key = args.sosu_access_key or env.get("SAUCE_ACCESS_KEY")

    if not username:
        raise UsageError("--sosu-username or SAUCE_USERNAME are not provided")

    if not access_key:
        raise UsageError("--sosu-access-key or SAUCE_ACCESS_KEY are not provided")

    region: Optional[str] = args.sosu_region or env.get("SAUCE_REGION")
    webdriver_url = args.sosu_webdriver_url or env.get("SAUCE_WEBDRIVER_URL")

    if not webdriver_url:
        host = get_host_by_region(region)
        webdriver_url_data = WebDriverUrlData(host=host)
    else:
        try:
            webdriver_url_data = WebDriverUrlData.from_url(webdriver_url)
        except ValueError:
            raise UsageError("Invalid WebDriver URL") from None

    return SosuConfig(
        username=username,
        access_key=access_key,
        region=region,
        webdriver_url_data=webdriver_url_data,
    )


def get_host_by_region(region: Optional[str]) -> str:
    if not region or region == "global":
        return "ondemand.saucelabs.com"
    host_region = REGION_MAP.get(region, region)
    return f"ondemand.{host_region}.saucelabs.com"


REGION_MAP = {
    "us": "us-west-1",
    "eu": "eu-central-1",
    "apac": "apac-southeast-1",
    "headless": "us-east-1",
}

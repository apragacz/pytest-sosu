from __future__ import annotations

import contextlib
from typing import Optional

from selenium.webdriver import Remote as WebDriver  # type: ignore
from selenium.webdriver.common.by import By  # noqa: F401 type: ignore

from pytest_sosu.exceptions import WebDriverTestFailed, WebDriverTestInterrupted
from pytest_sosu.logging import get_struct_logger
from pytest_sosu.webdriver.capabilities import Capabilities
from pytest_sosu.webdriver.url import WebDriverUrlData

logger = get_struct_logger(__name__)


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
    logger.debug("Dumping caps data", caps=caps)
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

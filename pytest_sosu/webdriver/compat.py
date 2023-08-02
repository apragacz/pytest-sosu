from typing import Optional

selenium_version: Optional[str] = None

try:
    import selenium  # type: ignore

    selenium_version = selenium.__version__
except ImportError:
    pass

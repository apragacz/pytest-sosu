from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


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

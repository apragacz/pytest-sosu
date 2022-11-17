from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

from pytest_sosu.utils import str_or_none


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

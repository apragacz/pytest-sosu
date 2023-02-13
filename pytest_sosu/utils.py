from __future__ import annotations

from enum import Enum
from numbers import Number
from types import MappingProxyType
from typing import Any, Callable, Dict, Iterator, Mapping, Optional, TypeVar, Union

from pytest_sosu.typing import Literal

_T = TypeVar("_T")
_S = TypeVar("_S")


class DefaultValues(Enum):
    RAISE_EXCEPTION = "raise-exception"


RAISE_EXCEPTION = DefaultValues.RAISE_EXCEPTION


class ImmutableDict(Mapping[_T, _S]):
    def __init__(self, _dict: Mapping[_T, _S]):
        self._mapping_proxy = MappingProxyType(_dict)

    def __getitem__(self, key: _T) -> _S:
        return self._mapping_proxy[key]

    def __iter__(self) -> Iterator[_T]:
        return iter(self._mapping_proxy)

    def __len__(self) -> int:
        return len(self._mapping_proxy)

    def __hash__(self) -> int:
        return hash(tuple(sorted((k, v) for k, v in self._mapping_proxy.items())))

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({dict(self._mapping_proxy)})"

    def merge(self, other: ImmutableDict[_T, _S]) -> ImmutableDict[_T, _S]:
        data: Dict[_T, _S] = {}
        data.update(self._mapping_proxy)
        data.update(other)
        return self.__class__(data)


TRUTHY_VALUES = {"true", "t", "yes", "y", "1"}
FALSY_VALUES = {"false", "f", "no", "n", "0"}


def smart_bool_or_none(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, Number):
        if value == 1:
            return True
        if value == 0:
            return False
    if isinstance(value, str):
        value_lower = value.lower()
        if value_lower in TRUTHY_VALUES:
            return True
        if value_lower in FALSY_VALUES:
            return False
    return None


def smart_bool(value: Any, default: bool = False) -> bool:
    return smart_bool_or_none(value) or default


def convert_or_none(value: Any, converter_func: Callable[[Any], _T]) -> Optional[_T]:
    if value is None:
        return None
    return converter_func(value)


def str_or_none(value: Any) -> Optional[str]:
    return convert_or_none(value, str)


def try_one_of_or_none(
    first: Optional[_T],
    *other_getters: Callable[[], Optional[_T]],
) -> Optional[_T]:
    try:
        return try_one_of(first, *other_getters)
    except ValueError:
        return None


def try_one_of(
    first: Optional[_T],
    *other_getters: Callable[[], Optional[_T]],
    default: Union[_T, Literal[DefaultValues.RAISE_EXCEPTION]] = RAISE_EXCEPTION,
) -> _T:
    value = first
    if value is not None:
        return value
    for value_getter in other_getters:
        value = value_getter()
        if value is not None:
            return value
    if default is RAISE_EXCEPTION:
        raise ValueError("Could not match any of the value")
    return default


def convert_snake_case_to_camel_case(value: str) -> str:
    first_segment, *other_segments = value.split("_")
    return first_segment + "".join(seg.capitalize() for seg in other_segments)

from enum import Enum
from typing import Any, Callable, Optional, TypeVar, Union

from pytest_sosu.typing import Literal

_T = TypeVar("_T")


class DefaultValues(Enum):
    RAISE_EXCEPTION = "raise-exception"


RAISE_EXCEPTION = DefaultValues.RAISE_EXCEPTION


def smart_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "t", "yes", "y", "1"}


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

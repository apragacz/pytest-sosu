from typing import Any, Callable, Optional, TypeVar, Union

_T = TypeVar("_T")


class _RaiseExceptionType:
    pass


_RAISE_EXCEPTION = _RaiseExceptionType()


def smart_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "t", "yes", "y", "1"}


def int_or_none(value: Any) -> Optional[int]:
    if value is None:
        return None
    return int(value)


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
    default: Union[_T, _RaiseExceptionType] = _RAISE_EXCEPTION,
) -> _T:
    value = first
    if value is not None:
        return value
    for value_getter in other_getters:
        value = value_getter()
        if value is not None:
            return value
    if default is _RAISE_EXCEPTION:
        raise ValueError("Could not match any of the value")
    return default

from typing import Any, Optional


def smart_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "t", "yes", "y", "1"}


def int_or_none(value: Any) -> Optional[int]:
    if value is None:
        return None
    return int(value)

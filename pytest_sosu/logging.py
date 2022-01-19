import logging

import structlog
from structlog.stdlib import filter_by_level, render_to_log_kwargs
from structlog.types import EventDict


def get_struct_logger(name):
    return _get_stdlib_struct_logger(name)


def _get_stdlib_struct_logger(name):
    logger = structlog.wrap_logger(
        logging.getLogger(name),
        processors=[
            filter_by_level,
            render_event_dict_into_msg,
            render_to_log_kwargs,
        ],
    )
    return logger


def render_event_dict_into_msg(
    logger: logging.Logger, method_name: str, event_dict: EventDict
):
    event = event_dict.pop("event")
    msg = event + " " + " ".join(_iter_kv_strings(event_dict))
    return {"event": msg}


def _iter_kv_strings(event_dict: EventDict):
    for name, value in event_dict.items():
        yield f"{name}={value}"

import logging
from typing import Callable, Mapping, Optional, Type


def get_struct_logger(name):
    return LazyStructLogger(struct_logger_factory, name)


class StructLogger:
    def __init__(self, name: str) -> None:
        self._name = name
        self._func_dict = {
            logging.DEBUG: self.debug,
            logging.INFO: self.info,
            logging.WARNING: self.warning,
            logging.ERROR: self.error,
            logging.CRITICAL: self.critical,
        }

    def debug(self, msg, **kwargs):
        raise NotImplementedError()

    def info(self, msg, **kwargs):
        raise NotImplementedError()

    def warning(self, msg, **kwargs):
        raise NotImplementedError()

    def error(self, msg, **kwargs):
        raise NotImplementedError()

    def critical(self, msg, **kwargs):
        raise NotImplementedError()

    def log(self, level, msg, **kwargs):
        func = self._func_dict.get(level, self.debug)
        return func(msg, **kwargs)

    def exception(self, msg, **kwargs):
        raise NotImplementedError()


class StdlibStructLogger(StructLogger):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._logger = logging.getLogger(name)

    def debug(self, msg, **kwargs):
        return self._logger.debug(render_full_message(msg, kwargs))

    def info(self, msg, **kwargs):
        return self._logger.info(render_full_message(msg, kwargs))

    def warning(self, msg, **kwargs):
        return self._logger.warning(render_full_message(msg, kwargs))

    def error(self, msg, **kwargs):
        return self._logger.error(render_full_message(msg, kwargs))

    def critical(self, msg, **kwargs):
        return self._logger.critical(render_full_message(msg, kwargs))

    def exception(self, msg, **kwargs):
        return self._logger.exception(render_full_message(msg, kwargs))


class LazyStructLogger(StructLogger):
    def __init__(
        self,
        factory: Callable[[str], StructLogger],
        name: str,
    ) -> None:
        super().__init__(name)
        self._factory = factory
        self._logger: Optional[StructLogger] = None

    @property
    def logger(self) -> StructLogger:
        if self._logger is not None:
            return self._logger
        self._logger = self._factory(self._name)
        return self._logger

    def debug(self, msg, **kwargs):
        return self.logger.debug(msg, **kwargs)

    def info(self, msg, **kwargs):
        return self.logger.info(msg, **kwargs)

    def warning(self, msg, **kwargs):
        return self.logger.warning(msg, **kwargs)

    def error(self, msg, **kwargs):
        return self.logger.error(msg, **kwargs)

    def critical(self, msg, **kwargs):
        return self.logger.critical(msg, **kwargs)

    def exception(self, msg, **kwargs):
        return self.logger.exception(msg, **kwargs)


class StructLoggerFactory:
    def __init__(self, struct_logger_cls: Type[StructLogger]) -> None:
        self._struct_logger_cls = struct_logger_cls

    def __call__(self, name: str) -> StructLogger:
        return self._struct_logger_cls(name)

    def set_struct_logger_class(self, struct_logger_cls: Type[StructLogger]) -> None:
        self._struct_logger_cls = struct_logger_cls


struct_logger_factory = StructLoggerFactory(StdlibStructLogger)
set_struct_logger_class = struct_logger_factory.set_struct_logger_class


def render_full_message(msg: str, data: Mapping) -> str:
    full_msg = msg + "     " + " ".join(_iter_kv_strings(data))
    return full_msg


def _iter_kv_strings(data: Mapping):
    for name, value in data.items():
        yield f"{name}={value!r}"

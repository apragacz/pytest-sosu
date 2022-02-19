class InvalidMarkerConfiguration(Exception):
    pass


class MultipleMarkerParametersFound(InvalidMarkerConfiguration):
    pass


class WebDriverTestMarkerException(Exception):
    pass


class WebDriverTestFailed(WebDriverTestMarkerException):
    pass


class WebDriverTestInterrupted(WebDriverTestMarkerException):
    pass

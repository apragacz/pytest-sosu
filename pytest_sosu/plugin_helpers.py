from typing import Any, List, Optional

import pytest
from _pytest.mark.structures import Mark
from _pytest.python import Metafunc

from pytest_sosu.exceptions import (
    InvalidMarkerConfiguration,
    MultipleMarkerParametersFound,
)
from pytest_sosu.webdriver import Capabilities, CapabilitiesMatrix

SOSU_MARKER_NAME = "sosu"


def parametrize_capabilities(metafunc: Metafunc):
    caps_list = get_marker_capabilites_list_or_none(metafunc)
    if (
        "sosu_webdriver_parameter_capabilities" in metafunc.fixturenames
        and caps_list is not None
    ):
        metafunc.parametrize(
            "sosu_webdriver_parameter_capabilities",
            [pytest.param(c, id=c.slug) for c in caps_list],
        )


def get_marker_capabilites_list_or_none(
    metafunc: Metafunc,
) -> Optional[List[Capabilities]]:
    markers = get_sosu_markers(metafunc)
    caps = _get_marker_capabilites_list_or_none(markers)
    caps_matrix = _get_marker_capabilites_matrix_or_none(markers)

    if caps is not None and caps_matrix is not None:
        raise InvalidMarkerConfiguration(
            "both capabilities_matrix and capabilities are provided"
        )

    if caps is not None:
        return caps

    if caps_matrix is not None:
        return list(caps_matrix.iter_capabilities())

    return None


def get_sosu_markers(metafunc: Metafunc) -> List[Mark]:
    return [
        item
        for item in metafunc.definition.own_markers
        if item.name == SOSU_MARKER_NAME
    ]


def _get_marker_capabilites_matrix_or_none(
    sosu_markers: List[Mark],
) -> Optional[CapabilitiesMatrix]:
    return get_marker_unique_parameter_or_none(sosu_markers, "capabilities_matrix")


def _get_marker_capabilites_list_or_none(
    sosu_markers: List[Mark],
) -> Optional[List[Capabilities]]:
    caps = get_marker_unique_parameter_or_none(sosu_markers, "capabilities")
    if isinstance(caps, Capabilities):
        return [caps]
    return caps


def get_marker_unique_parameter_or_none(sosu_markers: List[Mark], key: str) -> Any:
    values = [m.kwargs.get(key) for m in sosu_markers]
    values = [v for v in values if v is not None]

    if len(values) > 1:
        raise MultipleMarkerParametersFound()

    if not values:
        return None

    return values[0]

import pytest

from pytest_sosu.utils import smart_bool, smart_bool_or_none


@pytest.mark.parametrize(
    "value,"
    "output",
    (
        (True, True),
        (False, False),
        (None, None),
        (1, True),
        (0, False),
        (-1, None),
        (1.0, True),
        (0.0, False),
        (0.5, None),
        ("t", True),
        ("f", False),
        ("?", None),
    ),
)
def test_smart_bool_or_none(value, output):
    assert smart_bool_or_none(value) == output


@pytest.mark.parametrize(
    "value,"
    "output",
    (
        (True, True),
        (False, False),
        (None, False),
        (1, True),
        (0, False),
        (-1, False),
        (1.0, True),
        (0.0, False),
        (0.5, False),
        ("t", True),
        ("f", False),
        ("?", False),
    ),
)
def test_smart_bool(value, output):
    assert smart_bool(value) == output

import pytest

from src.exceptions import ValidationError
from src.services.clinic_service import validate_name, validate_slot_minutes


@pytest.mark.parametrize("minutes, valid", [(9, False), (10, True), (30, True), (120, True), (121, False), (0, False)])
def test_slot_minutes_boundaries(minutes, valid):
    if valid:
        assert validate_slot_minutes(minutes) == minutes
    else:
        with pytest.raises(ValidationError):
            validate_slot_minutes(minutes)


@pytest.mark.parametrize("name", ["", "   ", "x" * 101])
def test_invalid_names(name):
    with pytest.raises(ValidationError):
        validate_name(name)


def test_name_is_trimmed():
    assert validate_name("  Иванов Иван  ") == "Иванов Иван"

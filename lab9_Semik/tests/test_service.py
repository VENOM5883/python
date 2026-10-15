import pytest

from exceptions import PolicyNotFoundError, ValidationError
from repository import PolicyRepository
from service import PolicyService


@pytest.fixture
def service():
    return PolicyService(PolicyRepository())


def test_find_object(service):
    created = service.create({"holder": "Петрова", "insurance_type": "property",
                              "insured_value": "1000000", "term_months": "12"})
    assert service.get(created.id).holder == "Петрова"
    assert created.insured_value == 1_000_000.0


def test_invalid_object(service):
    with pytest.raises(ValidationError):
        service.create({"holder": "", "insurance_type": "auto", "insured_value": 1, "term_months": 1})
    with pytest.raises(ValidationError):
        service.create({"holder": "X", "insurance_type": "space", "insured_value": 1, "term_months": 1})


def test_calculate_cost(service):
    policy = service.create({"holder": "X", "insurance_type": "auto",
                             "insured_value": 1_000_000, "term_months": 12})
    assert service.calculate_cost(policy.id)["cost"] == 45000.0
    young = service.calculate_cost(policy.id, driver_experience=1, claims=2)
    assert young["cost"] == round(45000 * 1.3 * 1.5, 2)


def test_missing_policy(service):
    with pytest.raises(PolicyNotFoundError):
        service.calculate_cost(99)

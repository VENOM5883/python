import pytest

from exceptions import PolicyNotFoundError
from repository import PolicyRepository

DATA = {"holder": "Иванов", "insurance_type": "auto", "insured_value": 1000.0, "term_months": 12}


def test_add_object_assigns_ids():
    repo = PolicyRepository()
    first, second = repo.add(DATA), repo.add(DATA)
    assert (first.id, second.id) == (1, 2)
    assert len(repo.get_all()) == 2


def test_delete_object():
    repo = PolicyRepository()
    policy = repo.add(DATA)
    repo.delete(policy.id)
    with pytest.raises(PolicyNotFoundError):
        repo.get(policy.id)

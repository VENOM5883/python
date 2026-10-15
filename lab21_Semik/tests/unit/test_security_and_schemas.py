from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.exceptions import AuthError
from app.schemas import OrderIn, RegisterIn
from app.security import create_token, decode_token, hash_password, verify_password


def test_password_hash_is_salted_and_verifiable():
    first, second = hash_password("secret123"), hash_password("secret123")
    assert first != second and "secret123" not in first
    assert verify_password("secret123", first) and not verify_password("wrong", first)


def test_jwt_roundtrip_and_expiry():
    assert decode_token(create_token(7, "ADMIN"))["role"] == "ADMIN"
    expired = create_token(7, "USER", now=datetime.now(timezone.utc) - timedelta(hours=5))
    with pytest.raises(AuthError, match="expired"):
        decode_token(expired)
    with pytest.raises(AuthError):
        decode_token("not.a.token")


@pytest.mark.parametrize("field, value", [("email", "no-at-sign"), ("password", "short"), ("phone", "89001234567"),
                                          ("full_name", "A")])
def test_register_validation(field, value):
    data = {"email": "a@b.ru", "password": "password123", "full_name": "Иван Иванов", "phone": "+79001234567"}
    with pytest.raises(ValidationError):
        RegisterIn(**{**data, field: value})


@pytest.mark.parametrize("items", [[], [{"product_id": 1, "quantity": 0}], [{"product_id": 1, "quantity": 51}],
                                   [{"product_id": 1, "quantity": 1}, {"product_id": 1, "quantity": 2}]])
def test_order_validation(items):
    with pytest.raises(ValidationError):
        OrderIn(items=items)

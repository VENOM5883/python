from collections.abc import Iterator

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.exceptions import AuthError, ForbiddenError
from app.models import User
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_db(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
                 db: Session = Depends(get_db)) -> User:
    if credentials is None:
        raise AuthError("Authorization header with Bearer token is required")
    payload = decode_token(credentials.credentials)
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise AuthError("User not found")
    return user


def admin_user(user: User = Depends(current_user)) -> User:
    if user.role != "ADMIN":
        raise ForbiddenError("Administrator role required")
    return user

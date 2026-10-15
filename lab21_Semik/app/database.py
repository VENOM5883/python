from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def make_engine(url: str):
    if not url.startswith("sqlite"):
        return create_engine(url, pool_pre_ping=True)
    kwargs = {"connect_args": {"check_same_thread": False}}
    if url in ("sqlite://", "sqlite:///:memory:"):
        kwargs["poolclass"] = StaticPool
    engine = create_engine(url, **kwargs)

    @event.listens_for(engine, "connect")
    def _foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys = ON")
    return engine

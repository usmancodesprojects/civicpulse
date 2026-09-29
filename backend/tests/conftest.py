from collections.abc import Generator

import fakeredis
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from app.models import Base
from app.repositories.complaints import ComplaintRepository


@pytest.fixture
def redis_client() -> fakeredis.FakeRedis:
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def repository() -> Generator[ComplaintRepository, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def add_char_length(dbapi_connection, _connection_record) -> None:
        dbapi_connection.create_function("char_length", 1, len)

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield ComplaintRepository(session)
    engine.dispose()

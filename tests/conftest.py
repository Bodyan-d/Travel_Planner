from collections.abc import Generator
from base64 import b64encode
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


def basic_auth_header(username: str = "admin", password: str = "admin") -> dict[str, str]:
    token = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return {"Authorization": f"Basic {token}"}


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@contextmanager
def override_db_dependency(db_session: Session) -> Generator[None, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    with override_db_dependency(db_session):
        with TestClient(app, headers=basic_auth_header()) as test_client:
            yield test_client


@pytest.fixture()
def unauthenticated_client(db_session: Session) -> Generator[TestClient, None, None]:
    with override_db_dependency(db_session):
        with TestClient(app) as test_client:
            yield test_client

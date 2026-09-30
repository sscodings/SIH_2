import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.db.database import Base, get_db
from app.db.models import User
from app.core.security import get_password_hash, create_access_token
from app.main import app
from app.adapters.factory import clear_custom_adapters

@pytest.fixture(scope="function")
def db_session():
    """Creates a fresh in-memory SQLite database per test with standard test users."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSessionLocal()
    try:
        # Seed standard test users
        users = [
            User(
                email="investigator@demo",
                hashed_password=get_password_hash("demo123"),
                full_name="Vikram Rathore",
                role="investigator",
                is_active=True
            ),
            User(
                email="other_io@demo",
                hashed_password=get_password_hash("demo123"),
                full_name="Rajesh Kumar (IO)",
                role="investigator",
                is_active=True
            ),
            User(
                email="supervisor@demo",
                hashed_password=get_password_hash("demo123"),
                full_name="Meera Sharma",
                role="supervisor",
                is_active=True
            ),
            User(
                email="admin@demo",
                hashed_password=get_password_hash("demo123"),
                full_name="System Admin",
                role="admin",
                is_active=True
            ),
            User(
                email="inactive@demo",
                hashed_password=get_password_hash("demo123"),
                full_name="Inactive User",
                role="investigator",
                is_active=False
            )
        ]
        db.add_all(users)
        db.commit()

        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)
        clear_custom_adapters()

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def investigator_token():
    token, _, _ = create_access_token(data={"sub": "investigator@demo", "role": "investigator", "name": "Vikram Rathore"})
    return token

@pytest.fixture
def supervisor_token():
    token, _, _ = create_access_token(data={"sub": "supervisor@demo", "role": "supervisor", "name": "Meera Sharma"})
    return token

@pytest.fixture
def admin_token():
    token, _, _ = create_access_token(data={"sub": "admin@demo", "role": "admin", "name": "System Admin"})
    return token

@pytest.fixture
def auth_client(client, admin_token):
    """Client with default Admin Authorization header."""
    client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return client

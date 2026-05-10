import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client(tmp_path):
    db_file = tmp_path / "test.db"
    TEST_DB_URL = f"sqlite:///{db_file}"
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_create_user_v1(client):
    response = client.post(
        "/users",
        headers={"X-API-Version": "1"},
        json={"full_name": "John Doe", "email": "john@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "John Doe"
    assert "first_name" not in data
    assert "last_name" not in data
    assert "display_name" not in data


def test_create_user_v2(client):
    response = client.post(
        "/users",
        headers={"X-API-Version": "2"},
        json={"first_name": "Jane", "last_name": "Smith", "email": "jane@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Smith"
    assert "full_name" not in data
    assert "display_name" not in data


def test_create_user_v3(client):
    response = client.post(
        "/users",
        headers={"X-API-Version": "3"},
        json={
            "first_name": "Alice",
            "last_name": "Johnson",
            "display_name": "AJ",
            "email": "alice@example.com",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Alice"
    assert data["last_name"] == "Johnson"
    assert data["display_name"] == "AJ"
    assert "full_name" not in data


def test_version_route_prefix(client):
    response = client.post(
        "/v1/users",
        json={"full_name": "Test User", "email": "test@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Test User"
    assert response.headers["X-API-Version"] == "1"


def test_default_latest_version(client):
    response = client.post(
        "/users",
        json={
            "first_name": "Default",
            "last_name": "User",
            "display_name": "DU",
            "email": "default@example.com",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "display_name" in data
    assert response.headers["X-API-Version"] == "3"


def test_field_mapping_v1_from_v3(client):
    create_response = client.post(
        "/users",
        headers={"X-API-Version": "3"},
        json={
            "first_name": "Mapping",
            "last_name": "Test",
            "display_name": "MT",
            "email": "mapping@example.com",
        },
    )
    user_id = create_response.json()["id"]

    response = client.get(f"/users/{user_id}", headers={"X-API-Version": "1"})
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Mapping Test"
    assert "first_name" not in data
    assert "display_name" not in data


def test_field_mapping_v3_from_v1(client):
    create_response = client.post(
        "/users",
        headers={"X-API-Version": "1"},
        json={"full_name": "Reverse Map", "email": "reverse@example.com"},
    )
    user_id = create_response.json()["id"]

    response = client.get(f"/users/{user_id}", headers={"X-API-Version": "3"})
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Reverse"
    assert data["last_name"] == "Map"
    assert data["display_name"] == "Reverse Map"


def test_deprecated_headers(client):
    response = client.post(
        "/users",
        headers={"X-API-Version": "1"},
        json={"full_name": "Deprecated User", "email": "dep@example.com"},
    )
    assert response.headers["X-Deprecated"] == "true"
    assert response.headers["X-Sunset-Date"] == "2025-12-31"


def test_v2_deprecated_headers(client):
    response = client.post(
        "/users",
        headers={"X-API-Version": "2"},
        json={"first_name": "V2", "last_name": "User", "email": "v2@example.com"},
    )
    assert response.headers["X-Deprecated"] == "true"
    assert response.headers["X-Sunset-Date"] == "2026-06-30"


def test_active_version_no_deprecation(client):
    response = client.post(
        "/users",
        headers={"X-API-Version": "3"},
        json={
            "first_name": "Active",
            "last_name": "User",
            "display_name": "AU",
            "email": "active@example.com",
        },
    )
    assert "X-Deprecated" not in response.headers
    assert "X-Sunset-Date" not in response.headers


def test_list_versions(client):
    response = client.get("/api/versions")
    assert response.status_code == 200
    data = response.json()
    assert len(data["versions"]) == 3
    versions = {v["version"]: v for v in data["versions"]}
    assert versions["1"]["status"] == "deprecated"
    assert versions["2"]["status"] == "deprecated"
    assert versions["3"]["status"] == "active"


def test_get_changelog(client):
    response = client.get("/api/versions/1/changelog")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "1"
    assert "full_name" in data["changelog"]


def test_list_users_versioned(client):
    client.post(
        "/users",
        headers={"X-API-Version": "3"},
        json={
            "first_name": "List",
            "last_name": "Test",
            "display_name": "LT",
            "email": "list@example.com",
        },
    )

    response = client.get("/users", headers={"X-API-Version": "1"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "full_name" in data[0]
    assert "first_name" not in data[0]

    response = client.get("/users", headers={"X-API-Version": "3"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "display_name" in data[0]

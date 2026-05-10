import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///./test_users.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)


class TestVersionRouting:
    def test_default_version_is_latest(self):
        resp = client.post("/users", json={
            "first_name": "Alice",
            "last_name": "Smith",
            "display_name": "Ali",
            "email": "alice@example.com",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "display_name" in data
        assert "first_name" in data
        assert "last_name" in data
        assert "full_name" not in data

    def test_version_via_header_v1(self):
        resp = client.post("/users", json={
            "full_name": "Bob Jones",
            "email": "bob@example.com",
        }, headers={"X-API-Version": "1"})
        assert resp.status_code == 201
        data = resp.json()
        assert "full_name" in data
        assert data["full_name"] == "Bob Jones"
        assert "first_name" not in data
        assert "last_name" not in data
        assert "display_name" not in data

    def test_version_via_header_v2(self):
        resp = client.post("/users", json={
            "first_name": "Carol",
            "last_name": "White",
            "email": "carol@example.com",
        }, headers={"X-API-Version": "2"})
        assert resp.status_code == 201
        data = resp.json()
        assert "first_name" in data
        assert "last_name" in data
        assert "full_name" not in data
        assert "display_name" not in data

    def test_version_via_header_v3(self):
        resp = client.post("/users", json={
            "first_name": "Dave",
            "last_name": "Brown",
            "display_name": "Davie",
            "email": "dave@example.com",
        }, headers={"X-API-Version": "3"})
        assert resp.status_code == 201
        data = resp.json()
        assert "display_name" in data
        assert data["display_name"] == "Davie"
        assert "full_name" not in data

    def test_version_via_url_prefix_v1(self):
        create_resp = client.post("/users", json={
            "first_name": "Eve",
            "last_name": "Green",
            "display_name": "Evy",
            "email": "eve@example.com",
        })
        user_id = create_resp.json()["id"]

        resp = client.get(f"/v1/users/{user_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "full_name" in data
        assert data["full_name"] == "Eve Green"

    def test_version_via_url_prefix_v2(self):
        create_resp = client.post("/users", json={
            "first_name": "Frank",
            "last_name": "Blue",
            "display_name": "Franky",
            "email": "frank@example.com",
        })
        user_id = create_resp.json()["id"]

        resp = client.get(f"/v2/users/{user_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "first_name" in data
        assert "last_name" in data
        assert "full_name" not in data
        assert "display_name" not in data


class TestFieldMapping:
    def test_v1_full_name_concatenated(self):
        create_resp = client.post("/users", json={
            "first_name": "Grace",
            "last_name": "Lee",
            "display_name": "Gracie",
            "email": "grace@example.com",
        })
        user_id = create_resp.json()["id"]

        resp = client.get(f"/users/{user_id}", headers={"X-API-Version": "1"})
        data = resp.json()
        assert data["full_name"] == "Grace Lee"
        assert data["email"] == "grace@example.com"

    def test_v2_no_display_name(self):
        create_resp = client.post("/users", json={
            "first_name": "Henry",
            "last_name": "Kim",
            "display_name": "Hank",
            "email": "henry@example.com",
        })
        user_id = create_resp.json()["id"]

        resp = client.get(f"/users/{user_id}", headers={"X-API-Version": "2"})
        data = resp.json()
        assert data["first_name"] == "Henry"
        assert data["last_name"] == "Kim"
        assert "display_name" not in data

    def test_v3_has_display_name(self):
        create_resp = client.post("/users", json={
            "first_name": "Ivy",
            "last_name": "Chen",
            "display_name": "Ives",
            "email": "ivy@example.com",
        })
        user_id = create_resp.json()["id"]

        resp = client.get(f"/users/{user_id}", headers={"X-API-Version": "3"})
        data = resp.json()
        assert data["display_name"] == "Ives"

    def test_v1_create_transforms_full_name(self):
        resp = client.post("/users", json={
            "full_name": "Jack Black",
            "email": "jack@example.com",
        }, headers={"X-API-Version": "1"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["full_name"] == "Jack Black"
        assert data["email"] == "jack@example.com"

        v3_resp = client.get(f"/users/{data['id']}", headers={"X-API-Version": "3"})
        v3_data = v3_resp.json()
        assert v3_data["first_name"] == "Jack"
        assert v3_data["last_name"] == "Black"


class TestDeprecationHeaders:
    def test_v1_has_deprecation_headers(self):
        resp = client.get("/users", headers={"X-API-Version": "1"})
        assert resp.headers.get("X-Deprecated") == "true"
        assert resp.headers.get("X-Sunset-Date") == "2025-12-31"

    def test_v2_has_deprecation_headers(self):
        resp = client.get("/users", headers={"X-API-Version": "2"})
        assert resp.headers.get("X-Deprecated") == "true"
        assert resp.headers.get("X-Sunset-Date") == "2026-06-30"

    def test_v3_no_deprecation_headers(self):
        resp = client.get("/users", headers={"X-API-Version": "3"})
        assert resp.headers.get("X-Deprecated") is None
        assert resp.headers.get("X-Sunset-Date") is None

    def test_default_no_deprecation_headers(self):
        resp = client.get("/users")
        assert resp.headers.get("X-Deprecated") is None


class TestVersionHeader:
    def test_response_contains_version_header(self):
        resp = client.get("/users", headers={"X-API-Version": "2"})
        assert resp.headers.get("X-API-Version") == "2"

    def test_default_response_contains_latest_version_header(self):
        resp = client.get("/users")
        assert resp.headers.get("X-API-Version") == "3"


class TestVersionsAPI:
    def test_list_versions(self):
        resp = client.get("/api/versions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert data[0]["version"] == 1
        assert data[0]["status"] == "deprecated"
        assert data[1]["version"] == 2
        assert data[1]["status"] == "deprecated"
        assert data[2]["version"] == 3
        assert data[2]["status"] == "active"

    def test_get_changelog(self):
        resp = client.get("/api/versions/1/changelog")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == 1
        assert len(data["changelog"]) > 0

    def test_get_changelog_not_found(self):
        resp = client.get("/api/versions/99/changelog")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data


class TestCRUD:
    def test_create_and_get_user(self):
        create_resp = client.post("/users", json={
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
        })
        assert create_resp.status_code == 201
        user_id = create_resp.json()["id"]

        get_resp = client.get(f"/users/{user_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["first_name"] == "Test"

    def test_list_users(self):
        client.post("/users", json={
            "first_name": "A",
            "last_name": "B",
            "email": "a@example.com",
        })
        client.post("/users", json={
            "first_name": "C",
            "last_name": "D",
            "email": "c@example.com",
        })
        resp = client.get("/users")
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_update_user(self):
        create_resp = client.post("/users", json={
            "first_name": "Old",
            "last_name": "Name",
            "email": "old@example.com",
        })
        user_id = create_resp.json()["id"]

        update_resp = client.put(f"/users/{user_id}", json={
            "first_name": "New",
        })
        assert update_resp.status_code == 200
        assert update_resp.json()["first_name"] == "New"

    def test_update_user_v1_full_name(self):
        create_resp = client.post("/users", json={
            "first_name": "OldFirst",
            "last_name": "OldLast",
            "email": "upv1@example.com",
        })
        user_id = create_resp.json()["id"]

        update_resp = client.put(f"/users/{user_id}", json={
            "full_name": "NewFirst NewLast",
        }, headers={"X-API-Version": "1"})
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["full_name"] == "NewFirst NewLast"

    def test_delete_user(self):
        create_resp = client.post("/users", json={
            "first_name": "Del",
            "last_name": "Me",
            "email": "del@example.com",
        })
        user_id = create_resp.json()["id"]

        del_resp = client.delete(f"/users/{user_id}")
        assert del_resp.status_code == 200

        get_resp = client.get(f"/users/{user_id}")
        assert get_resp.status_code == 404

    def test_get_nonexistent_user(self):
        resp = client.get("/users/9999")
        assert resp.status_code == 404

import pytest


class TestVersionRouting:
    def test_default_version_is_latest(self, client):
        response = client.get("/api/versions")
        versions = response.json()["versions"]
        latest = [v for v in versions if v["is_latest"]][0]
        assert latest["version"] == 3

    def test_version_from_url_prefix(self, client):
        response = client.get("/v1/users")
        assert response.headers["X-API-Version"] == "1"

    def test_version_from_header(self, client):
        response = client.get("/users", headers={"X-API-Version": "2"})
        assert response.headers["X-API-Version"] == "2"

    def test_url_prefix_takes_precedence_over_header(self, client):
        response = client.get("/v1/users", headers={"X-API-Version": "2"})
        assert response.headers["X-API-Version"] == "1"

    def test_no_version_uses_latest(self, client):
        response = client.get("/users")
        assert response.headers["X-API-Version"] == "3"


class TestDeprecatedHeaders:
    def test_deprecated_version_has_deprecated_header(self, client):
        response = client.get("/v1/users")
        assert response.headers["X-Deprecated"] == "true"
        assert "X-Sunset-Date" in response.headers

    def test_v2_is_deprecated(self, client):
        response = client.get("/v2/users")
        assert response.headers["X-Deprecated"] == "true"

    def test_v3_is_not_deprecated(self, client):
        response = client.get("/v3/users")
        assert "X-Deprecated" not in response.headers


class TestVersionInfoAPI:
    def test_list_versions(self, client):
        response = client.get("/api/versions")
        assert response.status_code == 200
        versions = response.json()["versions"]
        assert len(versions) == 3
        assert versions[0]["version"] == 1
        assert versions[1]["version"] == 2
        assert versions[2]["version"] == 3

    def test_get_changelog_v1(self, client):
        response = client.get("/api/versions/1/changelog")
        assert response.status_code == 200
        assert "changelog" in response.json()

    def test_get_changelog_v2(self, client):
        response = client.get("/api/versions/2/changelog")
        assert response.status_code == 200
        changelog = response.json()["changelog"]
        assert any("Split" in item for item in changelog)

    def test_get_changelog_not_found(self, client):
        response = client.get("/api/versions/99/changelog")
        assert response.status_code == 404

import pytest


class TestCreateUserV1:
    def test_create_user_v1_full_name(self, client):
        response = client.post(
            "/v1/users",
            json={"full_name": "张 三"}
        )
        assert response.status_code == 201
        data = response.json()
        assert "full_name" in data
        assert data["full_name"] == "张 三"
        assert "first_name" not in data
        assert "last_name" not in data

    def test_create_user_v1_response_structure(self, client):
        response = client.post(
            "/v1/users",
            json={"full_name": "李 四"}
        )
        data = response.json()
        assert set(data.keys()) == {"id", "full_name"}


class TestCreateUserV2:
    def test_create_user_v2_split_names(self, client):
        response = client.post(
            "/v2/users",
            json={"first_name": "王", "last_name": "五"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "王"
        assert data["last_name"] == "五"
        assert "full_name" not in data

    def test_create_user_v2_response_structure(self, client):
        response = client.post(
            "/v2/users",
            json={"first_name": "赵", "last_name": "六"}
        )
        data = response.json()
        assert set(data.keys()) == {"id", "first_name", "last_name"}


class TestCreateUserV3:
    def test_create_user_v3_with_display_name(self, client):
        response = client.post(
            "/v3/users",
            json={"first_name": "钱", "last_name": "七", "display_name": "钱同学"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "钱"
        assert data["last_name"] == "七"
        assert data["display_name"] == "钱同学"

    def test_create_user_v3_response_structure(self, client):
        response = client.post(
            "/v3/users",
            json={"first_name": "孙", "last_name": "八", "display_name": "小孙"}
        )
        data = response.json()
        assert set(data.keys()) == {"id", "first_name", "last_name", "display_name"}


class TestCrossVersionAccess:
    def test_create_v1_read_v3(self, client):
        create_response = client.post(
            "/v1/users",
            json={"full_name": "周 九"}
        )
        user_id = create_response.json()["id"]

        read_response = client.get(f"/v3/users/{user_id}")
        data = read_response.json()
        assert data["first_name"] == "周"
        assert data["last_name"] == "九"
        assert "display_name" in data

    def test_create_v3_read_v1(self, client):
        create_response = client.post(
            "/v3/users",
            json={"first_name": "吴", "last_name": "十", "display_name": "老吴"}
        )
        user_id = create_response.json()["id"]

        read_response = client.get(f"/v1/users/{user_id}")
        data = read_response.json()
        assert data["full_name"] == "吴 十"
        assert "first_name" not in data

    def test_create_v3_read_v2(self, client):
        create_response = client.post(
            "/v3/users",
            json={"first_name": "郑", "last_name": "十一", "display_name": "小郑"}
        )
        user_id = create_response.json()["id"]

        read_response = client.get(f"/v2/users/{user_id}")
        data = read_response.json()
        assert data["first_name"] == "郑"
        assert data["last_name"] == "十一"
        assert "display_name" not in data


class TestListUsersCrossVersion:
    def test_list_v1_users(self, client):
        client.post("/v3/users", json={"first_name": "A", "last_name": "B", "display_name": "AB"})
        client.post("/v3/users", json={"first_name": "C", "last_name": "D", "display_name": "CD"})

        response = client.get("/v1/users")
        users = response.json()
        assert len(users) == 2
        for user in users:
            assert "full_name" in user
            assert "first_name" not in user

    def test_list_v3_users(self, client):
        client.post("/v1/users", json={"full_name": "E F"})

        response = client.get("/v3/users")
        users = response.json()
        assert len(users) == 1
        assert "display_name" in users[0]


class TestUpdateUser:
    def test_update_v1_read_v3(self, client):
        create_response = client.post(
            "/v1/users",
            json={"full_name": "Old Name"}
        )
        user_id = create_response.json()["id"]

        client.put(
            f"/v3/users/{user_id}",
            json={"first_name": "New", "last_name": "Name", "display_name": "Updated"}
        )

        read_response = client.get(f"/v3/users/{user_id}")
        assert read_response.json()["display_name"] == "Updated"


class TestDeleteUser:
    def test_delete_user(self, client):
        create_response = client.post(
            "/v1/users",
            json={"full_name": "To Delete"}
        )
        user_id = create_response.json()["id"]

        delete_response = client.delete(f"/v3/users/{user_id}")
        assert delete_response.status_code == 204

        get_response = client.get(f"/v1/users/{user_id}")
        assert get_response.status_code == 404

import pytest
from app.version_config import (
    transform_response,
    transform_create_input,
    transform_update_input,
    LATEST_VERSION,
    get_version_def,
)


class TestTransformResponse:
    def test_v3_passthrough(self):
        data = {
            "id": 1,
            "first_name": "Alice",
            "last_name": "Smith",
            "display_name": "Ali",
            "email": "alice@example.com",
        }
        result = transform_response(data, 3)
        assert result == data

    def test_v2_omits_display_name(self):
        data = {
            "id": 1,
            "first_name": "Alice",
            "last_name": "Smith",
            "display_name": "Ali",
            "email": "alice@example.com",
        }
        result = transform_response(data, 2)
        assert "first_name" in result
        assert "last_name" in result
        assert "display_name" not in result
        assert result["first_name"] == "Alice"

    def test_v1_concatenates_full_name(self):
        data = {
            "id": 1,
            "first_name": "Alice",
            "last_name": "Smith",
            "display_name": "Ali",
            "email": "alice@example.com",
        }
        result = transform_response(data, 1)
        assert result["full_name"] == "Alice Smith"
        assert "first_name" not in result
        assert "last_name" not in result
        assert "display_name" not in result
        assert result["email"] == "alice@example.com"

    def test_v1_handles_single_name(self):
        data = {
            "id": 2,
            "first_name": "Madonna",
            "last_name": "",
            "display_name": "Madonna",
            "email": "madonna@example.com",
        }
        result = transform_response(data, 1)
        assert result["full_name"] == "Madonna "


class TestTransformCreateInput:
    def test_v1_splits_full_name(self):
        data = {"full_name": "Bob Jones", "email": "bob@example.com"}
        result = transform_create_input(data, 1)
        assert result["first_name"] == "Bob"
        assert result["last_name"] == "Jones"
        assert result["display_name"] == "Bob Jones"
        assert "full_name" not in result

    def test_v2_adds_display_name(self):
        data = {"first_name": "Carol", "last_name": "White", "email": "carol@example.com"}
        result = transform_create_input(data, 2)
        assert result["display_name"] == "Carol White"

    def test_v3_passthrough(self):
        data = {
            "first_name": "Dave",
            "last_name": "Brown",
            "display_name": "Davie",
            "email": "dave@example.com",
        }
        result = transform_create_input(data, 3)
        assert result == data


class TestTransformUpdateInput:
    def test_v1_splits_full_name(self):
        data = {"full_name": "NewFirst NewLast"}
        result = transform_update_input(data, 1)
        assert result["first_name"] == "NewFirst"
        assert result["last_name"] == "NewLast"
        assert "full_name" not in result

    def test_v3_passthrough(self):
        data = {"first_name": "Updated"}
        result = transform_update_input(data, 3)
        assert result == data


class TestVersionDef:
    def test_deprecated_version(self):
        vd = get_version_def(1)
        assert vd.is_deprecated is True
        assert vd.is_sunset is False
        assert vd.sunset_date == "2025-12-31"

    def test_active_version(self):
        vd = get_version_def(3)
        assert vd.is_deprecated is False
        assert vd.is_sunset is False

    def test_latest_version(self):
        assert LATEST_VERSION == 3

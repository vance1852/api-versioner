from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class FieldMapping:
    target_field: str
    source_fields: List[str]
    transform: Optional[Callable] = None
    removed: bool = False
    added: bool = False


@dataclass
class VersionDef:
    version: int
    status: str
    sunset_date: Optional[str] = None
    changelog: List[str] = field(default_factory=list)
    field_mappings: Dict[str, FieldMapping] = field(default_factory=dict)

    @property
    def is_deprecated(self) -> bool:
        return self.status == "deprecated"

    @property
    def is_sunset(self) -> bool:
        return self.status == "sunset"


VERSIONS: Dict[int, VersionDef] = {
    1: VersionDef(
        version=1,
        status="deprecated",
        sunset_date="2025-12-31",
        changelog=[
            "Initial version",
            "User response contains: id, full_name, email",
        ],
        field_mappings={
            "id": FieldMapping(target_field="id", source_fields=["id"]),
            "full_name": FieldMapping(
                target_field="full_name",
                source_fields=["first_name", "last_name"],
                transform=lambda data: f"{data['first_name']} {data['last_name']}",
            ),
            "email": FieldMapping(target_field="email", source_fields=["email"]),
        },
    ),
    2: VersionDef(
        version=2,
        status="deprecated",
        sunset_date="2026-06-30",
        changelog=[
            "Split full_name into first_name and last_name",
            "User response contains: id, first_name, last_name, email",
        ],
        field_mappings={
            "id": FieldMapping(target_field="id", source_fields=["id"]),
            "first_name": FieldMapping(
                target_field="first_name", source_fields=["first_name"]
            ),
            "last_name": FieldMapping(
                target_field="last_name", source_fields=["last_name"]
            ),
            "email": FieldMapping(target_field="email", source_fields=["email"]),
        },
    ),
    3: VersionDef(
        version=3,
        status="active",
        changelog=[
            "Added display_name field",
            "User response contains: id, first_name, last_name, display_name, email",
        ],
        field_mappings={
            "id": FieldMapping(target_field="id", source_fields=["id"]),
            "first_name": FieldMapping(
                target_field="first_name", source_fields=["first_name"]
            ),
            "last_name": FieldMapping(
                target_field="last_name", source_fields=["last_name"]
            ),
            "display_name": FieldMapping(
                target_field="display_name", source_fields=["display_name"]
            ),
            "email": FieldMapping(target_field="email", source_fields=["email"]),
        },
    ),
}

LATEST_VERSION = max(VERSIONS.keys())
SUPPORTED_VERSIONS = sorted(VERSIONS.keys())


def get_version_def(version: int) -> Optional[VersionDef]:
    return VERSIONS.get(version)


def transform_response(data: Dict[str, Any], target_version: int) -> Dict[str, Any]:
    version_def = get_version_def(target_version)
    if not version_def:
        return data

    result = {}
    for output_field, mapping in version_def.field_mappings.items():
        if mapping.transform:
            try:
                result[output_field] = mapping.transform(data)
            except (KeyError, TypeError):
                result[output_field] = None
        else:
            result[output_field] = data.get(mapping.source_fields[0])

    return result


def transform_create_input(data: Dict[str, Any], source_version: int) -> Dict[str, Any]:
    if source_version == LATEST_VERSION:
        return data

    result = dict(data)

    if source_version == 1:
        full_name = result.pop("full_name", "")
        parts = full_name.split(" ", 1)
        result["first_name"] = parts[0] if len(parts) > 0 else ""
        result["last_name"] = parts[1] if len(parts) > 1 else ""
        if "display_name" not in result:
            result["display_name"] = full_name

    elif source_version == 2:
        if "display_name" not in result:
            fn = result.get("first_name", "")
            ln = result.get("last_name", "")
            result["display_name"] = f"{fn} {ln}".strip()

    return result


def transform_update_input(data: Dict[str, Any], source_version: int) -> Dict[str, Any]:
    if source_version == LATEST_VERSION:
        return data

    result = dict(data)

    if source_version == 1:
        full_name = result.pop("full_name", None)
        if full_name is not None:
            parts = full_name.split(" ", 1)
            result["first_name"] = parts[0] if len(parts) > 0 else ""
            result["last_name"] = parts[1] if len(parts) > 1 else ""

    return result
